"""Binary .aep writer — serialize chunk tree back to RIFX/RIFF format.

Supports modifying layer names and property values in-place on the chunk tree,
then writing the result to a new .aep file.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from aep_parser._parser.binary_reader import BinaryReader
from aep_parser._parser.chunk import Chunk, ChunkList

try:
    from aep_parser._core import ChunkList as _RustChunkList
except ImportError:
    _RustChunkList = None

def _is_chunk_list(data) -> bool:
    """Check if data is a ChunkList (Python or Rust implementation)."""
    if isinstance(data, ChunkList):
        return True
    return _RustChunkList is not None and isinstance(data, _RustChunkList)


# Template tdb4 for 1-component scalar properties (Opacity, Rotate Z, etc.)
# Captured from real AEP data — 124 bytes, big-endian, 24fps time_scale.
_TDB4_SCALAR_1 = bytes.fromhex(
    "db990001000100000001ffff000060003f1a36e2eb1c432d"
    "3ff00000000000003ff00000000000003ff00000000000003ff0000000000000"
    "0000000809"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000"
)

# Template tdb4 for 3-component properties (Scale).
_TDB4_SCALAR_3 = bytes.fromhex(
    "db990003000100000001ffff000180003f1a36e2eb1c432d"
    "3ff00000000000003ff00000000000003ff00000000000003ff0000000000000"
    "0000000809"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000"
)

# Template tdb4 for 2-component spatial properties (Anchor Point, Position).
_TDB4_SPATIAL_2 = bytes.fromhex(
    "db990002000900000001ffff00000c003f1a36e2eb1c432d"
    "3ff00000000000003ff00000000000003ff00000000000003ff0000000000000"
    "0000000809"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000000000000000000000"
    "000000000000000000000000000000"
)

# Template tdb4 for 3-component spatial properties (Anchor Point — always 3D in AE).
_TDB4_SPATIAL_3 = bytearray(_TDB4_SPATIAL_2)
_TDB4_SPATIAL_3[2:4] = b'\x00\x03'  # patch component count to 3
_TDB4_SPATIAL_3 = bytes(_TDB4_SPATIAL_3)

# Match name → (components, spatial, tdb4_template, tdum, tduM)
_PROPERTY_TEMPLATES: dict[str, tuple[int, bool, bytes, float, float]] = {
    "ADBE Opacity":      (1, False, _TDB4_SCALAR_1, 0.0, 100.0),
    "ADBE Rotate Z":     (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Scale":        (3, False, _TDB4_SCALAR_3, 0.0, 0.0),
    "ADBE Anchor Point": (3, True,  _TDB4_SPATIAL_3, 0.0, 0.0),
    "ADBE Position":     (2, True,  _TDB4_SPATIAL_2, 0.0, 0.0),
}


# RIFF Serializer


def serialize_chunk_tree(root: Chunk, big_endian: bool) -> bytes:
    """Serialize an entire chunk tree back to RIFX/RIFF binary."""
    buf = bytearray()
    _write_root(buf, root, big_endian)
    return bytes(buf)


def _pack_u32(val: int, big_endian: bool) -> bytes:
    return struct.pack(">I" if big_endian else "<I", val)


def _write_root(buf: bytearray, root: Chunk, big_endian: bool) -> None:
    """Write the RIFX/RIFF root chunk."""
    # header: "RIFX" or "RIFF"
    buf.extend(root.header.encode("ascii"))
    # size placeholder — will be filled after children are written
    size_pos = len(buf)
    buf.extend(b"\x00\x00\x00\x00")
    # file id (e.g. "Egg!")
    cl = root.data
    buf.extend(cl.type.encode("ascii"))
    # children
    for child in cl.children:
        _write_chunk(buf, child, big_endian)
    # patch size
    data_size = len(buf) - size_pos - 4
    buf[size_pos:size_pos + 4] = _pack_u32(data_size, big_endian)


def _write_chunk(buf: bytearray, chunk: Chunk, big_endian: bool) -> None:
    """Write a single chunk (recursively handles LIST and container types)."""
    data = chunk.data

    if _is_chunk_list(data):
        if chunk.header == "LIST":
            _write_list_chunk(buf, chunk, big_endian)
        else:
            # Non-LIST containers: tdsn, fnam, pdnm
            # Written as [header 4B][size 4B][children...]
            _write_container_chunk(buf, chunk, big_endian)
    elif isinstance(data, str):
        _write_string_chunk(buf, chunk, big_endian)
    elif isinstance(data, (bytes, bytearray)):
        _write_raw_chunk(buf, chunk, big_endian)
    else:
        raise TypeError(f"Unknown chunk data type: {type(data).__name__} "
                        f"for header {chunk.header!r}")


def _write_list_chunk(buf: bytearray, chunk: Chunk, big_endian: bool) -> None:
    """Write a LIST chunk: LIST [size] [type 4B] [children...]"""
    cl = chunk.data
    buf.extend(b"LIST")
    size_pos = len(buf)
    buf.extend(b"\x00\x00\x00\x00")
    buf.extend(cl.type.encode("ascii"))
    for child in cl.children:
        _write_chunk(buf, child, big_endian)
    data_size = len(buf) - size_pos - 4
    buf[size_pos:size_pos + 4] = _pack_u32(data_size, big_endian)


def _write_container_chunk(buf: bytearray, chunk: Chunk,
                           big_endian: bool) -> None:
    """Write a non-LIST container (tdsn, fnam, pdnm): [header][size][children]
    These have ChunkList with type="" — no type prefix written."""
    cl = chunk.data
    buf.extend(chunk.header.encode("ascii"))
    size_pos = len(buf)
    buf.extend(b"\x00\x00\x00\x00")
    for child in cl.children:
        _write_chunk(buf, child, big_endian)
    data_size = len(buf) - size_pos - 4
    buf[size_pos:size_pos + 4] = _pack_u32(data_size, big_endian)


def _write_string_chunk(buf: bytearray, chunk: Chunk,
                        big_endian: bool) -> None:
    """Write a string chunk (Utf8, alas, tdmn, wsnm)."""
    header = chunk.header
    text = chunk.data

    if header == "tdmn":
        # Null-terminated, padded to original size
        encoded = text.encode("utf-8") + b"\x00"
        # Pad to at least the original chunk length
        if len(encoded) < chunk.length:
            encoded = encoded + b"\x00" * (chunk.length - len(encoded))
        data_bytes = encoded
    elif header == "wsnm":
        data_bytes = text.encode("utf-16-le")
    else:
        # Utf8, alas
        data_bytes = text.encode("utf-8")

    buf.extend(header.encode("ascii"))
    buf.extend(_pack_u32(len(data_bytes), big_endian))
    buf.extend(data_bytes)
    # 2-byte alignment padding
    if len(data_bytes) % 2 == 1:
        buf.extend(b"\x00")


def _write_raw_chunk(buf: bytearray, chunk: Chunk, big_endian: bool) -> None:
    """Write a raw binary data chunk."""
    header = chunk.header
    data = chunk.data

    # btdk is special: it was parsed as LIST→btdk but stored with header="btdk"
    # and data=bytes. We need to write it back as LIST [size] btdk [data]
    if header == "btdk":
        buf.extend(b"LIST")
        size = len(data) + 4  # 4 for "btdk" type
        buf.extend(_pack_u32(size, big_endian))
        buf.extend(b"btdk")
        buf.extend(data)
        if len(data) % 2 == 1:
            buf.extend(b"\x00")
        return

    buf.extend(header.encode("ascii"))
    buf.extend(_pack_u32(len(data), big_endian))
    buf.extend(data)
    # 2-byte alignment padding
    if len(data) % 2 == 1:
        buf.extend(b"\x00")


# Chunk Tree Navigation


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
            # Item might be a folder — search inside it too
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
            # Need to go deeper — this must be a tdgp (PropertyGroup)
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
            # Recurse into folder Items
            result = _find_item_in_folder(child.list, item_id, big_endian)
            if result is not None:
                return result
        elif child.name == "Sfdr":
            result = _find_item_in_folder(child.list, item_id, big_endian)
            if result is not None:
                return result
    return None


# Modification Functions


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
    # No Utf8 chunk — create one after idta
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

    # Navigate: Item > Pin  > Als2 > alas
    pin = item_cl.find_optional("Pin ")
    if pin is None:
        return False
    als2 = pin.list.find_optional("Als2")
    if als2 is None:
        return False
    alas = als2.list.find_optional("alas")
    if alas is None:
        return False

    # Parse existing JSON and update fullpath
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

    # Find the Utf8 chunk in the Layr LIST
    layr_cl = layer_chunk.list
    for child in layr_cl.children:
        if child.header == "Utf8":
            child.data = new_name
            return True

    # No Utf8 chunk exists — create one after ldta
    utf8_chunk = Chunk("Utf8", len(new_name.encode("utf-8")), new_name)
    # Insert after ldta (typically the first chunk)
    insert_idx = 0
    for i, child in enumerate(layr_cl.children):
        if child.header == "ldta":
            insert_idx = i + 1
            break
    layr_cl.children.insert(insert_idx, utf8_chunk)
    return True


def _create_tdbs_chunk(match_name: str, value: list[float],
                       big_endian: bool) -> Chunk | None:
    """Create a new tdbs (animated property) chunk from a template.

    Adapts component count from ``len(value)`` when it exceeds the
    template default (e.g. 3-component Position on a 3D layer).
    """
    template = _PROPERTY_TEMPLATES.get(match_name)
    if template is None:
        return None

    components, is_spatial, tdb4_data, tdum_val, tduM_val = template

    # Override component count if value has more dimensions than template
    actual_components = max(components, len(value))

    fmt = ">" if big_endian else "<"

    # tdsb: flags (visible, not split)
    tdsb = Chunk("tdsb", 4, b"\x00\x00\x00\x01")

    # tdsn: display name placeholder
    tdsn_utf8 = Chunk("Utf8", 6, "-_0_/-")
    tdsn = Chunk("tdsn", 14, ChunkList("", [tdsn_utf8]))

    # tdb4: property metadata — patch component count at offset 2 (uint16 BE)
    tdb4_bytes = bytearray(tdb4_data)
    struct.pack_into(">H", tdb4_bytes, 2, actual_components)
    tdb4 = Chunk("tdb4", len(tdb4_bytes), bytes(tdb4_bytes))

    # cdat: value + tangent/velocity slots
    # Spatial properties: components*3 + 3 float64s (value, spatial_in, spatial_out, temporal)
    # Non-spatial:        components*5 float64s (value, ease_in, ease_out, influence_in, influence_out)
    cdat_count = actual_components * 3 + 3 if is_spatial else actual_components * 5
    cdat_floats = list(value) + [0.0] * (cdat_count - len(value))
    cdat_data = struct.pack(f"{fmt}{'d' * cdat_count}", *cdat_floats)
    cdat = Chunk("cdat", len(cdat_data), cdat_data)

    # tdum/tduM: min/max bounds (always present in real AEP files)
    tdum = Chunk("tdum", 8, struct.pack(f"{fmt}d", tdum_val))
    tduM = Chunk("tduM", 8, struct.pack(f"{fmt}d", tduM_val))

    children = [tdsb, tdsn, tdb4, cdat, tdum, tduM]

    tdbs_cl = ChunkList("tdbs", children)
    # Calculate total size: type(4) + sum of child (header(4) + size(4) + data + padding)
    total = 4  # "tdbs" type
    for c in children:
        total += 8 + c.length + (c.length % 2)
    return Chunk("LIST", total, tdbs_cl)


def _insert_property_into_group(parent_cl: ChunkList, match_name: str,
                                tdbs_chunk: Chunk) -> None:
    """Insert a tdmn + tdbs pair into a property group before ADBE Group End."""
    # Create tdmn chunk — null-terminated, padded to 32 bytes
    mn_bytes = match_name.encode("utf-8") + b"\x00"
    if len(mn_bytes) < 32:
        mn_bytes += b"\x00" * (32 - len(mn_bytes))
    tdmn = Chunk("tdmn", len(mn_bytes), match_name)
    tdmn.length = len(mn_bytes)

    # Find insertion point — before "ADBE Group End" if present
    children = parent_cl.children
    insert_idx = len(children)
    for i, c in enumerate(children):
        if c.header == "tdmn" and isinstance(c.data, str) and c.data == "ADBE Group End":
            insert_idx = i
            break

    children.insert(insert_idx, tdmn)
    children.insert(insert_idx + 1, tdbs_chunk)


def set_property_value(root: Chunk, comp_id: int, layer_id: int,
                       match_name_path: list[str], new_value: list[float] | float,
                       big_endian: bool) -> bool:
    """Set a property's static value (cdat) by navigating the property tree.

    Args:
        root: The root RIFX chunk.
        comp_id: Composition ID.
        layer_id: Layer ID.
        match_name_path: Path of match names, e.g.
            ["ADBE Transform Group", "ADBE Position"]
        new_value: New value — a single float or list of floats.
        big_endian: Endianness.

    Returns True if successful.
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False
    layer_chunk = find_layer_chunk(comp_cl, layer_id, big_endian)
    if layer_chunk is None:
        return False

    # Find the tdgp (root property group) in the layer
    layr_cl = layer_chunk.list
    tdgp = layr_cl.find_optional("tdgp")
    if tdgp is None:
        return False

    # Normalize value
    if isinstance(new_value, (int, float)):
        new_value = [float(new_value)]
    elif isinstance(new_value, list):
        new_value = [float(v) for v in new_value]

    # Navigate match_name_path to the target property
    prop_chunk = find_property_chunk(tdgp.list, match_name_path)

    if prop_chunk is None:
        # Property doesn't exist in the binary — create it from template
        if len(match_name_path) < 2:
            return False
        target_mn = match_name_path[-1]
        tdbs_chunk = _create_tdbs_chunk(target_mn, new_value, big_endian)
        if tdbs_chunk is None:
            return False
        # Navigate to the parent group
        parent_chunk = find_property_chunk(tdgp.list, match_name_path[:-1])
        if parent_chunk is None or not _is_chunk_list(parent_chunk.data):
            return False
        _insert_property_into_group(parent_chunk.data, target_mn, tdbs_chunk)
        return True

    # The prop_chunk should be a tdbs (animated property) containing a cdat
    if not _is_chunk_list(prop_chunk.data):
        return False

    prop_cl = prop_chunk.data
    cdat = prop_cl.find_optional("cdat")
    if cdat is None:
        return False

    fmt = ">" if big_endian else "<"

    # Check if the value has more components than the tdb4 declares.
    # This happens when a 3D layer has a 2-component Anchor Point / Position
    # in the binary — we must upgrade tdb4 and rebuild cdat.
    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is not None and isinstance(tdb4.data, (bytes, bytearray)) and len(tdb4.data) >= 6:
        cur_components = struct.unpack_from(">H", tdb4.data, 2)[0]
        if len(new_value) > cur_components:
            is_spatial = bool(tdb4.data[5] & (1 << 3))
            new_components = len(new_value)
            # Update tdb4 component count
            tdb4_bytes = bytearray(tdb4.data)
            struct.pack_into(">H", tdb4_bytes, 2, new_components)
            tdb4.data = bytes(tdb4_bytes)
            # Rebuild cdat with correct structure for the new component count
            cdat_count = new_components * 3 + 3 if is_spatial else new_components * 5
            cdat_floats = list(new_value) + [0.0] * (cdat_count - len(new_value))
            cdat_data = struct.pack(f"{fmt}{'d' * cdat_count}", *cdat_floats)
            cdat.data = cdat_data
            cdat.length = len(cdat_data)
            return True

    # Normal path: patch value floats at the start of cdat
    packed = struct.pack(f"{fmt}{'d' * len(new_value)}", *new_value)
    old_data = bytearray(cdat.data)
    old_data[:len(packed)] = packed
    cdat.data = bytes(old_data)
    return True


