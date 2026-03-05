"""Type stubs for the Rust RIFF parser extension (_core)."""

class ChunkList:
    type: str
    children: list[Chunk]

    def find_optional(self, name: str) -> Chunk | None: ...
    def find(self, name: str) -> Chunk: ...
    def find_multiple(self, names: list[str]) -> list[Chunk | None]: ...
    def find_all(self, name: str) -> list[Chunk]: ...

class Chunk:
    header: str
    length: int
    data: bytes | str | ChunkList

    @property
    def name(self) -> str: ...
    @property
    def list(self) -> ChunkList: ...

def parse_riff(data: bytes) -> tuple[Chunk, bool]:
    """Parse a RIFF/RIFX binary buffer. Returns (root_chunk, big_endian)."""
    ...
