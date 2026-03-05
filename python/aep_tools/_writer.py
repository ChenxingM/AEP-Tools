"""Binary .aep writer — serialize chunk tree back to RIFX/RIFF format.

Supports modifying layer names and property values in-place on the chunk tree,
then writing the result to a new .aep file.
"""

from __future__ import annotations

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

# Match name → (components, tdb4_template, tdum, tduM)
_PROPERTY_TEMPLATES: dict[str, tuple[int, bytes, float, float]] = {
    "ADBE Opacity":      (1, _TDB4_SCALAR_1, 0.0, 100.0),
    "ADBE Rotate Z":     (1, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Scale":        (3, _TDB4_SCALAR_3, 0.0, 0.0),
    "ADBE Anchor Point": (2, _TDB4_SPATIAL_2, 0.0, 0.0),
    "ADBE Position":     (2, _TDB4_SPATIAL_2, 0.0, 0.0),
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
    """Create a new tdbs (animated property) chunk from a template."""
    template = _PROPERTY_TEMPLATES.get(match_name)
    if template is None:
        return None

    components, tdb4_data, tdum_val, tduM_val = template
    fmt = ">" if big_endian else "<"

    # tdsb: flags (visible, not split)
    tdsb = Chunk("tdsb", 4, b"\x00\x00\x00\x01")

    # tdsn: display name placeholder
    tdsn_utf8 = Chunk("Utf8", 6, "-_0_/-")
    tdsn = Chunk("tdsn", 14, ChunkList("", [tdsn_utf8]))

    # tdb4: property metadata
    tdb4 = Chunk("tdb4", len(tdb4_data), tdb4_data)

    # cdat: value data — components * 5 float64s (value + 4 tangent/influence slots)
    cdat_floats = list(value) + [0.0] * (components * 5 - len(value))
    cdat_data = struct.pack(f"{fmt}{'d' * len(cdat_floats)}", *cdat_floats)
    cdat = Chunk("cdat", len(cdat_data), cdat_data)

    children = [tdsb, tdsn, tdb4, cdat]

    # tdum/tduM: min/max bounds (only if non-zero)
    if tdum_val != 0.0 or tduM_val != 0.0:
        tdum = Chunk("tdum", 8, struct.pack(f"{fmt}d", tdum_val))
        tduM = Chunk("tduM", 8, struct.pack(f"{fmt}d", tduM_val))
        children.extend([tdum, tduM])

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

    # Write new float64 values into cdat
    fmt = ">" if big_endian else "<"
    fmt += "d" * len(new_value)
    new_data = struct.pack(fmt, *new_value)
    cdat.data = new_data
    cdat.length = len(new_data)
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


# High-level Save


def save_aep(root: Chunk, big_endian: bool, path: str | Path) -> None:
    """Serialize the chunk tree and write to a file."""
    data = serialize_chunk_tree(root, big_endian)
    Path(path).write_bytes(data)