def set_keyframe_value(root: Chunk, comp_id: int, layer_id: int,
                       match_name_path: list[str], key_index: int,
                       new_value: list[float] | float,
                       big_endian: bool) -> bool:
    """Set a keyframe value in the ldat chunk of an animated property.

    Args:
        key_index: 1-based keyframe index.
        new_value: New value — a single float or list of floats.

    Returns True if successful.
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False
    layer_chunk = find_layer_chunk(comp_cl, layer_id, big_endian)
    if layer_chunk is None:
        return False

    layr_cl = layer_chunk.list
    tdgp = layr_cl.find_optional("tdgp")
    if tdgp is None:
        return False

    prop_chunk = find_property_chunk(tdgp.list, match_name_path)
    if prop_chunk is None or not _is_chunk_list(prop_chunk.data):
        return False

    prop_cl = prop_chunk.data

    # Read tdb4 to get components count and prop_type
    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is None or not isinstance(tdb4.data, (bytes, bytearray)):
        return False
    tdb4_r = BinaryReader(tdb4.data, 0, big_endian)
    tdb4_r.skip(2)
    components = tdb4_r.read_uint(2)
    flags2 = tdb4_r.read_flags(2)
    is_spatial = flags2.get_bit(1, 3)

    # Find the list chunk containing lhd3 + ldat
    lst = prop_cl.find_optional("list")
    if lst is None:
        return False
    lst_cl = lst.list
    lhd3 = lst_cl.find_optional("lhd3")
    ldat = lst_cl.find_optional("ldat")
    if lhd3 is None or ldat is None:
        return False
    if not isinstance(lhd3.data, (bytes, bytearray)):
        return False
    if not isinstance(ldat.data, (bytes, bytearray)):
        return False

    # Parse lhd3 for count and item_size
    hr = BinaryReader(lhd3.data, 0, big_endian)
    hr.skip(10)
    count = hr.read_uint(2)
    hr.skip(6)
    item_size = hr.read_uint(2)

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

    if isinstance(new_value, (int, float)):
        new_value = [float(new_value)]
    else:
        new_value = [float(v) for v in new_value]

    # Calculate value offset within the keyframe record
    # Layout: [1B skip][4B time][1B transition][1B label][1B flags] = 8 bytes
    # Then for spatial (prop_type=2): [16B skip][4B speed stuff] then values
    # For multi-dim (prop_type=3,5): values start right at offset 8
    # For scalar (prop_type=1): skip + values

    value_offset = 8  # after header bytes

    if is_spatial:
        # spatial: 16 bytes skip, then components * 8 bytes for values
        value_offset += 16
    # For non-spatial multi-dim, values start right at offset 8

    start = idx * item_size + value_offset
    fmt_prefix = ">" if big_endian else "<"
    packed = struct.pack(f"{fmt_prefix}{'d' * len(new_value)}", *new_value)

    if start + len(packed) > len(ldat.data):
        return False

    # ldat.data is bytes — need to make it mutable
    ldat_bytes = bytearray(ldat.data)
    ldat_bytes[start:start + len(packed)] = packed
    ldat.data = bytes(ldat_bytes)
    return True


def _get_ldat_info(prop_cl, big_endian: bool):
    """Read tdb4 metadata and ldat from a property ChunkList.

    Returns (components, is_spatial, time_scale, count, item_size, ldat_chunk)
    or None if not available.
    """
    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is None or not isinstance(tdb4.data, (bytes, bytearray)):
        return None
    br = BinaryReader(tdb4.data, 0, big_endian)
    br.skip(2)
    components = br.read_uint(2)
    flags2 = br.read_flags(2)
    is_spatial = flags2.get_bit(1, 3)
    br.skip(7)
    time_scale = br.read_uint(4)

    lst = prop_cl.find_optional("list")
    if lst is None:
        return None
    lst_cl = lst.list
    lhd3 = lst_cl.find_optional("lhd3")
    ldat = lst_cl.find_optional("ldat")
    if lhd3 is None or ldat is None:
        return None
    if not isinstance(lhd3.data, (bytes, bytearray)):
        return None
    if not isinstance(ldat.data, (bytes, bytearray)):
        return None

    hr = BinaryReader(lhd3.data, 0, big_endian)
    hr.skip(10)
    count = hr.read_uint(2)
    hr.skip(6)
    item_size = hr.read_uint(2)

    return components, is_spatial, time_scale, count, item_size, ldat


def _locate_prop_ldat(root: Chunk, comp_id: int, layer_id: int,
                      match_name_path: list[str], big_endian: bool):
    """Navigate to a property's ldat info. Returns (ldat_info, prop_cl) or (None, None)."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return None, None
    layer_chunk = find_layer_chunk(comp_cl, layer_id, big_endian)
    if layer_chunk is None:
        return None, None
    tdgp = layer_chunk.list.find_optional("tdgp")
    if tdgp is None:
        return None, None
    prop_chunk = find_property_chunk(tdgp.list, match_name_path)
    if prop_chunk is None or not _is_chunk_list(prop_chunk.data):
        return None, None
    info = _get_ldat_info(prop_chunk.data, big_endian)
    return info, prop_chunk.data


