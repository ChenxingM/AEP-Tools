"""GUI widgets: CompWidget, ProjectPanel, KeyframeDelegate, tree builders."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon
from PySide6.QtWidgets import (
    QHeaderView, QLabel, QStyle, QStyledItemDelegate,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .theme import (
    ROLE_KEYFRAMES, ROLE_NODE_TYPE,
    COLOR_ACCENT, COLOR_KF, COLOR_KF_HOLD, COLOR_TEXT, COLOR_TEXT_ANIM, COLOR_TEXT_DIM,
    LAYER_TYPE_LABELS, ADBE_NAMES,
    fmt_val, get_color_swatch, get_keyframes,
)


# -- Keyframe Timeline Delegate --

class KeyframeDelegate(QStyledItemDelegate):
    """Custom delegate that draws a mini timeline with keyframe diamonds."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.comp_in = 0.0
        self.comp_out = 1.0

    def set_time_range(self, in_time: float, out_time: float):
        self.comp_in = in_time
        self.comp_out = out_time if out_time > in_time else in_time + 1.0

    def paint(self, painter: QPainter, option, index):
        kfs = index.data(ROLE_KEYFRAMES)
        if not kfs:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect
        margin_x, margin_y = 8, 4
        bar_rect = QRect(rect.x() + margin_x, rect.y() + margin_y,
                         rect.width() - margin_x * 2,
                         rect.height() - margin_y * 2)

        if option.state & QStyle.State_Selected:
            painter.fillRect(rect, COLOR_ACCENT)
        else:
            painter.fillRect(rect, QColor("#1e1e1e"))

        bar_y = bar_rect.center().y()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#3c3c3c")))
        painter.drawRect(bar_rect.x(), bar_y, bar_rect.width(), 2)

        duration = max(self.comp_out - self.comp_in, 1.0)
        diamond_size = 4

        for kf in kfs:
            t = kf.get("time", 0)
            frac = max(0.0, min(1.0, (t - self.comp_in) / duration))
            cx = bar_rect.x() + int(frac * bar_rect.width())
            cy = bar_y + 1
            color = COLOR_KF_HOLD if kf.get("transitionType") == "hold" else COLOR_KF
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            poly = QPolygon([
                QPoint(cx, cy - diamond_size), QPoint(cx + diamond_size, cy),
                QPoint(cx, cy + diamond_size), QPoint(cx - diamond_size, cy),
            ])
            painter.drawPolygon(poly)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(200, option.rect.height() if option.rect.height() > 0 else 22)


# -- Tree Building --

def _display_name(match_name: str, value: dict | None = None) -> str:
    """Get human-readable name for a match name."""
    base = ADBE_NAMES.get(match_name, match_name)
    if match_name == "ADBE Vector Group" and isinstance(value, dict):
        name = value.get("name")
        if name:
            base = name
    return base


def build_layer_tree(tree: QTreeWidget, layers: list[dict],
                     comp_in: float, comp_out: float):
    """Populate tree widget with layers and their property hierarchies."""
    for i, layer in enumerate(layers, 1):
        layer_item = QTreeWidgetItem()
        name = layer.get("name", "(unnamed)")
        ltype = layer.get("type", "asset")
        label, color = LAYER_TYPE_LABELS.get(ltype, ("?", "#cccccc"))

        layer_item.setText(0, f"{i}  {name}")
        layer_item.setData(0, ROLE_NODE_TYPE, "layer")

        in_t = layer.get("inTime", 0)
        out_t = layer.get("outTime", 0)
        layer_item.setText(1, f"[{label}]  {in_t:.2f} \u2192 {out_t:.2f}s")

        font = QFont()
        font.setBold(True)
        layer_item.setFont(0, font)
        layer_item.setForeground(0, QColor(color))
        layer_item.setForeground(1, COLOR_TEXT_DIM)

        flags = layer.get("flags", {})
        if not flags.get("visible", True):
            layer_item.setForeground(0, QColor("#555555"))

        props = layer.get("properties", {})
        if isinstance(props, dict) and "properties" in props:
            _build_props(layer_item, props["properties"], comp_in, comp_out)

        tree.addTopLevelItem(layer_item)
        layer_item.setExpanded(False)


