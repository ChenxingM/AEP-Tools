"""Unit tests for aep_tools._writer — binary .aep serializer and modifier."""

import struct
import pytest

from aep_parser._parser.chunk import Chunk, ChunkList
from aep_tools._writer import (
    find_comp_chunklist,
    find_layer_chunk,
    find_property_chunk,
    serialize_chunk_tree,
    set_layer_name,
    set_property_value,
    save_aep,
    set_layer_flag,
    set_layer_label,
    set_layer_blend_mode,
    set_layer_track_matte,
    set_layer_quality,
    set_layer_time_field,
    set_comp_dimensions,
    set_comp_bgcolor,
    set_comp_framerate,
    set_comp_duration,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_idta(item_type: int, item_id: int, big_endian: bool = True) -> bytes:
    """Build a minimal idta chunk data: 2B type + 14B padding + 4B id."""
    fmt = ">H14xI" if big_endian else "<H14xI"
    return struct.pack(fmt, item_type, item_id)


def _make_ldta(layer_id: int, big_endian: bool = True) -> bytes:
    """Build minimal ldta with proper offsets for all fields.

    Layout (big-endian):
        0:  layer_id       (uint32)
        4:  quality        (uint16) = 2
        6:  (skip 2B)
        8:  stretch_num    (sint32) = 1
        12: start_num      (sint32) = 0
        16: start_den      (uint32) = 30
        20: in_num         (sint32) = 0
        24: in_den         (uint32) = 30
        28: out_num        (sint32) = 150
        32: out_den        (uint32) = 30
        36: flags          (4 bytes)  — byte 3 bit 0 = visible
        40: asset_id       (uint32) = 0
        44: (17B skip)
        61: label_color    (uint8) = 0
        62: (2B skip)
        64: (32B skip)
        96: blend_mode     (uint32) = 1 (Normal)
        100: (4B skip)
        104: matte_mode    (uint32) = 0
        108: (2B skip)
        110: stretch_den   (uint16) = 1
        112+: padding to 136 bytes total
    """
    fmt = ">" if big_endian else "<"
    buf = bytearray(136)
    struct.pack_into(f"{fmt}I", buf, 0, layer_id)    # id
    struct.pack_into(f"{fmt}H", buf, 4, 2)           # quality = BEST
    struct.pack_into(f"{fmt}i", buf, 8, 1)           # stretch_num = 1
    struct.pack_into(f"{fmt}i", buf, 12, 0)          # start_num = 0
    struct.pack_into(f"{fmt}I", buf, 16, 30)         # start_den = 30
    struct.pack_into(f"{fmt}i", buf, 20, 0)          # in_num = 0
    struct.pack_into(f"{fmt}I", buf, 24, 30)         # in_den = 30
    struct.pack_into(f"{fmt}i", buf, 28, 150)        # out_num = 150 → 5.0s
    struct.pack_into(f"{fmt}I", buf, 32, 30)         # out_den = 30
    buf[39] = 0x01                                    # flags: visible=True
    struct.pack_into(f"{fmt}I", buf, 96, 1)          # blend_mode = Normal
    struct.pack_into(f"{fmt}H", buf, 110, 1)         # stretch_den = 1
    return bytes(buf)


def _make_cdat(values: list[float], big_endian: bool = True) -> bytes:
    """Build cdat data from float64 values."""
    fmt = ">" if big_endian else "<"
    fmt += "d" * len(values)
    return struct.pack(fmt, *values)


def _make_tdb4(components: int, big_endian: bool = True) -> bytes:
    """Build minimal tdb4 metadata chunk."""
    fmt = ">" if big_endian else "<"
    # 2B skip + 2B components + rest zeros (enough to satisfy reader)
    data = struct.pack(f"{fmt}HH", 0, components)
    data += b"\x00" * 60  # padding
    return data


def _build_test_chunk_tree(big_endian: bool = True) -> Chunk:
    """Build a minimal chunk tree representing a simple AEP project.

    Structure:
        RIFX [Egg!]
         └─ Fold
             └─ Item (comp, id=100)
                 ├─ idta (type=4, id=100)
                 ├─ cdta (comp data)
                 └─ Layr (layer id=10)
                     ├─ ldta
                     ├─ Utf8 "TestLayer"
                     └─ tdgp (property tree)
                         ├─ tdmn "ADBE Transform Group"
                         └─ tdgp (transform group)
                             ├─ tdmn "ADBE Position"
                             └─ tdbs (position property)
                                 ├─ tdsb (flags)
                                 ├─ tdb4 (metadata)
                                 └─ cdat [960.0, 540.0]
    """
    # Position property: tdbs containing tdsb + tdb4 + cdat
    cdat = Chunk("cdat", 16, _make_cdat([960.0, 540.0], big_endian))
    tdsb = Chunk("tdsb", 4, b"\x00\x00\x00\x00")
    tdb4 = Chunk("tdb4", 64, _make_tdb4(2, big_endian))
    pos_tdbs = Chunk("tdbs", 0, ChunkList("", [tdsb, tdb4, cdat]))

    # Opacity property: tdbs with single-component cdat
    cdat_opacity = Chunk("cdat", 8, _make_cdat([100.0], big_endian))
    tdsb_o = Chunk("tdsb", 4, b"\x00\x00\x00\x00")
    tdb4_o = Chunk("tdb4", 64, _make_tdb4(1, big_endian))
    opacity_tdbs = Chunk("tdbs", 0, ChunkList("", [tdsb_o, tdb4_o, cdat_opacity]))

    # Transform group: tdgp containing match-named children
    transform_children = [
        Chunk("tdmn", 32, "ADBE Position"),
        pos_tdbs,
        Chunk("tdmn", 32, "ADBE Opacity"),
        opacity_tdbs,
    ]
    transform_tdgp = Chunk("LIST", 0, ChunkList("tdgp", transform_children))

    # Root property group: tdgp containing transform group
    root_prop_children = [
        Chunk("tdmn", 32, "ADBE Transform Group"),
        transform_tdgp,
    ]
    root_tdgp = Chunk("LIST", 0, ChunkList("tdgp", root_prop_children))

    # Layer
    ldta = Chunk("ldta", 124, _make_ldta(10, big_endian))
    utf8_name = Chunk("Utf8", 9, "TestLayer")
    layr_cl = ChunkList("Layr", [ldta, utf8_name, root_tdgp])
    layr = Chunk("LIST", 0, layr_cl)

    # Comp data (cdta with proper layout)
    cdta_buf = bytearray(144)
    fmt = ">" if big_endian else "<"
    struct.pack_into(f"{fmt}I", cdta_buf, 4, 1)      # time_denom = 1
    struct.pack_into(f"{fmt}I", cdta_buf, 8, 30)     # time_num = 30 → 30fps
    struct.pack_into(f"{fmt}H", cdta_buf, 45, 150)   # duration raw = 150
    struct.pack_into(f"{fmt}H", cdta_buf, 49, 30)    # dur_div = 30
    cdta_buf[52] = 51                                  # color R
    cdta_buf[53] = 51                                  # color G
    cdta_buf[54] = 51                                  # color B
    struct.pack_into(f"{fmt}HH", cdta_buf, 140, 1920, 1080)  # width, height
    cdta = Chunk("cdta", len(cdta_buf), bytes(cdta_buf))

    # Item (composition)
    idta = Chunk("idta", 20, _make_idta(4, 100, big_endian))
    item_cl = ChunkList("Item", [idta, cdta, layr])
    item = Chunk("LIST", 0, item_cl)

    # Fold
    fold_cl = ChunkList("Fold", [item])
    fold = Chunk("LIST", 0, fold_cl)

    # Root
    root_cl = ChunkList("Egg!", [fold])
    root = Chunk("RIFX" if big_endian else "RIFF", 0, root_cl)

    return root


# ── Tests: Chunk Tree Navigation ────────────────────────────────────────────


class TestFindCompChunklist:
    def test_find_existing_comp(self):
        root = _build_test_chunk_tree()
        cl = find_comp_chunklist(root, 100, True)
        assert cl is not None
        assert cl.type == "Item"

    def test_find_nonexistent_comp(self):
        root = _build_test_chunk_tree()
        cl = find_comp_chunklist(root, 999, True)
        assert cl is None


class TestFindLayerChunk:
    def test_find_existing_layer(self):
        root = _build_test_chunk_tree()
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        assert layer is not None
        assert layer.name == "Layr"

    def test_find_nonexistent_layer(self):
        root = _build_test_chunk_tree()
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 999, True)
        assert layer is None