def set_keyframe_time(root: Chunk, comp_id: int, layer_id: int,
                      match_name_path: list[str], key_index: int,
                      new_time: float, big_endian: bool) -> bool:
    """Set a keyframe's time in the ldat chunk.

    Args:
        key_index: 1-based keyframe index.
        new_time: New time in seconds.

    Returns True if successful.
    """
    info, _ = _locate_prop_ldat(root, comp_id, layer_id, match_name_path, big_endian)
    if info is None:
        return False
    components, is_spatial, time_scale, count, item_size, ldat = info

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

    # Time is at offset 1 (after 1 skip byte), 4 bytes signed int
    time_raw = int(round(new_time * time_scale))
    fmt = ">i" if big_endian else "<i"
    packed = struct.pack(fmt, time_raw)

    start = idx * item_size + 1  # skip 1 byte
    ldat_bytes = bytearray(ldat.data)
    ldat_bytes[start:start + 4] = packed
    ldat.data = bytes(ldat_bytes)
    return True


def set_keyframe_interpolation(root: Chunk, comp_id: int, layer_id: int,
                               match_name_path: list[str], key_index: int,
                               transition_type: int,
                               big_endian: bool) -> bool:
    """Set a keyframe's interpolation type in the ldat chunk.

    Args:
        key_index: 1-based keyframe index.
        transition_type: 1=linear, 2=bezier, 3=hold.

    Returns True if successful.
    """
    info, _ = _locate_prop_ldat(root, comp_id, layer_id, match_name_path, big_endian)
    if info is None:
        return False
    components, is_spatial, time_scale, count, item_size, ldat = info

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

    # Transition type at offset 5 (1 skip + 4 time), 1 byte
    start = idx * item_size + 5
    ldat_bytes = bytearray(ldat.data)
    ldat_bytes[start] = transition_type & 0xFF
    ldat.data = bytes(ldat_bytes)
    return True


