"""GUI widgets for the AEP Diff tool."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .diff_engine import DiffNode, DiffStatus, DiffSummary, compute_summary
from .theme import (
    COLOR_DIFF_ADDED, COLOR_DIFF_MODIFIED, COLOR_DIFF_REMOVED, COLOR_TEXT_DIM,
    fmt_val,
)


# ---------------------------------------------------------------------------
# FileDropWidget
# ---------------------------------------------------------------------------

class FileDropWidget(QWidget):
    """Accepts drag-drop of .aep/.aepx files or a Browse button."""

    file_loaded = Signal(str)  # emits file path

    def __init__(self, title: str = "File", parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._title = title
        self._path: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._title_label = QLabel(f"<b>{title}</b>")
        layout.addWidget(self._title_label)

        self._file_label = QLabel("No file loaded")
        self._file_label.setStyleSheet("color: #808080; font-size: 12px;")
        self._file_label.setWordWrap(True)
        layout.addWidget(self._file_label)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #9cdcfe; font-size: 11px;")
        layout.addWidget(self._info_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        layout.addWidget(browse_btn)

        self.setStyleSheet(
            "FileDropWidget { border: 1px dashed #555; border-radius: 4px; }"
        )

    @property
    def path(self) -> str | None:
        return self._path

    def set_file(self, path: str, info: str = ""):
        self._path = path
        name = Path(path).name
        self._file_label.setText(name)
        self._file_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        self._info_label.setText(info)
        self.file_loaded.emit(path)

    def set_info(self, info: str):
        self._info_label.setText(info)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self._title}",
            "", "AEP Files (*.aep *.aepx);;All Files (*)")
        if path:
            self.set_file(path)

    # -- Drag & Drop --

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
                self.set_file(p)
                return


# ---------------------------------------------------------------------------
# SummaryPanel
# ---------------------------------------------------------------------------

class SummaryPanel(QWidget):
    """Left sidebar: two FileDropWidgets + stats + filter checkbox."""

    filter_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.file_a = FileDropWidget("File A")
        layout.addWidget(self.file_a)

        self.file_b = FileDropWidget("File B")
        layout.addWidget(self.file_b)

        # Stats area
        self._stats_label = QLabel("")
        self._stats_label.setTextFormat(Qt.RichText)
        self._stats_label.setStyleSheet("padding: 8px; font-size: 13px;")
        layout.addWidget(self._stats_label)

        # Filter
        self._hide_unchanged = QCheckBox("Hide unchanged")
        self._hide_unchanged.setChecked(True)
        self._hide_unchanged.toggled.connect(self.filter_changed.emit)
        layout.addWidget(self._hide_unchanged)

        layout.addStretch()

    @property
    def hide_unchanged(self) -> bool:
        return self._hide_unchanged.isChecked()

    def update_stats(self, summary: DiffSummary):
        parts = [
            f'<span style="color:#4ec9b0;">+{summary.added}</span>',
            f'<span style="color:#e05050;">-{summary.removed}</span>',
            f'<span style="color:#e8a624;">~{summary.modified}</span>',
            f'<span style="color:#808080;">={summary.unchanged}</span>',
        ]
        self._stats_label.setText("  ".join(parts))

    def clear_stats(self):
        self._stats_label.setText("")


# ---------------------------------------------------------------------------
# DiffTreeWidget
# ---------------------------------------------------------------------------

_STATUS_LABELS = {
    DiffStatus.ADDED: "ADDED",
    DiffStatus.REMOVED: "REMOVED",
    DiffStatus.MODIFIED: "MODIFIED",
    DiffStatus.UNCHANGED: "",
}

_STATUS_COLORS = {
    DiffStatus.ADDED: COLOR_DIFF_ADDED,
    DiffStatus.REMOVED: COLOR_DIFF_REMOVED,
    DiffStatus.MODIFIED: COLOR_DIFF_MODIFIED,
    DiffStatus.UNCHANGED: COLOR_TEXT_DIM,
}


class DiffTreeWidget(QTreeWidget):
    """4-column tree showing the diff result with color coding."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setHeaderLabels(["Name", "Status", "Value A", "Value B"])
        self.setColumnCount(4)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setUniformRowHeights(True)
        header = self.header()
        header.setStretchLastSection(True)
        header.resizeSection(0, 280)
        header.resizeSection(1, 90)
        header.resizeSection(2, 200)
        header.resizeSection(3, 200)

    def load_diff(self, root: DiffNode, hide_unchanged: bool = True):
        """Populate tree from a DiffNode root."""
        self.clear()
        for child in root.children:
            self._build_item(self.invisibleRootItem(), child, hide_unchanged)
        # Auto-expand nodes with changes (first two levels)
        self._auto_expand(self.invisibleRootItem(), depth=0, max_depth=3)

    def _build_item(self, parent: QTreeWidgetItem, node: DiffNode,
                    hide_unchanged: bool) -> QTreeWidgetItem | None:
        # Skip unchanged nodes when filter is on
        if hide_unchanged and not node.has_changes:
            return None

        item = QTreeWidgetItem(parent)
        item.setText(0, node.label)
        item.setText(1, _STATUS_LABELS.get(node.status, ""))

        # Value columns
        val_a_str = self._format_value(node.value_a) if node.value_a is not None else ""
        val_b_str = self._format_value(node.value_b) if node.value_b is not None else ""

        if node.status is DiffStatus.MODIFIED and not node.children:
            item.setText(2, val_a_str)
            item.setText(3, val_b_str)
        elif node.status is DiffStatus.ADDED and not node.children:
            item.setText(3, val_b_str)
        elif node.status is DiffStatus.REMOVED and not node.children:
            item.setText(2, val_a_str)

        # Color coding
        color = _STATUS_COLORS.get(node.status, COLOR_TEXT_DIM)
        for col in range(4):
            item.setForeground(col, color)

        # Bold for container nodes
        if node.children:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        # Build children
        for child in node.children:
            self._build_item(item, child, hide_unchanged)

        # Remove empty container nodes (all children hidden)
        if hide_unchanged and node.children and item.childCount() == 0:
            idx = parent.indexOfChild(item)
            if idx >= 0:
                parent.takeChild(idx)
            return None

        return item

    def _auto_expand(self, parent: QTreeWidgetItem, depth: int, max_depth: int):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.childCount() > 0 and depth < max_depth:
                child.setExpanded(True)
                self._auto_expand(child, depth + 1, max_depth)

    @staticmethod
    def _format_value(v) -> str:
        if v is None:
            return ""
        return fmt_val(v)
