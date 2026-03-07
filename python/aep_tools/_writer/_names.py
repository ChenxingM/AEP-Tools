"""Modification functions for comp names, layer names, and asset paths."""

from __future__ import annotations

import json

from aep_parser._parser.chunk import Chunk, ChunkList

from ._navigate import find_comp_chunklist, find_item_chunklist, find_layer_chunk


def set_comp_name(root: Chunk, comp_id: int, new_name: str,
                  big_endian: bool) -> bool:
    """Set a composition's name by modifying its Utf8 chunk in the Item LIST.

    Returns True if successful, False if the comp was not found.
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False
    for child in comp_cl.children:
        if child.header == "Utf8":
            child.data = new_name
            return True
    utf8_chunk = Chunk("Utf8", len(new_name.encode("utf-8")), new_name)
    insert_idx = 0
    for i, child in enumerate(comp_cl.children):
        if child.header == "idta":
            insert_idx = i + 1
            break
    comp_cl.children.insert(insert_idx, utf8_chunk)
    return True


def set_asset_path(root: Chunk, asset_id: int, new_path: str,
                   big_endian: bool) -> bool:
    """Set a footage asset's file path by modifying its Als2 > alas chunk.

    The alas chunk contains JSON with a 'fullpath' key. This function
    updates that key while preserving all other metadata.

    Returns True if successful, False if the asset was not found.
    """
    item_cl = find_item_chunklist(root, asset_id, big_endian)
    if item_cl is None:
        return False

    pin = item_cl.find_optional("Pin ")
    if pin is None:
        return False
    als2 = pin.list.find_optional("Als2")
    if als2 is None:
        return False
    alas = als2.list.find_optional("alas")
    if alas is None:
        return False

    alas_data = alas.data
    if isinstance(alas_data, (bytes, bytearray)):
        alas_data = alas_data.decode("utf-8", errors="replace")

    try:
        ref_data = json.loads(alas_data)
    except (json.JSONDecodeError, TypeError):
        return False

    ref_data["fullpath"] = new_path
    new_json = json.dumps(ref_data, ensure_ascii=False, separators=(',', ':'))
    alas.data = new_json
    return True


def set_layer_name(root: Chunk, comp_id: int, layer_id: int,
                   new_name: str, big_endian: bool) -> bool:
    """Set a layer's name by modifying its Utf8 chunk in the Layr LIST.

    Returns True if successful, False if the layer was not found.
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False
    layer_chunk = find_layer_chunk(comp_cl, layer_id, big_endian)
    if layer_chunk is None:
        return False

    layr_cl = layer_chunk.list
    for child in layr_cl.children:
        if child.header == "Utf8":
            child.data = new_name
            return True

    utf8_chunk = Chunk("Utf8", len(new_name.encode("utf-8")), new_name)
    insert_idx = 0
    for i, child in enumerate(layr_cl.children):
        if child.header == "ldta":
            insert_idx = i + 1
            break
    layr_cl.children.insert(insert_idx, utf8_chunk)
    return True