class TestFindPropertyChunk:
    def test_find_position(self):
        root = _build_test_chunk_tree()
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Position"])
        assert prop is not None

    def test_find_opacity(self):
        root = _build_test_chunk_tree()
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Opacity"])
        assert prop is not None

    def test_find_nonexistent(self):
        root = _build_test_chunk_tree()
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Rotate Z"])
        assert prop is None


# ── Tests: Modification ─────────────────────────────────────────────────────


class TestSetLayerName:
    def test_change_name(self):
        root = _build_test_chunk_tree()
        result = set_layer_name(root, 100, 10, "NewName", True)
        assert result is True
        # Verify the Utf8 chunk was updated
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        for child in layer.list.children:
            if child.header == "Utf8":
                assert child.data == "NewName"
                break
        else:
            pytest.fail("Utf8 chunk not found")

    def test_change_name_nonexistent_layer(self):
        root = _build_test_chunk_tree()
        result = set_layer_name(root, 100, 999, "NewName", True)
        assert result is False

    def test_change_name_nonexistent_comp(self):
        root = _build_test_chunk_tree()
        result = set_layer_name(root, 999, 10, "NewName", True)
        assert result is False


class TestSetPropertyValue:
    def test_change_position(self):
        root = _build_test_chunk_tree()
        result = set_property_value(
            root, 100, 10,
            ["ADBE Transform Group", "ADBE Position"],
            [100.0, 200.0], True)
        assert result is True

        # Verify the cdat was updated
        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Position"])
        cdat = prop.data.find_optional("cdat")
        values = struct.unpack(">dd", cdat.data)
        assert values == (100.0, 200.0)

    def test_change_opacity(self):
        root = _build_test_chunk_tree()
        result = set_property_value(
            root, 100, 10,
            ["ADBE Transform Group", "ADBE Opacity"],
            50.0, True)
        assert result is True

        comp_cl = find_comp_chunklist(root, 100, True)
        layer = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Opacity"])
        cdat = prop.data.find_optional("cdat")
        values = struct.unpack(">d", cdat.data)
        assert values == (50.0,)

    def test_nonexistent_property_with_template_creates_it(self):
        root = _build_test_chunk_tree()
        result = set_property_value(
            root, 100, 10,
            ["ADBE Transform Group", "ADBE Rotate Z"],
            45.0, True)
        # ADBE Rotate Z has a template, so it should be auto-created
        assert result is True

    def test_nonexistent_property_no_template(self):
        root = _build_test_chunk_tree()
        result = set_property_value(
            root, 100, 10,
            ["ADBE Transform Group", "ADBE Nonexistent Prop"],
            45.0, True)
        assert result is False


