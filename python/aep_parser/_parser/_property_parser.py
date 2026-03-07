"""Property, keyframe, animation, shape, gradient, marker, and text parsing mixin."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from typing import Any

from .binary_reader import BinaryReader
from .chunk import Chunk, ChunkList
from .cos import CosParser
from ..models import (
    AnimatedProperty, BezierShape, CharacterStyle, Color, EffectInstance,
    Font, Gradient, GradientStop, Keyframe, LayerRef, LineStyle, Marker,
    MaskData, NamedProperty, ParagraphStyle, PropertyGroup, TextDocument,
    TextProperty, Vector,
)

_NAME_PLACEHOLDER = "-_0_/-"

# Groups that genuinely have on/off toggles in AE UI.
_TOGGLE_GROUPS = {
    "ADBE Layer Styles",
}

# Default properties for Transform Group — AE omits these from the binary.
_TRANSFORM_DEFAULTS = [
    ("ADBE Anchor Point", 2, 3, [0.0, 0.0, 0.0]),
    ("ADBE Position", 2, 2, [0.0, 0.0]),
    ("ADBE Scale", 3, 2, [1.0, 1.0]),
    ("ADBE Rotate Z", 3, 1, 0.0),
    ("ADBE Opacity", 3, 1, 1.0),
]


class PropertyParserMixin:
    """Mixin providing property/keyframe/animation/text parsing methods.

    Requires the host class to provide: big_endian, _chunk_reader(), _utf8_name(),
    _get_indexed_key(), _current_layer_3d.
    """

    def _parse_property_group(self, cl: ChunkList, group: PropertyGroup,
                              key_prefix: str = "") -> None:
        match_name = ""
        i = 0
        while i < len(cl.children):
            child = cl.children[i]

            if child.header == "tdmn":
                match_name = child.data

            elif child.header == "tdsb":
                fl = self._chunk_reader(child).read_flags(4)
                vis = fl.get_bit(3, 0)
                split = fl.get_bit(3, 1)
                group.split_position = split
                if split:
                    group.enabled = vis
                else:
                    group.visible = vis

            elif child.header == "tdsn":
                utf8 = child.list.find_optional("Utf8")
                group.name = self._utf8_name(utf8)

            elif child.name == "mkif":
                mask = MaskData()
                mr = self._chunk_reader(child)
                mask.inverted = bool(mr.read_uint(1))
                mask.locked = bool(mr.read_uint(1))
                mr.skip(4)
                mode_val = mr.read_uint(2)
                mask.mode = mode_val if mode_val <= 6 else 0
                i += 1
                mr.skip(3)
                mask.index = mr.read_uint(1)
                if i < len(cl.children):
                    parsed = self._parse_property(cl.children[i])
                    if isinstance(parsed, PropertyGroup):
                        mask.properties = parsed
                group.properties.append(NamedProperty(match_name, mask))
                match_name = ""

            elif child.name in ("OvG2", "blsi", "blsv"):
                match_name = ""

            elif match_name:
                suffix = ""
                if child.name == "tdgp" and match_name == "ADBE Vector Group":
                    tdsn = child.list.find_optional("tdsn")
                    if tdsn is not None:
                        utf8 = tdsn.list.find_optional("Utf8")
                        n = self._utf8_name(utf8)
                        if n:
                            suffix = f" - {n}"

                full_key = f"{key_prefix}/{match_name}{suffix}" if key_prefix else match_name
                indexed_key = self._get_indexed_key(full_key)
                parsed = self._parse_property(child, indexed_key)
                if parsed is not None:
                    if match_name == "ADBE Layer Styles" and isinstance(parsed, PropertyGroup):
                        self._fix_layer_styles_enabled(parsed)
                    elif isinstance(parsed, PropertyGroup) and parsed.enabled is not None \
                            and match_name not in _TOGGLE_GROUPS:
                        parsed.enabled = None
                    parsed.key = indexed_key
                    group.properties.append(NamedProperty(match_name, parsed))
                    if match_name == "ADBE Transform Group" and isinstance(parsed, PropertyGroup):
                        self._inject_transform_defaults(parsed, key_prefix)
                match_name = ""

            i += 1

    @staticmethod
    def _fix_layer_styles_enabled(group: PropertyGroup) -> None:
        """Derive correct enabled state for Layer Styles and its sub-styles."""
        from ..models import PropertyGroup as PG
        for np in group.properties:
            if not np.match_name.endswith("/enabled"):
                continue
            v = np.value
            if not isinstance(v, PG):
                continue
            if v.enabled is None:
                v.enabled = bool(v.properties)

        group.enabled = any(
            isinstance(np.value, PG) and np.value.enabled is True
            for np in group.properties
            if np.match_name.endswith("/enabled")
        )

    def _inject_transform_defaults(self, group: PropertyGroup,
                                     key_prefix: str) -> None:
        """Add default entries for standard Transform properties not in the binary."""
        existing = {np.match_name for np in group.properties}
        has_split_pos = any(mn.startswith("ADBE Position_") for mn in existing)
        is_3d = self._current_layer_3d
        for mn, prop_type, components, default_val in _TRANSFORM_DEFAULTS:
            if mn in existing:
                continue
            if mn == "ADBE Position" and has_split_pos:
                continue
            if is_3d and mn == "ADBE Position":
                components = 3
                default_val = [0.0, 0.0, 0.0]
            full_key = f"{key_prefix}/ADBE Transform Group/{mn}" if key_prefix else f"ADBE Transform Group/{mn}"
            prop = AnimatedProperty(
                key=full_key, prop_type=prop_type,
                components=components, value=default_val,
            )
            group.properties.append(NamedProperty(mn, prop))

    def _parse_property(self, chunk: Chunk,
                        key: str = "") -> PropertyGroup | AnimatedProperty | EffectInstance | TextProperty | None:
        name = chunk.name
        if name == "tdgp":
            pg = PropertyGroup()
            self._parse_property_group(chunk.list, pg, key)
            return pg
        if name == "sspc":
            return self._parse_effect_instance(chunk.list)
        if name == "tdbs":
            return self._parse_animated_property(chunk.list, [])
        if name == "om-s":
            return self._parse_animated_shape(chunk.list)
        if name == "GCst":
            return self._parse_animated_gradient(chunk.list)
        if name == "otst":
            return self._parse_animated_orientation(chunk.list)
        if name == "mrst":
            return self._parse_animated_marker(chunk.list)
        if name == "btds":
            return self._parse_animated_text(chunk.list)
        return None

    def _parse_animated_property(self, cl: ChunkList,
                                 extra_values: list) -> AnimatedProperty:
        prop = AnimatedProperty()
        tdsb, tdb4, cdat, lst, utf8, tdpi, tdps, tdli = cl.find_multiple(
            ["tdsb", "tdb4", "cdat", "list", "Utf8", "tdpi", "tdps", "tdli"])

        if tdsb is None or tdb4 is None:
            return prop

        fl = self._chunk_reader(tdsb).read_flags(4)
        prop.split = fl.get_bit(3, 1)

        br = self._chunk_reader(tdb4)
        br.skip(2)
        prop.components = br.read_uint(2)
        flags2 = br.read_flags(2)
        is_spatial = flags2.get_bit(1, 3)
        br.skip(7)
        time_scale = br.read_uint(4)
        br.skip(39)
        flags3 = br.read_flags(4)
        is_color = flags3.get_bit(1, 0)
        is_bool = flags3.get_bit(3, 0)
        is_ref = flags3.get_bit(3, 2)

        br.skip(8)
        if is_spatial:
            prop.prop_type = 2
        elif is_bool:
            prop.prop_type = 0
        elif is_color:
            prop.prop_type = 1
        elif is_ref:
            prop.prop_type = 5
        else:
            prop.prop_type = 3

        prop.animated = br.read_uint(1) == 1

        if is_ref and tdpi is not None:
            prop.prop_type = 4
            ref = LayerRef()
            ref.layer_id = self._chunk_reader(tdpi).read_uint(4)
            if tdps is not None:
                ref.layer_source = self._chunk_reader(tdps).read_sint(4)
            prop.value = ref
        elif is_ref and tdli is not None:
            prop.prop_type = 6
            prop.value = self._chunk_reader(tdli).read_uint(4)
        elif cdat is not None and prop.components > 0:
            cr = self._chunk_reader(cdat)
            if cr.remaining() >= prop.components * 8:
                raw = cr.read_array(prop.components, cr.read_float64)
                prop.value = self._property_value(0, raw, extra_values, prop.prop_type)

        if lst is not None:
            items = self._list_values(lst)
            for idx, item_reader in enumerate(items):
                kf = self._load_keyframe(idx, item_reader, prop, extra_values,
                                         time_scale)
                prop.keyframes.append(kf)

        if utf8 is not None:
            prop.expression = self._utf8_name(utf8)

        return prop

    def _property_value(self, idx: int, raw: list[float],
                        extra_values: list, prop_type: int) -> Any:
        if prop_type == 1:
            return extra_values[idx] if extra_values else None
        if prop_type == 0:
            r = self._clamp_color(raw[1])
            g = self._clamp_color(raw[2])
            b = self._clamp_color(raw[3])
            a = min(1.0, max(0.0, raw[0]))
            return Color(r, g, b, a)
        if len(raw) == 1:
            return raw[0]
        return Vector(*raw) if len(raw) <= 3 else Vector(raw[0], raw[1], raw[2] if len(raw) > 2 else None)

    @staticmethod
    def _clamp_color(v: float) -> float:
        if 0 <= v <= 255:
            return v
        if 0 <= v <= 1:
            return v * 255
        if v > 255:
            return min(255, max(0, v / 255))
        return min(255, max(0, v))

    def _list_values(self, list_chunk: Chunk) -> list[BinaryReader]:
        cl = list_chunk.list
        lhd3, ldat = cl.find_multiple(["lhd3", "ldat"])
        if lhd3 is None or ldat is None:
            return []

        hr = self._chunk_reader(lhd3)
        hr.skip(10)
        count = hr.read_uint(2)
        hr.skip(6)
        item_size = hr.read_uint(2)

        if not isinstance(ldat.data, (bytes, bytearray)):
            return []
        if len(ldat.data) < count * item_size:
            raise ValueError("Not enough data in ldat chunk")

        readers = []
        for i in range(count):
            start = i * item_size
            readers.append(BinaryReader(ldat.data[start:start + item_size], 0,
                                        self.big_endian))
        return readers

    def _load_keyframe(self, idx: int, reader: BinaryReader,
                       prop: AnimatedProperty, extra_values: list,
                       time_scale: int) -> Keyframe:
        kf = Keyframe()
        reader.skip(1)
        time_raw = reader.read_sint(4)
        kf.time = time_raw / time_scale if time_scale else 0
        kf.transition_type = reader.read_uint(1)
        kf.label_color = reader.read_uint(1)

        flag_byte = reader.read_flags(1)
        kf.roving = flag_byte.get_bit(0, 5)
        if flag_byte.get_bit(0, 3):
            kf.bezier_mode = 1
        elif flag_byte.get_bit(0, 4):
            kf.bezier_mode = 2
        else:
            kf.bezier_mode = 0

        ptype = prop.prop_type
        spv = BinaryReader.process_speed_value

        if ptype == 1:
            kf.value = extra_values[idx] if idx < len(extra_values) else None
            if reader.remaining() >= 48:
                reader.skip(16)
                kf.in_speed.append(spv(reader.read_float64()))
                kf.in_influence.append(reader.read_float64())
                kf.out_speed.append(spv(reader.read_float64()))
                kf.out_influence.append(reader.read_float64())

        elif ptype in (3, 5):
            needed = prop.components * 5 * 8
            if reader.remaining() >= needed:
                kf.value = Vector(*reader.read_array(prop.components,
                                                      reader.read_float64))
                kf.in_speed = [spv(reader.read_float64())
                               for _ in range(prop.components)]
                kf.in_influence = reader.read_array(prop.components,
                                                     reader.read_float64)
                kf.out_speed = [spv(reader.read_float64())
                                for _ in range(prop.components)]
                kf.out_influence = reader.read_array(prop.components,
                                                      reader.read_float64)

        elif ptype == 2:
            needed = 16 + (4 + prop.components * 3) * 8
            if reader.remaining() >= needed:
                reader.skip(16)
                kf.in_speed.append(spv(reader.read_float64()))
                kf.in_influence.append(reader.read_float64())
                kf.out_speed.append(spv(reader.read_float64()))
                kf.out_influence.append(reader.read_float64())
                kf.value = Vector(*reader.read_array(prop.components,
                                                      reader.read_float64))
                kf.in_tangent = Vector(*reader.read_array(prop.components,
                                                           reader.read_float64))
                kf.out_tangent = Vector(*reader.read_array(prop.components,
                                                            reader.read_float64))

        elif ptype == 0:
            if reader.remaining() >= 48:
                reader.skip(16)
                kf.in_speed.append(spv(reader.read_float64()))
                kf.in_influence.append(reader.read_float64())
                kf.out_speed.append(spv(reader.read_float64()))
                kf.out_influence.append(reader.read_float64())
            if reader.remaining() >= prop.components * 8:
                raw = reader.read_array(prop.components, reader.read_float64)
                if len(raw) >= 4:
                    kf.value = Color(raw[1], raw[2], raw[3], raw[0] / 255)
                else:
                    kf.value = Vector(*raw)

        return kf

    def _parse_animated_shape(self, cl: ChunkList) -> AnimatedProperty:
        omks, tdbs = cl.find_multiple(["omks", "tdbs"])
        if omks is None or tdbs is None:
            return AnimatedProperty()
        max_verts = 0
        shapes = []
        for shap in omks.list.find_all("shap"):
            bezier = self._parse_bezier(shap.list)
            max_verts = max(max_verts, len(bezier.points) // 3)
            shapes.append(bezier)

        for s in shapes:
            s.group_info["maxVertexCount"] = max_verts
            s.group_info["bezierCount"] = len(shapes)

        return self._parse_animated_property(tdbs.list, shapes)

    def _parse_bezier(self, cl: ChunkList) -> BezierShape:
        shape = BezierShape()
        shph = cl.find_optional("shph")
        if shph is None:
            return shape
        r = self._chunk_reader(shph)
        r.skip(3)
        fl = r.read_flags(1)
        shape.closed = not fl.get_bit(0, 3)
        shape.minimum.x = r.read_float32()
        shape.minimum.y = r.read_float32()
        shape.maximum.x = r.read_float32()
        shape.maximum.y = r.read_float32()

        list_chunk = cl.find_optional("list")
        if list_chunk is None:
            return shape
        for item_reader in self._list_values(list_chunk):
            x = item_reader.read_float32()
            y = item_reader.read_float32()
            if not (math.isnan(x) or math.isnan(y)):
                shape.points.append(Vector(x, y))

        return shape

    def _parse_animated_gradient(self, cl: ChunkList) -> AnimatedProperty:
        gcky, tdbs = cl.find_multiple(["GCky", "tdbs"])
        if gcky is None or tdbs is None:
            return AnimatedProperty()
        gradients = []
        for utf8 in gcky.list.find_all("Utf8"):
            gradients.append(self._parse_gradient(utf8.data))
        return self._parse_animated_property(tdbs.list, gradients)

    def _parse_gradient(self, xml_str: str) -> Gradient:
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return Gradient()
        data = self._parse_ae_prop_xml(root)
        grad_data = data.get("Gradient Color Data", {})
        gradient = Gradient()

        color_stops_data = grad_data.get("Color Stops", {})
        stops_list = color_stops_data.get("Stops List", {})
        for stop in stops_list.values():
            sc = stop.get("Stops Color", [])
            if len(sc) >= 6:
                gradient.color_stops.append(
                    GradientStop(sc[0], sc[1], Color(sc[2] * 255, sc[3] * 255,
                                                      sc[4] * 255, sc[5])))

        alpha_stops_data = grad_data.get("Alpha Stops", {})
        alpha_list = alpha_stops_data.get("Stops List", {})
        for stop in alpha_list.values():
            sa = stop.get("Stops Alpha", [])
            if len(sa) >= 3:
                gradient.alpha_stops.append(GradientStop(sa[0], sa[1], sa[2]))

        return gradient

    def _parse_ae_prop_xml(self, elem: ET.Element) -> Any:
        """Parse After Effects property XML (prop.map, prop.list, array, etc.)."""
        tag = elem.tag
        if tag == "prop.map":
            first = next(iter(elem), None)
            return self._parse_ae_prop_xml(first) if first is not None else {}
        if tag == "prop.list":
            result = {}
            for child in elem:
                if child.tag == "prop.pair":
                    children = list(child)
                    if len(children) >= 2:
                        key = children[0].text or ""
                        val = self._parse_ae_prop_xml(children[-1])
                        result[key] = val
            return result
        if tag == "array":
            items = []
            for child in elem:
                if child.tag != "array.type":
                    items.append(self._parse_ae_prop_xml(child))
            return items
        if tag in ("int", "float"):
            return float(elem.text) if elem.text else 0
        if tag == "string":
            return elem.text or ""
        return None

    def _parse_animated_orientation(self, cl: ChunkList) -> AnimatedProperty:
        otky, tdbs = cl.find_multiple(["otky", "tdbs"])
        if otky is None or tdbs is None:
            return AnimatedProperty()
        orientations = []
        for otda in otky.list.find_all("otda"):
            r = self._chunk_reader(otda)
            orientations.append(Vector(r.read_float64(), r.read_float64(),
                                       r.read_float64()))
        return self._parse_animated_property(tdbs.list, orientations)

    def _parse_animated_marker(self, cl: ChunkList) -> AnimatedProperty:
        mrky, tdbs = cl.find_multiple(["mrky", "tdbs"])
        if mrky is None or tdbs is None:
            return AnimatedProperty()
        markers = []
        for nmrd in mrky.list.find_all("Nmrd"):
            markers.append(self._parse_marker(nmrd))
        return self._parse_animated_property(tdbs.list, markers)

    def _parse_marker(self, chunk: Chunk) -> Marker:
        marker = Marker()
        cl = chunk.list
        nmhd = cl.find_optional("NmHd")
        if nmhd is None:
            return marker
        r = self._chunk_reader(nmhd)
        utf8 = cl.find_optional("Utf8")
        marker.name = self._utf8_name(utf8)
        r.skip(3)
        fl = r.read_flags(1)
        marker.is_protected = fl.get_bit(0, 1)
        r.skip(4)
        dur_num = r.read_uint(4)
        dur_den = r.read_uint(4)
        marker.duration = dur_num / dur_den if dur_den else 0
        marker.label_color = r.read_uint(1)
        return marker

    def _parse_animated_text(self, cl: ChunkList) -> TextProperty:
        btdk, tdbs = cl.find_multiple(["btdk", "tdbs"])
        if btdk is None or tdbs is None:
            return TextProperty()
        cos_data = CosParser(btdk.data).parse()

        text_prop = TextProperty()

        try:
            fonts_data = self._cos_val(cos_data, [0, 1, 0])
            for font_entry in fonts_data:
                family = self._cos_val(font_entry, [0, 0, 0])
                text_prop.fonts.append(Font(family=family))
        except (KeyError, IndexError, TypeError):
            pass

        text_docs: list = []
        try:
            docs_data = self._cos_val(cos_data, [1, 1])
            for doc_entry in docs_data:
                text_docs.append(self._parse_text_document(doc_entry))
        except (KeyError, IndexError, TypeError):
            pass

        text_prop.documents = self._parse_animated_property(tdbs.list, text_docs)
        return text_prop

    def _parse_text_document(self, data: Any) -> TextDocument:
        doc = TextDocument()

        try:
            doc.text = self._cos_val(data, [0, 0])
        except (KeyError, IndexError, TypeError):
            pass

        try:
            para_data = self._cos_val(data, [1, 2])
            for entry in para_data:
                if not isinstance(entry, dict) or "6" not in entry:
                    continue
                for item in self._cos_val(entry, [6]):
                    if not isinstance(item, dict):
                        continue
                    if "0" not in item:
                        continue
                    pos_data = self._cos_val(item, [0, 0])
                    size_data = self._cos_val(item, [1])
                    if (size_data[2] or size_data[3]) and (pos_data[0] or pos_data[1]):
                        ps = ParagraphStyle()
                        ps.wrap_size = Vector(size_data[2], size_data[3])
                        ps.wrap_position = Vector(pos_data[0], pos_data[1])
                        doc.paragraph_styles.append(ps)
        except (KeyError, IndexError, TypeError):
            pass

        try:
            line_data = self._cos_val(data, [0, 5, 0])
            for entry in line_data:
                ls = LineStyle()
                ls.character_count = self._cos_val(entry, [1])
                justify_data = self._cos_val(entry, [0, 0, 5])
                ls.text_justify = self._cos_val(justify_data, 0)
                doc.line_styles.append(ls)
        except (KeyError, IndexError, TypeError):
            pass

        try:
            char_data = self._cos_val(data, [0, 6, 0])
            for entry in char_data:
                cs = CharacterStyle()
                cs.character_count = self._cos_val(entry, [1])
                style = self._cos_val(entry, [0, 0, 6])
                cs.font_index = self._cos_val(style, 0)
                cs.size = self._cos_val(style, 1)
                cs.faux_bold = bool(self._cos_val(style, 2))
                cs.faux_italic = bool(self._cos_val(style, 3))
                cs.leading_auto = bool(self._cos_val(style, 4))
                cs.leading = self._cos_val(style, 5)
                cs.tracking = self._cos_val(style, 8)
                cs.text_transform = self._cos_val(style, 12)
                cs.vertical_align = self._cos_val(style, 13)

                fill_enabled = self._cos_val_safe(style, 56, True)
                cs.fill_enabled = bool(fill_enabled)
                if cs.fill_enabled:
                    fill_data = self._cos_val_safe(style, 53, None)
                    if fill_data:
                        cs.fill_color = self._cos_color(fill_data, [0, 1])
                    else:
                        cs.fill_color = Color(0, 0, 0)

                stroke_enabled = self._cos_val_safe(style, 57, False)
                cs.stroke_enabled = bool(stroke_enabled)
                if cs.stroke_enabled:
                    stroke_data = self._cos_val_safe(style, 54, None)
                    if stroke_data:
                        cs.stroke_color = self._cos_color(stroke_data, [0, 1])
                    else:
                        cs.stroke_color = Color(0, 0, 0)
                    cs.stroke_over_fill = bool(self._cos_val_safe(style, 58, False))
                    cs.stroke_width = self._cos_val_safe(style, 63, 1)

                doc.character_styles.append(cs)
        except (KeyError, IndexError, TypeError):
            pass

        return doc

    @staticmethod
    def _cos_val(data: Any, path: list | int) -> Any:
        if isinstance(path, int):
            keys = [str(path)]
        else:
            keys = [str(p) for p in path]
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result[key]
            elif isinstance(result, list):
                result = result[int(key)]
            else:
                raise KeyError(f"Cannot navigate to {key} in {type(result)}")
        return result

    @staticmethod
    def _cos_val_safe(data: Any, key: int, default: Any = None) -> Any:
        try:
            k = str(key)
            if isinstance(data, dict):
                return data.get(k, default)
            if isinstance(data, list) and key < len(data):
                return data[key]
        except (KeyError, IndexError, TypeError):
            pass
        return default

    @staticmethod
    def _cos_color(data: Any, path: list) -> Color:
        keys = [str(p) for p in path]
        result = data
        for key in keys:
            result = result[key] if isinstance(result, dict) else result[int(key)]
        return Color(result[1] * 255, result[2] * 255, result[3] * 255, result[0])
