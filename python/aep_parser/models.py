"""Data model classes for the AEP project structure."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


# ── Primitive types ──────────────────────────────────────────────────────────

@dataclass
class Vector:
    x: float = 0.0
    y: float = 0.0
    z: float | None = None

    @property
    def is_3d(self) -> bool:
        return self.z is not None

    def to_dict(self) -> dict:
        d = {"x": self.x, "y": self.y}
        if self.z is not None:
            d["z"] = self.z
        return d


@dataclass
class Color:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 1.0

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}


@dataclass
class LayerRef:
    layer_id: int = 0
    layer_source: int = 0

    def to_dict(self) -> dict:
        return {"layerId": self.layer_id, "layerSource": self.layer_source}


# ── Gradient ─────────────────────────────────────────────────────────────────

@dataclass
class GradientStop:
    offset: float
    mid_point: float
    value: Any  # Color for color stops, float for alpha stops

    def to_dict(self) -> dict:
        v = self.value.to_dict() if hasattr(self.value, "to_dict") else self.value
        return {"offset": self.offset, "midPoint": self.mid_point, "value": v}


@dataclass
class Gradient:
    color_stops: list[GradientStop] = field(default_factory=list)
    alpha_stops: list[GradientStop] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "colorStops": [s.to_dict() for s in self.color_stops],
            "alphaStops": [s.to_dict() for s in self.alpha_stops],
        }


# ── Bezier shape ─────────────────────────────────────────────────────────────

@dataclass
class BezierShape:
    closed: bool = False
    minimum: Vector = field(default_factory=Vector)
    maximum: Vector = field(default_factory=Vector)
    points: list[Vector] = field(default_factory=list)
    group_info: dict = field(default_factory=lambda: {"maxVertexCount": 0, "bezierCount": 0})

    def to_dict(self) -> dict:
        return {
            "closed": self.closed,
            "minimum": self.minimum.to_dict(),
            "maximum": self.maximum.to_dict(),
            "points": [p.to_dict() for p in self.points],
            "groupInfo": self.group_info,
        }


# ── Keyframe ─────────────────────────────────────────────────────────────────

TRANSITION_TYPES = {1: "linear", 2: "bezier", 3: "hold"}
BEZIER_MODES = {0: "normal", 1: "continuous", 2: "auto"}


@dataclass
class Keyframe:
    time: float = 0.0
    value: Any = None
    transition_type: int = 1  # 1=linear, 2=bezier, 3=hold
    bezier_mode: int = 0
    label_color: int = 0
    roving: bool = False
    in_tangent: Vector = field(default_factory=Vector)
    out_tangent: Vector = field(default_factory=Vector)
    in_speed: list[float] = field(default_factory=list)
    in_influence: list[float] = field(default_factory=list)
    out_speed: list[float] = field(default_factory=list)
    out_influence: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        v = _val(self.value)
        d: dict = {
            "time": self.time,
            "value": v,
            "transitionType": TRANSITION_TYPES.get(self.transition_type, self.transition_type),
            "bezierMode": BEZIER_MODES.get(self.bezier_mode, self.bezier_mode),
        }
        if self.in_speed:
            d["inSpeed"] = self.in_speed
            d["inInfluence"] = self.in_influence
            d["outSpeed"] = self.out_speed
            d["outInfluence"] = self.out_influence
        if self.in_tangent.x != 0 or self.in_tangent.y != 0:
            d["inTangent"] = self.in_tangent.to_dict()
            d["outTangent"] = self.out_tangent.to_dict()
        if self.roving:
            d["roving"] = True
        return d


# ── Properties ───────────────────────────────────────────────────────────────

PROPERTY_TYPE_NAMES = {
    0: "color", 1: "scalar", 2: "spatial",
    3: "multidimensional", 4: "layer_ref", 5: "custom", 6: "uint",
}


@dataclass
class AnimatedProperty:
    key: str = ""
    animated: bool = False
    components: int = 0
    expression: str | None = None
    keyframes: list[Keyframe] = field(default_factory=list)
    split: bool = False
    prop_type: int = 3
    value: Any = None

    def to_dict(self) -> dict:
        d: dict = {"type": PROPERTY_TYPE_NAMES.get(self.prop_type, self.prop_type)}
        if self.key:
            d["key"] = self.key
        d["animated"] = self.animated
        d["components"] = self.components
        if self.split:
            d["split"] = True
        if self.value is not None:
            d["value"] = _val(self.value)
        if self.keyframes:
            d["keyframes"] = [k.to_dict() for k in self.keyframes]
        if self.expression:
            d["expression"] = self.expression
        return d


@dataclass
class NamedProperty:
    match_name: str
    value: Any

    def to_dict(self) -> dict:
        return {"matchName": self.match_name, "value": _val(self.value)}


@dataclass
class PropertyGroup:
    key: str = ""
    name: str = ""
    visible: bool = True
    enabled: bool | None = None  # for Layer Styles sub-groups: tdsb visible when split=True
    split_position: bool = False
    properties: list[NamedProperty] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {}
        if self.key:
            d["key"] = self.key
        if self.name:
            d["name"] = self.name
        if self.enabled is not None:
            d["enabled"] = self.enabled
        elif not self.visible:
            d["visible"] = False
        if self.split_position:
            d["splitPosition"] = True
        if self.properties or self.enabled is not None:
            d["properties"] = [p.to_dict() for p in self.properties]
        return d


# ── Mask ─────────────────────────────────────────────────────────────────────

MASK_MODES = {0: "none", 1: "add", 2: "subtract", 3: "intersect",
              4: "darken", 5: "lighten", 6: "difference"}


@dataclass
class MaskData:
    key: str = ""
    index: int = 0
    inverted: bool = False
    locked: bool = False
    mode: int = 1  # add
    properties: PropertyGroup | None = None

    def to_dict(self) -> dict:
        d: dict = {
            "index": self.index,
            "mode": MASK_MODES.get(self.mode, self.mode),
            "inverted": self.inverted,
        }
        if self.locked:
            d["locked"] = True
        if self.properties:
            d["properties"] = self.properties.to_dict()
        return d


# ── Text ─────────────────────────────────────────────────────────────────────

@dataclass
class Font:
    family: str = ""

    def to_dict(self) -> dict:
        return {"family": self.family}


@dataclass
class CharacterStyle:
    character_count: int = 0
    faux_bold: bool = False
    faux_italic: bool = False
    fill_color: Color = field(default_factory=Color)
    fill_enabled: bool = True
    font_index: int = 0
    leading: float = 0.0
    leading_auto: bool = False
    size: float = 0.0
    stroke_color: Color = field(default_factory=Color)
    stroke_enabled: bool = False
    stroke_over_fill: bool = False
    stroke_width: float = 0.0
    text_transform: int = 0
    tracking: float = 0.0
    vertical_align: int = 0

    def to_dict(self) -> dict:
        d: dict = {"characterCount": self.character_count, "fontSize": self.size,
                    "fontIndex": self.font_index}
        if self.fill_enabled:
            d["fillColor"] = self.fill_color.to_dict()
        if self.stroke_enabled:
            d["strokeColor"] = self.stroke_color.to_dict()
            d["strokeWidth"] = self.stroke_width
        if self.faux_bold:
            d["fauxBold"] = True
        if self.faux_italic:
            d["fauxItalic"] = True
        if self.tracking:
            d["tracking"] = self.tracking
        if not self.leading_auto:
            d["leading"] = self.leading
        if self.text_transform:
            d["textTransform"] = self.text_transform
        return d


@dataclass
class LineStyle:
    character_count: int = 0
    text_justify: int = 0

    def to_dict(self) -> dict:
        return {"characterCount": self.character_count, "textJustify": self.text_justify}


@dataclass
class ParagraphStyle:
    wrap_position: Vector = field(default_factory=Vector)
    wrap_size: Vector = field(default_factory=Vector)

    def to_dict(self) -> dict:
        return {"wrapPosition": self.wrap_position.to_dict(),
                "wrapSize": self.wrap_size.to_dict()}


@dataclass
class TextDocument:
    text: str = ""
    character_styles: list[CharacterStyle] = field(default_factory=list)
    line_styles: list[LineStyle] = field(default_factory=list)
    paragraph_styles: list[ParagraphStyle] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {"text": self.text}
        if self.character_styles:
            d["characterStyles"] = [s.to_dict() for s in self.character_styles]
        if self.line_styles:
            d["lineStyles"] = [s.to_dict() for s in self.line_styles]
        if self.paragraph_styles:
            d["paragraphStyles"] = [s.to_dict() for s in self.paragraph_styles]
        return d


@dataclass
class TextProperty:
    key: str = ""
    fonts: list[Font] = field(default_factory=list)
    documents: AnimatedProperty = field(default_factory=AnimatedProperty)

    def to_dict(self) -> dict:
        return {
            "fonts": [f.to_dict() for f in self.fonts],
            "documents": self.documents.to_dict(),
        }


# ── Effects ──────────────────────────────────────────────────────────────────

@dataclass
class EffectParameter:
    match_name: str = ""
    name: str = ""
    param_type: int = 15
    default_value: Any = None
    last_value: Any = None

    def to_dict(self) -> dict:
        return {
            "matchName": self.match_name,
            "name": self.name,
            "type": self.param_type,
            "defaultValue": _val(self.default_value),
            "lastValue": _val(self.last_value),
        }


@dataclass
class EffectDefinition:
    match_name: str = ""
    name: str = ""
    parameters: list[EffectParameter] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "matchName": self.match_name,
            "name": self.name,
            "parameters": [p.to_dict() for p in self.parameters],
        }


@dataclass
class EffectInstance:
    key: str = ""
    name: str = ""
    parameters: PropertyGroup = field(default_factory=PropertyGroup)

    def to_dict(self) -> dict:
        return {"name": self.name, "parameters": self.parameters.to_dict()}


# ── Marker ───────────────────────────────────────────────────────────────────

@dataclass
class Marker:
    name: str = ""
    duration: float = 0.0
    is_protected: bool = False
    label_color: int = 0

    def to_dict(self) -> dict:
        d: dict = {"name": self.name, "duration": self.duration}
        if self.label_color:
            d["labelColor"] = self.label_color
        return d


# ── Layer ────────────────────────────────────────────────────────────────────

LAYER_TYPES = {0: "asset", 1: "light", 2: "camera", 3: "text", 4: "shape"}

BLEND_MODES = {
    2: "normal", 3: "dissolve",
    4: "add", 5: "multiply", 6: "screen",
    7: "overlay", 8: "softLight", 9: "hardLight",
    10: "darken", 11: "lighten", 12: "classicDifference",
    13: "hue", 14: "saturation", 15: "color", 16: "luminosity",
    17: "stencilAlpha", 18: "stencilLuma",
    19: "silhouetteAlpha", 20: "silhouetteLuma",
    21: "luminescentPremul", 22: "alphaAdd",
    23: "classicColorDodge", 24: "classicColorBurn",
    25: "exclusion", 26: "difference",
    27: "colorDodge", 28: "colorBurn",
    29: "linearDodge", 30: "linearBurn",
    31: "linearLight", 32: "vividLight", 33: "pinLight", 34: "hardMix",
    35: "lighterColor", 36: "darkerColor",
    37: "subtract", 38: "divide",
}

MATTE_MODES = {0: "none", 1: "alpha", 2: "alphaInverted", 3: "luma", 4: "lumaInverted"}


@dataclass
class Layer:
    id: int = 0
    name: str = ""
    layer_type: int = 4
    quality: int = 1
    asset_id: int = 0
    parent_id: int = 0
    matte_id: int = 0
    blend_mode: int = 2
    matte_mode: int = 0
    label_color: int = 0
    in_time: float = 0.0
    out_time: float = 0.0
    start_time: float = 0.0
    time_stretch: float = 1.0
    visible: bool = True
    solo: bool = False
    shy: bool = False
    locked: bool = False
    is_null: bool = False
    is_guide: bool = False
    is_adjustment: bool = False
    threedimensional: bool = False
    auto_orient: bool = False
    bicubic_sampling: bool = False
    continuously_rasterize: bool = False
    effects_enabled: bool = False
    motion_blur_enabled: bool = False
    properties: PropertyGroup = field(default_factory=PropertyGroup)

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "name": self.name,
            "type": LAYER_TYPES.get(self.layer_type, self.layer_type),
            "inTime": self.in_time,
            "outTime": self.out_time,
            "startTime": self.start_time,
        }
        if self.time_stretch != 1.0:
            d["timeStretch"] = self.time_stretch
        if self.asset_id:
            d["assetId"] = self.asset_id
        if self.parent_id:
            d["parentId"] = self.parent_id
        if self.blend_mode != 2:
            d["blendMode"] = BLEND_MODES.get(self.blend_mode, self.blend_mode)
        if self.matte_mode:
            d["matteMode"] = MATTE_MODES.get(self.matte_mode, self.matte_mode)
            d["matteId"] = self.matte_id
        # flags
        flags = {}
        for attr in ("visible", "solo", "shy", "locked", "is_null", "is_guide",
                      "is_adjustment", "threedimensional", "auto_orient",
                      "effects_enabled", "motion_blur_enabled",
                      "continuously_rasterize", "bicubic_sampling"):
            val = getattr(self, attr)
            default = attr == "visible"  # visible defaults to True
            if val != default:
                flags[_camel(attr)] = val
        if flags:
            d["flags"] = flags
        if self.properties.properties:
            d["properties"] = self.properties.to_dict()
        return d


# ── Composition ──────────────────────────────────────────────────────────────

@dataclass
class Composition:
    id: int = 0
    name: str = ""
    width: int = 0
    height: int = 0
    framerate: float = 0.0
    duration: float = 0.0
    in_time: float = 0.0
    out_time: float = 0.0
    playhead_time: float = 0.0
    color: Color = field(default_factory=Color)
    layers: list[Layer] = field(default_factory=list)
    markers: Layer | None = None
    views: list[Layer] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "id": self.id,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "framerate": self.framerate,
            "duration": self.duration,
            "inTime": self.in_time,
            "outTime": self.out_time,
            "backgroundColor": self.color.to_dict(),
            "layers": [l.to_dict() for l in self.layers],
        }
        if self.markers:
            d["markers"] = self.markers.to_dict()
        return d


# ── Assets ───────────────────────────────────────────────────────────────────

@dataclass
class SequenceInfo:
    count: int = 0
    start: int = 0
    end: int = 0
    max_length: int = 0

    def to_dict(self) -> dict:
        return {"count": self.count, "start": self.start,
                "end": self.end, "maxLength": self.max_length}


@dataclass
class ImageAsset:
    id: int = 0
    name: str = ""
    full_path: str = ""
    width: int = 0
    height: int = 0
    sequence_info: SequenceInfo | None = None

    def to_dict(self) -> dict:
        d: dict = {"type": "image", "id": self.id, "name": self.name,
                    "fullPath": self.full_path, "width": self.width, "height": self.height}
        if self.sequence_info:
            d["sequenceInfo"] = self.sequence_info.to_dict()
        return d


@dataclass
class SolidAsset:
    id: int = 0
    name: str = ""
    color: Color = field(default_factory=Color)
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict:
        return {"type": "solid", "id": self.id, "name": self.name,
                "color": self.color.to_dict(), "width": self.width, "height": self.height}


# ── Render Queue ─────────────────────────────────────────────────────────────

OUTPUT_FORMATS = {
    "MooV": "QuickTime",
    "JPEG": "JPEG Sequence",
    "png!": "PNG Sequence",
    "TIFF": "TIFF Sequence",
    "SGI ": "SGI Sequence",
    "TARG": "Targa Sequence",
    "BMPf": "BMP Sequence",
    "8BPS": "Photoshop Sequence",
    "EXRn": "OpenEXR Sequence",
    "WAVf": "WAV",
    "AIFF": "AIFF",
    "MPG ": "MPEG",
}


@dataclass
class OutputModule:
    format: str = ""
    format_label: str = ""
    template_name: str = ""
    file_template: str = ""
    output_path: str = ""
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict:
        d: dict = {"format": self.format}
        if self.format_label:
            d["formatLabel"] = self.format_label
        if self.template_name:
            d["templateName"] = self.template_name
        if self.file_template:
            d["fileTemplate"] = self.file_template
        if self.output_path:
            d["outputPath"] = self.output_path
        if self.width:
            d["width"] = self.width
            d["height"] = self.height
        return d


RQ_STATUS = {
    0: "unqueued",
    1: "queued",
    2: "unqueued",
    3: "rendering",
    4: "done",
    5: "needs_output",
}


@dataclass
class RenderQueueItem:
    comp_id: int = 0
    comp_name: str = ""
    status: int = 0
    render_settings: str = ""
    start_frame: int | None = None
    end_frame: int | None = None
    output_modules: list[OutputModule] = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {
            "compId": self.comp_id,
            "compName": self.comp_name,
            "status": RQ_STATUS.get(self.status, self.status),
        }
        if self.render_settings:
            d["renderSettings"] = self.render_settings
        if self.start_frame is not None:
            d["startFrame"] = self.start_frame
        if self.end_frame is not None:
            d["endFrame"] = self.end_frame
        if self.output_modules:
            d["outputModules"] = [om.to_dict() for om in self.output_modules]
        return d


# ── Folder / Project ─────────────────────────────────────────────────────────

@dataclass
class Folder:
    id: int = -1
    name: str = ""
    items: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d: dict = {"id": self.id}
        if self.name:
            d["name"] = self.name
        if self.items:
            d["items"] = [_val(i) for i in self.items]
        return d


@dataclass
class Project:
    folder: Folder = field(default_factory=Folder)
    compositions: list[Composition] = field(default_factory=list)
    assets: dict[int, ImageAsset | SolidAsset | Composition] = field(default_factory=dict)
    effects: dict[str, EffectDefinition] = field(default_factory=dict)
    render_queue: list[RenderQueueItem] = field(default_factory=list)
    current_item: Any = None

    def to_dict(self) -> dict:
        d: dict = {
            "folder": self.folder.to_dict(),
            "compositions": [c.to_dict() for c in self.compositions],
            "assets": {str(k): _val(v) for k, v in self.assets.items()},
            "effects": {k: v.to_dict() for k, v in self.effects.items()},
        }
        if self.render_queue:
            d["renderQueue"] = [rq.to_dict() for rq in self.render_queue]
        return d


# ── Helpers ──────────────────────────────────────────────────────────────────

def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _val(v: Any) -> Any:
    if v is None:
        return None
    if hasattr(v, "to_dict"):
        return v.to_dict()
    if isinstance(v, (int, float, str, bool)):
        return v
    if isinstance(v, list):
        return [_val(i) for i in v]
    if isinstance(v, dict):
        return {str(k): _val(val) for k, val in v.items()}
    return str(v)
