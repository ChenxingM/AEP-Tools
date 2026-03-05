"""Basic tests for the AEP parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aep_parser import parse_aep, parse_aepx
from aep_parser._parser import BinaryReader, BitFlags, Chunk, ChunkList
from aep_parser.models import (
    Color, Composition, Layer, Project, PropertyGroup, Vector,
)


# -- BinaryReader --

class TestBinaryReader:
    def test_read_uint_big_endian(self):
        r = BinaryReader(b"\x00\x01", big_endian=True)
        assert r.read_uint(2) == 1

    def test_read_uint_little_endian(self):
        r = BinaryReader(b"\x01\x00", big_endian=False)
        assert r.read_uint(2) == 1

    def test_read_sint_negative(self):
        r = BinaryReader(b"\xff\xff\xff\xfe", big_endian=True)
        assert r.read_sint(4) == -2

    def test_remaining(self):
        r = BinaryReader(b"\x00\x01\x02\x03", big_endian=True)
        assert r.remaining() == 4
        r.skip(2)
        assert r.remaining() == 2

    def test_read_nul_string(self):
        r = BinaryReader(b"hello\x00world\x00", big_endian=True)
        assert r.read_nul_string("utf-8", 12) == "hello"


class TestBitFlags:
    def test_get_bit(self):
        flags = BitFlags(b"\x00\x00\x00\x03")
        assert flags.get_bit(3, 0) is True
        assert flags.get_bit(3, 1) is True
        assert flags.get_bit(3, 2) is False


# -- Models --

class TestModels:
    def test_vector_to_dict(self):
        v = Vector(1.0, 2.0)
        assert v.to_dict() == {"x": 1.0, "y": 2.0}

    def test_vector_3d(self):
        v = Vector(1.0, 2.0, 3.0)
        assert v.is_3d
        assert v.to_dict() == {"x": 1.0, "y": 2.0, "z": 3.0}

    def test_color_to_dict(self):
        c = Color(255, 128, 0, 1.0)
        assert c.to_dict() == {"r": 255, "g": 128, "b": 0, "a": 1.0}

    def test_property_group_enabled(self):
        pg = PropertyGroup(enabled=True)
        d = pg.to_dict()
        assert d["enabled"] is True
        assert "properties" in d  # always present when enabled is set

    def test_property_group_no_enabled(self):
        pg = PropertyGroup()
        d = pg.to_dict()
        assert "enabled" not in d
        assert "properties" not in d

    def test_project_to_dict(self):
        p = Project()
        d = p.to_dict()
        assert "folder" in d
        assert "compositions" in d
        assert "assets" in d
        assert "effects" in d

    def test_layer_defaults(self):
        layer = Layer()
        d = layer.to_dict()
        assert d["id"] == 0
        assert d["type"] == "shape"
        assert "flags" not in d  # all defaults, no flags emitted


# -- Chunk --

class TestChunk:
    def test_find(self):
        children = [
            Chunk(header="tdmn", length=4, data=b"test"),
            Chunk(header="tdsb", length=4, data=b"\x00\x00\x00\x01"),
        ]
        cl = ChunkList(type="test", children=children)
        assert cl.find("tdmn").data == b"test"

    def test_find_optional_missing(self):
        cl = ChunkList(type="test", children=[])
        assert cl.find_optional("missing") is None

    def test_find_multiple(self):
        children = [
            Chunk(header="a", length=1, data=b"1"),
            Chunk(header="b", length=1, data=b"2"),
        ]
        cl = ChunkList(type="test", children=children)
        a, b, c = cl.find_multiple(["a", "b", "c"])
        assert a.data == b"1"
        assert b.data == b"2"
        assert c is None
