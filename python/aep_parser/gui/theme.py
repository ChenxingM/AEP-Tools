"""GUI theme constants, styles, and formatting utilities."""

from __future__ import annotations

from PySide6.QtGui import QColor

# -- Colors --

ROLE_KEYFRAMES = 257  # Qt.UserRole + 1
ROLE_NODE_TYPE = 261  # Qt.UserRole + 5

COLOR_BG = QColor("#1e1e1e")
COLOR_BG_ALT = QColor("#252526")
COLOR_PANEL = QColor("#2d2d2d")
COLOR_TEXT = QColor("#cccccc")
COLOR_TEXT_DIM = QColor("#808080")
COLOR_TEXT_ANIM = QColor("#5b9fd6")
COLOR_ACCENT = QColor("#264f78")
COLOR_KF = QColor("#e8a624")
COLOR_KF_HOLD = QColor("#d45555")

LAYER_TYPE_LABELS = {
    "shape": ("Shape", "#4ec9b0"),
    "text": ("Text", "#ce9178"),
    "camera": ("Camera", "#9cdcfe"),
    "light": ("Light", "#dcdcaa"),
    "asset": ("Asset", "#c586c0"),
}

# Match name -> human-readable display name
ADBE_NAMES = {
    "ADBE Transform Group": "Transform",
    "ADBE Anchor Point": "Anchor Point",
    "ADBE Position": "Position",
    "ADBE Position_0": "X Position",
    "ADBE Position_1": "Y Position",
    "ADBE Position_2": "Z Position",
    "ADBE Scale": "Scale",
    "ADBE Rotate X": "X Rotation",
    "ADBE Rotate Y": "Y Rotation",
    "ADBE Rotate Z": "Z Rotation",
    "ADBE Rotation": "Rotation",
    "ADBE Opacity": "Opacity",
    "ADBE Orientation": "Orientation",
    "ADBE Skew": "Skew",
    "ADBE Skew Axis": "Skew Axis",
    "ADBE Root Vectors Group": "Contents",
    "ADBE Vector Group": "Group",
    "ADBE Vectors Group": "Contents",
    "ADBE Vector Transform Group": "Transform",
    "ADBE Vector Shape - Rect": "Rectangle",
    "ADBE Vector Rect Position": "Position",
    "ADBE Vector Rect Size": "Size",
    "ADBE Vector Rect Roundness": "Roundness",
    "ADBE Vector Shape - Ellipse": "Ellipse",
    "ADBE Vector Ellipse Position": "Position",
    "ADBE Vector Ellipse Size": "Size",
    "ADBE Vector Shape - Star": "Polystar",
    "ADBE Vector Shape - Group": "Path",
    "ADBE Vector Shape": "Path",
    "ADBE Vector Graphic - Fill": "Fill",
    "ADBE Vector Fill Color": "Color",
    "ADBE Vector Fill Opacity": "Opacity",
    "ADBE Vector Fill Rule": "Fill Rule",
    "ADBE Vector Graphic - Stroke": "Stroke",
    "ADBE Vector Stroke Color": "Color",
    "ADBE Vector Stroke Opacity": "Opacity",
    "ADBE Vector Stroke Width": "Stroke Width",
    "ADBE Vector Stroke Line Cap": "Line Cap",
    "ADBE Vector Stroke Line Join": "Line Join",
    "ADBE Vector Stroke Miter Limit": "Miter Limit",
    "ADBE Vector Stroke Dashes": "Dashes",
    "ADBE Vector Graphic - G-Fill": "Gradient Fill",
    "ADBE Vector Graphic - G-Stroke": "Gradient Stroke",
    "ADBE Vector Grad Start Pt": "Start Point",
    "ADBE Vector Grad End Pt": "End Point",
    "ADBE Vector Grad Colors": "Colors",
    "ADBE Vector Grad Type": "Type",
    "ADBE Vector Filter - Trim": "Trim Paths",
    "ADBE Vector Trim Start": "Start",
    "ADBE Vector Trim End": "End",
    "ADBE Vector Trim Offset": "Offset",
    "ADBE Vector Filter - Merge": "Merge Paths",
    "ADBE Vector Filter - Offset": "Offset Paths",
    "ADBE Vector Filter - PB": "Pucker & Bloat",
    "ADBE Vector Filter - Repeater": "Repeater",
    "ADBE Vector Repeater Copies": "Copies",
    "ADBE Vector Repeater Offset": "Offset",
    "ADBE Vector Repeater Transform": "Transform",
    "ADBE Vector Filter - RC": "Round Corners",
    "ADBE Vector RoundCorner Radius": "Radius",
    "ADBE Vector Filter - Twist": "Twist",
    "ADBE Vector Filter - Zigzag": "Zig Zag",
    "ADBE Vector Blend Mode": "Blend Mode",
    "ADBE Vector Group Opacity": "Opacity",
    "ADBE Effect Parade": "Effects",
    "ADBE Mask Parade": "Masks",
    "ADBE Mask Atom": "Mask",
    "ADBE Mask Shape": "Mask Path",
    "ADBE Mask Feather": "Mask Feather",
    "ADBE Mask Opacity": "Mask Opacity",
    "ADBE Mask Offset": "Mask Expansion",
    "ADBE Text Properties": "Text",
    "ADBE Text Document": "Source Text",
    "ADBE Text Animators": "Animators",
    "ADBE Text Animator": "Animator",
    "ADBE Text Selectors": "Selectors",
    "ADBE Text Selector": "Range Selector",
    "ADBE Text Percent Start": "Start",
    "ADBE Text Percent End": "End",
    "ADBE Text Animator Properties": "Properties",
    "ADBE Text Path Options": "Path Options",
    "ADBE Text More Options": "More Options",
    "ADBE Time Remapping": "Time Remap",
    "ADBE Layer Styles": "Layer Styles",
    "ADBE Marker": "Markers",
    "ADBE Camera Options Group": "Camera Options",
    "ADBE Camera Aperture": "Aperture",
    "ADBE Camera Zoom": "Zoom",
    "ADBE Gaussian Blur 2": "Gaussian Blur",
    "ADBE Drop Shadow": "Drop Shadow",
    "ADBE Fill": "Fill",
    "ADBE Stroke": "Stroke",
    "ADBE Tint": "Tint",
    "ADBE Tritone": "Tritone",
    "ADBE Pro Levels2": "Levels",
    "ADBE Displacement Map": "Displacement Map",
    "ADBE Set Matte3": "Set Matte",
    "ADBE Twirl": "Twirl",
    "ADBE Spherize": "Spherize",
    "ADBE Radial Wipe": "Radial Wipe",
}

