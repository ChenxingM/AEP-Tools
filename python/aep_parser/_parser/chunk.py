"""Chunk data structures for RIFF-based AEP files."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChunkList:
    """A named list of child chunks (LIST or Fold container)."""
    type: str
    children: list[Chunk] = field(default_factory=list)

    def find_optional(self, name: str) -> Chunk | None:
        for c in self.children:
            if c.name == name:
                return c
        return None

    def find(self, name: str) -> Chunk:
        c = self.find_optional(name)
        if c is None:
            raise KeyError(f"Chunk '{name}' not found")
        return c

    def find_multiple(self, names: list[str]) -> list[Chunk | None]:
        result: list[Chunk | None] = [None] * len(names)
        found = 0
        for c in self.children:
            try:
                idx = names.index(c.name)
            except ValueError:
                continue
            if result[idx] is None:
                result[idx] = c
                found += 1
                if found >= len(names):
                    break
        return result

    def find_all(self, name: str) -> list[Chunk]:
        return [c for c in self.children if c.name == name]


@dataclass
class Chunk:
    """A single RIFF chunk with header, length, and data."""
    header: str
    length: int
    data: Any  # bytes | str | ChunkList | etc.

    @property
    def name(self) -> str:
        if self.header == "LIST":
            return self.data.type if isinstance(self.data, ChunkList) else self.header
        return self.header

    @property
    def list(self) -> ChunkList:
        if isinstance(self.data, ChunkList):
            return self.data
        raise TypeError(f"Chunk '{self.header}' is not a list (data is {type(self.data).__name__})")
