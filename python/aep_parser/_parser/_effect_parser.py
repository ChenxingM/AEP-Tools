"""Effect definition and instance parsing mixin."""

from __future__ import annotations

from .binary_reader import BinaryReader
from .chunk import Chunk, ChunkList
from ..models import (
    Color, EffectDefinition, EffectInstance, EffectParameter,
    LayerRef, Project, PropertyGroup, Vector,
)


class EffectParserMixin:
    """Mixin providing effect parsing methods.

    Requires the host class to provide: _chunk_reader(), _utf8_name(),
    _parse_property_group().
    """

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
