"""Property value and keyframe modification functions."""

from __future__ import annotations

import struct

from aep_parser._parser.binary_reader import BinaryReader
from aep_parser._parser.chunk import Chunk, ChunkList

from ._common import _is_chunk_list
from ._navigate import find_comp_chunklist, find_layer_chunk, find_property_chunk

# Template tdb4 for 1-component scalar properties (Opacity, Rotate Z, etc.)
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
_TDB4_SPATIAL_3[2:4] = b'\x00\x03'
_TDB4_SPATIAL_3 = bytes(_TDB4_SPATIAL_3)

# Match name → (components, spatial, tdb4_template, tdum, tduM)
_PROPERTY_TEMPLATES: dict[str, tuple[int, bool, bytes, float, float]] = {
    "ADBE Opacity":      (1, False, _TDB4_SCALAR_1, 0.0, 100.0),
    "ADBE Rotate Z":     (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Rotate X":     (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Rotate Y":     (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Scale":        (3, False, _TDB4_SCALAR_3, 0.0, 0.0),
    "ADBE Anchor Point": (3, True,  _TDB4_SPATIAL_3, 0.0, 0.0),
    "ADBE Position":     (2, True,  _TDB4_SPATIAL_2, 0.0, 0.0),
    "ADBE Position_0":   (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Position_1":   (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Position_2":   (1, False, _TDB4_SCALAR_1, 0.0, 0.0),
    "ADBE Orientation":  (3, False, _TDB4_SCALAR_3, 0.0, 0.0),
}


def _create_tdbs_chunk(match_name: str, value: list[float],
                       big_endian: bool) -> Chunk | None:
    """Create a new tdbs (animated property) chunk from a template."""
    template = _PROPERTY_TEMPLATES.get(match_name)
    if template is None:
        return None

    components, is_spatial, tdb4_data, tdum_val, tduM_val = template
    actual_components = max(components, len(value))
    fmt = ">" if big_endian else "<"

    tdsb = Chunk("tdsb", 4, b"\x00\x00\x00\x01")
    tdsn_utf8 = Chunk("Utf8", 6, "-_0_/-")
    tdsn = Chunk("tdsn", 14, ChunkList("", [tdsn_utf8]))

    tdb4_bytes = bytearray(tdb4_data)
    struct.pack_into(">H", tdb4_bytes, 2, actual_components)
    tdb4 = Chunk("tdb4", len(tdb4_bytes), bytes(tdb4_bytes))

    cdat_count = actual_components * 3 + 3 if is_spatial else actual_components * 5
    cdat_floats = list(value) + [0.0] * (cdat_count - len(value))
    cdat_data = struct.pack(f"{fmt}{'d' * cdat_count}", *cdat_floats)
    cdat = Chunk("cdat", len(cdat_data), cdat_data)

    tdum = Chunk("tdum", 8, struct.pack(f"{fmt}d", tdum_val))
    tduM = Chunk("tduM", 8, struct.pack(f"{fmt}d", tduM_val))

    children = [tdsb, tdsn, tdb4, cdat, tdum, tduM]
    tdbs_cl = ChunkList("tdbs", children)
    total = 4
    for c in children:
        total += 8 + c.length + (c.length % 2)
    return Chunk("LIST", total, tdbs_cl)


def _insert_property_into_group(parent_cl: ChunkList, match_name: str,
                                tdbs_chunk: Chunk) -> None:
    """Insert a tdmn + tdbs pair into a property group before ADBE Group End."""
    mn_bytes = match_name.encode("utf-8") + b"\x00"
    if len(mn_bytes) < 32:
        mn_bytes += b"\x00" * (32 - len(mn_bytes))
    tdmn = Chunk("tdmn", len(mn_bytes), match_name)
    tdmn.length = len(mn_bytes)

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
    """Set a property's static value (cdat) by navigating the property tree."""
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

    if isinstance(new_value, (int, float)):
        new_value = [float(new_value)]
    elif isinstance(new_value, list):
        new_value = [float(v) for v in new_value]

    prop_chunk = find_property_chunk(tdgp.list, match_name_path)

    if prop_chunk is None:
        if len(match_name_path) < 2:
            return False
        target_mn = match_name_path[-1]
        tdbs_chunk = _create_tdbs_chunk(target_mn, new_value, big_endian)
        if tdbs_chunk is None:
            return False
        parent_chunk = find_property_chunk(tdgp.list, match_name_path[:-1])
        if parent_chunk is None or not _is_chunk_list(parent_chunk.data):
            return False
        _insert_property_into_group(parent_chunk.data, target_mn, tdbs_chunk)
        return True

    if not _is_chunk_list(prop_chunk.data):
        return False

    prop_cl = prop_chunk.data
    cdat = prop_cl.find_optional("cdat")
    if cdat is None:
        return False

    fmt = ">" if big_endian else "<"

    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is not None and isinstance(tdb4.data, (bytes, bytearray)) and len(tdb4.data) >= 6:
        cur_components = struct.unpack_from(">H", tdb4.data, 2)[0]
        if len(new_value) > cur_components:
            is_spatial = bool(tdb4.data[5] & (1 << 3))
            new_components = len(new_value)
            tdb4_bytes = bytearray(tdb4.data)
            struct.pack_into(">H", tdb4_bytes, 2, new_components)
            tdb4.data = bytes(tdb4_bytes)
            cdat_count = new_components * 3 + 3 if is_spatial else new_components * 5
            cdat_floats = list(new_value) + [0.0] * (cdat_count - len(new_value))
            cdat_data = struct.pack(f"{fmt}{'d' * cdat_count}", *cdat_floats)
            cdat.data = cdat_data
            cdat.length = len(cdat_data)
            return True

    packed = struct.pack(f"{fmt}{'d' * len(new_value)}", *new_value)
    old_data = bytearray(cdat.data)
    old_data[:len(packed)] = packed
    cdat.data = bytes(old_data)
    return True


def set_keyframe_value(root: Chunk, comp_id: int, layer_id: int,
                       match_name_path: list[str], key_index: int,
                       new_value: list[float] | float,
                       big_endian: bool) -> bool:
    """Set a keyframe value in the ldat chunk of an animated property."""
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

    tdb4 = prop_cl.find_optional("tdb4")
    if tdb4 is None or not isinstance(tdb4.data, (bytes, bytearray)):
        return False
    tdb4_r = BinaryReader(tdb4.data, 0, big_endian)
    tdb4_r.skip(2)
    components = tdb4_r.read_uint(2)
    flags2 = tdb4_r.read_flags(2)
    is_spatial = flags2.get_bit(1, 3)

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

    value_offset = 8
    if is_spatial:
        value_offset += 16

    start = idx * item_size + value_offset
    fmt_prefix = ">" if big_endian else "<"
    packed = struct.pack(f"{fmt_prefix}{'d' * len(new_value)}", *new_value)

    if start + len(packed) > len(ldat.data):
        return False

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
    """Set a keyframe's time in the ldat chunk."""
    info, _ = _locate_prop_ldat(root, comp_id, layer_id, match_name_path, big_endian)
    if info is None:
        return False
    components, is_spatial, time_scale, count, item_size, ldat = info

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

    time_raw = int(round(new_time * time_scale))
    fmt = ">i" if big_endian else "<i"
    packed = struct.pack(fmt, time_raw)

    start = idx * item_size + 1
    ldat_bytes = bytearray(ldat.data)
    ldat_bytes[start:start + 4] = packed
    ldat.data = bytes(ldat_bytes)
    return True


def set_keyframe_interpolation(root: Chunk, comp_id: int, layer_id: int,
                               match_name_path: list[str], key_index: int,
                               transition_type: int,
                               big_endian: bool) -> bool:
    """Set a keyframe's interpolation type in the ldat chunk."""
    info, _ = _locate_prop_ldat(root, comp_id, layer_id, match_name_path, big_endian)
    if info is None:
        return False
    components, is_spatial, time_scale, count, item_size, ldat = info

    idx = key_index - 1
    if idx < 0 or idx >= count:
        return False

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
    """Set a keyframe's temporal ease (speed/influence) in the ldat chunk."""
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
