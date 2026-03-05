"""GUI widgets: CompWidget, ProjectPanel, KeyframeDelegate, tree builders."""

from __future__ import annotations

from PySide6.QtCore import Qt, QRect, QSize, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon
from PySide6.QtWidgets import (
    QHeaderView, QInputDialog, QLabel, QMenu, QStyle, QStyledItemDelegate,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .theme import (
    ROLE_KEYFRAMES, ROLE_NODE_TYPE, ROLE_ASSET_ID, ROLE_LAYER_ID, ROLE_MATCH_PATH,
    COLOR_ACCENT, COLOR_KF, COLOR_KF_HOLD, COLOR_TEXT, COLOR_TEXT_ANIM, COLOR_TEXT_DIM,
    LAYER_TYPE_LABELS, ADBE_NAMES,
    fmt_val, get_color_swatch, get_keyframes, resolve_layer_visual_type,
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
                     comp_in: float, comp_out: float,
                     assets: dict | None = None):
    """Populate tree widget with layers and their property hierarchies."""
    if assets is None:
        assets = {}
    for i, layer in enumerate(layers, 1):
        layer_item = QTreeWidgetItem()
        name = layer.get("name", "(unnamed)")
        ltype = resolve_layer_visual_type(layer, assets)
        label, color = LAYER_TYPE_LABELS.get(ltype, ("?", "#cccccc"))

        layer_item.setText(0, name)
        layer_item.setText(1, str(i))
        layer_item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        layer_item.setData(0, ROLE_NODE_TYPE, "layer")
        layer_item.setData(0, ROLE_LAYER_ID, layer.get("id"))
        if ltype == "precomp":
            layer_item.setData(0, ROLE_ASSET_ID, layer.get("assetId"))

        in_t = layer.get("inTime", 0)
        out_t = layer.get("outTime", 0)
        layer_item.setText(2, f"[{label}]  {in_t:.2f} \u2192 {out_t:.2f}s")

        font = QFont()
        font.setBold(True)
        layer_item.setFont(0, font)
        layer_item.setFont(1, font)
        layer_item.setForeground(0, QColor(color))
        layer_item.setForeground(2, COLOR_TEXT_DIM)

        flags = layer.get("flags", {})
        if not flags.get("visible", True):
            layer_item.setForeground(0, QColor("#555555"))

        props = layer.get("properties", {})
        if isinstance(props, dict) and "properties" in props:
            _build_props(layer_item, props["properties"], comp_in, comp_out, [])

        tree.addTopLevelItem(layer_item)
        layer_item.setExpanded(False)


def _build_props(parent: QTreeWidgetItem, props: list[dict],
                 comp_in: float, comp_out: float,
                 match_path: list[str] | None = None):
    """Recursively build property tree items."""
    if match_path is None:
        match_path = []
    for p in props:
        mn = p.get("matchName", "")
        val = p.get("value")

        cur_path = match_path + [mn] if mn else match_path
        item = QTreeWidgetItem()
        display = _display_name(mn, val)
        item.setText(0, display)
        item.setToolTip(0, mn)

        if val is None:
            item.setData(0, ROLE_NODE_TYPE, "property")
            item.setData(0, ROLE_MATCH_PATH, cur_path)
            item.setForeground(0, COLOR_TEXT_DIM)
            parent.addChild(item)
            continue

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
                _build_props(item, val["properties"], comp_in, comp_out, cur_path)

            # EffectInstance
            elif "parameters" in val and "name" in val:
                item.setData(0, ROLE_NODE_TYPE, "effect")
                item.setText(0, val.get("name", display))
                item.setForeground(0, QColor("#dcdcaa"))
                params = val["parameters"]
                if isinstance(params, dict) and "properties" in params:
                    _build_props(item, params["properties"], comp_in, comp_out,
                                 cur_path)

            # TextProperty
            elif "fonts" in val and "documents" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                item.setData(0, ROLE_MATCH_PATH, cur_path)
                item.setText(2, fmt_val(val))
                kfs = get_keyframes(val.get("documents", {}))
                if kfs:
                    item.setData(3, ROLE_KEYFRAMES, kfs)
                    item.setForeground(0, COLOR_TEXT_ANIM)

            # MaskData
            elif "mode" in val and "index" in val:
                item.setData(0, ROLE_NODE_TYPE, "mask")
                item.setText(0, f"{display} [{val.get('mode', 'add')}]")
                item.setForeground(0, QColor("#b5cea8"))
                mask_props = val.get("properties")
                if isinstance(mask_props, dict) and "properties" in mask_props:
                    _build_props(item, mask_props["properties"], comp_in, comp_out,
                                 cur_path)

            # AnimatedProperty
            elif "type" in val and "animated" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                item.setData(0, ROLE_MATCH_PATH, cur_path)
                static_val = val.get("value")
                item.setText(2, fmt_val(static_val))

                swatch = get_color_swatch(static_val)
                if swatch:
                    item.setBackground(2, swatch)
                    lum = swatch.red() * 0.299 + swatch.green() * 0.587 + swatch.blue() * 0.114
                    item.setForeground(2, QColor("#000000" if lum > 128 else "#ffffff"))

                kfs = get_keyframes(val)
                if kfs:
                    item.setData(3, ROLE_KEYFRAMES, kfs)
                    item.setForeground(0, COLOR_TEXT_ANIM)
                    item.setText(2, fmt_val(static_val) or f"\u25c6 {len(kfs)} keys")
                else:
                    item.setForeground(0, COLOR_TEXT)

                if val.get("expression"):
                    item.setText(0, f"{item.text(0)}  \u2261")

            # Empty PropertyGroup (has 'key' but no 'properties')
            elif "key" in val:
                item.setData(0, ROLE_NODE_TYPE, "group")
                item.setForeground(0, COLOR_TEXT_DIM)

            else:
                item.setText(2, fmt_val(val))
        else:
            item.setText(2, fmt_val(val))

        parent.addChild(item)


def _parse_value_text(text: str) -> list[float] | float | None:
    """Parse a user-entered value string into a number or list of numbers."""
    text = text.strip()
    if not text:
        return None
    # Tuple form: (x, y) or (x, y, z)
    if text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        try:
            return [float(v.strip()) for v in inner.split(",")]
        except ValueError:
            return None
    # Single number
    try:
        return float(text)
    except ValueError:
        return None


# -- Composition Widget --

class CompWidget(QWidget):
    """Widget showing a single composition's layers and properties."""

    precomp_requested = Signal(int)

    def __init__(self, comp: dict, parent=None, *,
                 assets: dict | None = None, tools_project=None):
        super().__init__(parent)
        self.comp = comp
        self._assets = assets or {}
        self._tools_project = tools_project
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
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Layer", "#", "Value", "Keyframes"])
        self.tree.setTextElideMode(Qt.ElideNone)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)

        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.resizeSection(0, 400)
        header.resizeSection(1, 36)
        header.resizeSection(2, 220)
        header.setMinimumSectionSize(36)

        kf_delegate = KeyframeDelegate(self.tree)
        kf_delegate.set_time_range(in_t, out_t)
        self.tree.setItemDelegateForColumn(3, kf_delegate)

        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        build_layer_tree(self.tree, c.get("layers", []), in_t, out_t,
                         assets=self._assets)
        layout.addWidget(self.tree)

    @property
    def _writable(self) -> bool:
        return self._tools_project is not None and self._tools_project.writable

    def _on_double_click(self, item: QTreeWidgetItem, col: int):
        """Double-click navigates into pre-comps only."""
        asset_id = item.data(0, ROLE_ASSET_ID)
        if asset_id is not None:
            self.precomp_requested.emit(asset_id)

    def _on_context_menu(self, pos: QPoint):
        item = self.tree.itemAt(pos)
        if item is None:
            return

        menu = QMenu(self.tree)
        node_type = item.data(0, ROLE_NODE_TYPE)

        # Layer rename
        if node_type == "layer" and self._writable:
            menu.addAction("Rename Layer", lambda: self._rename_layer(item))

        # Property value edit
        match_path = item.data(0, ROLE_MATCH_PATH)
        if match_path and self._writable:
            menu.addAction("Edit Value", lambda: self._edit_property(item))

        # Pre-comp navigation
        asset_id = item.data(0, ROLE_ASSET_ID)
        if asset_id is not None:
            menu.addAction("Open Pre-comp",
                           lambda: self.precomp_requested.emit(asset_id))

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _rename_layer(self, item: QTreeWidgetItem):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(
            self, "Rename Layer", "Layer name:", text=old_name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        self.tree.blockSignals(True)
        item.setText(0, new_name)
        self.tree.blockSignals(False)
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_name(comp_id, layer_id, new_name)

    def _edit_property(self, item: QTreeWidgetItem):
        match_path = item.data(0, ROLE_MATCH_PATH)
        if not match_path:
            return
        old_text = item.text(2)
        new_text, ok = QInputDialog.getText(
            self, "Edit Value", f"{item.text(0)}:", text=old_text)
        if not ok:
            return
        new_value = _parse_value_text(new_text)
        if new_value is None:
            return
        # Walk up to find the layer item
        layer_item = item
        while layer_item and layer_item.data(0, ROLE_NODE_TYPE) != "layer":
            layer_item = layer_item.parent()
        if not layer_item:
            return
        layer_id = layer_item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        self.tree.blockSignals(True)
        item.setText(2, new_text)
        self.tree.blockSignals(False)
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_property_value(
                comp_id, layer_id, match_path, new_value)


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
