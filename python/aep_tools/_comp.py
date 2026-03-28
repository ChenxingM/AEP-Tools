"""CompItem wrapper mirroring AE scripting CompItem object."""

from __future__ import annotations

from typing import Any, Iterator, TYPE_CHECKING

from aep_parser.models import (
    AnimatedProperty,
    Composition,
    Layer as LayerModel,
    NamedProperty,
)

from ._layer import (
    AVLayer,
    CameraLayer,
    Layer,
    LightLayer,
    ShapeLayer,
    TextLayer,
    _make_layer,
)
from ._property import MarkerProperty, _wrap_named_property

if TYPE_CHECKING:
    from ._project import Project


# LayerCollection


class LayerCollection:
    """1-based indexed collection of layers."""

    def __init__(self, layers: list[Layer]) -> None:
        self._layers = layers

    def __getitem__(self, index: int) -> Layer:
        """1-based index access."""
        if isinstance(index, int):
            idx = index - 1
            if 0 <= idx < len(self._layers):
                return self._layers[idx]
            raise IndexError(f"Layer index {index} out of range (1-{len(self._layers)})")
        raise TypeError(f"Layer index must be int, got {type(index).__name__}")

    def __len__(self) -> int:
        return len(self._layers)

    def __iter__(self) -> Iterator[Layer]:
        return iter(self._layers)

    def __repr__(self) -> str:
        return f"LayerCollection(num_layers={len(self._layers)})"


