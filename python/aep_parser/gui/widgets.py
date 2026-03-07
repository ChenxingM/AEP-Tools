"""GUI widgets: CompWidget, ProjectPanel, KeyframeDelegate, tree builders."""

from __future__ import annotations

import re

from PySide6.QtCore import Qt, QRect, QSize, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPolygon
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHeaderView, QInputDialog,
    QLabel, QLineEdit, QMenu, QStyle, QStyledItemDelegate,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .theme import (
    ROLE_KEYFRAMES, ROLE_NODE_TYPE, ROLE_ASSET_ID, ROLE_LAYER_ID, ROLE_MATCH_PATH,
    ROLE_KEY_INDEX, ROLE_KEY_DATA,
    COLOR_ACCENT, COLOR_KF, COLOR_KF_HOLD, COLOR_TEXT, COLOR_TEXT_ANIM, COLOR_TEXT_DIM,
    LAYER_TYPE_LABELS, ADBE_NAMES,
    fmt_val, get_color_swatch, get_keyframes, resolve_layer_visual_type,
)


# -- Constants for display --

# camelCase string (from to_dict) → display name
_BLEND_MODE_NAMES: dict[str, str] = {
    "normal": "Normal", "dissolve": "Dissolve",
    "add": "Add", "multiply": "Multiply", "screen": "Screen",
    "overlay": "Overlay", "softLight": "Soft Light", "hardLight": "Hard Light",
    "darken": "Darken", "lighten": "Lighten",
    "classicDifference": "Classic Difference",
    "hue": "Hue", "saturation": "Saturation", "color": "Color",
    "luminosity": "Luminosity",
    "stencilAlpha": "Stencil Alpha", "stencilLuma": "Stencil Luma",
    "silhouetteAlpha": "Silhouette Alpha", "silhouetteLuma": "Silhouette Luma",
    "luminescentPremul": "Luminescent Premul", "alphaAdd": "Alpha Add",
    "classicColorDodge": "Classic Color Dodge",
    "classicColorBurn": "Classic Color Burn",
    "exclusion": "Exclusion", "difference": "Difference",
    "colorDodge": "Color Dodge", "colorBurn": "Color Burn",
    "linearDodge": "Linear Dodge", "linearBurn": "Linear Burn",
    "linearLight": "Linear Light", "vividLight": "Vivid Light",
    "pinLight": "Pin Light", "hardMix": "Hard Mix",
    "lighterColor": "Lighter Color", "darkerColor": "Darker Color",
    "subtract": "Subtract", "divide": "Divide",
}

# int (from writer API) → display name
_BLEND_MODE_INT_NAMES: dict[int, str] = {
    2: "Normal", 3: "Dissolve",
    4: "Add", 5: "Multiply", 6: "Screen",
    7: "Overlay", 8: "Soft Light", 9: "Hard Light",
    10: "Darken", 11: "Lighten", 12: "Classic Difference",
    13: "Hue", 14: "Saturation", 15: "Color", 16: "Luminosity",
    17: "Stencil Alpha", 18: "Stencil Luma",
    19: "Silhouette Alpha", 20: "Silhouette Luma",
    21: "Luminescent Premul", 22: "Alpha Add",
    23: "Classic Color Dodge", 24: "Classic Color Burn",
    25: "Exclusion", 26: "Difference",
    27: "Color Dodge", 28: "Color Burn",
    29: "Linear Dodge", 30: "Linear Burn",
    31: "Linear Light", 32: "Vivid Light", 33: "Pin Light", 34: "Hard Mix",
    35: "Lighter Color", 36: "Darker Color",
    37: "Subtract", 38: "Divide",
}


def _flag_tags(flags: dict) -> str:
    """Return short tags for active non-default layer flags."""
    tags = []
    if not flags.get("visible", True):
        tags.append("Hidden")
    if flags.get("solo"):
        tags.append("Solo")
    if flags.get("shy"):
        tags.append("Shy")
    if flags.get("locked"):
        tags.append("Lock")
    if flags.get("threedimensional"):
        tags.append("3D")
    if flags.get("is_guide"):
        tags.append("Guide")
    if flags.get("is_adjustment"):
        tags.append("Adj")
    if flags.get("is_null"):
        tags.append("Null")
    if flags.get("continuously_rasterize"):
        tags.append("CR")
    if flags.get("motion_blur_enabled"):
        tags.append("MB")
    return " ".join(tags)


def _dim_labels(match_path: list[str] | None, n: int) -> list[str]:
    """Return per-dimension labels for a multi-value property edit dialog."""
    last = match_path[-1] if match_path else ""
    if "Color" in last or "Colour" in last:
        return ["R", "G", "B", "A"][:n]
    if n <= 3:
        return ["X", "Y", "Z"][:n]
    return [str(i + 1) for i in range(n)]


# -- Multi-value Edit Dialog --

