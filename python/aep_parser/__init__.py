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


def parse_aep_settings(data: bytes):
    """Parse only project-level settings from a binary .aep file.

    Reads color management, bit depth, working gamma, frame rate, audio sample
    rate, expression engine, GPU accel, etc. WITHOUT materializing the comp /
    layer / asset tree. Dramatically lower memory and faster than
    :func:`parse_aep` for large projects — use it when you only need
    project settings (e.g. the working color space).

    Args:
        data: Raw bytes of the .aep file.

    Returns:
        A ``models.Project`` with only the project-level settings populated
        (``compositions``/``assets`` are empty).

    Raises:
        AepParseError: If the file is malformed or truncated.
    """
    from .models import Project
    from ._parser._shallow import scan_top_level

    if not data or len(data) < 12:
        raise AepParseError("File is too small to be a valid AEP file.")
    try:
        cl, big_endian = scan_top_level(data)
        pp = ProjectParser(big_endian=big_endian)
        project = Project()
        pp._parse_project_settings(cl, project)
        return project
    except AepParseError:
        raise
    except Exception as e:
        raise AepParseError(f"Failed to parse AEP settings: {e}") from e


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