class TestSetCompName:
    def test_change_comp_name(self):
        from aep_tools._writer import set_comp_name
        root = _build_test_chunk_tree()
        result = set_comp_name(root, 100, "NewComp", True)
        assert result is True
        comp_cl = find_comp_chunklist(root, 100, True)
        for child in comp_cl.children:
            if child.header == "Utf8":
                assert child.data == "NewComp"
                break

    def test_change_nonexistent_comp(self):
        from aep_tools._writer import set_comp_name
        root = _build_test_chunk_tree()
        result = set_comp_name(root, 999, "NewComp", True)
        assert result is False


# ── Tests: Property setters (assignment syntax) ─────────────────────────────


class TestPropertySetters:
    """Test comp.name=, layer.name=, property.value= assignment syntax."""

    def _make_project_with_chunk_tree(self):
        """Build a Project with chunk tree for setter testing."""
        from aep_parser.models import (
            AnimatedProperty, Composition, Layer as LayerModel,
            NamedProperty, Project as ProjectModel,
            PropertyGroup as PGModel, Vector,
        )
        from aep_tools import CompItem, Project
        from aep_tools._layer import _make_layer

        # Build model
        pos_prop = AnimatedProperty()
        pos_prop.value = Vector(960.0, 540.0)
        pos_prop.components = 2

        opacity_prop = AnimatedProperty()
        opacity_prop.value = 50.0
        opacity_prop.components = 1

        transform_pg = PGModel()
        transform_pg.properties = [
            NamedProperty("ADBE Position", pos_prop),
            NamedProperty("ADBE Opacity", opacity_prop),
        ]

        root_pg = PGModel()
        root_pg.properties = [
            NamedProperty("ADBE Transform Group", transform_pg),
        ]

        layer_model = LayerModel()
        layer_model.id = 10
        layer_model.name = "TestLayer"
        layer_model.properties = root_pg
        layer_model.layer_type = 0

        comp_model = Composition(id=100, name="TestComp")
        comp_model.width = 1920
        comp_model.height = 1080
        comp_model.layers = [layer_model]

        proj_model = ProjectModel()
        proj_model.compositions = [comp_model]

        # Build chunk tree + project
        root_chunk = _build_test_chunk_tree(big_endian=True)
        proj = Project(proj_model, "test.aep",
                       chunk_tree=root_chunk, big_endian=True)

        return proj

    def test_comp_name_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp("TestComp")
        assert comp.name == "TestComp"
        comp.name = "RenamedComp"
        assert comp.name == "RenamedComp"
        # Verify chunk tree was updated
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        for child in comp_cl.children:
            if child.header == "Utf8":
                assert child.data == "RenamedComp"
                break

    def test_layer_name_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp("TestComp")
        layer = comp.layer(1)
        assert layer.name == "TestLayer"
        layer.name = "RenamedLayer"
        assert layer.name == "RenamedLayer"
        # Verify chunk tree was updated
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        layer_chunk = find_layer_chunk(comp_cl, 10, True)
        for child in layer_chunk.list.children:
            if child.header == "Utf8":
                assert child.data == "RenamedLayer"
                break

    def test_property_value_setter_vector(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp("TestComp")
        layer = comp.layer(1)
        pos = layer.position
        assert pos is not None
        pos.value = [100.0, 200.0]
        assert pos.value == [100.0, 200.0]
        # Verify chunk tree was updated
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        layer_chunk = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer_chunk.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Position"])
        cdat = prop.data.find_optional("cdat")
        values = struct.unpack(">dd", cdat.data)
        assert values == (100.0, 200.0)

    def test_property_value_setter_scalar(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp("TestComp")
        layer = comp.layer(1)
        opacity = layer.opacity
        assert opacity is not None
        opacity.value = 75.0
        assert opacity.value == 75.0
        # Verify chunk tree was updated
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        layer_chunk = find_layer_chunk(comp_cl, 10, True)
        tdgp = layer_chunk.list.find_optional("tdgp")
        prop = find_property_chunk(tdgp.list,
                                   ["ADBE Transform Group", "ADBE Opacity"])
        cdat = prop.data.find_optional("cdat")
        values = struct.unpack(">d", cdat.data)
        assert values == (75.0,)

    def test_property_value_setter_without_chunk_tree(self):
        """Setter should still update model even without chunk tree."""
        from aep_parser.models import AnimatedProperty, Vector
        from aep_tools._property import Property

        model = AnimatedProperty()
        model.value = Vector(0.0, 0.0)
        model.components = 2
        prop = Property(model, match_name="ADBE Position")
        prop.value = [100.0, 200.0]
        assert prop.value == [100.0, 200.0]


# ── Tests: Serialization ────────────────────────────────────────────────────


class TestSerialize:
    def test_roundtrip_basic(self):
        """Serialize a chunk tree and verify the output starts with RIFX Egg!"""
        root = _build_test_chunk_tree()
        data = serialize_chunk_tree(root, True)
        assert data[:4] == b"RIFX"
        # Size field
        size = struct.unpack(">I", data[4:8])[0]
        assert size == len(data) - 8
        # File ID
        assert data[8:12] == b"Egg!"

    def test_roundtrip_little_endian(self):
        root = _build_test_chunk_tree(big_endian=False)
        root.header = "RIFF"
        data = serialize_chunk_tree(root, False)
        assert data[:4] == b"RIFF"
        size = struct.unpack("<I", data[4:8])[0]
        assert size == len(data) - 8
        assert data[8:12] == b"Egg!"

    def test_modify_then_serialize(self):
        """Modify a property, serialize, and verify the change is present."""
        root = _build_test_chunk_tree()
        set_property_value(root, 100, 10,
                           ["ADBE Transform Group", "ADBE Position"],
                           [1920.0, 1080.0], True)
        data = serialize_chunk_tree(root, True)
        # The values should be somewhere in the binary
        expected = struct.pack(">dd", 1920.0, 1080.0)
        assert expected in data

    def test_string_chunks_serialized(self):
        """Verify Utf8 and tdmn string chunks appear in output."""
        root = _build_test_chunk_tree()
        data = serialize_chunk_tree(root, True)
        assert b"TestLayer" in data
        assert b"ADBE Position" in data
        assert b"ADBE Transform Group" in data

    def test_save_to_file(self, tmp_path):
        """Test saving to a file."""
        root = _build_test_chunk_tree()
        out_file = tmp_path / "test.aep"
        save_aep(root, True, out_file)
        assert out_file.exists()
        data = out_file.read_bytes()
        assert data[:4] == b"RIFX"
        assert data[8:12] == b"Egg!"


# ── Tests: btdk roundtrip ───────────────────────────────────────────────────


class TestBtdkRoundtrip:
    def test_btdk_serialized_as_list(self):
        """btdk chunks should be serialized as LIST btdk."""
        btdk_data = b"\x01\x02\x03\x04\x05\x06"
        btdk = Chunk("btdk", len(btdk_data) + 4, btdk_data)

        root_cl = ChunkList("Egg!", [btdk])
        root = Chunk("RIFX", 0, root_cl)
        data = serialize_chunk_tree(root, True)

        # Find LIST in the output after the root header
        # Should be: RIFX [size] Egg! LIST [size] btdk [data]
        assert b"LIST" in data
        idx = data.index(b"LIST", 12)
        list_size = struct.unpack(">I", data[idx+4:idx+8])[0]
        list_type = data[idx+8:idx+12]
        assert list_type == b"btdk"
        assert data[idx+12:idx+12+6] == btdk_data


# ── Tests: Container chunks (tdsn) ──────────────────────────────────────────


class TestContainerChunks:
    def test_tdsn_serialized(self):
        """tdsn container (non-LIST) should be serialized without type prefix."""
        utf8_inner = Chunk("Utf8", 4, "test")
        tdsn_cl = ChunkList("", [utf8_inner])
        tdsn = Chunk("tdsn", 0, tdsn_cl)

        root_cl = ChunkList("Egg!", [tdsn])
        root = Chunk("RIFX", 0, root_cl)
        data = serialize_chunk_tree(root, True)

        # tdsn should appear in output
        assert b"tdsn" in data
        # No LIST prefix before it
        idx = data.index(b"tdsn", 12)
        # After tdsn [size], the next chunk should be Utf8, not a type prefix
        tdsn_size = struct.unpack(">I", data[idx+4:idx+8])[0]
        assert data[idx+8:idx+12] == b"Utf8"


# ── Tests: Layer flag / field writers ──────────────────────────────────────


class TestLayerFlags:
    def test_set_visible_false(self):
        root = _build_test_chunk_tree()
        assert set_layer_flag(root, 100, 10, 'visible', False, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[39] & 0x01 == 0  # bit 0 of flags byte 3

    def test_set_visible_true(self):
        root = _build_test_chunk_tree()
        set_layer_flag(root, 100, 10, 'visible', False, True)
        set_layer_flag(root, 100, 10, 'visible', True, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[39] & 0x01 == 1

    def test_set_solo(self):
        root = _build_test_chunk_tree()
        assert set_layer_flag(root, 100, 10, 'solo', True, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[38] & 0x08 != 0  # bit 3 of flags byte 2

    def test_set_shy_locked(self):
        root = _build_test_chunk_tree()
        set_layer_flag(root, 100, 10, 'shy', True, True)
        set_layer_flag(root, 100, 10, 'locked', True, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[39] & 0x40 != 0  # shy: bit 6 of byte 3
        assert ldta.data[39] & 0x20 != 0  # locked: bit 5 of byte 3

    def test_set_three_d_layer(self):
        root = _build_test_chunk_tree()
        set_layer_flag(root, 100, 10, 'threedimensional', True, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[38] & 0x04 != 0  # bit 2 of byte 2

    def test_nonexistent_layer(self):
        root = _build_test_chunk_tree()
        assert not set_layer_flag(root, 100, 999, 'visible', True, True)

    def test_invalid_flag_name(self):
        root = _build_test_chunk_tree()
        assert not set_layer_flag(root, 100, 10, 'bogus', True, True)


class TestLayerFields:
    def test_set_label(self):
        root = _build_test_chunk_tree()
        assert set_layer_label(root, 100, 10, 5, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[61] == 5

    def test_set_blend_mode(self):
        root = _build_test_chunk_tree()
        assert set_layer_blend_mode(root, 100, 10, 4, True)  # MULTIPLY
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert struct.unpack(">I", ldta.data[96:100])[0] == 4

    def test_set_track_matte(self):
        root = _build_test_chunk_tree()
        assert set_layer_track_matte(root, 100, 10, 1, True)  # ALPHA
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert struct.unpack(">I", ldta.data[104:108])[0] == 1

    def test_set_quality(self):
        root = _build_test_chunk_tree()
        assert set_layer_quality(root, 100, 10, 0, True)  # WIREFRAME
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert struct.unpack(">H", ldta.data[4:6])[0] == 0


class TestLayerTimeFields:
    def test_set_in_time(self):
        root = _build_test_chunk_tree()
        assert set_layer_time_field(root, 100, 10, 'in_time', 1.0, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        num = struct.unpack(">i", ldta.data[20:24])[0]
        den = struct.unpack(">I", ldta.data[24:28])[0]
        assert num / den == pytest.approx(1.0)

    def test_set_out_time(self):
        root = _build_test_chunk_tree()
        assert set_layer_time_field(root, 100, 10, 'out_time', 10.0, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        num = struct.unpack(">i", ldta.data[28:32])[0]
        den = struct.unpack(">I", ldta.data[32:36])[0]
        assert num / den == pytest.approx(10.0)

    def test_set_start_time(self):
        root = _build_test_chunk_tree()
        assert set_layer_time_field(root, 100, 10, 'start_time', -2.5, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        num = struct.unpack(">i", ldta.data[12:16])[0]
        den = struct.unpack(">I", ldta.data[16:20])[0]
        assert num / den == pytest.approx(-2.5, abs=0.04)

    def test_set_time_stretch(self):
        root = _build_test_chunk_tree()
        assert set_layer_time_field(root, 100, 10, 'time_stretch', 2, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        num = struct.unpack(">i", ldta.data[8:12])[0]
        den = struct.unpack(">H", ldta.data[110:112])[0]
        assert num / den == pytest.approx(2.0)

    def test_invalid_field(self):
        root = _build_test_chunk_tree()
        assert not set_layer_time_field(root, 100, 10, 'bogus', 1.0, True)


# ── Tests: Comp field writers ──────────────────────────────────────────────


class TestCompFields:
    def test_set_dimensions(self):
        root = _build_test_chunk_tree()
        assert set_comp_dimensions(root, 100, 3840, 2160, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        cdta = comp_cl.find_optional("cdta")
        w, h = struct.unpack(">HH", cdta.data[140:144])
        assert w == 3840
        assert h == 2160

    def test_set_bgcolor(self):
        root = _build_test_chunk_tree()
        assert set_comp_bgcolor(root, 100, 255, 128, 0, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        cdta = comp_cl.find_optional("cdta")
        assert cdta.data[52] == 255
        assert cdta.data[53] == 128
        assert cdta.data[54] == 0

    def test_set_framerate(self):
        root = _build_test_chunk_tree()
        assert set_comp_framerate(root, 100, 60.0, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        cdta = comp_cl.find_optional("cdta")
        denom = struct.unpack(">I", cdta.data[4:8])[0]
        num = struct.unpack(">I", cdta.data[8:12])[0]
        assert num / denom == pytest.approx(60.0)

    def test_set_duration(self):
        root = _build_test_chunk_tree()
        assert set_comp_duration(root, 100, 10.0, True)
        comp_cl = find_comp_chunklist(root, 100, True)
        cdta = comp_cl.find_optional("cdta")
        raw = struct.unpack(">H", cdta.data[45:47])[0]
        dur_div = struct.unpack(">H", cdta.data[49:51])[0]
        denom = struct.unpack(">I", cdta.data[4:8])[0]
        num = struct.unpack(">I", cdta.data[8:12])[0]
        framerate = num / denom
        assert raw * framerate / dur_div == pytest.approx(10.0)

    def test_nonexistent_comp(self):
        root = _build_test_chunk_tree()
        assert not set_comp_dimensions(root, 999, 100, 100, True)


# ── Tests: Layer/Comp property setters (high-level) ───────────────────────


class TestLayerPropertySetters:
    """Test that property setters on Layer update both model and chunk tree."""

    def _make_project_with_chunk_tree(self):
        from aep_parser.models import (
            Project as PModel, Composition, Layer as LModel,
            PropertyGroup as PG, AnimatedProperty, NamedProperty, Vector, Folder,
        )
        lm = LModel()
        lm.id = 10
        lm.name = "TestLayer"
        lm.visible = True
        lm.solo = False
        lm.shy = False
        lm.locked = False
        lm.blend_mode = 1
        lm.matte_mode = 0
        lm.quality = 2
        lm.label_color = 0
        lm.in_time = 0.0
        lm.out_time = 5.0
        lm.start_time = 0.0
        lm.time_stretch = 1.0
        lm.is_null = False
        lm.is_guide = False
        lm.is_adjustment = False
        lm.threedimensional = False
        lm.auto_orient = False
        lm.bicubic_sampling = False
        lm.continuously_rasterize = False
        lm.effects_enabled = False
        lm.motion_blur_enabled = False

        pos = AnimatedProperty()
        pos.value = Vector(960.0, 540.0)
        pos.components = 2
        pos.prop_type = 2
        pg = PG()
        pg.properties = [NamedProperty("ADBE Position", pos)]
        tg = PG()
        tg.properties = [NamedProperty("ADBE Transform Group", pg)]
        lm.properties = tg

        comp = Composition()
        comp.id = 100
        comp.name = "TestComp"
        comp.width = 1920
        comp.height = 1080
        comp.framerate = 30.0
        comp.duration = 5.0
        comp.layers = [lm]

        model = PModel()
        model.compositions = [comp]
        model.folder = Folder()
        model.folder.items = [comp]

        root = _build_test_chunk_tree()
        from aep_tools._project import Project
        return Project(model, "test.aep", chunk_tree=root, big_endian=True)

    def test_enabled_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.enabled = False
        assert layer.enabled is False
        # Verify chunk tree
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[39] & 0x01 == 0

    def test_solo_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.solo = True
        assert layer.solo is True

    def test_label_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.label = 7
        assert layer.label == 7
        comp_cl = find_comp_chunklist(proj._chunk_tree, 100, True)
        ldta = find_layer_chunk(comp_cl, 10, True).list.find_optional("ldta")
        assert ldta.data[61] == 7

    def test_blend_mode_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.blending_mode = 4  # MULTIPLY
        assert layer.blending_mode == 4

    def test_in_point_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.in_point = 1.0
        assert layer.in_point == 1.0

    def test_out_point_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.out_point = 10.0
        assert layer.out_point == 10.0

    def test_quality_setter(self):
        proj = self._make_project_with_chunk_tree()
        layer = proj.comp(1).layer(1)
        layer.quality = 0  # WIREFRAME
        assert layer.quality == 0


class TestCompPropertySetters:
    def _make_project_with_chunk_tree(self):
        from aep_parser.models import (
            Project as PModel, Composition, Folder,
        )
        comp = Composition()
        comp.id = 100
        comp.name = "TestComp"
        comp.width = 1920
        comp.height = 1080
        comp.framerate = 30.0
        comp.duration = 5.0
        from aep_parser.models import Color
        comp.color = Color(51, 51, 51, 255)

        model = PModel()
        model.compositions = [comp]
        model.folder = Folder()
        model.folder.items = [comp]

        root = _build_test_chunk_tree()
        from aep_tools._project import Project
        return Project(model, "test.aep", chunk_tree=root, big_endian=True)

    def test_width_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp(1)
        comp.width = 3840
        assert comp.width == 3840
        cdta = find_comp_chunklist(proj._chunk_tree, 100, True).find_optional("cdta")
        w = struct.unpack(">H", cdta.data[140:142])[0]
        assert w == 3840

    def test_height_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp(1)
        comp.height = 2160
        assert comp.height == 2160

    def test_frame_rate_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp(1)
        comp.frame_rate = 60.0
        assert comp.frame_rate == 60.0

    def test_bg_color_setter(self):
        proj = self._make_project_with_chunk_tree()
        comp = proj.comp(1)
        comp.bg_color = [255, 128, 0]
        assert comp.bg_color == [255, 128, 0]
        cdta = find_comp_chunklist(proj._chunk_tree, 100, True).find_optional("cdta")
        assert cdta.data[52] == 255
        assert cdta.data[53] == 128
        assert cdta.data[54] == 0
