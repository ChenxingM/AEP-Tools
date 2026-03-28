"""RIFF/RIFX binary format parser for AEP files.

AEP files use the RIFX (big-endian) or RIFF (little-endian) container format
with the file identifier "Egg!".
"""

from __future__ import annotations

from .binary_reader import BinaryReader
from .chunk import Chunk, ChunkList


class RiffParser(BinaryReader):
    """Generic RIFF/RIFX parser. Subclass and override custom_parse_* methods."""

    def parse(self) -> Chunk:
        header = self.read_id()
        if header == "RIFF":
            self.big_endian = False
        elif header == "RIFX":
            self.big_endian = True
        else:
            raise ValueError(f"Unknown format: {header!r} (expected RIFF or RIFX)")

        size = self.read_uint(4)
        # Clamp declared size to actual remaining data
        available = self.remaining() + 4  # +4 because file_id is part of size
        if size > available:
            size = available
        file_id = self.read_id()
        self.on_file_start(file_id)
        chunk_list = self._parse_chunk_list(ChunkList(file_id), size - 4)
        root = Chunk(header, size, chunk_list)
        self.trailing_data = bytes(self._data[self.offset:])
        self.on_file_end(root)
        return root

    def on_file_start(self, file_id: str) -> None:
        pass

    def on_file_end(self, root: Chunk) -> None:
        pass

    def _parse_chunk_list(self, cl: ChunkList, size: int) -> ChunkList:
        end = min(self.offset + size, len(self._data))
        while self.offset < end and self.remaining() >= 8:
            chunk = self._parse_chunk()
            cl.children.append(chunk)
        self.offset = end  # Clamp to parent boundary
        return cl

    def _parse_chunk(self) -> Chunk:
        header = self.read_id()
        size = self.read_uint(4)
        # Clamp to remaining data to survive truncated files
        size = min(size, self.remaining())
        chunk = self._parse_chunk_data(header, size)
        # RIFF chunks are padded to 2-byte boundaries
        if size % 2 == 1:
            self.offset += 1
        return chunk

    def _parse_chunk_data(self, header: str, size: int) -> Chunk:
        if header == "LIST":
            if size < 4:
                return Chunk(header, size, self.read_bytes(size))
            list_type = self.read_id()
            custom = self.custom_parse_list(header, size, list_type)
            if custom is not None:
                return custom
            cl = self._parse_chunk_list(ChunkList(list_type), size - 4)
            return Chunk(header, size, cl)

        custom = self.custom_parse_chunk(header, size)
        if custom is not None:
            return custom
        return Chunk(header, size, self.read_bytes(size))

    def custom_parse_chunk(self, header: str, size: int) -> Chunk | None:
        return None

    def custom_parse_list(self, header: str, size: int,
                          list_type: str) -> Chunk | None:
        return None


class AepChunkParser(RiffParser):
    """AEP-specific RIFF parser that handles AEP chunk types."""

    def on_file_start(self, file_id: str) -> None:
        if file_id != "Egg!":
            raise ValueError(f"Invalid AEP file (expected 'Egg!', got {file_id!r})")

    def custom_parse_chunk(self, header: str, size: int) -> Chunk | None:
        if header in ("Utf8", "alas"):
            raw = self.read_bytes(size)
            try:
                return Chunk(header, size, raw.decode("utf-8"))
            except UnicodeDecodeError:
                return Chunk(header, size, raw)  # Store raw for round-trip safety
        if header == "tdmn":
            return Chunk(header, size, self.read_nul_string("utf-8", size))
        # wsnm: store raw bytes for perfect round-trip (not read by Python code)
        if header in ("tdsn", "fnam", "pdnm"):
            cl = self._parse_chunk_list(ChunkList(""), size)
            return Chunk(header, size, cl)
        return None

    def custom_parse_list(self, header: str, size: int,
                          list_type: str) -> Chunk | None:
        if list_type == "btdk":
            data = self.read_bytes(size - 4)
            return Chunk(list_type, size, data)
        return None