def _build_props(parent: QTreeWidgetItem, props: list[dict],
                 comp_in: float, comp_out: float):
    """Recursively build property tree items."""
    for p in props:
        mn = p.get("matchName", "")
        val = p.get("value")
        if val is None:
            continue

        item = QTreeWidgetItem()
        display = _display_name(mn, val)
        item.setText(0, display)
        item.setToolTip(0, mn)

        if isinstance(val, dict):
            # PropertyGroup
            if "properties" in val and isinstance(val["properties"], list):
                item.setData(0, ROLE_NODE_TYPE, "group")
                enabled = val.get("enabled")
                if enabled is not None:
                    tag = "ON" if enabled else "OFF"
                    color = QColor("#4ec9b0") if enabled else QColor("#555555")
                    item.setText(0, f"{display}  [{tag}]")
                    item.setForeground(0, color)
                else:
                    item.setForeground(0, COLOR_TEXT)
                _build_props(item, val["properties"], comp_in, comp_out)

            # EffectInstance
            elif "parameters" in val and "name" in val:
                item.setData(0, ROLE_NODE_TYPE, "effect")
                item.setText(0, val.get("name", display))
                item.setForeground(0, QColor("#dcdcaa"))
                params = val["parameters"]
                if isinstance(params, dict) and "properties" in params:
                    _build_props(item, params["properties"], comp_in, comp_out)

            # TextProperty
            elif "fonts" in val and "documents" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                item.setText(1, fmt_val(val))
                kfs = get_keyframes(val.get("documents", {}))
                if kfs:
                    item.setData(2, ROLE_KEYFRAMES, kfs)
                    item.setForeground(0, COLOR_TEXT_ANIM)

            # MaskData
            elif "mode" in val and "index" in val:
                item.setData(0, ROLE_NODE_TYPE, "mask")
                item.setText(0, f"{display} [{val.get('mode', 'add')}]")
                item.setForeground(0, QColor("#b5cea8"))
                mask_props = val.get("properties")
                if isinstance(mask_props, dict) and "properties" in mask_props:
                    _build_props(item, mask_props["properties"], comp_in, comp_out)

            # AnimatedProperty
            elif "type" in val and "animated" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                static_val = val.get("value")
                item.setText(1, fmt_val(static_val))

                swatch = get_color_swatch(static_val)
                if swatch:
                    item.setBackground(1, swatch)
                    lum = swatch.red() * 0.299 + swatch.green() * 0.587 + swatch.blue() * 0.114
                    item.setForeground(1, QColor("#000000" if lum > 128 else "#ffffff"))

                kfs = get_keyframes(val)
                if kfs:
                    item.setData(2, ROLE_KEYFRAMES, kfs)
                    item.setForeground(0, COLOR_TEXT_ANIM)
                    item.setText(1, fmt_val(static_val) or f"\u25c6 {len(kfs)} keys")
                else:
                    item.setForeground(0, COLOR_TEXT)

                if val.get("expression"):
                    item.setText(0, f"{item.text(0)}  \u2261")

            else:
                item.setText(1, fmt_val(val))
        else:
            item.setText(1, fmt_val(val))

        parent.addChild(item)


# -- Composition Widget --

