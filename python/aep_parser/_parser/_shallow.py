"""Lightweight top-level chunk scanner.

Builds only the root's direct child chunks (plus a small whitelist of
settings-bearing containers) so project-level settings can be read without
materializing the entire comp/layer/asset tree. Used by ``parse_aep_settings``.

A full ``parse_riff`` of a large .aep can expand a 73 MB file into ~1.3M Python
objects (~3x file size); this scanner builds only a few dozen.
"""

from __future__ import annotations

import struct

from .chunk import Chunk, ChunkList

# Small top-level LIST containers whose children hold project settings.
# Everything else (Fold, LRdr, CPPl, ...) is skipped without recursing.
_EXPAND = {"ExEn", "gpuG"}


def _decode_leaf(header: str, body: bytes):
    """Match how the full parser stores leaf chunk data (str for Utf8/alas)."""
    if header in ("Utf8", "alas"):
        try:
            return body.decode("utf-8")
        except UnicodeDecodeError:
            return body
    return body


def _parse_list(data: bytes, start: int, end: int, list_type: str,
                big_endian: bool) -> ChunkList:
    fmt = ">I" if big_endian else "<I"
    children: list[Chunk] = []
    off = start
    while off + 8 <= end:
        header = data[off:off + 4].decode("latin-1", "replace")
        size = struct.unpack_from(fmt, data, off + 4)[0]
        body_start = off + 8
        body_end = min(body_start + size, end)  # clamp: survive truncated files
        if header == "LIST":
            sub_type = data[body_start:body_start + 4].decode("latin-1", "replace")
            if sub_type in _EXPAND:
                cl = _parse_list(data, body_start + 4, body_end, sub_type, big_endian)
            else:
                cl = ChunkList(type=sub_type, children=[])  # body intentionally skipped
            children.append(Chunk(header="LIST", length=size, data=cl))
        else:
            body = data[body_start:body_end]
            children.append(Chunk(header=header, length=size,
                                  data=_decode_leaf(header, body)))
        off = body_end
        if size % 2 == 1 and off < end:
            off += 1  # RIFF pad byte
    return ChunkList(type=list_type, children=children)


def scan_top_level(data: bytes) -> tuple[ChunkList, bool]:
    """Return (top_level_chunklist, big_endian) for an .aep byte buffer.

    Only the root's direct children are materialized; heavy containers are
    recorded by name with an empty child list.
    """
    if len(data) < 12:
        raise ValueError("File is too small to be a valid AEP file.")
    magic = data[:4]
    if magic == b"RIFX":
        big_endian = True
    elif magic == b"RIFF":
        big_endian = False
    else:
        raise ValueError(f"Unknown format: {magic!r} (expected RIFF or RIFX)")
    if data[8:12] != b"Egg!":
        raise ValueError(f"Invalid AEP file (expected 'Egg!', got {data[8:12]!r})")
    fmt = ">I" if big_endian else "<I"
    size = struct.unpack_from(fmt, data, 4)[0]
    end = min(8 + size, len(data))
    cl = _parse_list(data, 12, end, "Egg!", big_endian)
    return cl, big_endian
