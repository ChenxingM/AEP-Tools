"""Property wrappers mirroring AE scripting Property / PropertyGroup objects."""

from __future__ import annotations

from typing import Any, Iterator

from aep_parser.models import (
    AnimatedProperty,
    BezierShape,
    Color,
    Gradient,
    Keyframe,
    LayerRef,
    Marker,
    NamedProperty,
    PropertyGroup as PGModel,
    TextDocument,
    TextProperty as TextPropertyModel,
    Vector,
)

from ._constants import (
    DISPLAY_NAMES,
    KeyframeInterpolationType,
    MATCH_NAMES,
    PropertyValueType,
)


# Value conversion 


def _convert_value(val: Any) -> Any:
    """Convert model values to plain Python types."""
    if val is None:
        return None
    if isinstance(val, Vector):
        if val.z is not None:
            return [val.x, val.y, val.z]
        return [val.x, val.y]
    if isinstance(val, Color):
        return [val.r, val.g, val.b, val.a]
    if isinstance(val, LayerRef):
        return val.layer_id
    if isinstance(val, BezierShape):
        return val
    if isinstance(val, Gradient):
        return val
    if isinstance(val, TextDocument):
        return val
    if isinstance(val, Marker):
        return val
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, list):
        return [_convert_value(v) for v in val]
    return val


