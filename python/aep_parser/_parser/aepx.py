"""AEPX (XML) format parser.

Converts AEPX XML into the same Chunk tree structure as the binary AEP parser,
so the project parser can work with both formats identically.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

from .chunk import Chunk, ChunkList


class AepxParser:
    """Parses AEPX XML text into a Chunk tree (always big-endian)."""

    def __init__(self, xml_string: str):
        self.big_endian = True
        self._root = ET.fromstring(xml_string)

    def parse(self) -> Chunk:
        return self._convert_element(self._root)

    def _convert_element(self, elem: ET.Element) -> Chunk:
        tag = elem.tag
        chunk = Chunk(header=tag, length=0, data=None)

        bdata = elem.get("bdata")
        if bdata is not None:
            # Binary data encoded as hex string
            hex_str = bdata
            if tag == "cdat":
                # Pad short hex values (00000000 -> 0000000000000000)
                hex_str = hex_str.replace("00000000", "0000000000000000")
            chunk.length = len(hex_str) // 2
            if hex_str:
                chunk.data = bytes.fromhex(hex_str)
            else:
                chunk.data = b""

        elif tag == "string":
            chunk.header = "Utf8"
            chunk.data = elem.text or ""

        elif tag == "fileReference":
            # Convert XML attributes to JSON (same as Als2/alas chunk)
            ref: dict = {}
            for name, value in elem.attrib.items():
                if name == "target_is_folder":
                    ref["target_is_folder"] = value in ("1", "true", "True")
                else:
                    ref[name] = value
            chunk.header = "alas"
            chunk.data = json.dumps(ref)

        else:
            # Container element -> LIST with children
            chunk.header = "LIST"
            list_type = "Pin " if tag == "Pin" else tag
            cl = ChunkList(list_type)
            for child in elem:
                cl.children.append(self._convert_element(child))
            chunk.data = cl

        return chunk
