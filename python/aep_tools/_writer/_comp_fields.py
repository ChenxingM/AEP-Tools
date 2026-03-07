"""Composition cdta field modifications — dimensions, framerate, flags, etc."""

from __future__ import annotations

import struct

from aep_parser._parser.chunk import Chunk, ChunkList

from ._navigate import find_comp_chunklist


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
    """Set composition frame rate (u2be integer + u2be fractional at cdta offset 156-159)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    fr_int = int(framerate)
    fr_frac = int(round((framerate - fr_int) * 65536))
    struct.pack_into(f"{fmt}HH", data, 156, fr_int, fr_frac)
    cdta.data = bytes(data)
    return True


def set_comp_duration(root: Chunk, comp_id: int, duration: float,
                      big_endian: bool) -> bool:
    """Set composition duration (u4be dividend/divisor at cdta offset 44-51)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    divisor = struct.unpack_from(f"{fmt}I", data, 48)[0]
    if divisor == 0:
        divisor = 24576
        struct.pack_into(f"{fmt}I", data, 48, divisor)
    new_dividend = int(round(duration * divisor))
    struct.pack_into(f"{fmt}I", data, 44, new_dividend)
    cdta.data = bytes(data)
    return True


def set_comp_work_area_start(root: Chunk, comp_id: int, start: float,
                              big_endian: bool) -> bool:
    """Set composition work area start (u4be dividend/divisor at cdta offset 28-35)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    divisor = struct.unpack_from(f"{fmt}I", data, 32)[0]
    if divisor == 0:
        divisor = 600
        struct.pack_into(f"{fmt}I", data, 32, divisor)
    new_dividend = int(round(start * divisor))
    struct.pack_into(f"{fmt}I", data, 28, new_dividend)
    cdta.data = bytes(data)
    return True


def set_comp_work_area_end(root: Chunk, comp_id: int, end: float,
                            big_endian: bool) -> bool:
    """Set composition work area end (u4be dividend/divisor at cdta offset 36-43)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    divisor = struct.unpack_from(f"{fmt}I", data, 40)[0]
    if divisor == 0:
        divisor = 600
        struct.pack_into(f"{fmt}I", data, 40, divisor)
    new_dividend = int(round(end * divisor))
    struct.pack_into(f"{fmt}I", data, 36, new_dividend)
    cdta.data = bytes(data)
    return True


# Comp flags in cdta (offset → bit position)
_COMP_FLAG_MAP: dict[str, tuple[int, int]] = {
    'draft3d':                     (138, 7),
    'preserve_nested_resolution':  (139, 7),
    'preserve_nested_frame_rate':  (139, 5),
    'frame_blending':              (139, 4),
    'motion_blur':                 (139, 3),
    'hide_shy_layers':             (139, 0),
}


def set_comp_flag(root: Chunk, comp_id: int, flag_name: str, value: bool,
                   big_endian: bool) -> bool:
    """Set a boolean flag in the cdta chunk."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    mapping = _COMP_FLAG_MAP.get(flag_name)
    if mapping is None:
        return False
    offset, bit = mapping
    data = bytearray(cdta.data)
    if value:
        data[offset] |= (1 << bit)
    else:
        data[offset] &= ~(1 << bit)
    cdta.data = bytes(data)
    return True


def set_comp_shutter_angle(root: Chunk, comp_id: int, angle: int,
                            big_endian: bool) -> bool:
    """Set composition shutter angle (uint16 at cdta offset 174)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    struct.pack_into(f"{fmt}H", data, 174, int(angle))
    cdta.data = bytes(data)
    return True


def set_comp_shutter_phase(root: Chunk, comp_id: int, phase: int,
                            big_endian: bool) -> bool:
    """Set composition shutter phase (sint32 at cdta offset 180)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    struct.pack_into(f"{fmt}i", data, 180, int(phase))
    cdta.data = bytes(data)
    return True


def set_comp_motion_blur_samples(root: Chunk, comp_id: int,
                                  samples_per_frame: int,
                                  adaptive_limit: int,
                                  big_endian: bool) -> bool:
    """Set composition motion blur sample counts (sint32 at cdta offset 196/200)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    struct.pack_into(f"{fmt}i", data, 196, int(adaptive_limit))
    struct.pack_into(f"{fmt}i", data, 200, int(samples_per_frame))
    cdta.data = bytes(data)
    return True


def set_comp_pixel_aspect(root: Chunk, comp_id: int, ratio: float,
                           big_endian: bool) -> bool:
    """Set composition pixel aspect ratio (uint32 pair at cdta offset 144-151)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    pixel_h = 10000
    pixel_w = int(round(ratio * pixel_h))
    struct.pack_into(f"{fmt}II", data, 144, pixel_w, pixel_h)
    cdta.data = bytes(data)
    return True


def set_comp_display_start_time(root: Chunk, comp_id: int, time: float,
                                 big_endian: bool) -> bool:
    """Set composition display start time (rational at cdta offset 164-171)."""
    cdta = _find_cdta(root, comp_id, big_endian)
    if cdta is None:
        return False
    fmt = ">" if big_endian else "<"
    data = bytearray(cdta.data)
    divisor = struct.unpack_from(f"{fmt}I", data, 168)[0]
    if divisor == 0:
        divisor = 1
    dividend = int(round(time * divisor))
    struct.pack_into(f"{fmt}i", data, 164, dividend)
    cdta.data = bytes(data)
    return True


def set_comp_drop_frame(root: Chunk, comp_id: int, drop_frame: bool,
                         big_endian: bool) -> bool:
    """Set composition drop frame flag (cdrp chunk)."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False
    cdrp = comp_cl.find_optional("cdrp")
    if cdrp is None:
        cdrp = Chunk("cdrp", 1, bytes([1 if drop_frame else 0]))
        comp_cl.children.append(cdrp)
    else:
        cdrp.data = bytes([1 if drop_frame else 0])
    return True