def _lerp_values(a: Any, b: Any, t: float) -> Any:
    """Linear interpolation between two converted values."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * t
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [_lerp_values(ai, bi, t) for ai, bi in zip(a, b)]
    return a


# KeyframeValue


class KeyframeValue:
    """Represents a single keyframe."""

    __slots__ = ("index", "time", "value")

    def __init__(self, index: int, time: float, value: Any) -> None:
        self.index = index
        self.time = time
        self.value = value

    def __repr__(self) -> str:
        return f"KeyframeValue(index={self.index}, time={self.time}, value={self.value})"


# Property


class Property:
    """Wraps an AnimatedProperty model, providing AE-scripting-style access."""

    def __init__(self, model: AnimatedProperty, match_name: str = "",
                 display_name: str = "") -> None:
        self._model = model
        self._match_name = match_name
        self._display_name = display_name or MATCH_NAMES.get(match_name, match_name)
        self._layer_ref: Any = None  # set by Layer/PropertyGroup for write support
        self._match_path: list[str] = []

    @property
    def name(self) -> str:
        return self._display_name

    @property
    def match_name(self) -> str:
        return self._match_name

    @property
    def value(self) -> Any:
        """Static value or value at first keyframe."""
        if self._model.value is not None:
            return _convert_value(self._model.value)
        if self._model.keyframes:
            return _convert_value(self._model.keyframes[0].value)
        return None

    @value.setter
    def value(self, new_val: Any) -> None:
        """Set the static property value.

        Accepts a float or list of floats. Updates both the in-memory model
        and the chunk tree (if opened from a .aep file).
        """
        # Update model
        self._model.value = _to_model_value(new_val)
        # Update chunk tree
        _sync_property_to_chunk(self)

    @property
    def num_keys(self) -> int:
        return len(self._model.keyframes)

    @property
    def is_time_varying(self) -> bool:
        return self._model.animated and len(self._model.keyframes) > 1

    @property
    def expression(self) -> str | None:
        return self._model.expression

    @property
    def expression_enabled(self) -> bool:
        return self._model.expression is not None

    @property
    def dimensions_separated(self) -> bool:
        return self._model.split

    @property
    def is_spatial(self) -> bool:
        return self._model.prop_type == PropertyValueType.SPATIAL

    @property
    def property_value_type(self) -> PropertyValueType:
        return PropertyValueType(self._model.prop_type)

    @property
    def keys(self) -> list[KeyframeValue]:
        """All keyframes as KeyframeValue objects (1-based index)."""
        return [
            KeyframeValue(i + 1, kf.time, _convert_value(kf.value))
            for i, kf in enumerate(self._model.keyframes)
        ]

    def _kf(self, index: int) -> Keyframe:
        """Get raw Keyframe by 1-based index."""
        if index < 1 or index > len(self._model.keyframes):
            raise IndexError(f"Keyframe index {index} out of range "
                             f"(1-{len(self._model.keyframes)})")
        return self._model.keyframes[index - 1]

    def key(self, index: int) -> KeyframeValue:
        """Return KeyframeValue at 1-based index."""
        kf = self._kf(index)
        return KeyframeValue(index, kf.time, _convert_value(kf.value))

    def key_value(self, index: int) -> Any:
        return _convert_value(self._kf(index).value)

    def key_time(self, index: int) -> float:
        return self._kf(index).time

    def key_in_temporal_ease(self, index: int) -> list[dict]:
        kf = self._kf(index)
        result = []
        for i in range(len(kf.in_speed)):
            result.append({
                "speed": kf.in_speed[i],
                "influence": kf.in_influence[i] if i < len(kf.in_influence) else 0.0,
            })
        return result

    def key_out_temporal_ease(self, index: int) -> list[dict]:
        kf = self._kf(index)
        result = []
        for i in range(len(kf.out_speed)):
            result.append({
                "speed": kf.out_speed[i],
                "influence": kf.out_influence[i] if i < len(kf.out_influence) else 0.0,
            })
        return result

    def key_in_spatial_tangent(self, index: int) -> list[float] | None:
        kf = self._kf(index)
        if kf.in_tangent.x == 0 and kf.in_tangent.y == 0:
            return None
        return _convert_value(kf.in_tangent)

    def key_out_spatial_tangent(self, index: int) -> list[float] | None:
        kf = self._kf(index)
        if kf.out_tangent.x == 0 and kf.out_tangent.y == 0:
            return None
        return _convert_value(kf.out_tangent)

    def key_in_interpolation_type(self, index: int) -> KeyframeInterpolationType:
        return KeyframeInterpolationType(self._kf(index).transition_type)

    def key_out_interpolation_type(self, index: int) -> KeyframeInterpolationType:
        kf = self._kf(index)
        return KeyframeInterpolationType(kf.transition_type)

    def key_roving(self, index: int) -> bool:
        return self._kf(index).roving

    def nearest_key_index(self, t: float) -> int:
        """Return 1-based index of keyframe nearest to time *t*."""
        kfs = self._model.keyframes
        if not kfs:
            raise ValueError("Property has no keyframes")
        best_i = 0
        best_dist = abs(kfs[0].time - t)
        for i in range(1, len(kfs)):
            dist = abs(kfs[i].time - t)
            if dist < best_dist:
                best_dist = dist
                best_i = i
        return best_i + 1

    def value_at_time(self, t: float) -> Any:
        """Evaluate property at time *t* using linear / hold interpolation."""
        kfs = self._model.keyframes
        if not kfs:
            return self.value

        # Before first keyframe
        if t <= kfs[0].time:
            return _convert_value(kfs[0].value)

        # After last keyframe
        if t >= kfs[-1].time:
            return _convert_value(kfs[-1].value)

        # Find surrounding keyframes
        for i in range(len(kfs) - 1):
            if kfs[i].time <= t <= kfs[i + 1].time:
                # Hold interpolation: return value at current keyframe
                if kfs[i].transition_type == KeyframeInterpolationType.HOLD:
                    return _convert_value(kfs[i].value)
                # Linear (and bezier treated as linear for now)
                span = kfs[i + 1].time - kfs[i].time
                frac = (t - kfs[i].time) / span if span > 0 else 0.0
                a = _convert_value(kfs[i].value)
                b = _convert_value(kfs[i + 1].value)
                return _lerp_values(a, b, frac)

        return _convert_value(kfs[-1].value)

    # Write methods (AE scripting style)

    def _sync_keyframe_to_chunk(self, method_name: str, key_index: int,
                                **kwargs) -> bool:
        """Call a writer method on the chunk tree if write context exists."""
        layer = self._layer_ref
        if layer is None or not self._match_path:
            return False
        comp = getattr(layer, '_containing_comp', None)
        if comp is None:
            return False
        project = getattr(comp, '_project', None)
        if project is None or project._chunk_tree is None:
            return False
        method = getattr(project, method_name, None)
        if method is None:
            return False
        return method(comp.id, layer._model.id, self._match_path,
                      key_index, **kwargs)

    def set_value_at_key(self, key_index: int, new_value: Any) -> None:
        """Set the value of a keyframe (1-based index).

        Mirrors AE scripting ``property.setValueAtKey(keyIndex, value)``.
        """
        kf = self._kf(key_index)
        kf.value = _to_model_value(new_value)
        if isinstance(new_value, (int, float)):
            floats = [float(new_value)]
        elif isinstance(new_value, list):
            floats = [float(v) for v in new_value]
        else:
            floats = new_value
        self._sync_keyframe_to_chunk(
            "change_keyframe_value", key_index, new_value=floats)

    def set_interpolation_type_at_key(self, key_index: int,
                                      in_type: KeyframeInterpolationType,
                                      out_type: KeyframeInterpolationType | None = None,
                                      ) -> None:
        """Set interpolation type at a keyframe.

        Mirrors AE scripting
        ``property.setInterpolationTypeAtKey(keyIndex, inType, outType)``.

        In AEP binary, each keyframe stores one transition_type that controls
        the **outgoing** curve. So:
        - *out_type* → sets this keyframe's transition_type
        - *in_type* → sets the previous keyframe's transition_type (key_index - 1)

        If *out_type* is None, it defaults to *in_type* (same as AE behavior
        when only one type is specified).
        """
        if out_type is None:
            out_type = in_type

        # Set out interpolation on this keyframe
        kf = self._kf(key_index)
        kf.transition_type = int(out_type)
        self._sync_keyframe_to_chunk(
            "change_keyframe_interpolation", key_index,
            transition_type=int(out_type))

        # Set in interpolation on the previous keyframe
        if key_index > 1:
            prev_kf = self._kf(key_index - 1)
            prev_kf.transition_type = int(in_type)
            self._sync_keyframe_to_chunk(
                "change_keyframe_interpolation", key_index - 1,
                transition_type=int(in_type))

    def set_temporal_ease_at_key(self, key_index: int,
                                 in_ease: list[dict] | None = None,
                                 out_ease: list[dict] | None = None) -> None:
        """Set temporal ease at a keyframe.

        Mirrors AE scripting
        ``property.setTemporalEaseAtKey(keyIndex, inEase, outEase)``.

        Each ease entry is ``{"speed": float, "influence": float}``.
        """
        kf = self._kf(key_index)
        in_speed = in_influence = out_speed = out_influence = None
        if in_ease is not None:
            in_speed = [e.get("speed", 0.0) for e in in_ease]
            in_influence = [e.get("influence", 0.0) for e in in_ease]
            kf.in_speed = in_speed[:]
            kf.in_influence = in_influence[:]
        if out_ease is not None:
            out_speed = [e.get("speed", 0.0) for e in out_ease]
            out_influence = [e.get("influence", 0.0) for e in out_ease]
            kf.out_speed = out_speed[:]
            kf.out_influence = out_influence[:]
        self._sync_keyframe_to_chunk(
            "change_keyframe_ease", key_index,
            in_speed=in_speed, in_influence=in_influence,
            out_speed=out_speed, out_influence=out_influence)

    def set_value_at_time(self, time: float, new_value: Any) -> None:
        """Set a keyframe's value by its time.

        Finds the nearest keyframe to *time* and updates its value.
        Mirrors AE scripting ``property.setValueAtTime(time, value)``.
        """
        idx = self.nearest_key_index(time)
        self.set_value_at_key(idx, new_value)

    def __repr__(self) -> str:
        return f"Property({self._display_name!r}, num_keys={self.num_keys})"


# PropertyGroup


class PropertyGroup:
    """Wraps a PropertyGroup model, providing AE-scripting-style access.

    Supports ``group("name")``, ``group[name]``, ``group(index)`` (1-based).
    """

    def __init__(self, model: PGModel, match_name: str = "",
                 display_name: str = "") -> None:
        self._model = model
        self._match_name = match_name
        self._display_name = display_name or MATCH_NAMES.get(match_name, match_name)
        self._children: list[tuple[str, str, Any]] | None = None  # (match, display, wrapped)
        self._layer_ref: Any = None  # set by Layer for write support
        self._match_path: list[str] = []

    @property
    def name(self) -> str:
        return self._model.name or self._display_name

    @property
    def match_name(self) -> str:
        return self._match_name

    @property
    def enabled(self) -> bool | None:
        return self._model.enabled

    def _ensure_children(self) -> list[tuple[str, str, Any]]:
        if self._children is not None:
            return self._children
        self._children = []
        for np in self._model.properties:
            wrapped = _wrap_named_property(np)
            mn = np.match_name
            if isinstance(wrapped, PropertyGroup):
                dn = wrapped.name
                wrapped._layer_ref = self._layer_ref
                wrapped._match_path = self._match_path + [mn]
            elif isinstance(wrapped, Property):
                dn = wrapped.name
                wrapped._layer_ref = self._layer_ref
                wrapped._match_path = self._match_path + [mn]
            else:
                dn = MATCH_NAMES.get(mn, mn)
            self._children.append((mn, dn, wrapped))
        return self._children

    @property
    def num_properties(self) -> int:
        return len(self._ensure_children())

    def property(self, name_or_index: str | int) -> Any:
        """Lookup by 1-based index or by name (match_name, display name, or model name)."""
        children = self._ensure_children()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(children):
                return children[idx][2]
            return None
        return _find_property_by_name(children, name_or_index)

    def __call__(self, name_or_index: str | int) -> Any:
        result = self.property(name_or_index)
        if result is None:
            raise KeyError(f"Property {name_or_index!r} not found in {self.name!r}")
        return result

    def __getitem__(self, name_or_index: str | int) -> Any:
        return self.__call__(name_or_index)

    def __len__(self) -> int:
        return self.num_properties

    def __iter__(self) -> Iterator:
        for _, _, wrapped in self._ensure_children():
            yield wrapped

    def __repr__(self) -> str:
        return f"PropertyGroup({self.name!r}, num_properties={self.num_properties})"


# MarkerValue / MarkerProperty


class MarkerValue:
    """Represents a single composition or layer marker."""

    __slots__ = ("comment", "duration", "label", "time")

    def __init__(self, comment: str, duration: float, label: int, time: float) -> None:
        self.comment = comment
        self.duration = duration
        self.label = label
        self.time = time

    def __repr__(self) -> str:
        return f"MarkerValue({self.comment!r}, time={self.time})"


class MarkerProperty:
    """Wraps a marker AnimatedProperty from a markers Layer."""

    def __init__(self, model: AnimatedProperty) -> None:
        self._model = model

    @property
    def num_keys(self) -> int:
        return len(self._model.keyframes)

    def key_value(self, index: int) -> MarkerValue:
        """Return MarkerValue at 1-based index."""
        if index < 1 or index > len(self._model.keyframes):
            raise IndexError(f"Marker index {index} out of range "
                             f"(1-{len(self._model.keyframes)})")
        kf = self._model.keyframes[index - 1]
        m = kf.value
        if isinstance(m, Marker):
            return MarkerValue(m.name, m.duration, m.label_color, kf.time)
        return MarkerValue(str(m) if m else "", 0.0, 0, kf.time)

    def key_time(self, index: int) -> float:
        if index < 1 or index > len(self._model.keyframes):
            raise IndexError(f"Marker index {index} out of range "
                             f"(1-{len(self._model.keyframes)})")
        return self._model.keyframes[index - 1].time

    def nearest_key_index(self, t: float) -> int:
        kfs = self._model.keyframes
        if not kfs:
            raise ValueError("No markers")
        best_i = 0
        best_dist = abs(kfs[0].time - t)
        for i in range(1, len(kfs)):
            dist = abs(kfs[i].time - t)
            if dist < best_dist:
                best_dist = dist
                best_i = i
        return best_i + 1

    def __repr__(self) -> str:
        return f"MarkerProperty(num_keys={self.num_keys})"


# TextSourceProperty


class TextSourceProperty:
    """Wraps a TextProperty model (source text with fonts and keyframes)."""

    def __init__(self, model: TextPropertyModel) -> None:
        self._model = model

    @property
    def value(self) -> TextDocument | None:
        """Current TextDocument (static value or first keyframe)."""
        doc_prop = self._model.documents
        if doc_prop.value is not None and isinstance(doc_prop.value, TextDocument):
            return doc_prop.value
        if doc_prop.keyframes:
            v = doc_prop.keyframes[0].value
            if isinstance(v, TextDocument):
                return v
        return None

    @property
    def text(self) -> str:
        doc = self.value
        return doc.text if doc else ""

    @property
    def fonts(self) -> list:
        return [f.family for f in self._model.fonts]

    @property
    def num_keys(self) -> int:
        return len(self._model.documents.keyframes)

    def key_value(self, index: int) -> TextDocument | None:
        kfs = self._model.documents.keyframes
        if index < 1 or index > len(kfs):
            raise IndexError(f"Text keyframe index {index} out of range (1-{len(kfs)})")
        v = kfs[index - 1].value
        return v if isinstance(v, TextDocument) else None

    def key_time(self, index: int) -> float:
        kfs = self._model.documents.keyframes
        if index < 1 or index > len(kfs):
            raise IndexError(f"Text keyframe index {index} out of range (1-{len(kfs)})")
        return kfs[index - 1].time

    def __repr__(self) -> str:
        return f"TextSourceProperty(text={self.text!r})"


# Helpers


def _wrap_named_property(np: NamedProperty) -> Any:
    """Wrap a NamedProperty.value into the appropriate wrapper class."""
    val = np.value
    mn = np.match_name
    if isinstance(val, AnimatedProperty):
        return Property(val, match_name=mn)
    if isinstance(val, PGModel):
        return PropertyGroup(val, match_name=mn)
    if isinstance(val, TextPropertyModel):
        return TextSourceProperty(val)
    # MaskData, EffectInstance are handled by their own wrappers in _mask.py / _effect.py
    return val


def _find_property_by_name(children: list[tuple[str, str, Any]], name: str) -> Any:
    """Find a child property by match_name, display name, or model name."""
    # Exact match_name
    for mn, dn, wrapped in children:
        if mn == name:
            return wrapped
    # Display name (from MATCH_NAMES or DISPLAY_NAMES lookup)
    resolved_mn = DISPLAY_NAMES.get(name)
    if resolved_mn:
        for mn, dn, wrapped in children:
            if mn == resolved_mn:
                return wrapped
    # Display name direct comparison
    name_lower = name.lower()
    for mn, dn, wrapped in children:
        if dn.lower() == name_lower:
            return wrapped
    # Model .name attribute (for user-defined names on effects, masks, etc.)
    for mn, dn, wrapped in children:
        obj_name = None
        if hasattr(wrapped, 'name'):
            obj_name = getattr(wrapped, 'name', None)
        elif hasattr(wrapped, 'name'):
            obj_name = wrapped.name
        if obj_name and isinstance(obj_name, str) and obj_name.lower() == name_lower:
            return wrapped
    return None


# Write helpers


def _to_model_value(val: Any) -> Any:
    """Convert a Python value back to a model value for storage."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, list):
        if len(val) == 2:
            return Vector(float(val[0]), float(val[1]))
        if len(val) == 3:
            return Vector(float(val[0]), float(val[1]), float(val[2]))
        if len(val) == 4:
            return Color(float(val[0]), float(val[1]), float(val[2]), float(val[3]))
    return val


