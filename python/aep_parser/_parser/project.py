"""Project parser: converts AEP/AEPX chunk tree into a structured Project model.

This corresponds to the we$3/pt$2 class in the original JS code.
"""

from __future__ import annotations

import json
import struct
from typing import Any

from .binary_reader import BinaryReader
from .chunk import Chunk, ChunkList
from ..models import (
    Color, Composition, Folder, ImageAsset, Layer, OutputModule,
    OUTPUT_FORMATS, Project, RenderQueueItem, SequenceInfo, SolidAsset, Vector,
)
from ._property_parser import PropertyParserMixin
from ._effect_parser import EffectParserMixin

_NAME_PLACEHOLDER = "-_0_/-"

# Mask mode constants
MASK_NONE = 0
MASK_ADD = 1
MASK_SUBTRACT = 2
MASK_INTERSECT = 3
MASK_DARKEN = 4
MASK_LIGHTEN = 5
MASK_DIFFERENCE = 6


class ProjectParser(PropertyParserMixin, EffectParserMixin):
    """Converts a parsed RIFF chunk tree into a Project model."""

    def __init__(self, big_endian: bool = True):
        self.big_endian = big_endian
        self._comp_chunks: dict[int, ChunkList] = {}
        self._layer_prop_key_index: dict[str, int] = {}
        self._current_layer_3d: bool = False

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

    # Top-level

    def parse_project(self, root_chunk: Chunk) -> Project:
        project = Project()
        cl = root_chunk.list
        fold, efdg, lrdr = cl.find_multiple(["Fold", "EfdG", "LRdr"])

        self._parse_project_settings(cl, project)

        if efdg is not None:
            self._parse_effects(efdg.list.find_all("EfDf"), project)

        if fold is None:
            raise ValueError("No Fold chunk found in AEP file")

        self._parse_folder(fold, project.folder, project)

        for comp in project.compositions:
            chunks = self._comp_chunks.get(comp.id)
            if chunks:
                self._parse_composition(comp, chunks, project)

        for comp in project.compositions:
            for layer in comp.layers:
                if not layer.name and layer.asset_id:
                    asset = project.assets.get(layer.asset_id)
                    if asset is not None:
                        layer.name = getattr(asset, "name", "")

        if lrdr is not None:
            self._parse_render_queue(lrdr, project)

        return project

    def _parse_project_settings(self, cl: ChunkList, project: Project) -> None:
        """Parse nnhd, acer, adfr, dwga and other project-level chunks."""
        _BITS_MAP = {0: 8, 1: 16, 2: 32}

        nnhd = cl.find_optional("nnhd")
        if nnhd is not None and isinstance(nnhd.data, (bytes, bytearray)):
            r = self._chunk_reader(nnhd)
            r.skip(8)
            flags_byte = r.read_uint(1)
            project.time_display_type = flags_byte & 0x7F
            r.skip(5)
            project.project_frame_rate = r.read_uint(2)
            r.skip(4)
            r.skip(1)  # frames_count_type
            r.skip(3)
            project.bits_per_channel = _BITS_MAP.get(r.read_uint(1), 8)
            project.transparency_grid_thumbnails = bool(r.read_uint(1))
            r.skip(5)
            lin_byte = r.read_uint(1)
            project.linearize_working_space = bool((lin_byte >> 5) & 1)

        acer = cl.find_optional("acer")
        if acer is not None and isinstance(acer.data, (bytes, bytearray)) and len(acer.data) >= 1:
            project.compensate_scene_referred = bool(acer.data[0])

        adfr = cl.find_optional("adfr")
        if adfr is not None and isinstance(adfr.data, (bytes, bytearray)) and len(adfr.data) >= 8:
            project.audio_sample_rate = struct.unpack(">d", adfr.data[:8])[0]

        dwga = cl.find_optional("dwga")
        if dwga is not None and isinstance(dwga.data, (bytes, bytearray)) and len(dwga.data) >= 1:
            project.working_gamma = 2.4 if dwga.data[0] else 2.2

        exen = cl.find_optional("ExEn")
        if exen is not None and exen.list is not None:
            utf8 = exen.list.find_optional("Utf8")
            if utf8 is not None and isinstance(utf8.data, str):
                project.expression_engine = utf8.data

        _GPU_UUIDS = {
            "7ee0ab59-822d-44cc-ac10-16279d041016": "CUDA",
            "f33089e2-1ede-47c1-8a9e-b232bb1cc1a4": "Software",
        }
        gpug = cl.find_optional("gpuG")
        if gpug is not None and gpug.list is not None:
            utf8 = gpug.list.find_optional("Utf8")
            if utf8 is not None and isinstance(utf8.data, str):
                project.gpu_accel_type = _GPU_UUIDS.get(utf8.data, utf8.data)

    # Render Queue

    def _parse_render_queue(self, lrdr_chunk: Chunk, project: Project) -> None:
        cl = lrdr_chunk.list

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

        litm = cl.find_optional("LItm")
        litm_children = litm.list.children if litm is not None else []

        comp_names: dict[int, str] = {}
        for comp in project.compositions:
            comp_names[comp.id] = comp.name

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

        r.skip(8)
        item.comp_id = r.read_uint(4)
        item.comp_name = comp_names.get(item.comp_id, "")
        item.status = r.read_uint(4)
        r.skip(4)

        start_num = r.read_sint(4)
        start_den = r.read_uint(4)
        dur_num = r.read_sint(4)
        dur_den = r.read_uint(4)

        if start_den > 0:
            fps_scale = start_den / 1024.0
            item.start_frame = round(start_num / 1024.0)
            if dur_num > 0:
                item.end_frame = item.start_frame + round(dur_num / 1024.0) - 1

        r.skip(54)

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
                fmt_start = 26
                fmt_end = roou_data.find(b"\x00", fmt_start, fmt_start + 20)
                if fmt_end > fmt_start:
                    fmt_code = roou_data[fmt_start:fmt_end].decode("ascii", errors="replace")
                    om.format = fmt_code
                    om.format_label = OUTPUT_FORMATS.get(fmt_code, fmt_code)

                om.width = int.from_bytes(roou_data[36:38], "big" if self.big_endian else "little")
                om.height = int.from_bytes(roou_data[40:42], "big" if self.big_endian else "little")

            i += 1
            if i < len(children) and children[i].header == "Ropt":
                i += 1
            while i < len(children):
                h = children[i].header
                n = getattr(children[i], "name", "") or ""
                if n == "Als2" or h == "Roou":
                    break
                i += 1
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
            if i < len(children) and children[i].header == "Utf8":
                name = children[i].data
                if isinstance(name, str):
                    om.template_name = name
                i += 1
            if i < len(children) and children[i].header == "Utf8":
                name = children[i].data
                if isinstance(name, str):
                    om.file_template = name
                i += 1

            modules.append(om)

        return modules

    # Folder / Items

    def _parse_folder(self, chunk: Chunk, folder: Folder, project: Project) -> None:
        cl = chunk.list
        for i, child in enumerate(cl.children):
            if child.name == "Item":
                self._process_item(child, folder, project)
            elif child.name == "Sfdr":
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
            sub_folder = Folder(id=item_id, name=name)
            folder.items.append(sub_folder)
            self._parse_folder(chunk, sub_folder, project)

        elif item_type == 4:
            comp = Composition(id=item_id, name=name)
            project.compositions.append(comp)
            project.assets[item_id] = comp
            self._comp_chunks[item_id] = cl
            folder.items.append(comp)

        elif item_type == 7:
            pin = cl.find_optional("Pin ")
            if pin is not None:
                asset = self._parse_asset(item_id, pin, project)
                if asset is not None:
                    folder.items.append(asset)

    # Assets

    def _parse_asset(self, asset_id: int, pin_chunk: Chunk,
                     project: Project) -> ImageAsset | SolidAsset | None:
        cl = pin_chunk.list
        sspc, als2, opti = cl.find_multiple(["sspc", "Als2", "opti"])
        utf8_chunks = cl.find_all("Utf8")

        if sspc is None or opti is None:
            return None

        name = "".join(self._utf8_name(u) for u in utf8_chunks)

        sr = self._chunk_reader(sspc)
        sr.skip(32)
        width = sr.read_uint(2)
        sr.skip(2)
        height = sr.read_uint(2)

        sspc_data = sspc.data if isinstance(sspc.data, (bytes, bytearray)) else b""
        dur_dividend = dur_divisor = 0
        frame_rate = 0.0
        alpha_mode = 3
        pixel_aspect = 1.0
        loop_count = 1
        footage_missing = False
        seq_start = seq_end = seq_max_len = 0
        if len(sspc_data) >= 62:
            dur_dividend = struct.unpack(">I", sspc_data[38:42])[0]
            dur_divisor = struct.unpack(">I", sspc_data[42:46])[0]
            fr_base = struct.unpack(">I", sspc_data[56:60])[0]
            fr_frac = struct.unpack(">H", sspc_data[60:62])[0]
            frame_rate = fr_base + fr_frac / 65536.0
        if len(sspc_data) >= 74:
            alpha_mode = sspc_data[73]
        if len(sspc_data) >= 116:
            footage_missing = bool(sspc_data[115])
        if len(sspc_data) >= 130:
            loop_count = sspc_data[129]
        if len(sspc_data) >= 144:
            pr_w = struct.unpack(">I", sspc_data[136:140])[0]
            pr_h = struct.unpack(">I", sspc_data[140:144])[0]
            if pr_h:
                pixel_aspect = pr_w / pr_h
        if len(sspc_data) >= 184:
            seq_start = struct.unpack(">I", sspc_data[172:176])[0]
            seq_end = struct.unpack(">I", sspc_data[176:180])[0]
            seq_max_len = struct.unpack(">I", sspc_data[180:184])[0]

        odr = self._chunk_reader(opti)
        opti_type = odr.read_string("utf-8", 4)
        odr.skip(2)
        odr.skip(4)

        if opti_type == "Soli":
            color = Color()
            color.a = odr.read_float32()
            color.r = self._solid_color_val(odr.read_float32())
            color.g = self._solid_color_val(odr.read_float32())
            color.b = self._solid_color_val(odr.read_float32())
            solid_name = odr.read_nul_string("utf-8", 256)
            asset = SolidAsset(id=asset_id, name=solid_name, color=color,
                               width=width, height=height)
        else:
            if als2 is None:
                return None
            alas = als2.list.find_optional("alas")
            if alas is None:
                return None
            try:
                ref_data = json.loads(alas.data)
            except (json.JSONDecodeError, TypeError):
                return None
            if not name:
                name = ref_data.get("fullpath", "").replace("\\", "/").split("/")[-1]
            full_path = ref_data.get("fullpath", "")
            seq_info = None
            if ref_data.get("target_is_folder"):
                count = (seq_end - seq_start + 1) if seq_end >= seq_start else 0
                seq_info = SequenceInfo(count=count, start=seq_start,
                                        end=seq_end, max_length=seq_max_len)
            duration = dur_dividend / dur_divisor if dur_divisor else 0.0
            asset = ImageAsset(
                id=asset_id, name=name, full_path=full_path,
                width=width, height=height,
                frame_rate=frame_rate, duration=duration,
                pixel_aspect=pixel_aspect, alpha_mode=alpha_mode,
                loop=loop_count, missing=footage_missing,
                sequence_info=seq_info,
            )

        project.assets[asset_id] = asset
        return asset

    @staticmethod
    def _solid_color_val(v: float) -> float:
        return v if v == 255 else v * 255

    # Composition

    def _parse_composition(self, comp: Composition, cl: ChunkList,
                           project: Project) -> None:
        """Parse cdta using fixed offsets per Kaitai spec.

        cdta layout (big-endian):
            0-3:   resolution_factor (u2be[2])
            5-6:   time_scale_integer (u2be)
            7:     time_scale_fractional (u1)
            20-23: time_dividend (s4be)
            24-27: time_divisor (u4be)
            28-31: in_point_dividend (u4be)
            32-35: in_point_divisor (u4be)
            36-39: out_point_dividend (u4be)
            40-43: out_point_divisor (u4be)
            44-47: duration_dividend (u4be)
            48-51: duration_divisor (u4be)
            52-54: bg_color (u1[3])
            138:   comp_flags_1
            139:   comp_flags_2
            140-143: width, height (u2be each)
            144-151: pixel_ratio_width, pixel_ratio_height (u4be each)
            156-157: frame_rate_integer (u2be)
            158-159: frame_rate_fractional (u2be)
            164-167: display_start_time_dividend (s4be)
            168-171: display_start_time_divisor (u4be)
            174-175: shutter_angle (u2be)
            180-183: shutter_phase (s4be)
            196-199: motion_blur_adaptive_sample_limit (s4be)
            200-203: motion_blur_samples_per_frame (s4be)
        """
        cdta = cl.find_optional("cdta")
        if cdta is None:
            return
        d = cdta.data
        if not isinstance(d, (bytes, bytearray)):
            return
        fmt = ">" if self.big_endian else "<"

        # Frame rate at offset 156-159
        if len(d) >= 160:
            fr_int = struct.unpack_from(f"{fmt}H", d, 156)[0]
            fr_frac = struct.unpack_from(f"{fmt}H", d, 158)[0]
            comp.framerate = fr_int + fr_frac / 65536.0 if fr_int else 30.0
        else:
            comp.framerate = 30.0

        # Current time (playhead) at offset 20-27
        if len(d) >= 28:
            time_div = struct.unpack_from(f"{fmt}i", d, 20)[0]
            time_dvs = struct.unpack_from(f"{fmt}I", d, 24)[0]
            comp.playhead_time = time_div / time_dvs if time_dvs else 0

        # Work area in point at offset 28-35
        if len(d) >= 36:
            in_div = struct.unpack_from(f"{fmt}I", d, 28)[0]
            in_dvs = struct.unpack_from(f"{fmt}I", d, 32)[0]
            comp.in_time = in_div / in_dvs if in_dvs else 0

        # Work area out point at offset 36-43
        out_dividend = 0xFFFFFFFF
        out_divisor = 1
        if len(d) >= 44:
            out_dividend = struct.unpack_from(f"{fmt}I", d, 36)[0]
            out_divisor = struct.unpack_from(f"{fmt}I", d, 40)[0]

        # Duration at offset 44-51
        if len(d) >= 52:
            dur_div = struct.unpack_from(f"{fmt}I", d, 44)[0]
            dur_dvs = struct.unpack_from(f"{fmt}I", d, 48)[0]
            comp.duration = dur_div / dur_dvs if dur_dvs else 0

        # Out time: 0xFFFFFFFF means use duration
        if out_dividend == 0xFFFFFFFF:
            comp.out_time = comp.duration
        else:
            comp.out_time = out_dividend / out_divisor if out_divisor else 0

        # Background color at offset 52-54
        if len(d) >= 55:
            comp.color.r = d[52]
            comp.color.g = d[53]
            comp.color.b = d[54]

        # Flags at offset 138-139
        if len(d) >= 140:
            comp.draft3d = bool(d[138] & 0x80)
            comp.preserve_nested_resolution = bool(d[139] & 0x80)
            comp.preserve_nested_frame_rate = bool(d[139] & 0x20)
            comp.frame_blending = bool(d[139] & 0x10)
            comp.motion_blur = bool(d[139] & 0x08)
            comp.hide_shy_layers = bool(d[139] & 0x01)

        # Dimensions at offset 140-143
        if len(d) >= 144:
            comp.width = struct.unpack_from(f"{fmt}H", d, 140)[0]
            comp.height = struct.unpack_from(f"{fmt}H", d, 142)[0]

        # Pixel aspect at offset 144-151
        if len(d) >= 152:
            pixel_w = struct.unpack_from(f"{fmt}I", d, 144)[0]
            pixel_h = struct.unpack_from(f"{fmt}I", d, 148)[0]
            if pixel_h:
                comp.pixel_aspect = pixel_w / pixel_h

        # Display start time at offset 164-171
        if len(d) >= 172:
            dst_dividend = struct.unpack_from(f"{fmt}i", d, 164)[0]
            dst_divisor = struct.unpack_from(f"{fmt}I", d, 168)[0]
            if dst_divisor:
                comp.display_start_time = dst_dividend / dst_divisor

        # Shutter angle at offset 174
        if len(d) >= 176:
            comp.shutter_angle = struct.unpack_from(f"{fmt}H", d, 174)[0]

        # Shutter phase at offset 180
        if len(d) >= 184:
            comp.shutter_phase = struct.unpack_from(f"{fmt}i", d, 180)[0]

        # Motion blur samples at offset 196-203
        if len(d) >= 204:
            comp.motion_blur_adaptive_sample_limit = struct.unpack_from(
                f"{fmt}i", d, 196)[0]
            comp.motion_blur_samples_per_frame = struct.unpack_from(
                f"{fmt}i", d, 200)[0]

        cdrp = cl.find_optional("cdrp")
        if cdrp is not None and isinstance(cdrp.data, (bytes, bytearray)) and len(cdrp.data) >= 1:
            comp.drop_frame = bool(cdrp.data[0])

        for child in cl.children:
            if child.name == "Layr":
                comp.layers.append(self._parse_layer(child))
            elif child.name == "SecL":
                comp.markers = self._parse_layer(child)

    # Layer

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
        r.skip(3)
        layer.blend_mode = r.read_uint(1)
        r.skip(3)
        layer.preserve_transparency = bool(r.read_uint(1))
        r.skip(3)
        layer.matte_mode = r.read_uint(1)
        time_stretch_den = r.read_uint(4)
        r.skip(19)
        layer.layer_type = r.read_uint(1)
        layer.parent_id = r.read_uint(4)
        r.skip(3)
        layer.light_type = r.read_uint(1)
        r.skip(20)
        layer.matte_id = r.read_uint(4)

        layer.is_guide = flags.get_bit(1, 1)
        layer.frame_blending_type = 1 if flags.get_bit(1, 2) else 0
        layer.environment_layer = flags.get_bit(1, 5)
        layer.bicubic_sampling = flags.get_bit(1, 6)
        auto_along_path = flags.get_bit(2, 0)
        layer.is_adjustment = flags.get_bit(2, 1)
        layer.threedimensional = flags.get_bit(2, 2)
        layer.solo = flags.get_bit(2, 3)
        auto_camera_poi = flags.get_bit(2, 5)
        layer.is_null = flags.get_bit(2, 7)
        layer.visible = flags.get_bit(3, 0)
        layer.audio_enabled = flags.get_bit(3, 1)
        layer.effects_enabled = flags.get_bit(3, 2)
        layer.motion_blur_enabled = flags.get_bit(3, 3)
        layer.frame_blending = flags.get_bit(3, 4)
        layer.locked = flags.get_bit(3, 5)
        layer.shy = flags.get_bit(3, 6)
        layer.collapse_transformation = flags.get_bit(3, 7)
        layer.continuously_rasterize = flags.get_bit(3, 7)
        chars_toward_cam = (flags._data[1] >> 3) & 0x03
        if chars_toward_cam == 3:
            layer.auto_orient = 3
        elif auto_camera_poi and layer.threedimensional:
            layer.auto_orient = 2
        elif auto_along_path:
            layer.auto_orient = 1
        else:
            layer.auto_orient = 0

        layer.start_time = start_time_num / start_time_den if start_time_den else 0
        layer.out_time = out_time_num / out_time_den if out_time_den else 0
        layer.in_time = in_time_num / in_time_den if in_time_den else 0
        layer.time_stretch = time_stretch_num / time_stretch_den if time_stretch_den else 1

        if tdgp is not None:
            self._current_layer_3d = layer.threedimensional
            self._parse_property_group(tdgp.list, layer.properties,
                                       str(layer.id))
            self._current_layer_3d = False

        return layer