class _MultiValueDialog(QDialog):
    """Dialog with separate input fields per dimension."""

    def __init__(self, title: str, labels: list[str],
                 values: list[float], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QFormLayout(self)
        self.edits: list[QLineEdit] = []
        for label, value in zip(labels, values):
            edit = QLineEdit(str(value))
            layout.addRow(f"{label}:", edit)
            self.edits.append(edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_values(self) -> list[float] | None:
        try:
            return [float(e.text()) for e in self.edits]
        except ValueError:
            return None


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
#
# Column layout:
#   0: "#"          (index — tree column with expand/collapse arrows)
#   1: "Name"       (layer / property / keyframe names)
#   2: "Value"      (property values, layer info)
#   3: "Keyframes"  (timeline delegate)
#
# Custom role data is always stored on column 0 (metadata).

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

        # Column 0: index
        layer_item.setText(0, str(i))
        layer_item.setTextAlignment(0, Qt.AlignRight | Qt.AlignVCenter)

        # Column 1: name
        layer_item.setText(1, name)

        # Column 2: attributes (blend mode + flags)
        flags = layer.get("flags", {})
        blend_mode = layer.get("blendMode", "")
        blend_name = _BLEND_MODE_NAMES.get(blend_mode, "") if blend_mode else ""
        ftags = _flag_tags(flags)

        attr_parts = []
        if blend_name and blend_name != "Normal":
            attr_parts.append(blend_name)
        if ftags:
            attr_parts.append(ftags)
        layer_item.setText(2, "  ".join(attr_parts))

        # Column 3: type + timing
        in_t = layer.get("inTime", 0)
        out_t = layer.get("outTime", 0)
        layer_item.setText(3, f"[{label}]  {in_t:.2f} \u2192 {out_t:.2f}s")

        # Data roles on column 0
        layer_item.setData(0, ROLE_NODE_TYPE, "layer")
        layer_item.setData(0, ROLE_LAYER_ID, layer.get("id"))
        if ltype == "precomp":
            layer_item.setData(0, ROLE_ASSET_ID, layer.get("assetId"))

        # Fonts & colors
        font = QFont()
        font.setBold(True)
        layer_item.setFont(0, font)
        layer_item.setFont(1, font)
        layer_item.setForeground(1, QColor(color))
        layer_item.setForeground(2, COLOR_TEXT_DIM)
        layer_item.setForeground(3, COLOR_TEXT_DIM)

        if not flags.get("visible", True):
            layer_item.setForeground(1, QColor("#555555"))

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
        item.setText(1, display)
        item.setToolTip(1, mn)

        if val is None:
            item.setData(0, ROLE_NODE_TYPE, "property")
            item.setData(0, ROLE_MATCH_PATH, cur_path)
            item.setForeground(1, COLOR_TEXT_DIM)
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
                    item.setText(1, f"{display}  [{tag}]")
                    item.setForeground(1, color)
                else:
                    item.setForeground(1, COLOR_TEXT)
                _build_props(item, val["properties"], comp_in, comp_out, cur_path)

            # EffectInstance
            elif "parameters" in val and "name" in val:
                item.setData(0, ROLE_NODE_TYPE, "effect")
                item.setText(1, val.get("name", display))
                item.setForeground(1, QColor("#dcdcaa"))
                params = val["parameters"]
                if isinstance(params, dict) and "properties" in params:
                    _build_props(item, params["properties"], comp_in, comp_out,
                                 cur_path)

            # TextProperty
            elif "fonts" in val and "documents" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                item.setData(0, ROLE_MATCH_PATH, cur_path)
                item.setText(3, fmt_val(val))
                kfs = get_keyframes(val.get("documents", {}))
                if kfs:
                    item.setData(4, ROLE_KEYFRAMES, kfs)
                    item.setForeground(1, COLOR_TEXT_ANIM)

            # MaskData
            elif "mode" in val and "index" in val:
                item.setData(0, ROLE_NODE_TYPE, "mask")
                item.setText(1, f"{display} [{val.get('mode', 'add')}]")
                item.setForeground(1, QColor("#b5cea8"))
                mask_props = val.get("properties")
                if isinstance(mask_props, dict) and "properties" in mask_props:
                    _build_props(item, mask_props["properties"], comp_in, comp_out,
                                 cur_path)

            # AnimatedProperty
            elif "type" in val and "animated" in val:
                item.setData(0, ROLE_NODE_TYPE, "property")
                item.setData(0, ROLE_MATCH_PATH, cur_path)
                static_val = val.get("value")
                item.setText(3, fmt_val(static_val))

                swatch = get_color_swatch(static_val)
                if swatch:
                    item.setBackground(3, swatch)
                    lum = swatch.red() * 0.299 + swatch.green() * 0.587 + swatch.blue() * 0.114
                    item.setForeground(3, QColor("#000000" if lum > 128 else "#ffffff"))

                kfs = get_keyframes(val)
                if kfs:
                    item.setData(4, ROLE_KEYFRAMES, kfs)
                    item.setForeground(1, COLOR_TEXT_ANIM)
                    item.setText(3, fmt_val(static_val) or f"\u25c6 {len(kfs)} keys")
                    _build_keyframe_children(item, kfs)
                else:
                    item.setForeground(1, COLOR_TEXT)

                if val.get("expression"):
                    item.setText(1, f"{item.text(1)}  \u2261")

            # Empty PropertyGroup (has 'key' but no 'properties')
            elif "key" in val:
                item.setData(0, ROLE_NODE_TYPE, "group")
                item.setForeground(1, COLOR_TEXT_DIM)

            else:
                item.setText(3, fmt_val(val))
        else:
            item.setText(3, fmt_val(val))

        parent.addChild(item)


def _fmt_interp(trans: str, bezier_mode: str = "normal") -> str:
    if trans == "bezier" and bezier_mode != "normal":
        return f"bezier ({bezier_mode})"
    return trans


def _build_keyframe_children(parent: QTreeWidgetItem, kfs: list[dict]):
    """Add child items for each keyframe showing time, type, value, and easing."""
    for i, kf in enumerate(kfs, 1):
        time = kf.get("time", 0)
        value = kf.get("value")
        out_trans = kf.get("transitionType", "linear")
        bezier_mode = kf.get("bezierMode", "normal")

        # In interpolation = previous keyframe's transitionType
        if i > 1:
            prev = kfs[i - 2]
            in_trans = prev.get("transitionType", "linear")
            in_bm = prev.get("bezierMode", "normal")
            in_str = _fmt_interp(in_trans, in_bm)
        else:
            in_str = None

        out_str = _fmt_interp(out_trans, bezier_mode)

        # Header: keyframe index + time + in/out types
        label = f"\u25c6 Key {i}"
        if in_str is not None:
            interp_text = f"in:{in_str} out:{out_str}"
        else:
            interp_text = f"out:{out_str}"

        kf_item = QTreeWidgetItem()
        kf_item.setText(1, label)
        kf_item.setText(3, f"t={time:.3f}s  [{interp_text}]  {fmt_val(value)}")
        color = COLOR_KF_HOLD if out_trans == "hold" else COLOR_KF
        kf_item.setForeground(1, color)
        kf_item.setForeground(3, COLOR_TEXT_DIM)
        kf_item.setData(0, ROLE_NODE_TYPE, "keyframe")
        kf_item.setData(0, ROLE_KEY_INDEX, i)
        kf_item.setData(0, ROLE_KEY_DATA, kf)

        # Temporal ease
        in_speed = kf.get("inSpeed")
        in_influence = kf.get("inInfluence")
        out_speed = kf.get("outSpeed")
        out_influence = kf.get("outInfluence")
        if in_speed or out_speed:
            ease_parts = []
            if in_speed:
                pairs = [f"({s:g}, {inf:g}%)"
                         for s, inf in zip(in_speed, in_influence or [0] * len(in_speed))]
                ease_parts.append(f"In: {' '.join(pairs)}")
            if out_speed:
                pairs = [f"({s:g}, {inf:g}%)"
                         for s, inf in zip(out_speed, out_influence or [0] * len(out_speed))]
                ease_parts.append(f"Out: {' '.join(pairs)}")
            ease_item = QTreeWidgetItem()
            ease_item.setText(1, "Temporal Ease")
            ease_item.setText(3, "  |  ".join(ease_parts))
            ease_item.setForeground(1, COLOR_TEXT_DIM)
            ease_item.setForeground(3, COLOR_TEXT_DIM)
            kf_item.addChild(ease_item)

        # Spatial tangents
        in_tan = kf.get("inTangent")
        out_tan = kf.get("outTangent")
        if in_tan or out_tan:
            tan_item = QTreeWidgetItem()
            tan_item.setText(1, "Spatial Tangent")
            parts = []
            if in_tan:
                parts.append(f"In: {fmt_val(in_tan)}")
            if out_tan:
                parts.append(f"Out: {fmt_val(out_tan)}")
            tan_item.setText(3, "  |  ".join(parts))
            tan_item.setForeground(1, COLOR_TEXT_DIM)
            tan_item.setForeground(3, COLOR_TEXT_DIM)
            kf_item.addChild(tan_item)

        # Roving
        if kf.get("roving"):
            rov_item = QTreeWidgetItem()
            rov_item.setText(1, "Roving")
            rov_item.setText(3, "Yes")
            rov_item.setForeground(1, COLOR_TEXT_DIM)
            rov_item.setForeground(3, COLOR_TEXT_DIM)
            kf_item.addChild(rov_item)

        parent.addChild(kf_item)


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


def _parse_old_value(text: str) -> list[float] | float | None:
    """Parse a displayed value text back into float(s)."""
    text = text.strip()
    if not text:
        return None
    if text.startswith("(") and text.endswith(")"):
        inner = text[1:-1]
        try:
            return [float(v.strip()) for v in inner.split(",")]
        except ValueError:
            return None
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
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["#", "Name", "Attributes", "Value", "Keyframes"])
        self.tree.setTextElideMode(Qt.ElideNone)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)

        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.resizeSection(0, 50)
        header.resizeSection(1, 300)
        header.resizeSection(2, 160)
        header.resizeSection(3, 180)
        header.setMinimumSectionSize(36)

        kf_delegate = KeyframeDelegate(self.tree)
        kf_delegate.set_time_range(in_t, out_t)
        self.tree.setItemDelegateForColumn(4, kf_delegate)

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
            # Layer flags
            flags_menu = menu.addMenu("Flags")
            for flag_label, flag_key in [
                ("Visible", "visible"), ("Solo", "solo"), ("Shy", "shy"),
                ("Locked", "locked"), ("3D Layer", "threedimensional"),
                ("Guide Layer", "is_guide"), ("Adjustment Layer", "is_adjustment"),
                ("Null Layer", "is_null"), ("Collapse Transformation", "continuously_rasterize"),
                ("Motion Blur", "motion_blur_enabled"), ("Effects Enabled", "effects_enabled"),
                ("Auto-Orient", "auto_orient"), ("Bicubic Sampling", "bicubic_sampling"),
                ("Frame Blending", "frame_blending"),
                ("Frame Blending Type (Pixel Motion)", "frame_blending_type"),
                ("Audio Enabled", "audio_enabled"),
                ("Environment Layer", "environment_layer"),
            ]:
                act = flags_menu.addAction(flag_label)
                act.setCheckable(True)
                act.setChecked(self._get_layer_flag(item, flag_key))
                act.triggered.connect(
                    lambda checked, k=flag_key: self._toggle_layer_flag(item, k, checked))
            # Preserve Transparency (separate API)
            pt_act = menu.addAction("Preserve Transparency")
            pt_act.setCheckable(True)
            pt_act.setChecked(self._get_layer_flag(item, "preserve_transparency"))
            pt_act.triggered.connect(
                lambda checked: self._toggle_preserve_transparency(item, checked))
            # Light Type (only for light layers)
            layer_id = item.data(0, ROLE_LAYER_ID)
            layer_type = None
            for layer in self.comp.get("layers", []):
                if layer.get("id") == layer_id:
                    layer_type = layer.get("type")
                    break
            if layer_type == "light":
                light_menu = menu.addMenu("Light Type")
                for lname, lval in [("Parallel", 0), ("Spot", 1),
                                     ("Point", 2), ("Ambient", 3)]:
                    light_menu.addAction(
                        lname, lambda v=lval: self._set_layer_light_type(item, v))
            # Label
            label_menu = menu.addMenu("Label")
            for idx, lbl in enumerate(
                ["None", "Red", "Yellow", "Aqua", "Pink", "Lavender",
                 "Peach", "Sea Foam", "Blue", "Green", "Purple",
                 "Orange", "Brown", "Fuchsia", "Cyan", "Tan", "Dark Green"]):
                label_menu.addAction(lbl, lambda i=idx: self._set_layer_label(item, i))
            # Blend mode
            blend_menu = menu.addMenu("Blend Mode")
            for bname, bval in [
                ("Normal", 2), ("Dissolve", 3),
                ("Add", 4), ("Multiply", 5), ("Screen", 6),
                ("Overlay", 7), ("Soft Light", 8), ("Hard Light", 9),
                ("Darken", 10), ("Lighten", 11),
                ("Classic Difference", 12),
                ("Hue", 13), ("Saturation", 14), ("Color", 15), ("Luminosity", 16),
                ("Stencil Alpha", 17), ("Stencil Luma", 18),
                ("Silhouette Alpha", 19), ("Silhouette Luma", 20),
                ("Luminescent Premul", 21), ("Alpha Add", 22),
                ("Classic Color Dodge", 23), ("Classic Color Burn", 24),
                ("Exclusion", 25), ("Difference", 26),
                ("Color Dodge", 27), ("Color Burn", 28),
                ("Linear Dodge", 29), ("Linear Burn", 30),
                ("Linear Light", 31), ("Vivid Light", 32),
                ("Pin Light", 33), ("Hard Mix", 34),
                ("Lighter Color", 35), ("Darker Color", 36),
                ("Subtract", 37), ("Divide", 38),
            ]:
                blend_menu.addAction(bname, lambda v=bval: self._set_layer_blend_mode(item, v))
            # Track matte
            matte_menu = menu.addMenu("Track Matte")
            for mname, mval in [
                ("None", 0), ("Alpha", 1), ("Alpha Inverted", 2),
                ("Luma", 3), ("Luma Inverted", 4),
            ]:
                matte_menu.addAction(mname, lambda v=mval: self._set_layer_track_matte(item, v))
            # Quality
            quality_menu = menu.addMenu("Quality")
            for qname, qval in [("Wireframe", 0), ("Draft", 1), ("Best", 2)]:
                quality_menu.addAction(qname, lambda v=qval: self._set_layer_quality(item, v))
            # Timing
            menu.addAction("Edit Timing...", lambda: self._edit_layer_timing(item))

        # Property value edit
        match_path = item.data(0, ROLE_MATCH_PATH)
        if match_path and self._writable:
            menu.addAction("Edit Value", lambda: self._edit_property(item))

        # Keyframe editing
        if node_type == "keyframe" and self._writable:
            menu.addAction("Edit Value", lambda: self._edit_kf_value(item))
            menu.addAction("Edit Time", lambda: self._edit_kf_time(item))
            menu.addAction("Edit Temporal Ease", lambda: self._edit_kf_ease(item))
            in_menu = menu.addMenu("In Interpolation")
            in_menu.addAction("Linear", lambda: self._set_kf_in_interp(item, 1))
            in_menu.addAction("Bezier", lambda: self._set_kf_in_interp(item, 2))
            in_menu.addAction("Hold", lambda: self._set_kf_in_interp(item, 3))
            out_menu = menu.addMenu("Out Interpolation")
            out_menu.addAction("Linear", lambda: self._set_kf_interp(item, 1))
            out_menu.addAction("Bezier", lambda: self._set_kf_interp(item, 2))
            out_menu.addAction("Hold", lambda: self._set_kf_interp(item, 3))

        # Pre-comp navigation
        asset_id = item.data(0, ROLE_ASSET_ID)
        if asset_id is not None:
            menu.addAction("Open Pre-comp",
                           lambda: self.precomp_requested.emit(asset_id))

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _rename_layer(self, item: QTreeWidgetItem):
        old_name = item.text(1)
        new_name, ok = QInputDialog.getText(
            self, "Rename Layer", "Layer name:", text=old_name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        self.tree.blockSignals(True)
        item.setText(1, new_name)
        self.tree.blockSignals(False)
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_name(comp_id, layer_id, new_name)

    def _get_layer_flag(self, item: QTreeWidgetItem, flag_key: str) -> bool:
        """Read a flag from the layer data in the comp dict."""
        layer_id = item.data(0, ROLE_LAYER_ID)
        for layer in self.comp.get("layers", []):
            if layer.get("id") == layer_id:
                flags = layer.get("flags", {})
                return bool(flags.get(flag_key, False))
        return False

    def _toggle_layer_flag(self, item: QTreeWidgetItem, flag_key: str, value: bool):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_flag(comp_id, layer_id, flag_key, value)

    def _toggle_preserve_transparency(self, item: QTreeWidgetItem, value: bool):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_preserve_transparency(
                comp_id, layer_id, value)

    def _set_layer_light_type(self, item: QTreeWidgetItem, light_type: int):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_light_type(
                comp_id, layer_id, light_type)

    def _set_layer_label(self, item: QTreeWidgetItem, label: int):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_label(comp_id, layer_id, label)

    def _set_layer_blend_mode(self, item: QTreeWidgetItem, mode: int):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_blend_mode(comp_id, layer_id, mode)
            # Update display — map int back to display name
            name = _BLEND_MODE_INT_NAMES.get(mode, "")
            self._update_layer_info(item, blend_name=name)

    def _set_layer_track_matte(self, item: QTreeWidgetItem, matte_type: int):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_track_matte(comp_id, layer_id, matte_type)

    def _set_layer_quality(self, item: QTreeWidgetItem, quality: int):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_layer_quality(comp_id, layer_id, quality)

    def _update_layer_info(self, item: QTreeWidgetItem, blend_name: str | None = None):
        """Refresh layer attributes (column 2) after a blend mode or flag change."""
        layer_id = item.data(0, ROLE_LAYER_ID)
        layer_data = None
        for layer in self.comp.get("layers", []):
            if layer.get("id") == layer_id:
                layer_data = layer
                break
        if layer_data is None:
            return
        flags = layer_data.get("flags", {})
        if blend_name is None:
            bm = layer_data.get("blendMode", "")
            blend_name = _BLEND_MODE_NAMES.get(bm, "") if bm else ""
        ftags = _flag_tags(flags)
        attr_parts = []
        if blend_name and blend_name != "Normal":
            attr_parts.append(blend_name)
        if ftags:
            attr_parts.append(ftags)
        item.setText(2, "  ".join(attr_parts))

    def _edit_layer_timing(self, item: QTreeWidgetItem):
        layer_id = item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is None or comp_id is None:
            return
        # Find current values from layer data
        layer_data = None
        for layer in self.comp.get("layers", []):
            if layer.get("id") == layer_id:
                layer_data = layer
                break
        in_t = layer_data.get("inTime", 0) if layer_data else 0
        out_t = layer_data.get("outTime", 0) if layer_data else 0
        start_t = layer_data.get("startTime", 0) if layer_data else 0
        stretch = layer_data.get("stretch", 1.0) if layer_data else 1.0

        dlg = _MultiValueDialog(
            "Edit Layer Timing",
            ["In Point (s)", "Out Point (s)", "Start Time (s)", "Stretch"],
            [in_t, out_t, start_t, stretch],
            self)
        if dlg.exec() != QDialog.Accepted:
            return
        vals = dlg.get_values()
        if vals is None or len(vals) != 4:
            return
        for field, val in zip(
            ["in_time", "out_time", "start_time", "time_stretch"], vals
        ):
            self._tools_project.change_layer_time_field(
                comp_id, layer_id, field, val)

    def _edit_property(self, item: QTreeWidgetItem):
        match_path = item.data(0, ROLE_MATCH_PATH)
        if not match_path:
            return
        old_text = item.text(3)
        old_value = _parse_old_value(old_text)

        # Multi-dimensional: use separate input dialog
        if isinstance(old_value, list) and len(old_value) > 1:
            labels = _dim_labels(match_path, len(old_value))
            dlg = _MultiValueDialog(item.text(1), labels, old_value, self)
            if dlg.exec() != QDialog.Accepted:
                return
            new_value = dlg.get_values()
            if new_value is None:
                return
        else:
            # Scalar: simple input
            new_text, ok = QInputDialog.getText(
                self, "Edit Value", f"{item.text(1)}:", text=old_text)
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
        item.setText(3, fmt_val(new_value))
        self.tree.blockSignals(False)
        if layer_id is not None and comp_id is not None:
            self._tools_project.change_property_value(
                comp_id, layer_id, match_path, new_value)

    def _find_kf_context(self, item: QTreeWidgetItem):
        """Walk up from a keyframe item to find layer_id and match_path."""
        key_index = item.data(0, ROLE_KEY_INDEX)
        if key_index is None:
            return None
        # Walk up to find the property item (parent of keyframe)
        prop_item = item.parent()
        if prop_item is None:
            return None
        match_path = prop_item.data(0, ROLE_MATCH_PATH)
        if not match_path:
            return None
        # Walk up to find the layer item
        layer_item = prop_item
        while layer_item and layer_item.data(0, ROLE_NODE_TYPE) != "layer":
            layer_item = layer_item.parent()
        if not layer_item:
            return None
        layer_id = layer_item.data(0, ROLE_LAYER_ID)
        comp_id = self.comp.get("id")
        if layer_id is None or comp_id is None:
            return None
        return comp_id, layer_id, match_path, key_index

    def _update_kf_display(self, item: QTreeWidgetItem, kf_data: dict):
        """Refresh a keyframe item's display text after editing."""
        time = kf_data.get("time", 0)
        value = kf_data.get("value")
        out_trans = kf_data.get("transitionType", "linear")
        bezier_mode = kf_data.get("bezierMode", "normal")
        out_str = _fmt_interp(out_trans, bezier_mode)

        # Determine in interpolation from the previous sibling's data
        key_index = item.data(0, ROLE_KEY_INDEX) or 1
        in_str = None
        if key_index > 1:
            parent = item.parent()
            if parent is not None:
                prev_item = parent.child(key_index - 2)
                if prev_item is not None:
                    prev_data = prev_item.data(0, ROLE_KEY_DATA) or {}
                    in_str = _fmt_interp(
                        prev_data.get("transitionType", "linear"),
                        prev_data.get("bezierMode", "normal"))

        if in_str is not None:
            interp_text = f"in:{in_str} out:{out_str}"
        else:
            interp_text = f"out:{out_str}"

        item.setText(3, f"t={time:.3f}s  [{interp_text}]  {fmt_val(value)}")
        color = COLOR_KF_HOLD if out_trans == "hold" else COLOR_KF
        item.setForeground(1, color)
        item.setData(0, ROLE_KEY_DATA, kf_data)

    def _edit_kf_value(self, item: QTreeWidgetItem):
        ctx = self._find_kf_context(item)
        if ctx is None:
            return
        comp_id, layer_id, match_path, key_index = ctx
        kf_data = item.data(0, ROLE_KEY_DATA)
        old_value = kf_data.get("value") if kf_data else None

        # Multi-dimensional: use separate input dialog
        if isinstance(old_value, list) and len(old_value) > 1:
            labels = _dim_labels(match_path, len(old_value))
            dlg = _MultiValueDialog(
                f"Key {key_index} Value", labels, old_value, self)
            if dlg.exec() != QDialog.Accepted:
                return
            new_value = dlg.get_values()
            if new_value is None:
                return
        else:
            old_text = fmt_val(old_value) if old_value is not None else ""
            new_text, ok = QInputDialog.getText(
                self, "Edit Keyframe Value",
                f"Key {key_index} value:", text=old_text)
            if not ok:
                return
            new_value = _parse_value_text(new_text)
            if new_value is None:
                return

        self._tools_project.change_keyframe_value(
            comp_id, layer_id, match_path, key_index, new_value)
        kf_data["value"] = new_value
        self._update_kf_display(item, kf_data)

    def _edit_kf_time(self, item: QTreeWidgetItem):
        ctx = self._find_kf_context(item)
        if ctx is None:
            return
        comp_id, layer_id, match_path, key_index = ctx
        kf_data = item.data(0, ROLE_KEY_DATA)
        old_time = kf_data.get("time", 0) if kf_data else 0
        new_text, ok = QInputDialog.getText(
            self, "Edit Keyframe Time", f"Key {key_index} time (seconds):",
            text=f"{old_time:.3f}")
        if not ok:
            return
        try:
            new_time = float(new_text.strip())
        except ValueError:
            return
        self._tools_project.change_keyframe_time(
            comp_id, layer_id, match_path, key_index, new_time)
        kf_data["time"] = new_time
        self._update_kf_display(item, kf_data)

    def _set_kf_interp(self, item: QTreeWidgetItem, transition_type: int):
        """Set out interpolation — modifies this keyframe's transition_type."""
        ctx = self._find_kf_context(item)
        if ctx is None:
            return
        comp_id, layer_id, match_path, key_index = ctx
        self._tools_project.change_keyframe_interpolation(
            comp_id, layer_id, match_path, key_index, transition_type)
        kf_data = item.data(0, ROLE_KEY_DATA) or {}
        type_names = {1: "linear", 2: "bezier", 3: "hold"}
        kf_data["transitionType"] = type_names.get(transition_type, str(transition_type))
        self._update_kf_display(item, kf_data)

    def _set_kf_in_interp(self, item: QTreeWidgetItem, transition_type: int):
        """Set in interpolation — modifies the previous keyframe's transition_type.

        In AEP binary, a keyframe's transition_type controls the outgoing curve.
        So to change "incoming" interpolation at key N, we modify key N-1.
        """
        ctx = self._find_kf_context(item)
        if ctx is None:
            return
        comp_id, layer_id, match_path, key_index = ctx
        if key_index <= 1:
            return  # first keyframe has no incoming interpolation
        prev_index = key_index - 1
        self._tools_project.change_keyframe_interpolation(
            comp_id, layer_id, match_path, prev_index, transition_type)
        # Update the previous keyframe's display
        parent = item.parent()
        if parent is not None:
            prev_item = parent.child(prev_index - 1)  # 0-based child index
            if prev_item is not None:
                prev_data = prev_item.data(0, ROLE_KEY_DATA) or {}
                type_names = {1: "linear", 2: "bezier", 3: "hold"}
                prev_data["transitionType"] = type_names.get(
                    transition_type, str(transition_type))
                self._update_kf_display(prev_item, prev_data)

    def _edit_kf_ease(self, item: QTreeWidgetItem):
        ctx = self._find_kf_context(item)
        if ctx is None:
            return
        comp_id, layer_id, match_path, key_index = ctx
        kf_data = item.data(0, ROLE_KEY_DATA) or {}

        in_spd = kf_data.get("inSpeed", [])
        in_inf = kf_data.get("inInfluence", [])
        out_spd = kf_data.get("outSpeed", [])
        out_inf = kf_data.get("outInfluence", [])

        # Format current ease as editable text
        current = (
            f"inSpeed={in_spd}, inInfluence={in_inf}, "
            f"outSpeed={out_spd}, outInfluence={out_inf}"
        )
        new_text, ok = QInputDialog.getText(
            self, "Edit Temporal Ease",
            "Format: inSpeed, inInfluence, outSpeed, outInfluence\n"
            "Single value or comma-separated per component:",
            text=current)
        if not ok:
            return

        # Parse: try to extract 4 groups from the text
        nums = re.findall(r'[\d.e+-]+', new_text)
        if not nums:
            return
        floats = [float(x) for x in nums]

        # Distribute evenly into 4 groups
        n = len(floats) // 4
        if n < 1:
            return
        new_in_spd = floats[:n]
        new_in_inf = floats[n:n*2]
        new_out_spd = floats[n*2:n*3]
        new_out_inf = floats[n*3:n*4]

        self._tools_project.change_keyframe_ease(
            comp_id, layer_id, match_path, key_index,
            in_speed=new_in_spd, in_influence=new_in_inf,
            out_speed=new_out_spd, out_influence=new_out_inf)
        kf_data["inSpeed"] = new_in_spd
        kf_data["inInfluence"] = new_in_inf
        kf_data["outSpeed"] = new_out_spd
        kf_data["outInfluence"] = new_out_inf
        self._update_kf_display(item, kf_data)

        # Update ease child item if present
        for ci in range(item.childCount()):
            child = item.child(ci)
            if child and child.text(1) == "Temporal Ease":
                ease_parts = []
                if new_in_spd:
                    pairs = [f"({s:g}, {inf:g}%)"
                             for s, inf in zip(new_in_spd, new_in_inf)]
                    ease_parts.append(f"In: {' '.join(pairs)}")
                if new_out_spd:
                    pairs = [f"({s:g}, {inf:g}%)"
                             for s, inf in zip(new_out_spd, new_out_inf)]
                    ease_parts.append(f"Out: {' '.join(pairs)}")
                child.setText(3, "  |  ".join(ease_parts))
                break


# -- Project Panel --

class ProjectPanel(QWidget):
    """Left sidebar showing project structure."""

    comp_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tools_project = None
        self._comp_data: dict[int, dict] = {}
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
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
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

    def load_project(self, data: dict, tools_project=None):
        self._tools_project = tools_project
        self._comp_data = {}
        self._collect_comps(data.get("folder", {}))
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

    def _collect_comps(self, folder: dict):
        """Recursively collect comp data dicts keyed by id."""
        for item in folder.get("items", []):
            if "items" in item:
                self._collect_comps(item)
            elif "layers" in item:
                cid = item.get("id")
                if cid is not None:
                    self._comp_data[cid] = item

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
                full_path = item.get("fullPath", "")
                label = f"\U0001f5bc {name}{suffix}"
                if full_path:
                    label += f"  \u2192 {full_path}"
                node = QTreeWidgetItem([label])
                node.setForeground(0, QColor("#808080"))
                node.setData(0, ROLE_NODE_TYPE, "footage")
                node.setData(0, ROLE_ASSET_ID, item.get("id"))
                node.setToolTip(0, full_path or name)
                parent_item.addChild(node)
            elif item.get("type") == "solid":
                name = item.get("name", "(solid)")
                node = QTreeWidgetItem([f"\u25a0 {name}"])
                c = item.get("color", {})
                r, g, b = int(c.get("r", 0)), int(c.get("g", 0)), int(c.get("b", 0))
                node.setForeground(0, QColor(r, g, b) if (r + g + b) > 100 else QColor("#808080"))
                parent_item.addChild(node)

    def _on_context_menu(self, pos: QPoint):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        if self._tools_project is None or not self._tools_project.writable:
            return
        node_type = item.data(0, ROLE_NODE_TYPE)
        menu = QMenu(self.tree)

        if node_type == "footage":
            menu.addAction("Edit File Path", lambda: self._edit_asset_path(item))

        # Comp items have a comp_id in UserRole
        comp_id = item.data(0, Qt.UserRole)
        if comp_id is not None:
            menu.addAction("Rename Composition", lambda: self._rename_comp(item, comp_id))
            menu.addAction("Edit Dimensions...", lambda: self._edit_comp_dimensions(comp_id))
            menu.addAction("Edit Frame Rate...", lambda: self._edit_comp_framerate(comp_id))
            menu.addAction("Edit Duration...", lambda: self._edit_comp_duration(comp_id))
            menu.addAction("Edit Background Color...", lambda: self._edit_comp_bgcolor(comp_id))
            # Comp Flags submenu
            comp_flags_menu = menu.addMenu("Comp Flags")
            for flag_label, flag_key in [
                ("Draft 3D", "draft3d"),
                ("Motion Blur", "motion_blur"),
                ("Frame Blending", "frame_blending"),
                ("Hide Shy Layers", "hide_shy_layers"),
                ("Preserve Nested Resolution", "preserve_nested_resolution"),
                ("Preserve Nested Frame Rate", "preserve_nested_frame_rate"),
                ("Drop Frame", "drop_frame"),
            ]:
                act = comp_flags_menu.addAction(flag_label)
                act.setCheckable(True)
                act.setChecked(self._get_comp_flag(comp_id, flag_key))
                act.triggered.connect(
                    lambda checked, k=flag_key, cid=comp_id: self._toggle_comp_flag(cid, k, checked))
            # Additional comp edit actions
            menu.addAction("Edit Work Area...", lambda: self._edit_comp_work_area(comp_id))
            menu.addAction("Edit Shutter...", lambda: self._edit_comp_shutter(comp_id))
            menu.addAction("Edit Motion Blur Samples...", lambda: self._edit_comp_mb_samples(comp_id))
            menu.addAction("Edit Pixel Aspect...", lambda: self._edit_comp_pixel_aspect(comp_id))
            menu.addAction("Edit Display Start Time...", lambda: self._edit_comp_display_start(comp_id))

        # Project Settings — always available when writable
        if self._tools_project is not None and self._tools_project.writable:
            settings_menu = menu.addMenu("Project Settings")
            bpc_menu = settings_menu.addMenu("Bits Per Channel")
            for bits in [8, 16, 32]:
                bpc_menu.addAction(f"{bits} bpc",
                                   lambda b=bits: self._set_project_bpc(b))
            gamma_menu = settings_menu.addMenu("Working Gamma")
            gamma_menu.addAction("2.2", lambda: self._set_project_gamma(2.2))
            gamma_menu.addAction("2.4", lambda: self._set_project_gamma(2.4))
            for plabel, pattr in [
                ("Linearize Working Space", "linearize_working_space"),
                ("Compensate Scene Referred", "compensate_scene_referred"),
            ]:
                act = settings_menu.addAction(plabel)
                act.setCheckable(True)
                act.setChecked(getattr(self._tools_project, pattr, False))
                act.triggered.connect(
                    lambda checked, a=pattr: setattr(self._tools_project, a, checked))
            settings_menu.addAction("Edit Audio Sample Rate...",
                                    self._edit_audio_sample_rate)

        if not menu.isEmpty():
            menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _edit_asset_path(self, item: QTreeWidgetItem):
        asset_id = item.data(0, ROLE_ASSET_ID)
        if asset_id is None:
            return
        old_path = item.toolTip(0) or ""
        new_path, ok = QInputDialog.getText(
            self, "Edit File Path", "File path:", text=old_path)
        if not ok or not new_path.strip():
            return
        new_path = new_path.strip()
        ok = self._tools_project.change_asset_path(asset_id, new_path)
        if ok:
            # Update tree display — rebuild label from current text
            old_text = item.text(0)
            # Strip old path suffix if present
            arrow_idx = old_text.find("  \u2192 ")
            base = old_text[:arrow_idx] if arrow_idx >= 0 else old_text
            item.setText(0, f"{base}  \u2192 {new_path}")
            item.setToolTip(0, new_path)

    def _rename_comp(self, item: QTreeWidgetItem, comp_id: int):
        old_text = item.text(0)
        # Strip icon prefix for editing
        name_match = re.search(r'[^\s].*?(?=\s+\()', old_text)
        old_name = name_match.group(0) if name_match else old_text
        new_name, ok = QInputDialog.getText(
            self, "Rename Composition", "Name:", text=old_name)
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        self._tools_project.change_comp_name(comp_id, new_name)
        # Update display — preserve icon and size suffix
        prefix = old_text[:old_text.index(old_name)] if old_name in old_text else ""
        suffix_match = re.search(r'\s+\(\d+.+\)$', old_text)
        suffix = suffix_match.group(0) if suffix_match else ""
        item.setText(0, f"{prefix}{new_name}{suffix}")

    def _edit_comp_dimensions(self, comp_id: int):
        text, ok = QInputDialog.getText(
            self, "Edit Dimensions", "Width x Height (e.g. 1920x1080):")
        if not ok or not text.strip():
            return
        m = re.match(r'(\d+)\s*[x\u00d7,]\s*(\d+)', text.strip())
        if not m:
            return
        self._tools_project.change_comp_dimensions(
            comp_id, int(m.group(1)), int(m.group(2)))

    def _edit_comp_framerate(self, comp_id: int):
        text, ok = QInputDialog.getText(
            self, "Edit Frame Rate", "Frame rate (fps):")
        if not ok or not text.strip():
            return
        try:
            fps = float(text.strip())
        except ValueError:
            return
        self._tools_project.change_comp_framerate(comp_id, fps)

    def _edit_comp_duration(self, comp_id: int):
        text, ok = QInputDialog.getText(
            self, "Edit Duration", "Duration (seconds):")
        if not ok or not text.strip():
            return
        try:
            dur = float(text.strip())
        except ValueError:
            return
        self._tools_project.change_comp_duration(comp_id, dur)

    def _edit_comp_bgcolor(self, comp_id: int):
        text, ok = QInputDialog.getText(
            self, "Edit Background Color",
            "RGB (0-255), e.g. 0,0,0 or #000000:")
        if not ok or not text.strip():
            return
        text = text.strip()
        if text.startswith("#") and len(text) >= 7:
            r = int(text[1:3], 16)
            g = int(text[3:5], 16)
            b = int(text[5:7], 16)
        else:
            nums = re.findall(r'\d+', text)
            if len(nums) < 3:
                return
            r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
        self._tools_project.change_comp_bgcolor(comp_id, r, g, b)

    def _get_comp_flag(self, comp_id: int, flag_key: str) -> bool:
        cd = self._comp_data.get(comp_id, {})
        flags = cd.get("flags", {})
        # Comp dict uses camelCase keys; convert snake_case to camelCase
        parts = flag_key.split("_")
        camel = parts[0] + "".join(p.capitalize() for p in parts[1:])
        return bool(flags.get(camel, False))

    def _toggle_comp_flag(self, comp_id: int, flag_key: str, value: bool):
        if flag_key == "drop_frame":
            self._tools_project.change_comp_drop_frame(comp_id, value)
        else:
            self._tools_project.change_comp_flag(comp_id, flag_key, value)

    def _edit_comp_work_area(self, comp_id: int):
        cd = self._comp_data.get(comp_id, {})
        cur_start = cd.get("inTime", 0)
        cur_end = cd.get("outTime", 0)
        text, ok = QInputDialog.getText(
            self, "Edit Work Area",
            "start, duration (seconds):",
            text=f"{cur_start}, {cur_end - cur_start}")
        if not ok or not text.strip():
            return
        nums = re.findall(r'[\d.]+', text.strip())
        if len(nums) < 2:
            return
        try:
            start, dur = float(nums[0]), float(nums[1])
        except ValueError:
            return
        self._tools_project.change_comp_work_area_start(comp_id, start)
        self._tools_project.change_comp_work_area_end(comp_id, start + dur)

    def _edit_comp_shutter(self, comp_id: int):
        cd = self._comp_data.get(comp_id, {})
        cur_angle = cd.get("shutterAngle", 0)
        cur_phase = cd.get("shutterPhase", 0)
        text, ok = QInputDialog.getText(
            self, "Edit Shutter",
            "angle, phase (e.g. 180, -90):",
            text=f"{cur_angle}, {cur_phase}")
        if not ok or not text.strip():
            return
        nums = re.findall(r'-?\d+', text.strip())
        if len(nums) < 2:
            return
        try:
            angle, phase = int(nums[0]), int(nums[1])
        except ValueError:
            return
        self._tools_project.change_comp_shutter_angle(comp_id, angle)
        self._tools_project.change_comp_shutter_phase(comp_id, phase)

    def _edit_comp_mb_samples(self, comp_id: int):
        cd = self._comp_data.get(comp_id, {})
        cur_spf = cd.get("motionBlurSamplesPerFrame", 16)
        cur_lim = cd.get("motionBlurAdaptiveSampleLimit", 128)
        text, ok = QInputDialog.getText(
            self, "Edit Motion Blur Samples",
            "samples_per_frame, adaptive_limit:",
            text=f"{cur_spf}, {cur_lim}")
        if not ok or not text.strip():
            return
        nums = re.findall(r'\d+', text.strip())
        if len(nums) < 2:
            return
        try:
            spf, lim = int(nums[0]), int(nums[1])
        except ValueError:
            return
        self._tools_project.change_comp_motion_blur_samples(comp_id, spf, lim)

    def _edit_comp_pixel_aspect(self, comp_id: int):
        cd = self._comp_data.get(comp_id, {})
        cur = cd.get("pixelAspect", 1.0)
        text, ok = QInputDialog.getText(
            self, "Edit Pixel Aspect Ratio",
            "Ratio (e.g. 1.0):",
            text=str(cur))
        if not ok or not text.strip():
            return
        try:
            ratio = float(text.strip())
        except ValueError:
            return
        self._tools_project.change_comp_pixel_aspect(comp_id, ratio)

    def _edit_comp_display_start(self, comp_id: int):
        cd = self._comp_data.get(comp_id, {})
        cur = cd.get("displayStartTime", 0.0)
        text, ok = QInputDialog.getText(
            self, "Edit Display Start Time",
            "Start time (seconds):",
            text=str(cur))
        if not ok or not text.strip():
            return
        try:
            t = float(text.strip())
        except ValueError:
            return
        self._tools_project.change_comp_display_start_time(comp_id, t)

    def _set_project_bpc(self, bits: int):
        self._tools_project.bits_per_channel = bits

    def _set_project_gamma(self, gamma: float):
        self._tools_project.working_gamma = gamma

    def _edit_audio_sample_rate(self):
        cur = getattr(self._tools_project, 'audio_sample_rate', 48000.0)
        text, ok = QInputDialog.getText(
            self, "Edit Audio Sample Rate",
            "Sample rate (Hz):",
            text=str(cur))
        if not ok or not text.strip():
            return
        try:
            rate = float(text.strip())
        except ValueError:
            return
        self._tools_project.audio_sample_rate = rate

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
