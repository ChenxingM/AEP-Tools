"""RIFF/RIFX binary serialization and save function."""

from __future__ import annotations

import struct
from pathlib import Path

from aep_parser._parser.chunk import Chunk, ChunkList

from ._common import _is_chunk_list
from ._navigate import _find_named_child
from ._layer_fields import _LDTA_FLAGS_OFF


def serialize_chunk_tree(root: Chunk, big_endian: bool) -> bytes:
    """Serialize an entire chunk tree back to RIFX/RIFF binary."""
    buf = bytearray()
    _write_root(buf, root, big_endian)
    return bytes(buf)


def _pack_u32(val: int, big_endian: bool) -> bytes:
    return struct.pack(">I" if big_endian else "<I", val)


def _write_root(buf: bytearray, root: Chunk, big_endian: bool) -> None:
    """Write the RIFX/RIFF root chunk."""
    buf.extend(root.header.encode("ascii"))
    size_pos = len(buf)
    buf.extend(b"\x00\x00\x00\x00")
    cl = root.data
    buf.extend(cl.type.encode("ascii"))
    for child in cl.children:
        _write_chunk(buf, child, big_endian)
    data_size = len(buf) - size_pos - 4
    buf[size_pos:size_pos + 4] = _pack_u32(data_size, big_endian)


def _write_chunk(buf: bytearray, chunk: Chunk, big_endian: bool) -> None:
    """Write a single chunk (recursively handles LIST and container types)."""
    data = chunk.data

    if _is_chunk_list(data):
        if chunk.header == "LIST":
            _write_list_chunk(buf, chunk, big_endian)
        else:
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
    """Write a non-LIST container (tdsn, fnam, pdnm)."""
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
    """Write a string chunk (Utf8, alas, tdmn)."""
    header = chunk.header
    text = chunk.data

    if header == "tdmn":
        encoded = text.encode("utf-8") + b"\x00"
        if len(encoded) < chunk.length:
            encoded = encoded + b"\x00" * (chunk.length - len(encoded))
        data_bytes = encoded
    else:
        data_bytes = text.encode("utf-8")

    buf.extend(header.encode("ascii"))
    buf.extend(_pack_u32(len(data_bytes), big_endian))
    buf.extend(data_bytes)
    if len(data_bytes) % 2 == 1:
        buf.extend(b"\x00")


def _write_raw_chunk(buf: bytearray, chunk: Chunk, big_endian: bool) -> None:
    """Write a raw binary data chunk."""
    header = chunk.header
    data = chunk.data

    if header == "btdk":
        buf.extend(b"LIST")
        size = len(data) + 4
        buf.extend(_pack_u32(size, big_endian))
        buf.extend(b"btdk")
        buf.extend(data)
        if len(data) % 2 == 1:
            buf.extend(b"\x00")
        return

    buf.extend(header.encode("ascii"))
    buf.extend(_pack_u32(len(data), big_endian))
    buf.extend(data)
    if len(data) % 2 == 1:
        buf.extend(b"\x00")


# Pre-save fixup

_ALWAYS_3_PROPS = ("ADBE Anchor Point",)
_3D_ONLY_PROPS = ("ADBE Position",)


def _fix_spatial_dimensions(root: Chunk, big_endian: bool) -> None:
    """Scan all layers and upgrade 2-component spatial properties."""
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
        for prop_mn in _ALWAYS_3_PROPS:
            prop_chunk = _find_named_child(transform.data, prop_mn)
            if prop_chunk is None or not _is_chunk_list(prop_chunk.data):
                continue
            _upgrade_prop_to_3(prop_chunk.data, big_endian)
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
        return
    is_spatial = bool(tdb4.data[5] & (1 << 3))
    if not is_spatial:
        return

    tdb4_bytes = bytearray(tdb4.data)
    struct.pack_into(">H", tdb4_bytes, 2, 3)
    tdb4.data = bytes(tdb4_bytes)

    cdat = prop_cl.find_optional("cdat")
    if cdat is None or not isinstance(cdat.data, (bytes, bytearray)):
        return
    fmt = ">" if big_endian else "<"
    old_count = cur * 3 + 3
    new_count = 3 * 3 + 3
    try:
        old_floats = list(struct.unpack_from(f"{fmt}{'d' * old_count}", cdat.data))
    except struct.error:
        return
    vals = old_floats[0:cur] + [0.0]
    sin = old_floats[cur:cur * 2] + [0.0]
    sout = old_floats[cur * 2:cur * 3] + [0.0]
    temp = old_floats[cur * 3:cur * 3 + 3]
    new_floats = vals + sin + sout + temp
    cdat_data = struct.pack(f"{fmt}{'d' * new_count}", *new_floats)
    cdat.data = cdat_data
    cdat.length = len(cdat_data)


def save_aep(root: Chunk, big_endian: bool, path: str | Path,
             trailing_data: bytes = b"") -> None:
    """Serialize the chunk tree and write to a file."""
    _fix_spatial_dimensions(root, big_endian)
    data = serialize_chunk_tree(root, big_endian)
    Path(path).write_bytes(data + trailing_data)