class CompWidget(QWidget):
    """Widget showing a single composition's layers and properties."""

    def __init__(self, comp: dict, parent=None):
        super().__init__(parent)
        self.comp = comp
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        c = self.comp
        fps = c.get("framerate", 0)
        w, h = c.get("width", 0), c.get("height", 0)
        dur = c.get("duration", 0)
        in_t = c.get("inTime", 0)
        out_t = c.get("outTime", 0)
        n_layers = len(c.get("layers", []))

        info = QLabel(
            f"  {w}\u00d7{h}  |  {fps:g} fps  |  "
            f"Duration: {dur:.2f}s  |  Work Area: {in_t:.2f} \u2013 {out_t:.2f}s  |  "
            f"{n_layers} layers"
        )
        info.setObjectName("comp_info")
        info.setFixedHeight(32)
        layout.addWidget(info)

        self.tree = QTreeWidget()
        self.tree.setAlternatingRowColors(True)
        self.tree.setIndentation(18)
        self.tree.setAnimated(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Property", "Value", "Keyframes"])
        self.tree.setTextElideMode(Qt.ElideNone)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)

        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.resizeSection(0, 400)
        header.resizeSection(1, 220)
        header.setMinimumSectionSize(80)

        kf_delegate = KeyframeDelegate(self.tree)
        kf_delegate.set_time_range(in_t, out_t)
        self.tree.setItemDelegateForColumn(2, kf_delegate)

        build_layer_tree(self.tree, c.get("layers", []), in_t, out_t)
        layout.addWidget(self.tree)


# -- Project Panel --