DARK_STYLESHEET = """
QMainWindow, QWidget { background-color: #1e1e1e; color: #cccccc; }
QMenuBar { background-color: #2d2d2d; color: #cccccc; border-bottom: 1px solid #3c3c3c; }
QMenuBar::item:selected { background-color: #094771; }
QMenu { background-color: #2d2d2d; color: #cccccc; border: 1px solid #3c3c3c; }
QMenu::item:selected { background-color: #094771; }
QTabWidget::pane { border: 1px solid #3c3c3c; background: #1e1e1e; }
QTabBar::tab {
    background: #2d2d2d; color: #808080; padding: 6px 16px;
    border: 1px solid #3c3c3c; border-bottom: none; margin-right: 2px;
    min-width: 80px;
}
QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; border-bottom: 2px solid #007acc; }
QTabBar::tab:hover { color: #cccccc; }
QTreeWidget {
    background-color: #1e1e1e; alternate-background-color: #252526;
    color: #cccccc; border: none; outline: none;
    selection-background-color: #264f78;
}
QTreeWidget::item { padding: 2px 0; border: none; }
QTreeWidget::item:selected { background-color: #264f78; }
QTreeWidget::item:hover { background-color: #2a2d2e; }
QHeaderView::section {
    background-color: #2d2d2d; color: #cccccc; padding: 4px 8px;
    border: none; border-right: 1px solid #3c3c3c; border-bottom: 1px solid #3c3c3c;
    font-weight: bold; font-size: 11px;
}
QSplitter::handle { background-color: #3c3c3c; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical { height: 2px; }
QStatusBar { background-color: #007acc; color: #ffffff; font-size: 12px; }
QLabel#comp_info {
    background-color: #2d2d2d; color: #9cdcfe; padding: 6px 12px;
    border-bottom: 1px solid #3c3c3c; font-size: 12px;
}
QLabel#section_title {
    color: #808080; font-size: 11px; font-weight: bold;
    padding: 8px 8px 4px 8px; text-transform: uppercase;
}
QScrollBar:vertical { background: #1e1e1e; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #424242; min-height: 20px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #1e1e1e; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #424242; min-width: 20px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


# -- Value Formatting --

def fmt_val(v) -> str:
    """Format a parsed property value as a readable string."""
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return f"{v:g}"
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        if "r" in v and "g" in v and "b" in v:
            return f"({v['r']:.0f}, {v['g']:.0f}, {v['b']:.0f})"
        if "x" in v and "y" in v:
            if v.get("z") is not None:
                return f"({v['x']:.1f}, {v['y']:.1f}, {v['z']:.1f})"
            return f"({v['x']:.1f}, {v['y']:.1f})"
        if "layerId" in v:
            return f"Layer #{v['layerId']}"
        if "closed" in v and "points" in v:
            n = len(v["points"])
            return f"Shape ({n} pts, {'closed' if v['closed'] else 'open'})"
        if "colorStops" in v:
            return f"Gradient ({len(v['colorStops'])} stops)"
        if "duration" in v and "name" in v:
            return f'"{v["name"]}" ({v["duration"]:.2f}s)'
        if "text" in v and "characterStyles" in v:
            txt = v["text"][:30].replace("\r", "\u21b5")
            return f'"{txt}"'
        if "fonts" in v and "documents" in v:
            docs = v.get("documents", {})
            val = docs.get("value")
            if val and isinstance(val, dict) and "text" in val:
                return fmt_val(val)
            return "(text)"
        if "type" in v and "animated" in v:
            if v.get("animated") and v.get("keyframes"):
                return f"({len(v['keyframes'])} keyframes)"
            return fmt_val(v.get("value"))
        return str(v)[:60]
    if isinstance(v, list):
        return f"[{len(v)} items]"
    return str(v)[:60]


def get_color_swatch(v) -> QColor | None:
    """Return a QColor if the value represents a color."""
    if isinstance(v, dict) and "r" in v and "g" in v and "b" in v:
        return QColor(int(v["r"]), int(v["g"]), int(v["b"]))
    return None


def get_keyframes(prop: dict) -> list[dict]:
    """Extract keyframe list from an animated property dict."""
    if isinstance(prop, dict) and prop.get("animated") and prop.get("keyframes"):
        return prop["keyframes"]
    return []