def set_keyframe_ease(root: Chunk, comp_id: int, layer_id: int,
                      match_name_path: list[str], key_index: int,
                      in_speed: list[float] | None, in_influence: list[float] | None,
                      out_speed: list[float] | None, out_influence: list[float] | None,
                      big_endian: bool) -> bool:
    """Set a keyframe's temporal ease (speed/influence) in the ldat chunk.

    Args:
        key_index: 1-based keyframe index.
        in_speed, in_influence, out_speed, out_influence: Per-component ease values.
            Pass None to leave unchanged.

    Returns True if successful.
    """
    info, _ = _locate_prop_ldat(root, comp_id, layer_id, match_name_path, big_endian)
    if info is None:
        return False
    components, is_spatial, time_scale, count, item_size, ldat = info

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

    fmt = ">" if big_endian else "<"
    ldat_bytes = bytearray(ldat.data)
    record_start = idx * item_size

    if is_spatial or components == 1:
        # Scalar / spatial / color: ease at offset 8 + 16 = 24
        # Layout: [8 header][16 skip][in_speed f64][in_influence f64]
        #         [out_speed f64][out_influence f64]
        ease_offset = record_start + 8 + 16
        if ease_offset + 32 > len(ldat_bytes):
            return False
        if in_speed is not None and len(in_speed) >= 1:
            struct.pack_into(f"{fmt}d", ldat_bytes, ease_offset, in_speed[0])
        if in_influence is not None and len(in_influence) >= 1:
            struct.pack_into(f"{fmt}d", ldat_bytes, ease_offset + 8, in_influence[0])
        if out_speed is not None and len(out_speed) >= 1:
            struct.pack_into(f"{fmt}d", ldat_bytes, ease_offset + 16, out_speed[0])
        if out_influence is not None and len(out_influence) >= 1:
            struct.pack_into(f"{fmt}d", ldat_bytes, ease_offset + 24, out_influence[0])
    else:
        # Multi-dimensional (type 3/5): ease is interleaved after value
        # Layout: [8 header][value: C*8][in_speed: C*8][in_influence: C*8]
        #         [out_speed: C*8][out_influence: C*8]
        val_offset = record_start + 8
        c = components
        is_off = val_offset + c * 8
        ii_off = is_off + c * 8
        os_off = ii_off + c * 8
        oi_off = os_off + c * 8
        if oi_off + c * 8 > len(ldat_bytes):
            return False
        for i in range(c):
            if in_speed is not None and i < len(in_speed):
                struct.pack_into(f"{fmt}d", ldat_bytes, is_off + i * 8, in_speed[i])
            if in_influence is not None and i < len(in_influence):
                struct.pack_into(f"{fmt}d", ldat_bytes, ii_off + i * 8, in_influence[i])
            if out_speed is not None and i < len(out_speed):
                struct.pack_into(f"{fmt}d", ldat_bytes, os_off + i * 8, out_speed[i])
            if out_influence is not None and i < len(out_influence):
                struct.pack_into(f"{fmt}d", ldat_bytes, oi_off + i * 8, out_influence[i])

    ldat.data = bytes(ldat_bytes)
    return True


