"""Layer wrappers mirroring AE scripting Layer subclasses."""

from __future__ import annotations

from typing import Any, Iterator, TYPE_CHECKING

from aep_parser.models import (
    AnimatedProperty,
    EffectInstance,
    Layer as LayerModel,
    MaskData,
    NamedProperty,
    PropertyGroup as PGModel,
    TextProperty as TextPropertyModel,
)

from ._constants import (
    BlendingMode,
    LayerQuality,
    LayerType,
    MATCH_NAMES,
    TrackMatteType,
)
from ._effect import Effect
from ._mask import Mask
from ._property import (
    MarkerProperty,
    Property,
    PropertyGroup,
    TextSourceProperty,
    _find_property_by_name,
    _wrap_named_property,
)

if TYPE_CHECKING:
    from ._comp import CompItem

# Save builtin property before it gets shadowed by method definitions
_property = property


# Layer base class


class Layer:
    """Base layer wrapper mirroring AE scripting Layer object."""

    def __init__(self, model: LayerModel, index: int,
                 containing_comp: CompItem | None = None) -> None:
        self._model = model
        self._index = index
        self._containing_comp = containing_comp
        self._children: list[tuple[str, str, Any]] | None = None
        self._effects_list: list[Effect] | None = None
        self._masks_list: list[Mask] | None = None

    # Identity

    @_property
    def id(self) -> int:
        """Internal layer ID (used for write operations)."""
        return self._model.id

    @_property
    def index(self) -> int:
        """1-based index in the composition."""
        return self._index

    @_property
    def name(self) -> str:
        return self._model.name

    @name.setter
    def name(self, new_name: str) -> None:
        self._model.name = new_name
        if self._containing_comp is not None:
            project = getattr(self._containing_comp, '_project', None)
            if project is not None and project._chunk_tree is not None:
                from ._writer import set_layer_name
                set_layer_name(project._chunk_tree,
                               self._containing_comp.id, self._model.id,
                               new_name, project._big_endian)

    @_property
    def containing_comp(self) -> CompItem | None:
        return self._containing_comp

    @_property
    def label(self) -> int:
        return self._model.label_color

    # Flags

    @_property
    def enabled(self) -> bool:
        return self._model.visible

    @_property
    def solo(self) -> bool:
        return self._model.solo

    @_property
    def shy(self) -> bool:
        return self._model.shy

    @_property
    def locked(self) -> bool:
        return self._model.locked

    # Timing

    @_property
    def in_point(self) -> float:
        return self._model.in_time

    @_property
    def out_point(self) -> float:
        return self._model.out_time

    @_property
    def start_time(self) -> float:
        return self._model.start_time

    @_property
    def stretch(self) -> float:
        return self._model.time_stretch

    # Layer type flags

    @_property
    def null_layer(self) -> bool:
        return self._model.is_null

    @_property
    def guide_layer(self) -> bool:
        return self._model.is_guide

    @_property
    def adjustment_layer(self) -> bool:
        return self._model.is_adjustment

    @_property
    def three_d_layer(self) -> bool:
        return self._model.threedimensional

    @_property
    def auto_orient(self) -> bool:
        return self._model.auto_orient

    @_property
    def blending_mode(self) -> BlendingMode | int:
        try:
            return BlendingMode(self._model.blend_mode)
        except ValueError:
            return self._model.blend_mode

    @_property
    def track_matte_type(self) -> TrackMatteType | int:
        try:
            return TrackMatteType(self._model.matte_mode)
        except ValueError:
            return self._model.matte_mode

    @_property
    def effects_active(self) -> bool:
        return self._model.effects_enabled

    @_property
    def motion_blur(self) -> bool:
        return self._model.motion_blur_enabled

    @_property
    def quality(self) -> LayerQuality:
        return LayerQuality(self._model.quality)

    @_property
    def sampling_quality(self) -> bool:
        return self._model.bicubic_sampling

    @_property
    def collapse_transformation(self) -> bool:
        return self._model.continuously_rasterize

    # Parent

    @_property
    def parent(self) -> Layer | None:
        if not self._model.parent_id or self._containing_comp is None:
            return None
        for layer_wrapper in self._containing_comp.layers:
            if layer_wrapper._model.id == self._model.parent_id:
                return layer_wrapper
        return None

    # Property tree

    def _ensure_children(self) -> list[tuple[str, str, Any]]:
        if self._children is not None:
            return self._children
        self._children = []
        for np in self._model.properties.properties:
            wrapped = _wrap_layer_named_property(np)
            mn = np.match_name
            if isinstance(wrapped, (Property, PropertyGroup)):
                dn = wrapped.name
                wrapped._layer_ref = self
                wrapped._match_path = [mn]
            else:
                dn = MATCH_NAMES.get(mn, mn)
            self._children.append((mn, dn, wrapped))
        return self._children

    @_property
    def num_properties(self) -> int:
        return len(self._ensure_children())

    def property(self, name_or_index: str | int) -> Any:
        """Lookup by 1-based index or name."""
        children = self._ensure_children()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(children):
                return children[idx][2]
            return None
        return _find_property_by_name(children, name_or_index)

    def __call__(self, name_or_index: str | int) -> Any:
        result = self.property(name_or_index)
        if result is None:
            raise KeyError(f"Property {name_or_index!r} not found on layer {self.name!r}")
        return result

    def __getitem__(self, name_or_index: str | int) -> Any:
        return self.__call__(name_or_index)

    # Transform shortcuts

    def _find_transform_prop(self, match_name: str) -> Property | None:
        transform_group = self.property("ADBE Transform Group")
        if transform_group is None:
            transform_group = self.property("Transform")
        if isinstance(transform_group, PropertyGroup):
            result = transform_group.property(match_name)
            if isinstance(result, Property):
                return result
        return None

    @_property
    def transform(self) -> PropertyGroup | None:
        result = self.property("ADBE Transform Group")
        if result is None:
            result = self.property("Transform")
        return result if isinstance(result, PropertyGroup) else None

    @_property
    def position(self) -> Property | None:
        return self._find_transform_prop("ADBE Position")

    @_property
    def scale(self) -> Property | None:
        return self._find_transform_prop("ADBE Scale")

    @_property
    def rotation(self) -> Property | None:
        return self._find_transform_prop("ADBE Rotate Z")

    @_property
    def opacity(self) -> Property | None:
        return self._find_transform_prop("ADBE Opacity")

    @_property
    def anchor_point(self) -> Property | None:
        return self._find_transform_prop("ADBE Anchor Point")

    @_property
    def orientation(self) -> Property | None:
        return self._find_transform_prop("ADBE Orientation")

    @_property
    def rotation_x(self) -> Property | None:
        return self._find_transform_prop("ADBE Rotate X")

    @_property
    def rotation_y(self) -> Property | None:
        return self._find_transform_prop("ADBE Rotate Y")

    @_property
    def rotation_z(self) -> Property | None:
        return self._find_transform_prop("ADBE Rotate Z")

    @_property
    def position_x(self) -> Property | None:
        return self._find_transform_prop("ADBE Position_0")

    @_property
    def position_y(self) -> Property | None:
        return self._find_transform_prop("ADBE Position_1")

    @_property
    def position_z(self) -> Property | None:
        return self._find_transform_prop("ADBE Position_2")

    # Time remap

    @_property
    def time_remap_enabled(self) -> bool:
        tr = self.property("ADBE Time Remapping")
        return tr is not None

    @_property
    def time_remap(self) -> Property | None:
        result = self.property("ADBE Time Remapping")
        return result if isinstance(result, Property) else None

    # Markers

    @_property
    def marker_property(self) -> MarkerProperty | None:
        result = self.property("ADBE Marker")
        if isinstance(result, Property):
            return MarkerProperty(result._model)
        return None

    # Effects

    def _ensure_effects(self) -> list[Effect]:
        if self._effects_list is not None:
            return self._effects_list
        self._effects_list = []
        # Scan raw model properties for effect parade -> effect instances
        for np in self._model.properties.properties:
            if np.match_name == "ADBE Effect Parade" and isinstance(np.value, PGModel):
                for child_np in np.value.properties:
                    if isinstance(child_np.value, EffectInstance):
                        self._effects_list.append(
                            Effect(child_np.value, match_name=child_np.match_name))
                break
        return self._effects_list

    @_property
    def num_effects(self) -> int:
        return len(self._ensure_effects())

    def effect(self, name_or_index: str | int) -> Effect | None:
        """Lookup effect by 1-based index or name."""
        effects = self._ensure_effects()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(effects):
                return effects[idx]
            return None
        name_lower = name_or_index.lower()
        for e in effects:
            if e.match_name == name_or_index or e.name.lower() == name_lower:
                return e
        return None

    # Masks

    def _ensure_masks(self) -> list[Mask]:
        if self._masks_list is not None:
            return self._masks_list
        self._masks_list = []
        for np in self._model.properties.properties:
            if np.match_name == "ADBE Mask Parade" and isinstance(np.value, PGModel):
                for child_np in np.value.properties:
                    if isinstance(child_np.value, MaskData):
                        self._masks_list.append(
                            Mask(child_np.value, match_name=child_np.match_name))
                break
        return self._masks_list

    @_property
    def num_masks(self) -> int:
        return len(self._ensure_masks())

    def mask(self, index: int) -> Mask | None:
        """Get mask by 1-based index."""
        masks = self._ensure_masks()
        idx = index - 1
        if 0 <= idx < len(masks):
            return masks[idx]
        return None

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, index={self.index})"


