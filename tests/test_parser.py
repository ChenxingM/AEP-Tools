"""Basic tests for the AEP parser."""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from aep_parser import parse_aep, parse_aep_settings, parse_aepx
from aep_parser import ProjectParser
from aep_parser._parser import BinaryReader, BitFlags, Chunk, ChunkList
from aep_parser.models import (
    Color, Composition, Layer, Project, PropertyGroup, SolidAsset, Vector,
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


# -- Layer ldta format variants --

def _layer_chunk(ldta_bytes: bytes):
    """Wrap a raw ldta byte string in a Layr LIST chunk for _parse_layer."""
    ldta = Chunk(header="ldta", length=len(ldta_bytes), data=ldta_bytes)
    return Chunk(header="LIST", length=0,
                 data=ChunkList(type="Layr", children=[ldta]))


class TestLayerLdtaFormat:
    def test_old_160_byte_ldta_has_no_matte_id(self):
        # Older AE writes a 160-byte ldta with no trailing matte_id field.
        chunk = _layer_chunk(bytes(160))
        layer = ProjectParser(big_endian=True)._parse_layer(chunk)
        assert layer.matte_id == 0

    def test_new_164_byte_ldta_reads_matte_id(self):
        # Newer AE appends a 4-byte matte_id at offset 160.
        data = bytearray(164)
        data[160:164] = (7).to_bytes(4, "big")
        layer = ProjectParser(big_endian=True)._parse_layer(_layer_chunk(bytes(data)))
        assert layer.matte_id == 7


# -- Asset opti (solid) format variants --

def _pin_chunk(opti_bytes: bytes):
    """Wrap sspc + opti into a 'Pin ' LIST chunk for _parse_asset."""
    sspc = Chunk(header="sspc", length=62, data=bytes(62))
    opti = Chunk(header="opti", length=len(opti_bytes), data=opti_bytes)
    return Chunk(header="LIST", length=0,
                 data=ChunkList(type="Pin ", children=[sspc, opti]))


def _soli_opti(name: bytes, total_name_field: int | None = None) -> bytes:
    # 4 (type) + 2 + 4 skip + a/r/g/b float32 (16) = 26 bytes header, then name.
    head = b"Soli" + bytes(2) + bytes(4) + bytes(16)
    field = name if total_name_field is None else name.ljust(total_name_field, b"\x00")
    return head + field


class TestAssetOptiFormat:
    def test_short_opti_solid_name(self):
        # Older/shorter opti: name field is much smaller than 256 bytes.
        opti = _soli_opti(b"Red\x00")  # only 4 bytes of name after offset 26
        asset = ProjectParser(big_endian=True)._parse_asset(
            1, _pin_chunk(opti), Project())
        assert isinstance(asset, SolidAsset)
        assert asset.name == "Red"

    def test_full_256_opti_solid_name(self):
        opti = _soli_opti(b"Blue", total_name_field=256)
        asset = ProjectParser(big_endian=True)._parse_asset(
            1, _pin_chunk(opti), Project())
        assert asset.name == "Blue"


# -- Lightweight settings-only parse (parse_aep_settings) --

def _riff(cid: bytes, body: bytes) -> bytes:
    out = cid + struct.pack(">I", len(body)) + body
    if len(body) % 2 == 1:
        out += b"\x00"
    return out


def _riff_list(list_type: bytes, body: bytes) -> bytes:
    return _riff(b"LIST", list_type + body)


def _build_aep(children: bytes) -> bytes:
    inner = b"Egg!" + children
    return b"RIFX" + struct.pack(">I", len(inner)) + inner


_SRGB_PWCS_JSON = ('{"baseColorProfile":{"colorProfileName":"sRGB IEC61966-2.1"},'
                   '"baseProfileType":2}').encode()


class TestParseSettingsOnly:
    def test_reads_ocio_without_full_tree(self):
        # A heavy Fold body that the full parser would walk — settings parse skips it.
        children = (
            _riff(b"pcms", b"\x01")
            + _riff(b"Utf8", b'{"ocioConfigurationFile":"ACES 1.2"}')
            + _riff_list(b"Fold", b"\xde\xad\xbe\xef" * 64)  # garbage, must be skipped
        )
        proj = parse_aep_settings(_build_aep(children))
        assert proj.ocio_config == "ACES 1.2"
        assert proj.color_space == "ACES 1.2"
        assert proj.compositions == []  # tree not materialized

    def test_reads_classic_srgb(self):
        children = (
            _riff(b"pcms", b"\x01") + _riff(b"Utf8", b'{"autoToneMapEnabled":true}')
            + _riff(b"PwCs", b"\x01") + _riff(b"Utf8", _SRGB_PWCS_JSON)
            + _riff_list(b"Fold", b"\x00" * 32)
        )
        proj = parse_aep_settings(_build_aep(children))
        assert proj.color_space == "sRGB IEC61966-2.1"

    def test_reads_bits_per_channel(self):
        nnhd = bytearray(40)
        nnhd[24] = 1  # _BITS_MAP: 1 -> 16 bpc
        children = _riff(b"nnhd", bytes(nnhd)) + _riff_list(b"Fold", b"\x00" * 16)
        proj = parse_aep_settings(_build_aep(children))
        assert proj.bits_per_channel == 16

    def test_none_when_unmanaged(self):
        children = _riff_list(b"Fold", b"\x00" * 8)
        proj = parse_aep_settings(_build_aep(children))
        assert proj.color_space == "None"

    def test_rejects_non_aep(self):
        with pytest.raises(Exception):
            parse_aep_settings(b"not an aep file at all")


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


# -- Color management (pcms / PwCs / pdvc) --

def _color_mgmt_chunklist(pcms="{}", pwcs="{}", pdvc="{}"):
    """Build a project-level ChunkList with the color-management key/Utf8 layout."""
    return ChunkList(type="Fold", children=[
        Chunk(header="pcms", length=1, data=b"\x01"),
        Chunk(header="Utf8", length=len(pcms), data=pcms),
        Chunk(header="PwCs", length=1, data=b"\x01"),
        Chunk(header="Utf8", length=len(pwcs), data=pwcs),
        Chunk(header="pdvc", length=1, data=b"\x01"),
        Chunk(header="Utf8", length=len(pdvc), data=pdvc),
    ])


# A classic (pre-OCIO) PwCs value: the working space is an ICC profile whose
# name lives in baseColorProfile.colorProfileName.
_SRGB_PWCS = ('{"baseColorProfile":{"colorProfileData":"AAAMSExpbm8=",'
              '"colorProfileName":"sRGB IEC61966-2.1"},"baseProfileType":2}')


class TestColorManagement:
    def test_project_defaults_empty(self):
        p = Project()
        assert p.color_management_settings == {}
        assert p.working_color_space == {}
        assert p.display_color_space == {}
        assert p.ocio_config == ""
        assert p.working_color_space_name == ""
        assert p.color_space == "None"

    def test_parse_ocio_config_from_pcms(self):
        cl = _color_mgmt_chunklist(pcms='{"ocioConfigurationFile":"ACES 1.2"}')
        project = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, project)
        assert project.color_management_settings == {"ocioConfigurationFile": "ACES 1.2"}
        assert project.ocio_config == "ACES 1.2"
        assert project.color_space == "ACES 1.2"

    def test_parse_extra_pcms_keys(self):
        cl = _color_mgmt_chunklist(
            pcms='{"autoToneMapEnabled":true,"ocioConfigurationFile":"ACES 1.2"}')
        project = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, project)
        assert project.color_management_settings["autoToneMapEnabled"] is True
        assert project.ocio_config == "ACES 1.2"
        assert project.color_space == "ACES 1.2"

    def test_parse_classic_srgb_from_pwcs(self):
        # Classic mode: pcms has no OCIO config, working space is in PwCs.
        cl = _color_mgmt_chunklist(pcms='{"autoToneMapEnabled":true}', pwcs=_SRGB_PWCS)
        project = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, project)
        assert project.ocio_config == ""
        assert project.working_color_space_name == "sRGB IEC61966-2.1"
        assert project.color_space == "sRGB IEC61966-2.1"

    def test_parse_empty_is_none(self):
        cl = _color_mgmt_chunklist()  # all "{}"
        project = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, project)
        assert project.color_space == "None"
        assert project.working_color_space_name == ""

    def test_parse_missing_chunks_is_none(self):
        cl = ChunkList(type="Fold", children=[])
        project = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, project)
        assert project.color_management_settings == {}
        assert project.color_space == "None"

    def test_to_dict_includes_color_space(self):
        cl = _color_mgmt_chunklist(pwcs=_SRGB_PWCS)
        p = Project()
        ProjectParser(big_endian=True)._parse_project_settings(cl, p)
        settings = p.to_dict()["settings"]
        assert settings["colorSpace"] == "sRGB IEC61966-2.1"

    def test_to_dict_omits_color_space_when_none(self):
        p = Project()
        d = p.to_dict()
        assert "colorSpace" not in d.get("settings", {})
        assert "colorManagementSettings" not in d.get("settings", {})