# ── ldta / cdta field writers ──────────────────────────────────────────────


# Flag name → (byte_index within 4-byte flags field, bit_index)
_FLAG_MAP: dict[str, tuple[int, int]] = {
    'is_guide':               (1, 1),
    'bicubic_sampling':       (1, 6),
    'auto_orient':            (2, 0),
    'is_adjustment':          (2, 1),
    'threedimensional':       (2, 2),
    'solo':                   (2, 3),
    'is_null':                (2, 7),
    'visible':                (3, 0),
    'effects_enabled':        (3, 2),
    'motion_blur_enabled':    (3, 3),
    'locked':                 (3, 5),
    'shy':                    (3, 6),
    'continuously_rasterize': (3, 7),
}

_LDTA_FLAGS_OFF = 36


def _find_ldta(root: Chunk, comp_id: int, layer_id: int,
               big_endian: bool) -> Chunk | None:
    """Find the ldta chunk for a layer."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return None
    layer_chunk = find_layer_chunk(comp_cl, layer_id, big_endian)
    if layer_chunk is None:
        return None
    ldta = layer_chunk.list.find_optional("ldta")
    if ldta is not None and isinstance(ldta.data, (bytes, bytearray)):
        return ldta
    return None


def set_layer_flag(root: Chunk, comp_id: int, layer_id: int,
                   flag_name: str, value: bool, big_endian: bool) -> bool:
    """Set a boolean flag in the ldta chunk."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    mapping = _FLAG_MAP.get(flag_name)
    if mapping is None:
        return False
    byte_idx, bit_idx = mapping
    offset = _LDTA_FLAGS_OFF + byte_idx
    data = bytearray(ldta.data)
    if value:
        data[offset] |= (1 << bit_idx)
    else:
        data[offset] &= ~(1 << bit_idx)
    ldta.data = bytes(data)
    return True


