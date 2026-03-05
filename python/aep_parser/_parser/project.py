"""Project parser: converts AEP/AEPX chunk tree into a structured Project model.

This corresponds to the we$3/pt$2 class in the original JS code.
"""

from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from typing import Any

from .binary_reader import BinaryReader
from .chunk import Chunk, ChunkList
from .cos import CosParser
from ..models import (
    AnimatedProperty, BezierShape, CharacterStyle, Color, Composition,
    EffectDefinition, EffectInstance, EffectParameter, Folder, Font, Gradient,
    GradientStop, ImageAsset, Keyframe, Layer, LayerRef, LineStyle, Marker,
    MaskData, NamedProperty, OutputModule, OUTPUT_FORMATS, ParagraphStyle,
    Project, PropertyGroup, RenderQueueItem, SequenceInfo, SolidAsset,
    TextDocument, TextProperty, Vector,
)

_NAME_PLACEHOLDER = "-_0_/-"

# Groups that genuinely have on/off toggles in AE UI.
# All other groups with split=True in tdsb should NOT show enabled state.
_TOGGLE_GROUPS = {
    "ADBE Layer Styles",
}

# Mask mode constants
MASK_NONE = 0
MASK_ADD = 1
MASK_SUBTRACT = 2
MASK_INTERSECT = 3
MASK_DARKEN = 4
MASK_LIGHTEN = 5
MASK_DIFFERENCE = 6


