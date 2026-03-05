"""Enums and match-name mappings mirroring After Effects scripting constants."""

from __future__ import annotations

from enum import IntEnum


class BlendingMode(IntEnum):
    NORMAL = 1
    DARKEN = 3
    MULTIPLY = 4
    COLOR_BURN = 5
    LINEAR_BURN = 6
    DARKER_COLOR = 7
    LIGHTEN = 9
    SCREEN = 10
    COLOR_DODGE = 11
    LINEAR_DODGE = 12
    LIGHTER_COLOR = 13
    OVERLAY = 15
    SOFT_LIGHT = 16
    HARD_LIGHT = 17
    LINEAR_LIGHT = 18
    VIVID_LIGHT = 19
    PIN_LIGHT = 20
    HARD_MIX = 21
    DIFFERENCE = 23
    EXCLUSION = 24
    HUE = 26
    SATURATION = 27
    COLOR = 28
    LUMINOSITY = 29


class TrackMatteType(IntEnum):
    NONE = 0
    ALPHA = 1
    ALPHA_INVERTED = 2
    LUMA = 3
    LUMA_INVERTED = 4


class MaskMode(IntEnum):
    NONE = 0
    ADD = 1
    SUBTRACT = 2
    INTERSECT = 3
    DARKEN = 4
    LIGHTEN = 5
    DIFFERENCE = 6


class LayerQuality(IntEnum):
    WIREFRAME = 0
    DRAFT = 1
    BEST = 2


class KeyframeInterpolationType(IntEnum):
    LINEAR = 1
    BEZIER = 2
    HOLD = 3


class AutoOrientType(IntEnum):
    NO_AUTO_ORIENT = 0
    ALONG_PATH = 1
    CAMERA_OR_POINT_OF_INTEREST = 2
    CHARACTERS_TOWARD_CAMERA = 3


class PropertyValueType(IntEnum):
    COLOR = 0
    SCALAR = 1
    SPATIAL = 2
    MULTIDIMENSIONAL = 3
    LAYER_REF = 4
    CUSTOM = 5
    UINT = 6


class LayerType(IntEnum):
    ASSET = 0
    LIGHT = 1
    CAMERA = 2
    TEXT = 3
    SHAPE = 4


# Match name -> display name mapping (AE internal names)
MATCH_NAMES: dict[str, str] = {
    # Layer top-level groups
    "ADBE Root Vectors Group": "Contents",
    "ADBE Transform Group": "Transform",
    "ADBE Material Options Group": "Material Options",
    "ADBE Layer Styles": "Layer Styles",
    "ADBE Effect Parade": "Effects",
    "ADBE Mask Parade": "Masks",
    "ADBE Audio Group": "Audio",
    "ADBE Camera Options Group": "Camera Options",
    "ADBE Light Options Group": "Light Options",
    "ADBE Text Properties": "Text",

    # Transform properties
    "ADBE Anchor Point": "Anchor Point",
    "ADBE Position": "Position",
    "ADBE Position_0": "X Position",
    "ADBE Position_1": "Y Position",
    "ADBE Position_2": "Z Position",
    "ADBE Scale": "Scale",
    "ADBE Orientation": "Orientation",
    "ADBE Rotate X": "X Rotation",
    "ADBE Rotate Y": "Y Rotation",
    "ADBE Rotate Z": "Z Rotation",
    "ADBE Opacity": "Opacity",

    # Camera options
    "ADBE Camera Zoom": "Zoom",
    "ADBE Camera Focus Distance": "Focus Distance",
    "ADBE Camera Aperture": "Aperture",
    "ADBE Camera Blur Level": "Blur Level",

    # Light options
    "ADBE Light Intensity": "Intensity",
    "ADBE Light Color": "Color",
    "ADBE Light Cone Angle": "Cone Angle",
    "ADBE Light Cone Feather2": "Cone Feather",
    "ADBE Light Shadow Darkness": "Shadow Darkness",
    "ADBE Light Shadow Diffusion": "Shadow Diffusion",

    # Time remap
    "ADBE Time Remapping": "Time Remap",

    # Mask properties
    "ADBE Mask Shape": "Mask Path",
    "ADBE Mask Feather": "Mask Feather",
    "ADBE Mask Opacity": "Mask Opacity",
    "ADBE Mask Offset": "Mask Expansion",

    # Text
    "ADBE Text Document": "Source Text",
    "ADBE Text Path Options": "Path Options",
    "ADBE Text More Options": "More Options",
    "ADBE Text Animators": "Animators",

    # Audio
    "ADBE Audio Levels": "Audio Levels",

    # Markers
    "ADBE Marker": "Marker",

    # Shape layer
    "ADBE Vector Group": "Group",
    "ADBE Vectors Group": "Contents",
    "ADBE Vector Transform Group": "Transform",
    "ADBE Vector Fill": "Fill",
    "ADBE Vector Stroke": "Stroke",
    "ADBE Vector Shape - Rect": "Rectangle Path",
    "ADBE Vector Shape - Ellipse": "Ellipse Path",
    "ADBE Vector Shape - Star": "Polystar Path",
    "ADBE Vector Shape - Group": "Path",
    "ADBE Vector Trim": "Trim Paths",
    "ADBE Vector Merge": "Merge Paths",
    "ADBE Vector Offset": "Offset Paths",
    "ADBE Vector Repeater": "Repeater",
    "ADBE Vector Round": "Round Corners",

    # Material options
    "ADBE Casts Shadows": "Casts Shadows",
    "ADBE Light Transmission": "Light Transmission",
    "ADBE Accepts Shadows": "Accepts Shadows",
    "ADBE Accepts Lights": "Accepts Lights",
    "ADBE Ambient Coefficient": "Ambient",
    "ADBE Diffuse Coefficient": "Diffuse",
    "ADBE Specular Coefficient": "Specular Intensity",
    "ADBE Shininess Coefficient": "Specular Shininess",
    "ADBE Metal Coefficient": "Metal",
}

# Reverse lookup: display name -> match name
DISPLAY_NAMES: dict[str, str] = {v: k for k, v in MATCH_NAMES.items()}