def set_layer_label(root: Chunk, comp_id: int, layer_id: int,
                    label: int, big_endian: bool) -> bool:
    """Set a layer's label color index (uint8 at ldta offset 61)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    data = bytearray(ldta.data)
    data[61] = label & 0xFF
    ldta.data = bytes(data)
    return True


def set_layer_blend_mode(root: Chunk, comp_id: int, layer_id: int,
                         mode: int, big_endian: bool) -> bool:
    """Set a layer's blend mode (uint32 at ldta offset 96)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    fmt = ">I" if big_endian else "<I"
    data = bytearray(ldta.data)
    struct.pack_into(fmt, data, 96, int(mode))
    ldta.data = bytes(data)
    return True


def set_layer_track_matte(root: Chunk, comp_id: int, layer_id: int,
                          matte_type: int, big_endian: bool) -> bool:
    """Set a layer's track matte type (uint32 at ldta offset 104)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    fmt = ">I" if big_endian else "<I"
    data = bytearray(ldta.data)
    struct.pack_into(fmt, data, 104, int(matte_type))
    ldta.data = bytes(data)
    return True


def set_layer_quality(root: Chunk, comp_id: int, layer_id: int,
                      quality: int, big_endian: bool) -> bool:
    """Set a layer's quality (uint16 at ldta offset 4)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    fmt = ">H" if big_endian else "<H"
    data = bytearray(ldta.data)
    struct.pack_into(fmt, data, 4, int(quality))
    ldta.data = bytes(data)
    return True


