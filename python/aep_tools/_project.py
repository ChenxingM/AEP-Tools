"""Project wrapper mirroring AE scripting app.project object."""

from __future__ import annotations

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
from ._writer import save_aep, set_comp_name, set_layer_name, set_property_value


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

    def __init__(self, model: ImageAsset | SolidAsset) -> None:
        self._model = model

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
                 big_endian: bool = True) -> None:
        self._model = model
        self._file = file_path
        self._chunk_tree = chunk_tree
        self._big_endian = big_endian
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
        save_aep(self._chunk_tree, self._big_endian, out_path)

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
        return FootageItem(item)
    return item


# Top-level functions


def open_aep(path: str | Path) -> Project:
    """Open a binary .aep file and return a Project wrapper.

    Retains the parsed chunk tree so the project can be modified and saved.
    """
    from aep_parser._parser import AepChunkParser, ProjectParser
    try:
        from aep_parser._core import parse_riff as _rust_parse_riff
        _HAS_RUST = True
    except ImportError:
        _HAS_RUST = False

    p = Path(path)
    raw = p.read_bytes()

    if _HAS_RUST:
        root_chunk, big_endian = _rust_parse_riff(raw)
        pp = ProjectParser(big_endian=big_endian)
        model = pp.parse_project(root_chunk)
        return Project(model, str(p), chunk_tree=root_chunk, big_endian=big_endian)

    parser = AepChunkParser(raw, 0, True)
    root_chunk = parser.parse()
    big_endian = parser.big_endian
    pp = ProjectParser(big_endian=big_endian)
    model = pp.parse_project(root_chunk)
    return Project(model, str(p), chunk_tree=root_chunk, big_endian=big_endian)


def open_aepx(path: str | Path) -> Project:
    """Open an .aepx XML file and return a Project wrapper."""
    p = Path(path)
    xml_string = p.read_text(encoding="utf-8")
    model = parse_aepx(xml_string)
    return Project(model, str(p))


def load_project(model: ProjectModel) -> Project:
    """Wrap an already-parsed Project model."""
    return Project(model)
