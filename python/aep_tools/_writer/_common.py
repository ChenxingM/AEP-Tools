"""Shared imports and utilities for the writer package."""

from __future__ import annotations

import struct

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
