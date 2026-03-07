"""Chunk tree navigation — locating comps, layers, properties, and items."""

from __future__ import annotations

from aep_parser._parser.binary_reader import BinaryReader
from aep_parser._parser.chunk import Chunk, ChunkList

from ._common import _is_chunk_list


def find_comp_chunklist(root: Chunk, comp_id: int,
                        big_endian: bool) -> ChunkList | None:
    """Find the Item ChunkList for a composition by its ID."""
    fold = root.list.find_optional("Fold")
    if fold is None:
        return None
    return _find_comp_in_folder(fold.list, comp_id, big_endian)


def _find_comp_in_folder(cl: ChunkList, comp_id: int,
                         big_endian: bool) -> ChunkList | None:
    for child in cl.children:
        if child.name == "Item":
            result = _check_item_comp(child.list, comp_id, big_endian)
            if result is not None:
                return result
            result = _find_comp_in_folder(child.list, comp_id, big_endian)
            if result is not None:
                return result
        elif child.name == "Sfdr":
            result = _find_comp_in_folder(child.list, comp_id, big_endian)
            if result is not None:
                return result
    return None


def _check_item_comp(cl: ChunkList, comp_id: int,
                     big_endian: bool) -> ChunkList | None:
    """Check if an Item ChunkList is a comp with the given ID."""
    idta = cl.find_optional("idta")
    if idta is None or not isinstance(idta.data, (bytes, bytearray)):
        return None
    r = BinaryReader(idta.data, 0, big_endian)
    item_type = r.read_uint(2)
    if item_type != 4:  # not a composition
        return None
    r.skip(14)
    item_id = r.read_uint(4)
    if item_id == comp_id:
        return cl
    return None


def find_layer_chunk(comp_cl: ChunkList, layer_id: int,
                     big_endian: bool) -> Chunk | None:
    """Find a Layr LIST chunk within a composition by layer ID."""
    for child in comp_cl.children:
        if child.name == "Layr":
            ldta = child.list.find_optional("ldta")
            if ldta is not None and isinstance(ldta.data, (bytes, bytearray)):
                r = BinaryReader(ldta.data, 0, big_endian)
                lid = r.read_uint(4)
                if lid == layer_id:
                    return child
    return None


def find_property_chunk(parent_cl: ChunkList, match_name_path: list[str],
                        ) -> Chunk | None:
    """Navigate the property tree by a list of match names.

    e.g. ["ADBE Transform Group", "ADBE Position"] → finds the tdbs/tdgp
    chunk for Position inside the Transform group.
    """
    cl = parent_cl
    for depth, mn in enumerate(match_name_path):
        found = _find_named_child(cl, mn)
        if found is None:
            return None
        if depth < len(match_name_path) - 1:
            if not _is_chunk_list(found.data):
                return None
            cl = found.data
        else:
            return found
    return None


def _find_named_child(cl: ChunkList, match_name: str) -> Chunk | None:
    """Find a child chunk preceded by a tdmn with the given match_name."""
    children = cl.children
    i = 0
    while i < len(children):
        child = children[i]
        if child.header == "tdmn" and isinstance(child.data, str):
            if child.data == match_name and i + 1 < len(children):
                return children[i + 1]
        i += 1
    return None


def find_item_chunklist(root: Chunk, item_id: int,
                        big_endian: bool) -> ChunkList | None:
    """Find any Item ChunkList by its ID (regardless of item type)."""
    fold = root.list.find_optional("Fold")
    if fold is None:
        return None
    return _find_item_in_folder(fold.list, item_id, big_endian)


def _find_item_in_folder(cl: ChunkList, item_id: int,
                         big_endian: bool) -> ChunkList | None:
    for child in cl.children:
        if child.name == "Item":
            idta = child.list.find_optional("idta")
            if idta is not None and isinstance(idta.data, (bytes, bytearray)):
                r = BinaryReader(idta.data, 0, big_endian)
                r.skip(2)  # item_type
                r.skip(14)
                iid = r.read_uint(4)
                if iid == item_id:
                    return child.list
            result = _find_item_in_folder(child.list, item_id, big_endian)
            if result is not None:
                return result
        elif child.name == "Sfdr":
            result = _find_item_in_folder(child.list, item_id, big_endian)
            if result is not None:
                return result
    return None
