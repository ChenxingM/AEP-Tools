"""Project wrapper mirroring AE scripting app.project object."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import Any, Iterator

from aep_parser import parse_aepx
from aep_parser._parser.chunk import Chunk
from aep_parser.models import (
    Composition,
    Folder,
    ImageAsset,
    OutputModule,
    Project as ProjectModel,
    RenderQueueItem as RQItemModel,
    SolidAsset,
)

from ._comp import CompItem
from ._writer import (
    save_aep, set_asset_path, set_comp_name, set_layer_name,
    set_property_value, set_keyframe_value, set_keyframe_time,
    set_keyframe_interpolation, set_keyframe_ease,
    set_layer_flag, set_layer_label, set_layer_blend_mode,
    set_layer_track_matte, set_layer_quality, set_layer_time_field,
    set_layer_preserve_transparency, set_layer_light_type,
    set_comp_dimensions, set_comp_bgcolor, set_comp_framerate,
    set_comp_duration,
    set_comp_work_area_start, set_comp_work_area_end,
    set_comp_flag, set_comp_shutter_angle, set_comp_shutter_phase,
    set_comp_motion_blur_samples, set_comp_pixel_aspect,
    set_comp_display_start_time, set_comp_drop_frame,
    set_project_bits_per_channel, set_project_linearize_working_space,
    set_project_audio_sample_rate, set_project_working_gamma,
    set_project_compensate_scene_referred,
)


# Item wrappers


class FolderItem:
    """Wraps a Folder model."""

    def __init__(self, model: Folder, project: Project) -> None:
        self._model = model
        self._project = project
        self._items_cache: list[Any] | None = None

    @property
    def type_name(self) -> str:
        return "Folder"

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def id(self) -> int:
        return self._model.id

    def _ensure_items(self) -> list[Any]:
        if self._items_cache is not None:
            return self._items_cache
        self._items_cache = []
        for item in self._model.items:
            self._items_cache.append(_wrap_item(item, self._project))
        return self._items_cache

    @property
    def num_items(self) -> int:
        return len(self._ensure_items())

    @property
    def items(self) -> ItemCollection:
        return ItemCollection(self._ensure_items())


class FootageItem:
    """Wraps an ImageAsset or SolidAsset."""

    def __init__(self, model: ImageAsset | SolidAsset,
                 project: Project | None = None) -> None:
        self._model = model
        self._project = project

    @property
    def type_name(self) -> str:
        if isinstance(self._model, SolidAsset):
            return "Solid"
        return "Footage"

    @property
    def name(self) -> str:
        return self._model.name

    @property
    def id(self) -> int:
        return self._model.id

    @property
    def width(self) -> int:
        return self._model.width

    @property
    def height(self) -> int:
        return self._model.height

    @property
    def file(self) -> str | None:
        if isinstance(self._model, ImageAsset):
            return self._model.full_path or None
        return None

    @file.setter
    def file(self, new_path: str) -> None:
        """Set the footage file path.

        Updates both the in-memory model and the chunk tree.
        Mirrors AE scripting ``footageItem.file = new File(path)``.
        """
        if not isinstance(self._model, ImageAsset):
            raise TypeError("Cannot set file path on a SolidAsset")
        self._model.full_path = new_path
        if self._project is not None and self._project._chunk_tree is not None:
            set_asset_path(self._project._chunk_tree, self._model.id,
                           new_path, self._project._big_endian)

    @property
    def color(self) -> list[float] | None:
        if isinstance(self._model, SolidAsset):
            c = self._model.color
            return [c.r, c.g, c.b, c.a]
        return None

    def __repr__(self) -> str:
        return f"FootageItem({self.name!r})"


# ItemCollection


class ItemCollection:
    """1-based indexed collection of project items."""

    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def __getitem__(self, index: int) -> Any:
        if isinstance(index, int):
            idx = index - 1
            if 0 <= idx < len(self._items):
                return self._items[idx]
            raise IndexError(f"Item index {index} out of range (1-{len(self._items)})")
        raise TypeError(f"Item index must be int, got {type(index).__name__}")

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator:
        return iter(self._items)

    def __repr__(self) -> str:
        return f"ItemCollection(num_items={len(self._items)})"


# Render Queue


class RenderQueueItemWrapper:
    """Wraps a RenderQueueItem model."""

    def __init__(self, model: RQItemModel) -> None:
        self._model = model

    @property
    def comp_name(self) -> str:
        return self._model.comp_name

    @property
    def status(self) -> int:
        return self._model.status

    @property
    def num_output_modules(self) -> int:
        return len(self._model.output_modules)

    def output_module(self, index: int) -> OutputModule | None:
        idx = index - 1
        if 0 <= idx < len(self._model.output_modules):
            return self._model.output_modules[idx]
        return None

    def __repr__(self) -> str:
        return f"RenderQueueItem({self.comp_name!r})"


class RenderQueue:
    """Wraps the project render queue."""

    def __init__(self, items: list[RQItemModel]) -> None:
        self._items = [RenderQueueItemWrapper(m) for m in items]

    @property
    def num_items(self) -> int:
        return len(self._items)

    def item(self, index: int) -> RenderQueueItemWrapper | None:
        idx = index - 1
        if 0 <= idx < len(self._items):
            return self._items[idx]
        return None

    def __repr__(self) -> str:
        return f"RenderQueue(num_items={len(self._items)})"


# Project


class Project:
    """Top-level project wrapper mirroring AE scripting ``app.project``."""

    def __init__(self, model: ProjectModel, file_path: str | None = None,
                 chunk_tree: Chunk | None = None,
                 big_endian: bool = True,
                 trailing_data: bytes = b"") -> None:
        self._model = model
        self._file = file_path
        self._chunk_tree = chunk_tree
        self._big_endian = big_endian
        self._trailing_data = trailing_data
        self._comps_cache: list[CompItem] | None = None
        self._items_cache: list[Any] | None = None

    @property
    def file(self) -> str | None:
        return self._file

    # Items

    def _ensure_items(self) -> list[Any]:
        if self._items_cache is not None:
            return self._items_cache
        self._items_cache = []
        for item in self._model.folder.items:
            self._items_cache.append(_wrap_item(item, self))
        return self._items_cache

    @property
    def num_items(self) -> int:
        return len(self._ensure_items())

    @property
    def items(self) -> ItemCollection:
        return ItemCollection(self._ensure_items())

    def item(self, index: int) -> Any:
        """Get item by 1-based index."""
        items = self._ensure_items()
        idx = index - 1
        if 0 <= idx < len(items):
            return items[idx]
        return None

    @property
    def active_item(self) -> CompItem | None:
        if self._model.current_item is not None:
            # Try to find the active comp
            for comp in self.compositions:
                if comp.id == getattr(self._model.current_item, 'id', None):
                    return comp
        return None

    # Compositions

    def _ensure_comps(self) -> list[CompItem]:
        if self._comps_cache is not None:
            return self._comps_cache
        self._comps_cache = [
            CompItem(c, self) for c in self._model.compositions
        ]
        return self._comps_cache

    @property
    def compositions(self) -> list[CompItem]:
        return self._ensure_comps()

    def comp(self, name_or_index: str | int) -> CompItem | None:
        """Lookup composition by name or 1-based index."""
        comps = self._ensure_comps()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(comps):
                return comps[idx]
            return None
        for c in comps:
            if c.name == name_or_index:
                return c
        return None

    # Render Queue

    @property
    def render_queue(self) -> RenderQueue:
        return RenderQueue(self._model.render_queue)

    # Version info

    _OS_NAMES: dict[int, str] = {12: "Windows", 13: "macOS", 14: "macOS ARM"}

    def _decode_version_id(self) -> dict | None:
        """Decode version_id bit fields from the ``head`` chunk.

        Returns a dict with keys: major, minor, patch, build, os, os_code,
        beta, version (formatted string), or ``None`` if unavailable.
        """
        if self._chunk_tree is None:
            return None
        try:
            head = self._chunk_tree.list.find_optional("head")
            if not head or not isinstance(head.data, (bytes, bytearray)) or len(head.data) < 8:
                return None
            vid = struct.unpack(">I", head.data[4:8])[0]
            maj_a = (vid >> 26) & 0x1F
            os_code = (vid >> 22) & 0x0F
            maj_b = (vid >> 19) & 0x07
            minor = (vid >> 15) & 0x0F
            patch = (vid >> 11) & 0x0F
            beta_flag = (vid >> 9) & 0x01
            build = vid & 0xFF
            major = maj_a * 8 + maj_b
            ver = f"{major}.{minor}.{patch}" if patch else f"{major}.{minor}"
            return {
                "major": major,
                "minor": minor,
                "patch": patch,
                "build": build,
                "os": self._OS_NAMES.get(os_code, f"Unknown({os_code})"),
                "os_code": os_code,
                "beta": not beta_flag,
                "version": ver,
            }
        except Exception:
            return None

    @property
    def ae_version(self) -> str | None:
        """AE version string, e.g. ``"25.6.4"``.

        Returns ``None`` for ``.aepx`` files or if the header is missing.
        """
        info = self._decode_version_id()
        return info["version"] if info else None

    @property
    def ae_version_info(self) -> dict | None:
        """Full AE version info decoded from the ``version_id`` bit field.

        Returns a dict with keys: ``major``, ``minor``, ``patch``, ``build``,
        ``os`` (str), ``os_code`` (int), ``beta`` (bool), ``version`` (str).
        Returns ``None`` for ``.aepx`` files or if the header is missing.
        """
        return self._decode_version_id()

    # Write support

    @property
    def writable(self) -> bool:
        """True if this project was loaded from a binary .aep file."""
        return self._chunk_tree is not None

    def save(self, path: str | Path | None = None) -> None:
        """Save the project to a .aep file.

        If *path* is None, overwrites the original file.
        Raises RuntimeError if no chunk tree is available (e.g. loaded from .aepx).
        """
        if self._chunk_tree is None:
            raise RuntimeError(
                "Cannot save: project has no chunk tree. "
                "Only projects opened from .aep files support save()."
            )
        out_path = path or self._file
        if out_path is None:
            raise RuntimeError("No output path specified and no original file path.")
        save_aep(self._chunk_tree, self._big_endian, out_path,
                 self._trailing_data)

    def change_layer_name(self, comp_id: int, layer_id: int,
                          new_name: str) -> bool:
        """Change a layer's name in the chunk tree.

        Args:
            comp_id: Composition ID (from ``comp.id``).
            layer_id: Layer ID (from ``layer._model.id``).
            new_name: New layer name.

        Returns True if successful.
        """
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_name(self._chunk_tree, comp_id, layer_id,
                              new_name, self._big_endian)

    def change_property_value(self, comp_id: int, layer_id: int,
                              match_name_path: list[str],
                              new_value: list[float] | float) -> bool:
        """Change a property's static value (cdat) in the chunk tree.

        Args:
            comp_id: Composition ID.
            layer_id: Layer ID.
            match_name_path: Path of match names, e.g.
                ``["ADBE Transform Group", "ADBE Position"]``.
            new_value: New value — a single float or list of floats.

        Returns True if successful.
        """
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_property_value(self._chunk_tree, comp_id, layer_id,
                                  match_name_path, new_value, self._big_endian)

    def change_keyframe_value(self, comp_id: int, layer_id: int,
                              match_name_path: list[str], key_index: int,
                              new_value: list[float] | float) -> bool:
        """Change a keyframe's value in the chunk tree."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_keyframe_value(self._chunk_tree, comp_id, layer_id,
                                  match_name_path, key_index, new_value,
                                  self._big_endian)

    def change_keyframe_time(self, comp_id: int, layer_id: int,
                             match_name_path: list[str], key_index: int,
                             new_time: float) -> bool:
        """Change a keyframe's time in the chunk tree."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_keyframe_time(self._chunk_tree, comp_id, layer_id,
                                 match_name_path, key_index, new_time,
                                 self._big_endian)

    def change_keyframe_interpolation(self, comp_id: int, layer_id: int,
                                      match_name_path: list[str], key_index: int,
                                      transition_type: int) -> bool:
        """Change a keyframe's interpolation type (1=linear, 2=bezier, 3=hold)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_keyframe_interpolation(self._chunk_tree, comp_id, layer_id,
                                          match_name_path, key_index,
                                          transition_type, self._big_endian)

    def change_keyframe_ease(self, comp_id: int, layer_id: int,
                             match_name_path: list[str], key_index: int,
                             in_speed: list[float] | None = None,
                             in_influence: list[float] | None = None,
                             out_speed: list[float] | None = None,
                             out_influence: list[float] | None = None) -> bool:
        """Change a keyframe's temporal ease (speed/influence)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_keyframe_ease(self._chunk_tree, comp_id, layer_id,
                                 match_name_path, key_index,
                                 in_speed, in_influence,
                                 out_speed, out_influence,
                                 self._big_endian)

    def change_asset_path(self, asset_id: int, new_path: str) -> bool:
        """Change a footage asset's file path in the chunk tree.

        Args:
            asset_id: Asset ID (from ``footage_item.id``).
            new_path: New file path string.

        Returns True if successful.
        """
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_asset_path(self._chunk_tree, asset_id, new_path,
                              self._big_endian)

    def change_comp_name(self, comp_id: int, new_name: str) -> bool:
        """Change a composition's name."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_name(self._chunk_tree, comp_id, new_name,
                             self._big_endian)

    def change_layer_flag(self, comp_id: int, layer_id: int,
                          flag_name: str, value: bool) -> bool:
        """Toggle a layer flag (visible, solo, shy, locked, threedimensional, etc.)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_flag(self._chunk_tree, comp_id, layer_id,
                              flag_name, value, self._big_endian)

    def change_layer_label(self, comp_id: int, layer_id: int,
                           label: int) -> bool:
        """Change a layer's label color index."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_label(self._chunk_tree, comp_id, layer_id,
                               label, self._big_endian)

    def change_layer_blend_mode(self, comp_id: int, layer_id: int,
                                mode: int) -> bool:
        """Change a layer's blend mode."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_blend_mode(self._chunk_tree, comp_id, layer_id,
                                    mode, self._big_endian)

    def change_layer_track_matte(self, comp_id: int, layer_id: int,
                                 matte_type: int) -> bool:
        """Change a layer's track matte type."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_track_matte(self._chunk_tree, comp_id, layer_id,
                                     matte_type, self._big_endian)

    def change_layer_quality(self, comp_id: int, layer_id: int,
                             quality: int) -> bool:
        """Change a layer's quality (0=wireframe, 1=draft, 2=best)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_quality(self._chunk_tree, comp_id, layer_id,
                                 quality, self._big_endian)

    def change_layer_time_field(self, comp_id: int, layer_id: int,
                                field: str, value: float) -> bool:
        """Change a layer time field (in_time, out_time, start_time, time_stretch)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_time_field(self._chunk_tree, comp_id, layer_id,
                                    field, value, self._big_endian)

    def change_layer_preserve_transparency(self, comp_id: int, layer_id: int,
                                            value: bool) -> bool:
        """Change a layer's preserve transparency flag."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_preserve_transparency(self._chunk_tree, comp_id,
                                                layer_id, value,
                                                self._big_endian)

    def change_layer_light_type(self, comp_id: int, layer_id: int,
                                 light_type: int) -> bool:
        """Change a light layer's light type (0=parallel, 1=spot, 2=point, 3=ambient)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_layer_light_type(self._chunk_tree, comp_id, layer_id,
                                     light_type, self._big_endian)

    def change_comp_dimensions(self, comp_id: int, width: int,
                               height: int) -> bool:
        """Change a composition's width and height."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_dimensions(self._chunk_tree, comp_id, width, height,
                                   self._big_endian)

    def change_comp_bgcolor(self, comp_id: int,
                            r: int, g: int, b: int) -> bool:
        """Change a composition's background color (0-255 each)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_bgcolor(self._chunk_tree, comp_id, r, g, b,
                                self._big_endian)

    def change_comp_framerate(self, comp_id: int, framerate: float) -> bool:
        """Change a composition's frame rate."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_framerate(self._chunk_tree, comp_id, framerate,
                                  self._big_endian)

    def change_comp_duration(self, comp_id: int, duration: float) -> bool:
        """Change a composition's duration in seconds."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_duration(self._chunk_tree, comp_id, duration,
                                 self._big_endian)

    def change_comp_work_area_start(self, comp_id: int, start: float) -> bool:
        """Change a composition's work area start time."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_work_area_start(self._chunk_tree, comp_id, start,
                                         self._big_endian)

    def change_comp_work_area_end(self, comp_id: int, end: float) -> bool:
        """Change a composition's work area end time."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_work_area_end(self._chunk_tree, comp_id, end,
                                       self._big_endian)

    def change_comp_flag(self, comp_id: int, flag_name: str,
                          value: bool) -> bool:
        """Toggle a composition flag (draft3d, motion_blur, frame_blending, etc.)."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_flag(self._chunk_tree, comp_id, flag_name, value,
                              self._big_endian)

    def change_comp_shutter_angle(self, comp_id: int, angle: int) -> bool:
        """Change a composition's shutter angle."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_shutter_angle(self._chunk_tree, comp_id, angle,
                                       self._big_endian)

    def change_comp_shutter_phase(self, comp_id: int, phase: int) -> bool:
        """Change a composition's shutter phase."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_shutter_phase(self._chunk_tree, comp_id, phase,
                                       self._big_endian)

    def change_comp_motion_blur_samples(self, comp_id: int,
                                         samples_per_frame: int,
                                         adaptive_limit: int) -> bool:
        """Change a composition's motion blur sample counts."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_motion_blur_samples(self._chunk_tree, comp_id,
                                             samples_per_frame,
                                             adaptive_limit,
                                             self._big_endian)

    def change_comp_pixel_aspect(self, comp_id: int, ratio: float) -> bool:
        """Change a composition's pixel aspect ratio."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_pixel_aspect(self._chunk_tree, comp_id, ratio,
                                      self._big_endian)

    def change_comp_display_start_time(self, comp_id: int,
                                        time: float) -> bool:
        """Change a composition's display start time."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_display_start_time(self._chunk_tree, comp_id, time,
                                            self._big_endian)

    def change_comp_drop_frame(self, comp_id: int,
                                drop_frame: bool) -> bool:
        """Change a composition's drop frame flag."""
        if self._chunk_tree is None:
            raise RuntimeError("Cannot modify: project has no chunk tree.")
        return set_comp_drop_frame(self._chunk_tree, comp_id, drop_frame,
                                    self._big_endian)

    # Project settings

    def _write_project_setting(self, writer_fn_name: str, *args) -> None:
        """Call a project settings writer function."""
        if self._chunk_tree is not None:
            import importlib
            mod = importlib.import_module('._writer', package='aep_tools')
            fn = getattr(mod, writer_fn_name)
            fn(self._chunk_tree, *args, self._big_endian)

    @property
    def bits_per_channel(self) -> int:
        return self._model.bits_per_channel

    @bits_per_channel.setter
    def bits_per_channel(self, value: int) -> None:
        self._model.bits_per_channel = value
        self._write_project_setting('set_project_bits_per_channel', value)

    @property
    def linearize_working_space(self) -> bool:
        return self._model.linearize_working_space

    @linearize_working_space.setter
    def linearize_working_space(self, value: bool) -> None:
        self._model.linearize_working_space = value
        self._write_project_setting('set_project_linearize_working_space', value)

    @property
    def audio_sample_rate(self) -> float:
        return self._model.audio_sample_rate

    @audio_sample_rate.setter
    def audio_sample_rate(self, value: float) -> None:
        self._model.audio_sample_rate = value
        self._write_project_setting('set_project_audio_sample_rate', value)

    @property
    def working_gamma(self) -> float:
        return self._model.working_gamma

    @working_gamma.setter
    def working_gamma(self, value: float) -> None:
        self._model.working_gamma = value
        self._write_project_setting('set_project_working_gamma', value)

    @property
    def compensate_scene_referred(self) -> bool:
        return self._model.compensate_scene_referred

    @compensate_scene_referred.setter
    def compensate_scene_referred(self, value: bool) -> None:
        self._model.compensate_scene_referred = value
        self._write_project_setting('set_project_compensate_scene_referred', value)

    def __repr__(self) -> str:
        return f"Project(file={self._file!r}, num_comps={len(self._model.compositions)})"

    # Class methods

    @classmethod
    def open(cls, path: str | Path) -> Project:
        """Open a .aep or .aepx file and return a Project wrapper."""
        p = Path(path)
        if p.suffix.lower() == ".aepx":
            return open_aepx(str(p))
        return open_aep(str(p))