def _sync_property_to_chunk(prop: Property) -> None:
    """Push a Property's new value to the chunk tree (if write context exists)."""
    layer = prop._layer_ref
    if layer is None or not prop._match_path:
        return
    comp = getattr(layer, '_containing_comp', None)
    if comp is None:
        return
    project = getattr(comp, '_project', None)
    if project is None or project._chunk_tree is None:
        return

    from ._writer import set_property_value
    val = prop._model.value
    if isinstance(val, (int, float)):
        floats = [float(val)]
    elif isinstance(val, Vector):
        floats = [val.x, val.y] if val.z is None else [val.x, val.y, val.z]
    elif isinstance(val, Color):
        floats = [val.r, val.g, val.b, val.a]
    elif isinstance(val, list):
        floats = [float(v) for v in val]
    else:
        return

    # AE always expects Anchor Point to be 3-component (even on 2D layers).
    # Position needs 3 components only on 3D layers.
    if len(prop._match_path) >= 1:
        last_mn = prop._match_path[-1]
        if last_mn == "ADBE Anchor Point" and len(floats) == 2:
            floats.append(0.0)
        elif last_mn == "ADBE Position" and len(floats) == 2:
            is_3d = getattr(layer._model, 'threedimensional', False)
            if is_3d:
                floats.append(0.0)

    set_property_value(project._chunk_tree, comp.id, layer._model.id,
                       prop._match_path, floats, project._big_endian)