# CompItem
class CompItem:
    """Wraps a Composition model, providing AE-scripting-style access."""

    def __init__(self, model: Composition, project: Project | None = None) -> None:
        self._model = model
        self._project = project
        self._layers_cache: list[Layer] | None = None

    @property
    def type_name(self) -> str:
        return "Composition"

    @property
    def id(self) -> int:
        return self._model.id

    @property
    def name(self) -> str:
        return self._model.name

    @name.setter
    def name(self, new_name: str) -> None:
        self._model.name = new_name
        if self._project is not None and self._project._chunk_tree is not None:
            from ._writer import set_comp_name
            set_comp_name(self._project._chunk_tree, self._model.id,
                          new_name, self._project._big_endian)

    def _write_cdta(self, writer_fn_name: str, *args) -> None:
        """Call a cdta writer function with (root, comp_id, *args, big_endian)."""
        if self._project is not None and self._project._chunk_tree is not None:
            import importlib
            mod = importlib.import_module('._writer', package='aep_tools')
            fn = getattr(mod, writer_fn_name)
            fn(self._project._chunk_tree, self._model.id,
               *args, self._project._big_endian)

    @property
    def width(self) -> int:
        return self._model.width

    @width.setter
    def width(self, value: int) -> None:
        self._model.width = value
        self._write_cdta('set_comp_dimensions', value, self._model.height)

    @property
    def height(self) -> int:
        return self._model.height

    @height.setter
    def height(self, value: int) -> None:
        self._model.height = value
        self._write_cdta('set_comp_dimensions', self._model.width, value)

    @property
    def duration(self) -> float:
        return self._model.duration

    @duration.setter
    def duration(self, value: float) -> None:
        self._model.duration = value
        self._write_cdta('set_comp_duration', value)

    @property
    def frame_rate(self) -> float:
        return self._model.framerate

    @frame_rate.setter
    def frame_rate(self, value: float) -> None:
        self._model.framerate = value
        self._write_cdta('set_comp_framerate', value)

    @property
    def frame_duration(self) -> float:
        return 1.0 / self._model.framerate if self._model.framerate > 0 else 0.0

    @property
    def work_area_start(self) -> float:
        return self._model.in_time

    @work_area_start.setter
    def work_area_start(self, value: float) -> None:
        self._model.in_time = value
        self._write_cdta('set_comp_work_area_start', value)

    @property
    def work_area_duration(self) -> float:
        return self._model.out_time - self._model.in_time

    @work_area_duration.setter
    def work_area_duration(self, value: float) -> None:
        end = self._model.in_time + value
        self._model.out_time = end
        self._write_cdta('set_comp_work_area_end', end)

    # Comp flags

    def _write_comp_flag(self, model_attr: str, flag_name: str, value: bool) -> None:
        setattr(self._model, model_attr, value)
        self._write_cdta('set_comp_flag', flag_name, value)

    @property
    def draft3d(self) -> bool:
        return self._model.draft3d

    @draft3d.setter
    def draft3d(self, value: bool) -> None:
        self._write_comp_flag('draft3d', 'draft3d', value)

    @property
    def motion_blur(self) -> bool:
        return self._model.motion_blur

    @motion_blur.setter
    def motion_blur(self, value: bool) -> None:
        self._write_comp_flag('motion_blur', 'motion_blur', value)

    @property
    def frame_blending(self) -> bool:
        return self._model.frame_blending

    @frame_blending.setter
    def frame_blending(self, value: bool) -> None:
        self._write_comp_flag('frame_blending', 'frame_blending', value)

    @property
    def hide_shy_layers(self) -> bool:
        return self._model.hide_shy_layers

    @hide_shy_layers.setter
    def hide_shy_layers(self, value: bool) -> None:
        self._write_comp_flag('hide_shy_layers', 'hide_shy_layers', value)

    @property
    def preserve_nested_resolution(self) -> bool:
        return self._model.preserve_nested_resolution

    @preserve_nested_resolution.setter
    def preserve_nested_resolution(self, value: bool) -> None:
        self._write_comp_flag('preserve_nested_resolution', 'preserve_nested_resolution', value)

    @property
    def preserve_nested_frame_rate(self) -> bool:
        return self._model.preserve_nested_frame_rate

    @preserve_nested_frame_rate.setter
    def preserve_nested_frame_rate(self, value: bool) -> None:
        self._write_comp_flag('preserve_nested_frame_rate', 'preserve_nested_frame_rate', value)

    # Shutter / motion blur settings

    @property
    def shutter_angle(self) -> int:
        return self._model.shutter_angle

    @shutter_angle.setter
    def shutter_angle(self, value: int) -> None:
        self._model.shutter_angle = value
        self._write_cdta('set_comp_shutter_angle', value)

    @property
    def shutter_phase(self) -> int:
        return self._model.shutter_phase

    @shutter_phase.setter
    def shutter_phase(self, value: int) -> None:
        self._model.shutter_phase = value
        self._write_cdta('set_comp_shutter_phase', value)

    @property
    def motion_blur_samples_per_frame(self) -> int:
        return self._model.motion_blur_samples_per_frame

    @motion_blur_samples_per_frame.setter
    def motion_blur_samples_per_frame(self, value: int) -> None:
        self._model.motion_blur_samples_per_frame = value
        self._write_cdta('set_comp_motion_blur_samples', value,
                         self._model.motion_blur_adaptive_sample_limit)

    @property
    def motion_blur_adaptive_sample_limit(self) -> int:
        return self._model.motion_blur_adaptive_sample_limit

    @motion_blur_adaptive_sample_limit.setter
    def motion_blur_adaptive_sample_limit(self, value: int) -> None:
        self._model.motion_blur_adaptive_sample_limit = value
        self._write_cdta('set_comp_motion_blur_samples',
                         self._model.motion_blur_samples_per_frame, value)

    # Pixel aspect / display start time / drop frame

    @property
    def pixel_aspect(self) -> float:
        return self._model.pixel_aspect

    @pixel_aspect.setter
    def pixel_aspect(self, value: float) -> None:
        self._model.pixel_aspect = value
        self._write_cdta('set_comp_pixel_aspect', value)

    @property
    def display_start_time(self) -> float:
        return self._model.display_start_time

    @display_start_time.setter
    def display_start_time(self, value: float) -> None:
        self._model.display_start_time = value
        self._write_cdta('set_comp_display_start_time', value)

    @property
    def drop_frame(self) -> bool:
        return self._model.drop_frame

    @drop_frame.setter
    def drop_frame(self, value: bool) -> None:
        self._model.drop_frame = value
        self._write_cdta('set_comp_drop_frame', value)

    @property
    def bg_color(self) -> list[float]:
        c = self._model.color
        return [c.r, c.g, c.b]

    @bg_color.setter
    def bg_color(self, value: list[float]) -> None:
        self._model.color.r = value[0]
        self._model.color.g = value[1]
        self._model.color.b = value[2]
        self._write_cdta('set_comp_bgcolor', int(value[0]), int(value[1]),
                         int(value[2]))

    # Layers

    def _ensure_layers(self) -> list[Layer]:
        if self._layers_cache is not None:
            return self._layers_cache
        self._layers_cache = [
            _make_layer(lm, i + 1, self)
            for i, lm in enumerate(self._model.layers)
        ]
        return self._layers_cache

    @property
    def num_layers(self) -> int:
        return len(self._model.layers)

    @property
    def layers(self) -> LayerCollection:
        return LayerCollection(self._ensure_layers())

    def layer(self, name_or_index: str | int) -> Layer | None:
        """Lookup layer by 1-based index or name."""
        layers = self._ensure_layers()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(layers):
                return layers[idx]
            return None
        for lyr in layers:
            if lyr.name == name_or_index:
                return lyr
        return None

    # Layer CRUD

    def _invalidate_layers(self) -> None:
        self._layers_cache = None

    def add_solid(self, name: str = "Black Solid",
                  color: tuple[float, float, float] = (0.0, 0.0, 0.0),
                  width: int | None = None,
                  height: int | None = None) -> int:
        """Add a solid layer. Returns the new layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_solid_layer
        w = width if width is not None else self._model.width
        h = height if height is not None else self._model.height
        lid = add_solid_layer(
            self._project._chunk_tree, self._model.id, name,
            w, h, color[0], color[1], color[2],
            self._project._big_endian)
        self._invalidate_layers()
        return lid

    def remove_layer(self, index_or_layer) -> None:
        """Remove a layer by 1-based index or Layer object."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot remove layer: project not writable")
        from ._writer import remove_layer as _remove
        if isinstance(index_or_layer, int):
            lyr = self.layer(index_or_layer)
            if lyr is None:
                raise IndexError(f"Layer index {index_or_layer} out of range")
        else:
            lyr = index_or_layer
        _remove(self._project._chunk_tree, self._model.id,
                lyr._model.id, self._project._big_endian)
        self._invalidate_layers()

    def duplicate_layer(self, index_or_layer) -> Layer:
        """Duplicate a layer. Returns the new Layer."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot duplicate layer: project not writable")
        from ._writer import duplicate_layer as _dup
        if isinstance(index_or_layer, int):
            lyr = self.layer(index_or_layer)
            if lyr is None:
                raise IndexError(f"Layer index {index_or_layer} out of range")
        else:
            lyr = index_or_layer
        new_id = _dup(self._project._chunk_tree, self._model.id,
                      lyr._model.id, self._project._big_endian)
        self._invalidate_layers()
        # Find the new layer
        for l in self._ensure_layers():
            if l._model.id == new_id:
                return l
        return self.layer(lyr.index + 1)

    def move_layer(self, index_or_layer, new_index: int) -> None:
        """Move a layer to a new position (1-based)."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot move layer: project not writable")
        from ._writer import move_layer as _move
        if isinstance(index_or_layer, int):
            lyr = self.layer(index_or_layer)
            if lyr is None:
                raise IndexError(f"Layer index {index_or_layer} out of range")
        else:
            lyr = index_or_layer
        _move(self._project._chunk_tree, self._model.id,
              lyr._model.id, new_index, self._project._big_endian)
        self._invalidate_layers()

    def add_null(self, name: str = "Null 1") -> int:
        """Add a null object layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_null_layer
        lid = add_null_layer(self._project._chunk_tree, self._model.id,
                             name, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def add_adjustment(self, name: str = "Adjustment Layer",
                       width: int | None = None,
                       height: int | None = None) -> int:
        """Add an adjustment layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_adjustment_layer
        lid = add_adjustment_layer(
            self._project._chunk_tree, self._model.id, name,
            width, height, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def add_shape(self, name: str = "Shape Layer") -> int:
        """Add an empty shape layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_shape_layer
        lid = add_shape_layer(self._project._chunk_tree, self._model.id,
                              name, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def add_text(self, name: str = "Text Layer") -> int:
        """Add a text layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_text_layer
        lid = add_text_layer(self._project._chunk_tree, self._model.id,
                             name, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def add_camera(self, name: str = "Camera") -> int:
        """Add a camera layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_camera_layer
        lid = add_camera_layer(self._project._chunk_tree, self._model.id,
                               name, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def add_light(self, name: str = "Light") -> int:
        """Add a light layer. Returns layer_id."""
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot add layer: project not writable")
        from ._writer import add_light_layer
        lid = add_light_layer(self._project._chunk_tree, self._model.id,
                              name, self._project._big_endian)
        self._invalidate_layers()
        return lid

    def precompose(self, layer_ids: list[int],
                   new_comp_name: str) -> tuple[int, int]:
        """Precompose layers into a new composition.

        Args:
            layer_ids: List of layer IDs to precompose.
            new_comp_name: Name for the new composition.

        Returns:
            (new_comp_id, precomp_layer_id)
        """
        if self._project is None or self._project._chunk_tree is None:
            raise RuntimeError("Cannot precompose: project not writable")
        from ._writer import precompose_layers
        result = precompose_layers(
            self._project._chunk_tree, self._model.id,
            layer_ids, new_comp_name, self._project._big_endian)
        self._invalidate_layers()
        return result

    # Markers

    @property
    def marker_property(self) -> MarkerProperty | None:
        if self._model.markers is None:
            return None
        # markers is a Layer model; find the marker AnimatedProperty in its properties
        for np in self._model.markers.properties.properties:
            if np.match_name == "ADBE Marker":
                val = np.value
                if isinstance(val, AnimatedProperty):
                    return MarkerProperty(val)
        return None

    def __repr__(self) -> str:
        return f"CompItem({self.name!r}, {self.width}x{self.height})"
