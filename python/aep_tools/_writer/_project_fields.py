"""Project-level settings writers — bits per channel, gamma, audio, etc."""

from __future__ import annotations

import struct

from aep_parser._parser.chunk import Chunk

_BITS_REV = {8: 0, 16: 1, 32: 2}


def set_project_bits_per_channel(root: Chunk, bits: int,
                                  big_endian: bool) -> bool:
    """Set project bits per channel (uint8 at nnhd offset 24)."""
    nnhd = root.list.find_optional("nnhd")
    if nnhd is None or not isinstance(nnhd.data, (bytes, bytearray)):
        return False
    data = bytearray(nnhd.data)
    data[24] = _BITS_REV.get(bits, 0)
    nnhd.data = bytes(data)
    return True


def set_project_linearize_working_space(root: Chunk, value: bool,
                                         big_endian: bool) -> bool:
    """Set project linearize working space flag (nnhd offset 31, bit 5)."""
    nnhd = root.list.find_optional("nnhd")
    if nnhd is None or not isinstance(nnhd.data, (bytes, bytearray)):
        return False
    data = bytearray(nnhd.data)
    if value:
        data[31] |= (1 << 5)
    else:
        data[31] &= ~(1 << 5)
    nnhd.data = bytes(data)
    return True


def set_project_audio_sample_rate(root: Chunk, rate: float,
                                   big_endian: bool) -> bool:
    """Set project audio sample rate (float64 in adfr chunk, always big-endian)."""
    adfr = root.list.find_optional("adfr")
    if adfr is None or not isinstance(adfr.data, (bytes, bytearray)):
        return False
    data = bytearray(adfr.data)
    struct.pack_into(">d", data, 0, rate)
    adfr.data = bytes(data)
    return True


def set_project_working_gamma(root: Chunk, gamma: float,
                               big_endian: bool) -> bool:
    """Set project working gamma (dwga chunk: 0=2.2, 1=2.4)."""
    dwga = root.list.find_optional("dwga")
    if dwga is None or not isinstance(dwga.data, (bytes, bytearray)):
        return False
    dwga.data = bytes([1 if gamma > 2.3 else 0])
    return True


def set_project_compensate_scene_referred(root: Chunk, value: bool,
                                           big_endian: bool) -> bool:
    """Set project compensate for scene-referred profiles (acer chunk)."""
    acer = root.list.find_optional("acer")
    if acer is None or not isinstance(acer.data, (bytes, bytearray)):
        return False
    acer.data = bytes([1 if value else 0])
    return True