class ProjectParser:
    """Converts a parsed RIFF chunk tree into a Project model."""

    def __init__(self, big_endian: bool = True):
        self.big_endian = big_endian
        self._comp_chunks: dict[int, ChunkList] = {}
        self._layer_prop_key_index: dict[str, int] = {}

    def _chunk_reader(self, chunk: Chunk) -> BinaryReader:
        if not isinstance(chunk.data, (bytes, bytearray)):
            raise TypeError(f"Expected binary chunk, got {type(chunk.data).__name__}")
        return BinaryReader(chunk.data, 0, self.big_endian)

    def _utf8_name(self, chunk: Chunk | None, default: str = "") -> str:
        if chunk is None:
            return default
        if isinstance(chunk.data, str) and chunk.data != _NAME_PLACEHOLDER:
            return chunk.data
        return default

    def _get_indexed_key(self, key: str) -> str:
        count = self._layer_prop_key_index.get(key)
        if count is None:
            self._layer_prop_key_index[key] = 1
            return key
        self._layer_prop_key_index[key] = count + 1
        return f"{key} {count}"

    # ── Top-level ────────────────────────────────────────────────────────

    def parse_project(self, root_chunk: Chunk) -> Project:
        project = Project()
        cl = root_chunk.list
        fold, efdg, lrdr = cl.find_multiple(["Fold", "EfdG", "LRdr"])

        if efdg is not None:
            self._parse_effects(efdg.list.find_all("EfDf"), project)

        if fold is None:
            raise ValueError("No Fold chunk found in AEP file")

        self._parse_folder(fold, project.folder, project)

        for comp in project.compositions:
            chunks = self._comp_chunks.get(comp.id)
            if chunks:
                self._parse_composition(comp, chunks, project)

        # Resolve empty layer names → use source asset/comp name
        for comp in project.compositions:
            for layer in comp.layers:
                if not layer.name and layer.asset_id:
                    asset = project.assets.get(layer.asset_id)
                    if asset is not None:
                        layer.name = getattr(asset, "name", "")

        # Parse render queue
        if lrdr is not None:
            self._parse_render_queue(lrdr, project)

        return project

    # ── Render Queue ──────────────────────────────────────────────────────

    def _parse_render_queue(self, lrdr_chunk: Chunk, project: Project) -> None:
        cl = lrdr_chunk.list

        # Top-level list contains the RQ item records (lhd3 + ldat)
        item_list = cl.find_optional("list")
        if item_list is None:
            return

        item_list_cl = item_list.list
        lhd3 = item_list_cl.find_optional("lhd3")
        ldat = item_list_cl.find_optional("ldat")
        if lhd3 is None or ldat is None:
            return

        r = self._chunk_reader(lhd3)
        r.skip(10)
        count = r.read_uint(2)
        r.skip(6)
        item_size = r.read_uint(2)

        ldat_data = ldat.data
        if not isinstance(ldat_data, (bytes, bytearray)):
            return

        # LItm contains per-item timing lists and LOm output modules
        litm = cl.find_optional("LItm")
        litm_children = litm.list.children if litm is not None else []

        # Build comp name lookup
        comp_names: dict[int, str] = {}
        for comp in project.compositions:
            comp_names[comp.id] = comp.name

        # Parse each RQ item record
        # LItm has alternating: LIST list (timing) + LIST LOm (outputs)
        # for each of the `count` items
        om_lists: list[ChunkList] = []
        for c in litm_children:
            if c.name.rstrip() == "LOm":
                om_lists.append(c.list)

        for idx in range(count):
            start = idx * item_size
            if start + item_size > len(ldat_data):
                break
            item_data = ldat_data[start:start + item_size]
            rq_item = self._parse_rq_item(item_data, comp_names)
            if idx < len(om_lists):
                rq_item.output_modules = self._parse_output_modules(om_lists[idx])
            project.render_queue.append(rq_item)

    def _parse_rq_item(self, data: bytes, comp_names: dict[int, str]) -> RenderQueueItem:
        r = BinaryReader(data, 0, self.big_endian)
        item = RenderQueueItem()

        # offset 0-7: flags/version
        r.skip(8)
        # offset 8-11: composition ID
        item.comp_id = r.read_uint(4)
        item.comp_name = comp_names.get(item.comp_id, "")
        # offset 12-15: status
        item.status = r.read_uint(4)
        # offset 16-19: unknown
        r.skip(4)

        # offset 20-27: start time (num/den, in 1024-based units)
        start_num = r.read_sint(4)
        start_den = r.read_uint(4)
        # offset 28-35: duration/end (num/den)
        dur_num = r.read_sint(4)
        dur_den = r.read_uint(4)

        if start_den > 0:
            # Scale: num is in 1024-unit frames, den is fps*1024
            fps_scale = start_den / 1024.0
            item.start_frame = round(start_num / 1024.0)
            if dur_num > 0:
                item.end_frame = item.start_frame + round(dur_num / 1024.0) - 1
        # If start_den == 0, it's a full comp render (no custom range)

        # offset 36-89: reserved
        r.skip(54)

        # offset 90+: render settings name (null-terminated UTF-8)
        remaining = data[90:]
        nul = remaining.find(b"\x00")
        if nul > 0:
            item.render_settings = remaining[:nul].decode("utf-8", errors="replace")

        return item

    def _parse_output_modules(self, om_cl: ChunkList) -> list[OutputModule]:
        modules: list[OutputModule] = []
        children = om_cl.children
        i = 0
        while i < len(children):
            c = children[i]
            if c.header != "Roou":
                i += 1
                continue

            om = OutputModule()
            roou_data = c.data
            if isinstance(roou_data, (bytes, bytearray)) and len(roou_data) >= 42:
                # offset 26: format name (4-byte code, null-terminated string)
                fmt_start = 26
                fmt_end = roou_data.find(b"\x00", fmt_start, fmt_start + 20)
                if fmt_end > fmt_start:
                    fmt_code = roou_data[fmt_start:fmt_end].decode("ascii", errors="replace")
                    om.format = fmt_code
                    om.format_label = OUTPUT_FORMATS.get(fmt_code, fmt_code)

                # offset 36-37: width, offset 40-41: height
                om.width = int.from_bytes(roou_data[36:38], "big" if self.big_endian else "little")
                om.height = int.from_bytes(roou_data[40:42], "big" if self.big_endian else "little")

            # Collect associated chunks after Roou.
            # Known order: Ropt, [hdrm], [Utf8 extras], Als2, Utf8, Utf8
            i += 1
            # Skip Ropt
            if i < len(children) and children[i].header == "Ropt":
                i += 1
            # Skip any intermediate chunks (hdrm, extra Utf8) until Als2 or next Roou
            while i < len(children):
                h = children[i].header
                n = getattr(children[i], "name", "") or ""
                if n == "Als2" or h == "Roou":
                    break
                i += 1
            # Als2 → output path
            if i < len(children) and children[i].name == "Als2":
                als2 = children[i].list
                alas = als2.find_optional("alas")
                if alas is not None:
                    alas_data = alas.data
                    text = alas_data if isinstance(alas_data, str) else alas_data.decode("utf-8", errors="replace")
                    try:
                        info = json.loads(text)
                        om.output_path = info.get("fullpath", "")
                    except (json.JSONDecodeError, AttributeError):
                        pass
                i += 1
            # First Utf8 → template name
            if i < len(children) and children[i].header == "Utf8":
                name = children[i].data
                if isinstance(name, str):
                    om.template_name = name
                i += 1
            # Second Utf8 → file name template
            if i < len(children) and children[i].header == "Utf8":
                name = children[i].data
                if isinstance(name, str):
                    om.file_template = name
                i += 1

            modules.append(om)

        return modules

    # ── Folder / Items ───────────────────────────────────────────────────

    def _parse_folder(self, chunk: Chunk, folder: Folder, project: Project) -> None:
        cl = chunk.list
        for i, child in enumerate(cl.children):
            if child.name == "Item":
                self._process_item(child, folder, project)
            elif child.name == "Sfdr":
                # Sub-folder: flatten Items from nested Sfdr
                for sub in child.list.children:
                    if sub.name == "Item":
                        self._process_item(sub, folder, project)
                    elif sub.name == "Sfdr":
                        for subsub in sub.list.children:
                            if subsub.name == "Item":
                                self._process_item(subsub, folder, project)

    def _process_item(self, chunk: Chunk, folder: Folder, project: Project) -> None:
        cl = chunk.list
        idta, utf8 = cl.find_multiple(["idta", "Utf8"])
        if idta is None:
            return

        name = self._utf8_name(utf8)
        reader = self._chunk_reader(idta)
        item_type = reader.read_uint(2)
        reader.skip(14)
        item_id = reader.read_uint(4)

        if item_type == 1:
            # Folder
            sub_folder = Folder(id=item_id, name=name)
            folder.items.append(sub_folder)
            self._parse_folder(chunk, sub_folder, project)

        elif item_type == 4:
            # Composition
            comp = Composition(id=item_id, name=name)
            project.compositions.append(comp)
            project.assets[item_id] = comp
            self._comp_chunks[item_id] = cl
            folder.items.append(comp)

        elif item_type == 7:
            # Asset
            pin = cl.find_optional("Pin ")
            if pin is not None:
                asset = self._parse_asset(item_id, pin, project)
                if asset is not None:
                    folder.items.append(asset)

    # ── Assets ───────────────────────────────────────────────────────────

    def _parse_asset(self, asset_id: int, pin_chunk: Chunk,
                     project: Project) -> ImageAsset | SolidAsset | None:
        cl = pin_chunk.list
        sspc, als2, opti = cl.find_multiple(["sspc", "Als2", "opti"])
        utf8_chunks = cl.find_all("Utf8")

        if sspc is None or opti is None:
            return None

        name = "".join(self._utf8_name(u) for u in utf8_chunks)

        # Parse sspc (source parameters)
        sr = self._chunk_reader(sspc)
        sr.skip(32)
        width = sr.read_uint(2)
        sr.skip(2)
        height = sr.read_uint(2)
        sr.skip(2)
        seq_count = sr.read_uint(2)
        sr.skip(132)
        seq_start = sr.read_uint(2)
        sr.skip(2)
        seq_end = sr.read_uint(2)
        sr.skip(2)
        seq_max_len = sr.read_uint(2)

        # Parse opti (asset options)
        odr = self._chunk_reader(opti)
        opti_type = odr.read_string("utf-8", 4)
        odr.skip(2)
        odr.skip(4)

        if opti_type == "Soli":
            # Solid color asset
            color = Color()
            color.a = odr.read_float32()
            color.r = self._solid_color_val(odr.read_float32())
            color.g = self._solid_color_val(odr.read_float32())
            color.b = self._solid_color_val(odr.read_float32())
            solid_name = odr.read_nul_string("utf-8", 256)
            asset = SolidAsset(id=asset_id, name=solid_name, color=color,
                               width=width, height=height)
        else:
            # File reference asset (image, audio, etc.)
            if als2 is None:
                return None
            ref_data = json.loads(als2.list.find("alas").data)
            if not name:
                name = ref_data.get("fullpath", "").replace("\\", "/").split("/")[-1]
            full_path = ref_data.get("fullpath", "")
            seq_info = None
            if ref_data.get("target_is_folder"):
                seq_info = SequenceInfo(count=seq_count, start=seq_start,
                                        end=seq_end, max_length=seq_max_len)
            asset = ImageAsset(id=asset_id, name=name, full_path=full_path,
                               width=width, height=height, sequence_info=seq_info)

        project.assets[asset_id] = asset
        return asset

    @staticmethod
    def _solid_color_val(v: float) -> float:
        return v if v == 255 else v * 255

    # ── Composition ──────────────────────────────────────────────────────

    def _parse_composition(self, comp: Composition, cl: ChunkList,
                           project: Project) -> None:
        cdta = cl.find("cdta")
        r = self._chunk_reader(cdta)

        r.skip(4)
        time_denom = r.read_uint(4)
        time_num = r.read_uint(4)
        comp.framerate = time_num / time_denom if time_denom else 30.0

        r.skip(9)
        comp.playhead_time = r.read_uint(2)
        r.skip(2)
        ph_div = r.read_uint(2) / comp.framerate if comp.framerate else 1
        comp.playhead_time /= (ph_div or 1)

        r.skip(2)
        comp.in_time = r.read_uint(2)
        r.skip(2)
        in_div = r.read_uint(2) / comp.framerate if comp.framerate else 1
        comp.in_time /= (in_div or 1)

        r.skip(2)
        comp.out_time = r.read_uint(2)
        r.skip(2)
        out_div = r.read_uint(2) / comp.framerate if comp.framerate else 1

        r.skip(2)
        comp.duration = r.read_uint(2)
        r.skip(2)
        dur_div = r.read_uint(2) / comp.framerate if comp.framerate else 1
        comp.duration /= (dur_div or 1)

        if comp.out_time == 65535:
            comp.out_time = comp.duration
        else:
            comp.out_time /= (out_div or 1)

        r.skip(1)
        comp.color.r = r.read_uint(1)
        comp.color.g = r.read_uint(1)
        comp.color.b = r.read_uint(1)

        r.skip(85)
        comp.width = r.read_uint(2)
        comp.height = r.read_uint(2)
        r.skip(12)

        for child in cl.children:
            if child.name == "Layr":
                comp.layers.append(self._parse_layer(child))
            elif child.name == "SecL":
                comp.markers = self._parse_layer(child)

    # ── Layer ────────────────────────────────────────────────────────────

    def _parse_layer(self, chunk: Chunk) -> Layer:
        layer = Layer()
        cl = chunk.list
        ldta, utf8, tdgp = cl.find_multiple(["ldta", "Utf8", "tdgp"])

        r = self._chunk_reader(ldta)
        layer.name = self._utf8_name(utf8)
        layer.id = r.read_uint(4)
        layer.quality = r.read_uint(2)
        r.skip(2)

        time_stretch_num = r.read_sint(4)
        start_time_num = r.read_sint(4)
        start_time_den = r.read_uint(4)
        in_time_num = r.read_sint(4)
        in_time_den = r.read_uint(4)
        out_time_num = r.read_sint(4)
        out_time_den = r.read_uint(4)

        flags = r.read_flags(4)
        layer.asset_id = r.read_uint(4)
        r.skip(17)
        layer.label_color = r.read_uint(1)
        r.skip(2)
        r.skip(32)
        layer.blend_mode = r.read_uint(4)
        r.skip(4)
        layer.matte_mode = r.read_uint(4)
        r.skip(2)
        time_stretch_den = r.read_uint(2)
        r.skip(19)
        layer.layer_type = r.read_uint(1)
        layer.parent_id = r.read_uint(4)
        r.skip(24)
        layer.matte_id = r.read_uint(4)

        # Decode bit flags
        layer.is_guide = flags.get_bit(1, 1)
        layer.bicubic_sampling = flags.get_bit(1, 6)
        layer.auto_orient = flags.get_bit(2, 0)
        layer.is_adjustment = flags.get_bit(2, 1)
        layer.threedimensional = flags.get_bit(2, 2)
        layer.solo = flags.get_bit(2, 3)
        layer.is_null = flags.get_bit(2, 7)
        layer.visible = flags.get_bit(3, 0)
        layer.effects_enabled = flags.get_bit(3, 2)
        layer.motion_blur_enabled = flags.get_bit(3, 3)
        layer.locked = flags.get_bit(3, 5)
        layer.shy = flags.get_bit(3, 6)
        layer.continuously_rasterize = flags.get_bit(3, 7)

        # Time values (rational numbers)
        layer.start_time = start_time_num / start_time_den if start_time_den else 0
        layer.out_time = out_time_num / out_time_den if out_time_den else 0
        layer.in_time = in_time_num / in_time_den if in_time_den else 0
        layer.time_stretch = time_stretch_num / time_stretch_den if time_stretch_den else 1

        # Parse property tree
        if tdgp is not None:
            self._parse_property_group(tdgp.list, layer.properties,
                                       str(layer.id))

        return layer

    # ── Property Group ───────────────────────────────────────────────────

    def _parse_property_group(self, cl: ChunkList, group: PropertyGroup,
                              key_prefix: str = "") -> None:
        match_name = ""
        i = 0
        while i < len(cl.children):
            child = cl.children[i]

            if child.header == "tdmn":
                match_name = child.data

            elif child.header == "tdsb":
                # Property visibility / split flags
                fl = self._chunk_reader(child).read_flags(4)
                vis = fl.get_bit(3, 0)
                split = fl.get_bit(3, 1)
                group.split_position = split
                if split:
                    # In Layer Styles sub-groups, split=True means this is
                    # an enable/disable toggle, not a visibility flag
                    group.enabled = vis
                else:
                    group.visible = vis

            elif child.header == "tdsn":
                # Property name
                utf8 = child.list.find_optional("Utf8")
                group.name = self._utf8_name(utf8)

            elif child.name == "mkif":
                # Mask info
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
                match_name = ""

            i += 1

    @staticmethod
    def _fix_layer_styles_enabled(group: PropertyGroup) -> None:
        """Derive correct enabled state for Layer Styles and its sub-styles.

        Some sub-styles have split=True with an explicit enabled flag, while
        others have split=False (enabled stays None) but contain child
        properties indicating they are active.  Normalise both cases so every
        */enabled sub-group gets an explicit enabled bool, then derive the
        root group state from its children.
        """
        from ..models import PropertyGroup as PG
        for np in group.properties:
            if not np.match_name.endswith("/enabled"):
                continue
            v = np.value
            if not isinstance(v, PG):
                continue
            # If tdsb didn't set enabled (split was False), infer from props
            if v.enabled is None:
                v.enabled = bool(v.properties)

        # Root enabled = any sub-style is on
        group.enabled = any(
            isinstance(np.value, PG) and np.value.enabled is True
            for np in group.properties
            if np.match_name.endswith("/enabled")
        )

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

    # ── Animated Property ────────────────────────────────────────────────

    def _parse_animated_property(self, cl: ChunkList,
                                 extra_values: list) -> AnimatedProperty:
        prop = AnimatedProperty()
        tdsb, tdb4, cdat, lst, utf8, tdpi, tdps, tdli = cl.find_multiple(
            ["tdsb", "tdb4", "cdat", "list", "Utf8", "tdpi", "tdps", "tdli"])

        # Flags
        fl = self._chunk_reader(tdsb).read_flags(4)
        prop.split = fl.get_bit(3, 1)

        # tdb4: property metadata
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

        # Handle special ref types
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
            # Only read float64 values if we have enough data
            if cr.remaining() >= prop.components * 8:
                raw = cr.read_array(prop.components, cr.read_float64)
                prop.value = self._property_value(0, raw, extra_values, prop.prop_type)

        # Keyframes
        if lst is not None:
            items = self._list_values(lst)
            for idx, item_reader in enumerate(items):
                kf = self._load_keyframe(idx, item_reader, prop, extra_values,
                                         time_scale)
                prop.keyframes.append(kf)

        # Expression
        if utf8 is not None:
            prop.expression = self._utf8_name(utf8)

        return prop

    def _property_value(self, idx: int, raw: list[float],
                        extra_values: list, prop_type: int) -> Any:
        if prop_type == 1:
            return extra_values[idx] if extra_values else None
        if prop_type == 0:
            # Color: [alpha, red, green, blue]
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
            # Scalar
            kf.value = extra_values[idx] if idx < len(extra_values) else None
            if reader.remaining() >= 48:  # 16 skip + 4×8 floats
                reader.skip(16)
                kf.in_speed.append(spv(reader.read_float64()))
                kf.in_influence.append(reader.read_float64())
                kf.out_speed.append(spv(reader.read_float64()))
                kf.out_influence.append(reader.read_float64())

        elif ptype in (3, 5):
            # Multi-dimensional
            needed = prop.components * 5 * 8  # value + 4 arrays
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
            # Spatial (with bezier tangents)
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
            # Color
            if reader.remaining() >= 48:  # 16 skip + 4×8 floats
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

    # ── Animated Shape ───────────────────────────────────────────────────

    def _parse_animated_shape(self, cl: ChunkList) -> AnimatedProperty:
        omks, tdbs = cl.find_multiple(["omks", "tdbs"])
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
        shph = cl.find("shph")
        r = self._chunk_reader(shph)
        r.skip(3)
        fl = r.read_flags(1)
        shape.closed = not fl.get_bit(0, 3)
        shape.minimum.x = r.read_float32()
        shape.minimum.y = r.read_float32()
        shape.maximum.x = r.read_float32()
        shape.maximum.y = r.read_float32()

        list_chunk = cl.find("list")
        for item_reader in self._list_values(list_chunk):
            x = item_reader.read_float32()
            y = item_reader.read_float32()
            if not (math.isnan(x) or math.isnan(y)):
                shape.points.append(Vector(x, y))

        return shape

    # ── Animated Gradient ────────────────────────────────────────────────

    def _parse_animated_gradient(self, cl: ChunkList) -> AnimatedProperty:
        gcky, tdbs = cl.find_multiple(["GCky", "tdbs"])
        gradients = []
        for utf8 in gcky.list.find_all("Utf8"):
            gradients.append(self._parse_gradient(utf8.data))
        return self._parse_animated_property(tdbs.list, gradients)

    def _parse_gradient(self, xml_str: str) -> Gradient:
        root = ET.fromstring(xml_str)
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

    # ── Animated Orientation ─────────────────────────────────────────────

    def _parse_animated_orientation(self, cl: ChunkList) -> AnimatedProperty:
        otky, tdbs = cl.find_multiple(["otky", "tdbs"])
        orientations = []
        for otda in otky.list.find_all("otda"):
            r = self._chunk_reader(otda)
            orientations.append(Vector(r.read_float64(), r.read_float64(),
                                       r.read_float64()))
        return self._parse_animated_property(tdbs.list, orientations)

    # ── Animated Marker ──────────────────────────────────────────────────

    def _parse_animated_marker(self, cl: ChunkList) -> AnimatedProperty:
        mrky, tdbs = cl.find_multiple(["mrky", "tdbs"])
        markers = []
        for nmrd in mrky.list.find_all("Nmrd"):
            markers.append(self._parse_marker(nmrd))
        return self._parse_animated_property(tdbs.list, markers)

    def _parse_marker(self, chunk: Chunk) -> Marker:
        marker = Marker()
        cl = chunk.list
        nmhd = cl.find("NmHd")
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

    # ── Animated Text ────────────────────────────────────────────────────

    def _parse_animated_text(self, cl: ChunkList) -> TextProperty:
        btdk, tdbs = cl.find_multiple(["btdk", "tdbs"])
        cos_data = CosParser(btdk.data).parse()

        text_prop = TextProperty()

        # Parse fonts: cos_data["0"]["1"]["0"]
        try:
            fonts_data = self._cos_val(cos_data, [0, 1, 0])
            for font_entry in fonts_data:
                family = self._cos_val(font_entry, [0, 0, 0])
                text_prop.fonts.append(Font(family=family))
        except (KeyError, IndexError, TypeError):
            pass

        # Parse text documents: cos_data["1"]["1"]
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

        # Paragraph styles
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

        # Line styles
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

        # Character styles
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

                # Fill
                fill_enabled = self._cos_val_safe(style, 56, True)
                cs.fill_enabled = bool(fill_enabled)
                if cs.fill_enabled:
                    fill_data = self._cos_val_safe(style, 53, None)
                    if fill_data:
                        cs.fill_color = self._cos_color(fill_data, [0, 1])
                    else:
                        cs.fill_color = Color(0, 0, 0)

                # Stroke
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
        # result should be [alpha, r, g, b] with r,g,b in 0-1 range
        return Color(result[1] * 255, result[2] * 255, result[3] * 255, result[0])

    # ── Effects ──────────────────────────────────────────────────────────

    def _parse_effects(self, effect_chunks: list[Chunk],
                       project: Project) -> None:
        for chunk in effect_chunks:
            cl = chunk.list
            tdmn, sspc = cl.find_multiple(["tdmn", "sspc"])
            if tdmn is None or sspc is None:
                continue

            effect_def = EffectDefinition()
            effect_def.match_name = tdmn.data

            fnam, parT = sspc.list.find_multiple(["fnam", "parT"])
            if fnam is not None:
                utf8 = fnam.list.find_optional("Utf8")
                if utf8 is not None:
                    effect_def.name = self._utf8_name(utf8)

            project.effects[effect_def.match_name] = effect_def

            if parT is None:
                continue

            i = 0
            children = parT.list.children
            while i < len(children):
                child = children[i]
                if child.name != "tdmn":
                    i += 1
                    continue

                param = EffectParameter()
                param.match_name = child.data

                if i + 1 < len(children):
                    self._parse_effect_parameter(
                        self._chunk_reader(children[i + 1]), param)

                if (i + 2 < len(children) and
                        children[i + 2].name == "pdnm" and not param.name):
                    utf8 = children[i + 2].list.find_optional("Utf8")
                    if utf8:
                        param.name = self._utf8_name(utf8)
                    i += 3
                else:
                    i += 2

                effect_def.parameters.append(param)

    def _parse_effect_parameter(self, r: BinaryReader,
                                param: EffectParameter) -> None:
        r.skip(14)
        param.param_type = r.read_uint(2)
        param.name = r.read_nul_string("utf-8", 32)
        r.skip(8)

        t = param.param_type
        if t == 0:
            param.last_value = LayerRef()
            param.default_value = param.last_value
        elif t in (2, 3):
            param.last_value = Vector(r.read_sint(4) / 65536)
            param.default_value = Vector(0)
        elif t == 4:
            param.last_value = Vector(r.read_uint(4))
            param.default_value = Vector(r.read_uint(1))
        elif t == 5:
            a = r.read_uint(1) / 255
            rv = r.read_uint(1)
            gv = r.read_uint(1)
            bv = r.read_uint(1)
            param.last_value = Color(rv, gv, bv, a)
            r.skip(1)
            rv2 = r.read_uint(1)
            gv2 = r.read_uint(1)
            bv2 = r.read_uint(1)
            param.default_value = Color(rv2, gv2, bv2, 1.0)
        elif t == 6:
            px = r.read_sint(4) / 128
            py = r.read_sint(4) / 128
            param.last_value = Vector(px, py)
            param.default_value = Vector(0, 0)
        elif t == 7:
            param.last_value = Vector(r.read_uint(4))
            r.skip(2)
            param.default_value = Vector(r.read_uint(2))
        elif t == 10:
            param.last_value = Vector(r.read_float64())
            param.default_value = Vector(0)
        elif t == 18:
            param.last_value = Vector(r.read_float64() * 512,
                                      r.read_float64() * 512,
                                      r.read_float64() * 512)
            param.default_value = Vector(0, 0, 0)
        else:
            param.last_value = Vector(0)
            param.default_value = param.last_value

    def _parse_effect_instance(self, cl: ChunkList) -> EffectInstance:
        inst = EffectInstance()
        fnam, tdgp = cl.find_multiple(["fnam", "tdgp"])
        if fnam is not None:
            utf8 = fnam.list.find_optional("Utf8")
            if utf8:
                inst.name = self._utf8_name(utf8)
        if tdgp is not None:
            self._parse_property_group(tdgp.list, inst.parameters)
        return inst
