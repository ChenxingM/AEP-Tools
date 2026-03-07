"""AEP Diff — Main application window."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QLabel, QMainWindow, QMessageBox, QProgressDialog,
    QSplitter, QStatusBar,
)

from aep_tools import Project as ToolsProject
from .diff_engine import DiffSummary, compute_summary, diff_projects, export_diff_json
from .diff_widgets import DiffTreeWidget, SummaryPanel


class DiffMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEP Diff")
        self.resize(1400, 850)
        self.setAcceptDrops(True)

        self._dict_a: dict | None = None
        self._dict_b: dict | None = None
        self._path_a: str | None = None
        self._path_b: str | None = None
        self._drop_count = 0  # for alternating A/B on window-level drop

        self._setup_ui()
        self._setup_menu()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        self._summary = SummaryPanel()
        self._summary.setMinimumWidth(240)
        self._summary.setMaximumWidth(400)
        self._summary.filter_changed.connect(self._on_filter_changed)
        self._summary.file_a.file_loaded.connect(self._on_file_a)
        self._summary.file_b.file_loaded.connect(self._on_file_b)
        splitter.addWidget(self._summary)

        self._tree = DiffTreeWidget()
        splitter.addWidget(self._tree)

        splitter.setSizes([280, 1120])

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet(
            "QStatusBar { background-color: #007acc; color: #ffffff; font-size: 12px; }"
            "QStatusBar QLabel { background: transparent; color: #ffffff; }"
        )
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("  Open two AEP/AEPX files to compare")
        self._status_bar.addPermanentWidget(self._status_label, 1)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        open_a = QAction("Open File A...", self)
        open_a.setShortcut("Ctrl+1")
        open_a.triggered.connect(lambda: self._summary.file_a._browse())
        file_menu.addAction(open_a)

        open_b = QAction("Open File B...", self)
        open_b.setShortcut("Ctrl+2")
        open_b.triggered.connect(lambda: self._summary.file_b._browse())
        file_menu.addAction(open_b)

        file_menu.addSeparator()

        export_prompt = QAction("Export Diff + Prompt...", self)
        export_prompt.setShortcut("Ctrl+S")
        export_prompt.triggered.connect(lambda: self._export_diff(include_prompt=True))
        file_menu.addAction(export_prompt)

        export_json = QAction("Export Diff JSON...", self)
        export_json.setShortcut("Ctrl+Shift+S")
        export_json.triggered.connect(lambda: self._export_diff(include_prompt=False))
        file_menu.addAction(export_json)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")

        expand_all = QAction("Expand All", self)
        expand_all.setShortcut("Ctrl+E")
        expand_all.triggered.connect(self._tree.expandAll)
        view_menu.addAction(expand_all)

        collapse_all = QAction("Collapse All", self)
        collapse_all.setShortcut("Ctrl+Shift+E")
        collapse_all.triggered.connect(self._tree.collapseAll)
        view_menu.addAction(collapse_all)

    # ------------------------------------------------------------------ Loading

    def _on_file_a(self, path: str):
        self._load_file("A", path)

    def _on_file_b(self, path: str):
        self._load_file("B", path)

    def _load_file(self, side: str, path: str):
        progress = QProgressDialog(f"Loading {Path(path).name}...", None, 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        try:
            proj = ToolsProject.open(path)
            d = proj._model.to_dict()
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Error", f"Failed to load {path}:\n{e}")
            return

        progress.close()

        # Summarize
        comps = d.get("compositions", [])
        total_layers = sum(len(c.get("layers", [])) for c in comps)
        info = f"{len(comps)} comps, {total_layers} layers"

        if side == "A":
            self._dict_a = d
            self._path_a = path
            self._summary.file_a.set_info(info)
        else:
            self._dict_b = d
            self._path_b = path
            self._summary.file_b.set_info(info)

        self._try_diff()

    def _try_diff(self):
        if self._dict_a is None or self._dict_b is None:
            return

        root = diff_projects(self._dict_a, self._dict_b)
        summary = compute_summary(root)

        self._summary.update_stats(summary)
        self._tree.load_diff(root, hide_unchanged=self._summary.hide_unchanged)

        # Status bar
        name_a = Path(self._path_a).name if self._path_a else "?"
        name_b = Path(self._path_b).name if self._path_b else "?"
        self._status_label.setText(
            f"  {name_a} vs {name_b}  |  "
            f"+{summary.added}  -{summary.removed}  "
            f"~{summary.modified}  ={summary.unchanged}"
        )

        # Store for re-filter
        self._last_root = root

    def _on_filter_changed(self):
        if hasattr(self, "_last_root"):
            self._tree.load_diff(
                self._last_root, hide_unchanged=self._summary.hide_unchanged)

    # ------------------------------------------------------------------ Export

    def _export_diff(self, include_prompt: bool):
        if not hasattr(self, "_last_root"):
            QMessageBox.information(self, "Export", "No diff to export yet.")
            return

        ext = "Text Files (*.txt)" if include_prompt else "JSON Files (*.json)"
        suffix = ".txt" if include_prompt else ".json"
        default_name = "diff_prompt" + suffix if include_prompt else "diff" + suffix

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Diff", default_name, f"{ext};;All Files (*)")
        if not path:
            return

        name_a = Path(self._path_a).name if self._path_a else "File A"
        name_b = Path(self._path_b).name if self._path_b else "File B"
        summary = compute_summary(self._last_root)

        export_diff_json(
            self._last_root, summary,
            name_a=name_a, name_b=name_b,
            path=path, include_prompt=include_prompt,
        )
        self._status_bar.showMessage(f"Exported to {path}", 5000)

    # ------------------------------------------------------------------ Drag & Drop (window level)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                p = url.toLocalFile().lower()
                if p.endswith(".aep") or p.endswith(".aepx"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith((".aep", ".aepx")):
                if self._drop_count % 2 == 0:
                    self._summary.file_a.set_file(p)
                else:
                    self._summary.file_b.set_file(p)
                self._drop_count += 1
                return

    # ------------------------------------------------------------------ CLI support

    def load_paths(self, path_a: str | None, path_b: str | None):
        """Programmatic loading from CLI arguments."""
        if path_a:
            self._summary.file_a.set_file(path_a)
        if path_b:
            self._summary.file_b.set_file(path_b)