class ProjectPanel(QWidget):
    """Left sidebar showing project structure."""

    comp_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("PROJECT")
        title.setObjectName("section_title")
        layout.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.setAnimated(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setTextElideMode(Qt.ElideNone)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setStretchLastSection(False)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, stretch=1)

        self.rq_label = QLabel("RENDER QUEUE")
        self.rq_label.setObjectName("section_title")
        layout.addWidget(self.rq_label)

        self.rq_tree = QTreeWidget()
        self.rq_tree.setHeaderHidden(True)
        self.rq_tree.setIndentation(16)
        self.rq_tree.setMaximumHeight(250)
        self.rq_tree.setTextElideMode(Qt.ElideNone)
        self.rq_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.rq_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.rq_tree.header().setStretchLastSection(False)
        self.rq_tree.itemDoubleClicked.connect(self._on_rq_double_click)
        layout.addWidget(self.rq_tree)

        self.effects_label = QLabel("EFFECTS")
        self.effects_label.setObjectName("section_title")
        layout.addWidget(self.effects_label)

        self.effects_tree = QTreeWidget()
        self.effects_tree.setHeaderHidden(True)
        self.effects_tree.setIndentation(16)
        self.effects_tree.setMaximumHeight(200)
        layout.addWidget(self.effects_tree)

    def load_project(self, data: dict):
        self.tree.clear()
        self.rq_tree.clear()
        self.effects_tree.clear()

        folder = data.get("folder", {})
        self._build_folder(self.tree.invisibleRootItem(), folder)
        self.tree.expandAll()

        # Render Queue
        rq_items = data.get("renderQueue", [])
        if rq_items:
            self.rq_label.show()
            self.rq_tree.show()
            for rq in rq_items:
                self._build_rq_item(rq)
        else:
            self.rq_label.hide()
            self.rq_tree.hide()

        # Effects
        for mn, edef in data.get("effects", {}).items():
            name = edef.get("name", mn)
            item = QTreeWidgetItem([name])
            item.setToolTip(0, mn)
            item.setForeground(0, QColor("#dcdcaa"))
            for param in edef.get("parameters", []):
                pname = param.get("name", param.get("matchName", "?"))
                ptype = param.get("type", "?")
                child = QTreeWidgetItem([f"{pname} (type {ptype})"])
                child.setForeground(0, COLOR_TEXT_DIM)
                item.addChild(child)
            self.effects_tree.addTopLevelItem(item)

    def _build_rq_item(self, rq: dict):
        comp_name = rq.get("compName", f"Comp #{rq.get('compId', '?')}")
        status = rq.get("status", "?")
        status_color = {"queued": "#4ec9b0", "done": "#4ec9b0",
                        "rendering": "#e8a624"}.get(status, "#808080")

        label_parts = [f"\U0001f3ac {comp_name}"]
        start = rq.get("startFrame")
        end = rq.get("endFrame")
        if start is not None:
            if start == end:
                label_parts.append(f"  [frame {start}]")
            else:
                label_parts.append(f"  [frame {start}\u2013{end}]")
        label_parts.append(f"  ({status})")
        item = QTreeWidgetItem(["".join(label_parts)])
        item.setForeground(0, QColor(status_color))
        item.setData(0, Qt.UserRole, rq.get("compId"))

        rs = rq.get("renderSettings", "")
        if rs:
            rs_node = QTreeWidgetItem([f"Settings: {rs}"])
            rs_node.setForeground(0, COLOR_TEXT_DIM)
            item.addChild(rs_node)

        for om in rq.get("outputModules", []):
            fmt_label = om.get("formatLabel", om.get("format", "?"))
            tpl = om.get("templateName", "")
            label = f"\u25b6 {fmt_label}"
            if tpl:
                label += f"  [{tpl}]"
            om_node = QTreeWidgetItem([label])
            om_node.setForeground(0, QColor("#9cdcfe"))

            w, h = om.get("width", 0), om.get("height", 0)
            if w and h:
                size_node = QTreeWidgetItem([f"Size: {w}\u00d7{h}"])
                size_node.setForeground(0, COLOR_TEXT_DIM)
                om_node.addChild(size_node)

            file_tpl = om.get("fileTemplate", "")
            if file_tpl:
                file_node = QTreeWidgetItem([f"File: {file_tpl}"])
                file_node.setForeground(0, COLOR_TEXT_DIM)
                om_node.addChild(file_node)

            out_path = om.get("outputPath", "")
            if out_path:
                path_node = QTreeWidgetItem([f"Path: {out_path}"])
                path_node.setForeground(0, COLOR_TEXT_DIM)
                om_node.addChild(path_node)

            item.addChild(om_node)

        self.rq_tree.addTopLevelItem(item)
        item.setExpanded(True)

    def _build_folder(self, parent_item, folder: dict):
        for item in folder.get("items", []):
            if "items" in item:
                name = item.get("name", "(folder)")
                node = QTreeWidgetItem([f"\U0001f4c1 {name}"])
                node.setForeground(0, QColor("#cccccc"))
                self._build_folder(node, item)
                parent_item.addChild(node)
            elif "layers" in item:
                name = item.get("name", "(comp)")
                w, h = item.get("width", 0), item.get("height", 0)
                node = QTreeWidgetItem([f"\U0001f3ac {name}  ({w}\u00d7{h})"])
                node.setForeground(0, QColor("#4ec9b0"))
                node.setData(0, Qt.UserRole, item.get("id", 0))
                parent_item.addChild(node)
            elif item.get("type") == "image":
                name = item.get("name", "(image)")
                w, h = item.get("width", 0), item.get("height", 0)
                suffix = f"  ({w}\u00d7{h})" if w and h else ""
                node = QTreeWidgetItem([f"\U0001f5bc {name}{suffix}"])
                node.setForeground(0, QColor("#808080"))
                parent_item.addChild(node)
            elif item.get("type") == "solid":
                name = item.get("name", "(solid)")
                node = QTreeWidgetItem([f"\u25a0 {name}"])
                c = item.get("color", {})
                r, g, b = int(c.get("r", 0)), int(c.get("g", 0)), int(c.get("b", 0))
                node.setForeground(0, QColor(r, g, b) if (r + g + b) > 100 else QColor("#808080"))
                parent_item.addChild(node)

    def _on_double_click(self, item: QTreeWidgetItem, col: int):
        comp_id = item.data(0, Qt.UserRole)
        if comp_id is not None:
            self.comp_selected.emit(comp_id)

    def _on_rq_double_click(self, item: QTreeWidgetItem, col: int):
        while item.parent() is not None:
            item = item.parent()
        comp_id = item.data(0, Qt.UserRole)
        if comp_id is not None:
            self.comp_selected.emit(comp_id)
