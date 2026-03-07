"""AEP Tools — AE scripting-style read API for After Effects project files."""

from ._constants import (
    AutoOrientType,
    BlendingMode,
    KeyframeInterpolationType,
    LayerQuality,
    LayerType,
    MaskMode,
    PropertyValueType,
    TrackMatteType,
)
from ._comp import CompItem
from ._effect import Effect
from ._layer import AVLayer, CameraLayer, Layer, LightLayer, ShapeLayer, TextLayer
from ._mask import Mask
from ._project import (
    FootageItem,
    FolderItem,
    Project,
    RenderQueue,
    load_project,
    open_aep,
    open_aepx,
)
from ._property import (
    KeyframeValue,
    MarkerProperty,
    MarkerValue,
    Property,
    PropertyGroup,
    TextSourceProperty,
)

__version__ = "0.1.0"

__all__ = [
    # Project
    "Project",
    "open_aep",
    "open_aepx",
    "load_project",
    # Composition
    "CompItem",
    # Layers
    "Layer",
    "AVLayer",
    "TextLayer",
    "ShapeLayer",
    "CameraLayer",
    "LightLayer",
    # Properties
    "Property",
    "PropertyGroup",
    "KeyframeValue",
    "MarkerProperty",
    "MarkerValue",
    "TextSourceProperty",
    # Effects / Masks
    "Effect",
    "Mask",
    # Items
    "FolderItem",
    "FootageItem",
    "RenderQueue",
    # Enums
    "BlendingMode",
    "TrackMatteType",
    "MaskMode",
    "LayerQuality",
    "KeyframeInterpolationType",
    "AutoOrientType",
    "PropertyValueType",
    "LayerType",
]
