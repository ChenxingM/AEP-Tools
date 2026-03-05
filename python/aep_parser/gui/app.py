"""Main application window."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QMainWindow, QMessageBox, QProgressDialog,
    QSplitter, QStatusBar, QTabWidget,
)

from aep_tools import Project as ToolsProject
from .widgets import CompWidget, ProjectPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AEP Viewer")
        self.resize(1400, 850)
        self.setAcceptDrops(True)

        self._project_data: dict | None = None
        self._tools_project: ToolsProject | None = None
        self._source_path: Path | None = None
        self._comp_tab_map: dict[int, int] = {}

        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        self.project_panel = ProjectPanel()
        self.project_panel.setMinimumWidth(250)
        self.project_panel.setMaximumWidth(450)
        self.project_panel.comp_selected.connect(self._switch_to_comp)
        splitter.addWidget(self.project_panel)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        splitter.addWidget(self.tab_widget)

        splitter.setSizes([300, 1100])

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("  Open an AEP/AEPX file to begin")

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")

        open_action = QAction("Open AEP/AEPX...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        open_json_action = QAction("Open parsed JSON...", self)
        open_json_action.triggered.connect(self._open_json)
        file_menu.addAction(open_json_action)

        file_menu.addSeparator()

        export_action = QAction("Export JSON...", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self._export_json)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")

        expand_action = QAction("Expand All Layers", self)
        expand_action.setShortcut("Ctrl+E")
        expand_action.triggered.connect(self._expand_all)
        view_menu.addAction(expand_action)

        collapse_action = QAction("Collapse All", self)
        collapse_action.setShortcut("Ctrl+Shift+E")
        collapse_action.triggered.connect(self._collapse_all)
        view_menu.addAction(collapse_action)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open AEP/AEPX File", "",
            "After Effects Project (*.aep *.aepx);;All Files (*)")
        if path:
            self._load_file(Path(path))

    def _open_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Parsed JSON", "",
            "JSON Files (*.json);;All Files (*)")
        if path:
            self._load_json(Path(path))

    def _load_file(self, path: Path):
        progress = QProgressDialog(f"Loading {path.name}...", None, 0, 3, self)
        progress.setWindowTitle("AEP Viewer")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        QApplication.processEvents()

        try:
            progress.setLabelText("Parsing...")
            progress.setValue(1)
            QApplication.processEvents()

            self._tools_project = ToolsProject.open(path)
            self._source_path = path

            progress.setLabelText("Building UI...")
            progress.setValue(2)
            QApplication.processEvents()

            self._project_data = self._tools_project._model.to_dict()
            self._display_project(path.name)
            progress.setValue(3)
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "Parse Error", f"Failed to parse:\n{e}")

    def _load_json(self, path: Path):
        self.setCursor(Qt.WaitCursor)
        try:
            self._tools_project = None
            self._source_path = None
            self._project_data = json.loads(path.read_text(encoding="utf-8"))
            self._display_project(path.name)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load JSON:\n{e}")
        finally:
            self.unsetCursor()

    def _display_project(self, filename: str):
        data = self._project_data
        if not data:
            return

        self.setWindowTitle(f"AEP Viewer \u2014 {filename}")
        self.tab_widget.clear()
        self._comp_tab_map.clear()

        self.project_panel.load_project(data)

        assets = data.get("assets", {})
        comps = data.get("compositions", [])
        for comp in comps:
            widget = CompWidget(comp, assets=assets)
            widget.precomp_requested.connect(self._switch_to_comp)
            name = comp.get("name", f"Comp {comp.get('id', '?')}")
            idx = self.tab_widget.addTab(widget, name)
            self._comp_tab_map[comp.get("id", 0)] = idx

        n_comps = len(comps)
        n_assets = len(data.get("assets", {}))
        n_effects = len(data.get("effects", {}))
        n_rq = len(data.get("renderQueue", []))
        total_layers = sum(len(c.get("layers", [])) for c in comps)
        parts = [
            f"  {filename}",
            f"{n_comps} compositions",
            f"{total_layers} layers",
            f"{n_assets} assets",
            f"{n_effects} effects",
        ]
        if n_rq:
            parts.append(f"{n_rq} render queue items")
        self.status.showMessage("  |  ".join(parts))

    def _switch_to_comp(self, comp_id: int):
        idx = self._comp_tab_map.get(comp_id)
        if idx is not None:
            self.tab_widget.setCurrentIndex(idx)

    def _export_json(self):
        if not self._project_data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if path:
            text = json.dumps(self._project_data, indent=2, ensure_ascii=False, default=str)
            Path(path).write_text(text, encoding="utf-8")
            self.status.showMessage(f"  Exported to {path}")

    def _expand_all(self):
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, CompWidget):
            widget.tree.expandAll()

    def _collapse_all(self):
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, CompWidget):
            widget.tree.collapseAll()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith((".aep", ".aepx", ".json")):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".json":
                self._load_json(path)
            elif path.suffix.lower() in (".aep", ".aepx"):
                self._load_file(path)
            break