# Time fields in ldta stored as rational numbers (numerator / denominator).
# time_stretch denominator is uint16 at a separate offset.
_LDTA_TIME_FIELDS: dict[str, tuple[int, int, str]] = {
    # field → (num_offset, den_offset, den_struct_format)
    'in_time':      (20, 24, 'I'),
    'out_time':     (28, 32, 'I'),
    'start_time':   (12, 16, 'I'),
    'time_stretch': (8, 110, 'H'),
}


def set_layer_time_field(root: Chunk, comp_id: int, layer_id: int,
                         field: str, value: float,
                         big_endian: bool) -> bool:
    """Set a layer time field (in_time, out_time, start_time, time_stretch).

    Reads the existing denominator and adjusts the numerator.
    """
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    offsets = _LDTA_TIME_FIELDS.get(field)
    if offsets is None:
        return False
    num_off, den_off, den_fmt = offsets
    fmt = ">" if big_endian else "<"
    data = bytearray(ldta.data)
    den = struct.unpack_from(f"{fmt}{den_fmt}", data, den_off)[0]
    if den == 0:
        return False
    new_num = int(round(value * den))
    struct.pack_into(f"{fmt}i", data, num_off, new_num)
    ldta.data = bytes(data)
    return True


# ── cdta helpers ──────────────────────────────────────────────────────────


def _find_cdta(root: Chunk, comp_id: int, big_endian: bool) -> Chunk | None:
    """Find the cdta chunk for a composition."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return None
    cdta = comp_cl.find_optional("cdta")
    if cdta is not None and isinstance(cdta.data, (bytes, bytearray)):
        return cdta
    return None


def set_comp_dimensions(root: Chunk, comp_id: int, width: int, height: int,
                        big_endian: bool) -> bool:
    """Set composition width and height (uint16 each at cdta offset 140/142)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    struct.pack_into(f"{fmt}HH", data, 140, width, height)
    cdta.data = bytes(data)
    return True


def set_comp_bgcolor(root: Chunk, comp_id: int,
                     r: int, g: int, b: int, big_endian: bool) -> bool:
    """Set composition background color (3 bytes at cdta offset 52)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    data = bytearray(cdta.data)
    data[52] = int(r) & 0xFF
    data[53] = int(g) & 0xFF
    data[54] = int(b) & 0xFF
    cdta.data = bytes(data)
    return True


def set_comp_framerate(root: Chunk, comp_id: int, framerate: float,
                       big_endian: bool) -> bool:
    """Set composition frame rate by adjusting numerator (cdta offset 4-11)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    time_denom = struct.unpack_from(f"{fmt}I", data, 4)[0]
    if time_denom == 0:
        time_denom = 1
    new_num = int(round(framerate * time_denom))
    struct.pack_into(f"{fmt}I", data, 8, new_num)
    cdta.data = bytes(data)
    return True


def set_comp_duration(root: Chunk, comp_id: int, duration: float,
                      big_endian: bool) -> bool:
    """Set composition duration (cdta offset 45).

    Reads the existing divisor and frame rate to compute the raw frame count.
    """
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    time_denom = struct.unpack_from(f"{fmt}I", data, 4)[0]
    time_num = struct.unpack_from(f"{fmt}I", data, 8)[0]
    framerate = time_num / time_denom if time_denom else 30.0
    raw_dur_div = struct.unpack_from(f"{fmt}H", data, 49)[0]
    if raw_dur_div == 0 or framerate == 0:
        return False
    new_raw = int(round(duration * raw_dur_div / framerate))
    struct.pack_into(f"{fmt}H", data, 45, new_raw)
    cdta.data = bytes(data)
    return True