# Layer subclasses


class AVLayer(Layer):
    """Asset-based layer (footage, solid, precomp)."""

    @_property
    def source(self) -> Any:
        if self._containing_comp is None:
            return None
        proj = getattr(self._containing_comp, '_project', None)
        if proj is None:
            return None
        return proj._model.assets.get(self._model.asset_id)


class TextLayer(Layer):
    """Text layer."""

    @_property
    def source_text(self) -> TextSourceProperty | None:
        text_group = self.property("ADBE Text Properties")
        if isinstance(text_group, PropertyGroup):
            for _, _, child in text_group._ensure_children():
                if isinstance(child, TextSourceProperty):
                    return child
        return None


class ShapeLayer(Layer):
    """Shape layer."""

    @_property
    def contents(self) -> PropertyGroup | None:
        result = self.property("ADBE Root Vectors Group")
        if result is None:
            result = self.property("Contents")
        return result if isinstance(result, PropertyGroup) else None


class CameraLayer(Layer):
    """Camera layer."""

    @_property
    def camera_options(self) -> PropertyGroup | None:
        result = self.property("ADBE Camera Options Group")
        if result is None:
            result = self.property("Camera Options")
        return result if isinstance(result, PropertyGroup) else None


class LightLayer(Layer):
    """Light layer (placeholder for future expansion)."""
    pass


# Factory


def _make_layer(model: LayerModel, index: int,
                containing_comp: CompItem | None = None) -> Layer:
    """Create the appropriate Layer subclass based on layer_type."""
    lt = model.layer_type
    if lt == LayerType.TEXT:
        return TextLayer(model, index, containing_comp)
    if lt == LayerType.SHAPE:
        return ShapeLayer(model, index, containing_comp)
    if lt == LayerType.CAMERA:
        return CameraLayer(model, index, containing_comp)
    if lt == LayerType.LIGHT:
        return LightLayer(model, index, containing_comp)
    if lt == LayerType.ASSET:
        return AVLayer(model, index, containing_comp)
    return Layer(model, index, containing_comp)


# Helpers


def _wrap_layer_named_property(np: NamedProperty) -> Any:
    """Wrap a NamedProperty, handling EffectInstance and MaskData specially."""
    val = np.value
    mn = np.match_name
    if isinstance(val, EffectInstance):
        return Effect(val, match_name=mn)
    if isinstance(val, MaskData):
        return Mask(val, match_name=mn)
    return _wrap_named_property(np)
