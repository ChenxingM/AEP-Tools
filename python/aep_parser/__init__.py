"""AEP/AEPX file parser — converts After Effects project files to JSON."""

from __future__ import annotations

from ._parser import AepChunkParser, AepxParser, ProjectParser

try:
    from ._core import parse_riff as _rust_parse_riff
    _HAS_RUST = True
except ImportError:
    _HAS_RUST = False

__version__ = "0.1.0a1"


class AepParseError(Exception):
    """Raised when an AEP/AEPX file cannot be parsed."""


def parse_aep(data: bytes):
    """Parse a binary .aep file.

    Args:
        data: Raw bytes of the .aep file.

    Returns:
        A ``models.Project`` dataclass.

    Raises:
        AepParseError: If the file is malformed or truncated.
    """
    if not data or len(data) < 12:
        raise AepParseError("File is too small to be a valid AEP file.")
    try:
        if _HAS_RUST:
            root_chunk, big_endian, _trailing = _rust_parse_riff(data)
            pp = ProjectParser(big_endian=big_endian)
            return pp.parse_project(root_chunk)
        parser = AepChunkParser(data, 0, True)
        root_chunk = parser.parse()
        pp = ProjectParser(big_endian=parser.big_endian)
        return pp.parse_project(root_chunk)
    except AepParseError:
        raise
    except Exception as e:
        raise AepParseError(f"Failed to parse AEP data: {e}") from e


def parse_aepx(xml_string: str):
    """Parse an .aepx XML string.

    Args:
        xml_string: Contents of an .aepx file as a string.

    Returns:
        A ``models.Project`` dataclass.

    Raises:
        AepParseError: If the XML is malformed or cannot be parsed.
    """
    if not xml_string:
        raise AepParseError("Empty AEPX data.")
    try:
        parser = AepxParser(xml_string)
        root_chunk = parser.parse()
        pp = ProjectParser(big_endian=parser.big_endian)
        return pp.parse_project(root_chunk)
    except AepParseError:
        raise
    except Exception as e:
        raise AepParseError(f"Failed to parse AEPX data: {e}") from e