# ── Pre-save fixup ─────────────────────────────────────────────────────


# Properties that always need 3 components regardless of 2D/3D state.
_ALWAYS_3_PROPS = ("ADBE Anchor Point",)
# Properties that need 3 components only on 3D layers.
_3D_ONLY_PROPS = ("ADBE Position",)


def _fix_spatial_dimensions(root: Chunk, big_endian: bool) -> None:
    """Scan all layers and upgrade 2-component spatial properties.

    AE always requires Anchor Point to have 3 components (even on 2D layers).
    Position needs 3 components only on 3D layers.
    """
    fold = root.list.find_optional("Fold")
    if fold is None:
        return
    _fix_dims_in_folder(fold.list, big_endian)


def _fix_dims_in_folder(cl, big_endian: bool) -> None:
    for child in cl.children:
        if child.name == "Item":
            _fix_dims_in_item(child.list, big_endian)
            _fix_dims_in_folder(child.list, big_endian)
        elif child.name == "Sfdr":
            _fix_dims_in_folder(child.list, big_endian)


def _fix_dims_in_item(item_cl, big_endian: bool) -> None:
    """Check all layers in an item (comp) for dimension mismatches."""
    for child in item_cl.children:
        if child.name != "Layr":
            continue
        layr_cl = child.list
        ldta = layr_cl.find_optional("ldta")
        if ldta is None or not isinstance(ldta.data, (bytes, bytearray)):
            continue
        if len(ldta.data) < 40:
            continue
        is_3d = bool(ldta.data[_LDTA_FLAGS_OFF + 2] & (1 << 2))
        tdgp = layr_cl.find_optional("tdgp")
        if tdgp is None or not _is_chunk_list(tdgp.data):
            continue
        transform = _find_named_child(tdgp.data, "ADBE Transform Group")
        if transform is None or not _is_chunk_list(transform.data):
            continue
        # Anchor Point: always 3 components
        for prop_mn in _ALWAYS_3_PROPS:
            prop_chunk = _find_named_child(transform.data, prop_mn)
            if prop_chunk is None or not _is_chunk_list(prop_chunk.data):
                continue
            _upgrade_prop_to_3(prop_chunk.data, big_endian)
        # Position: 3 components only on 3D layers
        if is_3d:
            for prop_mn in _3D_ONLY_PROPS:
                prop_chunk = _find_named_child(transform.data, prop_mn)
                if prop_chunk is None or not _is_chunk_list(prop_chunk.data):
                    continue
                _upgrade_prop_to_3(prop_chunk.data, big_endian)


def _upgrade_prop_to_3(prop_cl, big_endian: bool) -> None:
    """Upgrade a 2-component spatial property to 3 components in-place."""
    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is None or not isinstance(tdb4.data, (bytes, bytearray)):
        return
    if len(tdb4.data) < 6:
        return
    cur = struct.unpack_from(">H", tdb4.data, 2)[0]
    if cur >= 3:
        return  # already 3+ components
    is_spatial = bool(tdb4.data[5] & (1 << 3))
    if not is_spatial:
        return

    # Update tdb4 component count to 3
    tdb4_bytes = bytearray(tdb4.data)
    struct.pack_into(">H", tdb4_bytes, 2, 3)
    tdb4.data = bytes(tdb4_bytes)

    # Rebuild cdat: [3 values][3 spatial_in][3 spatial_out][3 temporal]
    cdat = prop_cl.find_optional("cdat")
    if cdat is None or not isinstance(cdat.data, (bytes, bytearray)):
        return
    fmt = ">" if big_endian else "<"
    old_count = cur * 3 + 3  # old: 2*3+3 = 9
    new_count = 3 * 3 + 3    # new: 12
    try:
        old_floats = list(struct.unpack_from(f"{fmt}{'d' * old_count}", cdat.data))
    except struct.error:
        return
    # Rearrange: [val*2][sin*2][sout*2][temp*3] → [val*3][sin*3][sout*3][temp*3]
    vals = old_floats[0:cur] + [0.0]
    sin = old_floats[cur:cur * 2] + [0.0]
    sout = old_floats[cur * 2:cur * 3] + [0.0]
    temp = old_floats[cur * 3:cur * 3 + 3]
    new_floats = vals + sin + sout + temp
    cdat_data = struct.pack(f"{fmt}{'d' * new_count}", *new_floats)
    cdat.data = cdat_data
    cdat.length = len(cdat_data)


# High-level Save


def save_aep(root: Chunk, big_endian: bool, path: str | Path,
             trailing_data: bytes = b"") -> None:
    """Serialize the chunk tree and write to a file."""
    _fix_spatial_dimensions(root, big_endian)
    data = serialize_chunk_tree(root, big_endian)
    Path(path).write_bytes(data + trailing_data)
