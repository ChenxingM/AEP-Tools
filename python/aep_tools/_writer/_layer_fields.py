"""Layer ldta field modifications — flags, blend mode, timing, etc."""

from __future__ import annotations

import struct

from aep_parser._parser.chunk import Chunk

from ._navigate import find_comp_chunklist, find_layer_chunk

# Flag name → (byte_index within 4-byte flags field, bit_index)
_FLAG_MAP: dict[str, tuple[int, int]] = {
    'is_guide':               (1, 1),
    'frame_blending_type':    (1, 2),
    'environment_layer':      (1, 5),
    'bicubic_sampling':       (1, 6),
    'auto_orient':            (2, 0),
    'is_adjustment':          (2, 1),
    'threedimensional':       (2, 2),
    'solo':                   (2, 3),
    'is_null':                (2, 7),
    'visible':                (3, 0),
    'audio_enabled':          (3, 1),
    'effects_enabled':        (3, 2),
    'motion_blur_enabled':    (3, 3),
    'frame_blending':         (3, 4),
    'locked':                 (3, 5),
    'shy':                    (3, 6),
    'continuously_rasterize': (3, 7),
    'collapse_transformation': (3, 7),
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


def set_layer_preserve_transparency(root: Chunk, comp_id: int, layer_id: int,
                                     value: bool, big_endian: bool) -> bool:
    """Set a layer's preserve transparency flag (uint8 at ldta offset 103)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    data = bytearray(ldta.data)
    data[103] = 1 if value else 0
    ldta.data = bytes(data)
    return True


def set_layer_light_type(root: Chunk, comp_id: int, layer_id: int,
                          light_type: int, big_endian: bool) -> bool:
    """Set a layer's light type (uint8 at ldta offset 139)."""
    ldta = _find_ldta(root, comp_id, layer_id, big_endian)
    if ldta is None:
        return False
    data = bytearray(ldta.data)
    data[139] = light_type & 0xFF
    ldta.data = bytes(data)
    return True


# Time fields in ldta stored as rational numbers (numerator / denominator).
_LDTA_TIME_FIELDS: dict[str, tuple[int, int, str]] = {
    'in_time':      (20, 24, 'I'),
    'out_time':     (28, 32, 'I'),
    'start_time':   (12, 16, 'I'),
    'time_stretch': (8, 110, 'H'),
}


def set_layer_time_field(root: Chunk, comp_id: int, layer_id: int,
                         field: str, value: float,
                         big_endian: bool) -> bool:
    """Set a layer time field (in_time, out_time, start_time, time_stretch)."""
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