# Helpers


def _wrap_item(item: Any, project: Project) -> Any:
    """Wrap a folder item into the appropriate wrapper."""
    if isinstance(item, Folder):
        return FolderItem(item, project)
    if isinstance(item, Composition):
        return CompItem(item, project)
    if isinstance(item, (ImageAsset, SolidAsset)):
        return FootageItem(item, project)
    return item


# Top-level functions


def open_aep(path: str | Path) -> Project:
    """Open a binary .aep file and return a Project wrapper.

    Retains the parsed chunk tree so the project can be modified and saved.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is too small or not a valid AEP file.
    """
    from aep_parser import AepParseError
    from aep_parser._parser import AepChunkParser, ProjectParser
    try:
        from aep_parser._core import parse_riff as _rust_parse_riff
        _HAS_RUST = True
    except ImportError:
        _HAS_RUST = False

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    raw = p.read_bytes()

    if len(raw) < 12:
        raise ValueError(f"File too small to be a valid AEP file ({len(raw)} bytes): {p}")

    # Extract trailing data (XMP metadata) after the RIFX chunk
    import struct as _st
    try:
        _rifx_end = 8 + _st.unpack_from(">I", raw, 4)[0]
    except _st.error:
        raise ValueError(f"Cannot read RIFF header from: {p}")
    trailing = raw[_rifx_end:] if _rifx_end < len(raw) else b""

    if _HAS_RUST:
        root_chunk, big_endian = _rust_parse_riff(raw)
        pp = ProjectParser(big_endian=big_endian)
        model = pp.parse_project(root_chunk)
        return Project(model, str(p), chunk_tree=root_chunk,
                       big_endian=big_endian, trailing_data=trailing)

    parser = AepChunkParser(raw, 0, True)
    root_chunk = parser.parse()
    big_endian = parser.big_endian
    pp = ProjectParser(big_endian=big_endian)
    model = pp.parse_project(root_chunk)
    return Project(model, str(p), chunk_tree=root_chunk,
                   big_endian=big_endian, trailing_data=trailing)


def open_aepx(path: str | Path) -> Project:
    """Open an .aepx XML file and return a Project wrapper.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be decoded or parsed.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    try:
        xml_string = p.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"Cannot decode AEPX file as UTF-8: {p}: {e}") from e
    model = parse_aepx(xml_string)
    return Project(model, str(p))


def load_project(model: ProjectModel) -> Project:
    """Wrap an already-parsed Project model."""
    return Project(model)
