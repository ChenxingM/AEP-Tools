"""AEP/AEPX file parser — converts After Effects project files to JSON."""

from __future__ import annotations

from ._parser import AepChunkParser, AepxParser, ProjectParser

try:
    from ._core import parse_riff as _rust_parse_riff
    _HAS_RUST = True
except ImportError:
    _HAS_RUST = False

__version__ = "0.1.0"


def parse_aep(data: bytes):
    """Parse a binary .aep file."""
    if _HAS_RUST:
        root_chunk, big_endian = _rust_parse_riff(data)
        pp = ProjectParser(big_endian=big_endian)
        return pp.parse_project(root_chunk)
    parser = AepChunkParser(data, 0, True)
    root_chunk = parser.parse()
    pp = ProjectParser(big_endian=parser.big_endian)
    return pp.parse_project(root_chunk)


def parse_aepx(xml_string: str):
    """Parse an .aepx XML string."""
    parser = AepxParser(xml_string)
    root_chunk = parser.parse()
    pp = ProjectParser(big_endian=parser.big_endian)
    return pp.parse_project(root_chunk)
