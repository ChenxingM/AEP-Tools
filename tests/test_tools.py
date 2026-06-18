"""Unit tests for aep_tools — AE scripting-style read API."""

import pytest
from aep_parser.models import (
    AnimatedProperty,
    Color,
    Composition,
    EffectInstance,
    Folder,
    ImageAsset,
    Keyframe,
    Layer as LayerModel,
    Marker,
    MaskData,
    NamedProperty,
    OutputModule,
    Project as ProjectModel,
    PropertyGroup as PGModel,
    RenderQueueItem as RQItemModel,
    SolidAsset,
    TextDocument,
    TextProperty as TextPropertyModel,
    Font,
    Vector,
)

from aep_tools import (
    AVLayer,
    BlendingMode,
    CameraLayer,
    CompItem,
    Effect,
    KeyframeInterpolationType,
    KeyframeValue,
    Layer,
    LightLayer,
    Mask,
    MaskMode,
    MarkerProperty,
    MarkerValue,
    Project,
    Property,
    PropertyGroup,
    ShapeLayer,
    TextLayer,
    TextSourceProperty,
    TrackMatteType,
    load_project,
)


# Helpers


def _make_animated_prop(value=None, keyframes=None, match_name="", prop_type=3,
                        expression=None, split=False, animated=False) -> AnimatedProperty:
    return AnimatedProperty(
        key=match_name,
        animated=animated or bool(keyframes),
        components=2,
        expression=expression,
        keyframes=keyframes or [],
        split=split,
        prop_type=prop_type,
        value=value,
    )


def _make_named_prop(match_name, value) -> NamedProperty:
    return NamedProperty(match_name=match_name, value=value)


def _make_transform_group(position=None, scale=None, opacity=None, rotation=None):
    """Build a Transform PropertyGroup with common properties."""
    props = []
    if position is not None:
        props.append(_make_named_prop("ADBE Anchor Point",
                                      _make_animated_prop(Vector(0, 0))))
        props.append(_make_named_prop("ADBE Position", position))
    if scale is not None:
        props.append(_make_named_prop("ADBE Scale", scale))
    if opacity is not None:
        props.append(_make_named_prop("ADBE Opacity", opacity))
    if rotation is not None:
        props.append(_make_named_prop("ADBE Rotate Z", rotation))
    return PGModel(key="transform", name="Transform", properties=props)


def _make_layer_model(name="Layer 1", layer_type=0, **kwargs):
    """Build a Layer model with given properties group entries."""
    props = kwargs.pop("properties", [])
    pg = PGModel(properties=props)
    return LayerModel(
        id=kwargs.get("id", 1),
        name=name,
        layer_type=layer_type,
        quality=kwargs.get("quality", 2),
        blend_mode=kwargs.get("blend_mode", 1),
        matte_mode=kwargs.get("matte_mode", 0),
        label_color=kwargs.get("label_color", 0),
        in_time=kwargs.get("in_time", 0.0),
        out_time=kwargs.get("out_time", 10.0),
        start_time=kwargs.get("start_time", 0.0),
        time_stretch=kwargs.get("time_stretch", 1.0),
        visible=kwargs.get("visible", True),
        solo=kwargs.get("solo", False),
        shy=kwargs.get("shy", False),
        locked=kwargs.get("locked", False),
        is_null=kwargs.get("is_null", False),
        is_guide=kwargs.get("is_guide", False),
        is_adjustment=kwargs.get("is_adjustment", False),
        threedimensional=kwargs.get("threedimensional", False),
        auto_orient=kwargs.get("auto_orient", False),
        effects_enabled=kwargs.get("effects_enabled", False),
        motion_blur_enabled=kwargs.get("motion_blur_enabled", False),
        properties=pg,
        parent_id=kwargs.get("parent_id", 0),
        asset_id=kwargs.get("asset_id", 0),
    )


def _make_comp_model(name="Main Comp", layers=None, markers=None, **kwargs):
    return Composition(
        id=kwargs.get("id", 1),
        name=name,
        width=kwargs.get("width", 1920),
        height=kwargs.get("height", 1080),
        framerate=kwargs.get("framerate", 30.0),
        duration=kwargs.get("duration", 10.0),
        in_time=kwargs.get("in_time", 0.0),
        out_time=kwargs.get("out_time", 10.0),
        color=kwargs.get("color", Color(0, 0, 0)),
        layers=layers or [],
        markers=markers,
    )


def _make_project_model(compositions=None, assets=None, render_queue=None):
    return ProjectModel(
        folder=Folder(id=0, name="Root", items=compositions or []),
        compositions=compositions or [],
        assets=assets or {},
        render_queue=render_queue or [],
    )


# Property tests


class TestProperty:
    def test_static_value_scalar(self):
        prop = Property(_make_animated_prop(value=42.0), "test")
        assert prop.value == 42.0
        assert prop.num_keys == 0
        assert not prop.is_time_varying

    def test_static_value_vector(self):
        prop = Property(_make_animated_prop(value=Vector(960, 540)), "ADBE Position")
        assert prop.value == [960, 540]
        assert prop.name == "Position"

    def test_static_value_vector_3d(self):
        prop = Property(_make_animated_prop(value=Vector(960, 540, 0)), "ADBE Position")
        assert prop.value == [960, 540, 0]

    def test_static_value_color(self):
        prop = Property(_make_animated_prop(value=Color(1, 0, 0, 1)), "color")
        assert prop.value == [1, 0, 0, 1]

    def test_keyframes(self):
        kfs = [
            Keyframe(time=0.0, value=0.0, transition_type=1),
            Keyframe(time=1.0, value=100.0, transition_type=1),
            Keyframe(time=2.0, value=50.0, transition_type=1),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs, animated=True), "test")
        assert prop.num_keys == 3
        assert prop.is_time_varying

    def test_key_access_1_based(self):
        kfs = [
            Keyframe(time=0.0, value=10.0),
            Keyframe(time=1.0, value=20.0),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_value(1) == 10.0
        assert prop.key_value(2) == 20.0
        assert prop.key_time(1) == 0.0
        assert prop.key_time(2) == 1.0

    def test_key_index_out_of_range(self):
        kfs = [Keyframe(time=0.0, value=10.0)]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        with pytest.raises(IndexError):
            prop.key_value(0)
        with pytest.raises(IndexError):
            prop.key_value(2)

    def test_key_returns_keyframe_value(self):
        kfs = [Keyframe(time=0.5, value=Vector(100, 200))]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        kv = prop.key(1)
        assert isinstance(kv, KeyframeValue)
        assert kv.index == 1
        assert kv.time == 0.5
        assert kv.value == [100, 200]

    def test_keys_list(self):
        kfs = [
            Keyframe(time=0.0, value=0.0),
            Keyframe(time=1.0, value=100.0),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        keys = prop.keys
        assert len(keys) == 2
        assert keys[0].index == 1
        assert keys[1].index == 2

    def test_nearest_key_index(self):
        kfs = [
            Keyframe(time=0.0, value=0.0),
            Keyframe(time=1.0, value=100.0),
            Keyframe(time=3.0, value=50.0),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.nearest_key_index(0.3) == 1
        assert prop.nearest_key_index(0.6) == 2
        assert prop.nearest_key_index(2.5) == 3

    def test_value_at_time_linear(self):
        kfs = [
            Keyframe(time=0.0, value=0.0, transition_type=1),
            Keyframe(time=1.0, value=100.0, transition_type=1),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.value_at_time(0.0) == 0.0
        assert prop.value_at_time(0.5) == 50.0
        assert prop.value_at_time(1.0) == 100.0

    def test_value_at_time_before_first_key(self):
        kfs = [
            Keyframe(time=1.0, value=100.0, transition_type=1),
            Keyframe(time=2.0, value=200.0, transition_type=1),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.value_at_time(0.0) == 100.0

    def test_value_at_time_after_last_key(self):
        kfs = [
            Keyframe(time=0.0, value=0.0, transition_type=1),
            Keyframe(time=1.0, value=100.0, transition_type=1),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.value_at_time(5.0) == 100.0

    def test_value_at_time_hold(self):
        kfs = [
            Keyframe(time=0.0, value=0.0, transition_type=3),  # hold
            Keyframe(time=1.0, value=100.0, transition_type=3),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.value_at_time(0.5) == 0.0
        assert prop.value_at_time(1.0) == 100.0

    def test_value_at_time_vector_lerp(self):
        kfs = [
            Keyframe(time=0.0, value=Vector(0, 0), transition_type=1),
            Keyframe(time=1.0, value=Vector(100, 200), transition_type=1),
        ]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        result = prop.value_at_time(0.5)
        assert result == [50.0, 100.0]

    def test_value_at_time_no_keyframes(self):
        prop = Property(_make_animated_prop(value=42.0), "test")
        assert prop.value_at_time(5.0) == 42.0

    def test_expression(self):
        prop = Property(_make_animated_prop(value=0, expression="wiggle(1,50)"), "test")
        assert prop.expression == "wiggle(1,50)"
        assert prop.expression_enabled

    def test_no_expression(self):
        prop = Property(_make_animated_prop(value=0), "test")
        assert prop.expression is None
        assert not prop.expression_enabled

    def test_dimensions_separated(self):
        prop = Property(_make_animated_prop(value=0, split=True), "test")
        assert prop.dimensions_separated

    def test_key_interpolation_type(self):
        kfs = [Keyframe(time=0.0, value=0.0, transition_type=2)]  # bezier
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_in_interpolation_type(1) == KeyframeInterpolationType.BEZIER

    def test_key_roving(self):
        kfs = [Keyframe(time=0.0, value=0.0, roving=True)]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_roving(1) is True

    def test_key_temporal_ease(self):
        kfs = [Keyframe(time=0.0, value=0.0,
                        in_speed=[1.0], in_influence=[33.0],
                        out_speed=[2.0], out_influence=[66.0])]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_in_temporal_ease(1) == [{"speed": 1.0, "influence": 33.0}]
        assert prop.key_out_temporal_ease(1) == [{"speed": 2.0, "influence": 66.0}]

    def test_key_spatial_tangent(self):
        kfs = [Keyframe(time=0.0, value=Vector(0, 0),
                        in_tangent=Vector(10, 20), out_tangent=Vector(30, 40))]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_in_spatial_tangent(1) == [10, 20]
        assert prop.key_out_spatial_tangent(1) == [30, 40]

    def test_key_spatial_tangent_none_when_zero(self):
        kfs = [Keyframe(time=0.0, value=0.0)]
        prop = Property(_make_animated_prop(keyframes=kfs), "test")
        assert prop.key_in_spatial_tangent(1) is None


# PropertyGroup tests


class TestPropertyGroup:
    def test_access_by_match_name(self):
        inner = _make_animated_prop(value=100.0)
        pg = PGModel(properties=[_make_named_prop("ADBE Opacity", inner)])
        group = PropertyGroup(pg, "ADBE Transform Group")
        result = group.property("ADBE Opacity")
        assert isinstance(result, Property)
        assert result.value == 100.0

    def test_access_by_display_name(self):
        inner = _make_animated_prop(value=50.0)
        pg = PGModel(properties=[_make_named_prop("ADBE Opacity", inner)])
        group = PropertyGroup(pg, "ADBE Transform Group")
        result = group.property("Opacity")
        assert isinstance(result, Property)
        assert result.value == 50.0

    def test_access_by_1_based_index(self):
        inner_a = _make_animated_prop(value=1.0)
        inner_b = _make_animated_prop(value=2.0)
        pg = PGModel(properties=[
            _make_named_prop("A", inner_a),
            _make_named_prop("B", inner_b),
        ])
        group = PropertyGroup(pg)
        assert group.property(1).value == 1.0
        assert group.property(2).value == 2.0

    def test_index_out_of_range_returns_none(self):
        pg = PGModel(properties=[_make_named_prop("A", _make_animated_prop(value=1.0))])
        group = PropertyGroup(pg)
        assert group.property(0) is None
        assert group.property(2) is None

    def test_call_syntax(self):
        inner = _make_animated_prop(value=42.0)
        pg = PGModel(properties=[_make_named_prop("ADBE Opacity", inner)])
        group = PropertyGroup(pg, "ADBE Transform Group")
        result = group("Opacity")
        assert result.value == 42.0

    def test_call_raises_on_missing(self):
        pg = PGModel(properties=[])
        group = PropertyGroup(pg, "test")
        with pytest.raises(KeyError):
            group("Nonexistent")

    def test_bracket_access(self):
        inner = _make_animated_prop(value=42.0)
        pg = PGModel(properties=[_make_named_prop("ADBE Opacity", inner)])
        group = PropertyGroup(pg, "ADBE Transform Group")
        assert group["Opacity"].value == 42.0

    def test_num_properties(self):
        pg = PGModel(properties=[
            _make_named_prop("A", _make_animated_prop(value=1.0)),
            _make_named_prop("B", _make_animated_prop(value=2.0)),
        ])
        group = PropertyGroup(pg)
        assert group.num_properties == 2
        assert len(group) == 2

    def test_iter(self):
        pg = PGModel(properties=[
            _make_named_prop("A", _make_animated_prop(value=1.0)),
            _make_named_prop("B", _make_animated_prop(value=2.0)),
        ])
        group = PropertyGroup(pg)
        values = [p.value for p in group]
        assert values == [1.0, 2.0]

    def test_nested_group(self):
        inner_prop = _make_animated_prop(value=100.0)
        inner_group = PGModel(properties=[_make_named_prop("ADBE Opacity", inner_prop)])
        outer_group = PGModel(properties=[
            _make_named_prop("ADBE Transform Group", inner_group),
        ])
        group = PropertyGroup(outer_group)
        transform = group("Transform")
        assert isinstance(transform, PropertyGroup)
        opacity = transform("Opacity")
        assert isinstance(opacity, Property)
        assert opacity.value == 100.0

    def test_case_insensitive_display_name(self):
        inner = _make_animated_prop(value=50.0)
        pg = PGModel(properties=[_make_named_prop("ADBE Opacity", inner)])
        group = PropertyGroup(pg)
        assert group.property("opacity") is not None

    def test_missing_property_returns_none(self):
        pg = PGModel(properties=[])
        group = PropertyGroup(pg)
        assert group.property("ADBE Nonexistent") is None


# MarkerProperty tests


class TestMarkerProperty:
    def test_marker_values(self):
        kfs = [
            Keyframe(time=1.0, value=Marker(name="intro", duration=0.5, label_color=2)),
            Keyframe(time=5.0, value=Marker(name="outro", duration=1.0, label_color=3)),
        ]
        mp = MarkerProperty(_make_animated_prop(keyframes=kfs))
        assert mp.num_keys == 2
        mv1 = mp.key_value(1)
        assert isinstance(mv1, MarkerValue)
        assert mv1.comment == "intro"
        assert mv1.duration == 0.5
        assert mv1.label == 2
        assert mv1.time == 1.0

    def test_marker_key_time(self):
        kfs = [Keyframe(time=3.0, value=Marker(name="x"))]
        mp = MarkerProperty(_make_animated_prop(keyframes=kfs))
        assert mp.key_time(1) == 3.0

    def test_marker_nearest_key_index(self):
        kfs = [
            Keyframe(time=1.0, value=Marker(name="a")),
            Keyframe(time=5.0, value=Marker(name="b")),
        ]
        mp = MarkerProperty(_make_animated_prop(keyframes=kfs))
        assert mp.nearest_key_index(0.5) == 1
        assert mp.nearest_key_index(4.0) == 2

    def test_marker_index_out_of_range(self):
        kfs = [Keyframe(time=1.0, value=Marker(name="x"))]
        mp = MarkerProperty(_make_animated_prop(keyframes=kfs))
        with pytest.raises(IndexError):
            mp.key_value(0)
        with pytest.raises(IndexError):
            mp.key_value(2)

    def test_empty_markers(self):
        mp = MarkerProperty(_make_animated_prop())
        assert mp.num_keys == 0
        with pytest.raises(ValueError):
            mp.nearest_key_index(0.0)


# TextSourceProperty tests


class TestTextSourceProperty:
    def test_text_from_static_value(self):
        doc = TextDocument(text="Hello World")
        doc_prop = AnimatedProperty(value=doc)
        tp = TextPropertyModel(fonts=[Font(family="Arial")], documents=doc_prop)
        tsp = TextSourceProperty(tp)
        assert tsp.text == "Hello World"
        assert tsp.fonts == ["Arial"]

    def test_text_from_keyframes(self):
        doc1 = TextDocument(text="Frame 1")
        doc2 = TextDocument(text="Frame 2")
        doc_prop = AnimatedProperty(
            animated=True,
            keyframes=[
                Keyframe(time=0.0, value=doc1),
                Keyframe(time=1.0, value=doc2),
            ],
        )
        tp = TextPropertyModel(documents=doc_prop)
        tsp = TextSourceProperty(tp)
        assert tsp.text == "Frame 1"
        assert tsp.num_keys == 2
        assert tsp.key_value(1).text == "Frame 1"
        assert tsp.key_value(2).text == "Frame 2"
        assert tsp.key_time(1) == 0.0

    def test_text_key_out_of_range(self):
        doc_prop = AnimatedProperty(keyframes=[Keyframe(time=0.0, value=TextDocument(text="x"))])
        tp = TextPropertyModel(documents=doc_prop)
        tsp = TextSourceProperty(tp)
        with pytest.raises(IndexError):
            tsp.key_value(2)


# Effect tests


class TestEffect:
    def test_effect_basics(self):
        param_pg = PGModel(
            visible=True,
            properties=[
                _make_named_prop("param1", _make_animated_prop(value=50.0)),
                _make_named_prop("param2", _make_animated_prop(value=1.0)),
            ],
        )
        ei = EffectInstance(name="Blur", parameters=param_pg)
        eff = Effect(ei, match_name="ADBE Gaussian Blur 2")
        assert eff.name == "Blur"
        assert eff.match_name == "ADBE Gaussian Blur 2"
        assert eff.num_params == 2

    def test_effect_param_by_index(self):
        param_pg = PGModel(properties=[
            _make_named_prop("p1", _make_animated_prop(value=10.0)),
        ])
        ei = EffectInstance(name="E", parameters=param_pg)
        eff = Effect(ei)
        p = eff.param(1)
        assert p.value == 10.0

    def test_effect_param_by_name(self):
        param_pg = PGModel(properties=[
            _make_named_prop("myParam", _make_animated_prop(value=77.0)),
        ])
        ei = EffectInstance(name="E", parameters=param_pg)
        eff = Effect(ei)
        p = eff.param("myParam")
        assert p.value == 77.0

    def test_effect_call_syntax(self):
        param_pg = PGModel(properties=[
            _make_named_prop("p1", _make_animated_prop(value=5.0)),
        ])
        ei = EffectInstance(name="E", parameters=param_pg)
        eff = Effect(ei)
        assert eff(1).value == 5.0

    def test_effect_call_raises_on_missing(self):
        param_pg = PGModel(properties=[])
        ei = EffectInstance(name="E", parameters=param_pg)
        eff = Effect(ei)
        with pytest.raises(KeyError):
            eff("nope")


# Mask tests


class TestMask:
    def test_mask_basics(self):
        mask_props = PGModel(name="Mask 1", properties=[
            _make_named_prop("ADBE Mask Shape", _make_animated_prop(value=None)),
            _make_named_prop("ADBE Mask Opacity", _make_animated_prop(value=100.0)),
        ])
        md = MaskData(index=0, mode=1, inverted=False, locked=True, properties=mask_props)
        m = Mask(md)
        assert m.name == "Mask 1"
        assert m.mode == MaskMode.ADD
        assert not m.inverted
        assert m.locked
        assert m.index == 1  # 1-based

    def test_mask_properties(self):
        mask_props = PGModel(properties=[
            _make_named_prop("ADBE Mask Opacity", _make_animated_prop(value=50.0)),
            _make_named_prop("ADBE Mask Feather", _make_animated_prop(value=Vector(5, 5))),
        ])
        md = MaskData(index=2, mode=2, properties=mask_props)
        m = Mask(md)
        assert m.mask_opacity is not None
        assert m.mask_opacity.value == 50.0
        assert m.mask_feather is not None
        assert m.mask_feather.value == [5, 5]
        assert m.mask_path is None  # not present
        assert m.mask_expansion is None


# Layer tests


class TestLayer:
    def test_layer_basic_properties(self):
        lm = _make_layer_model(
            name="My Layer", in_time=1.0, out_time=5.0, start_time=0.5,
            blend_mode=5, visible=True, locked=True, solo=True,
        )
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.name == "My Layer"
        assert layer.index == 1
        assert layer.in_point == 1.0
        assert layer.out_point == 5.0
        assert layer.start_time == 0.5
        assert layer.blending_mode == BlendingMode.MULTIPLY
        assert layer.enabled is True
        assert layer.locked is True
        assert layer.solo is True

    def test_layer_call_for_property_access(self):
        pos = _make_animated_prop(value=Vector(960, 540))
        transform = _make_transform_group(position=pos)
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Transform Group", transform),
        ])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        # Chain: layer("Transform")("Position")
        result = layer("Transform")("Position")
        assert isinstance(result, Property)
        assert result.value == [960, 540]

    def test_layer_transform_shortcuts(self):
        pos = _make_animated_prop(value=Vector(960, 540))
        opacity = _make_animated_prop(value=100.0)
        transform = _make_transform_group(position=pos, opacity=opacity)
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Transform Group", transform),
        ])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.position.value == [960, 540]
        assert layer.opacity.value == 100.0

    def test_layer_missing_transform_returns_none(self):
        lm = _make_layer_model(properties=[])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.position is None
        assert layer.opacity is None
        assert layer.transform is None

    def test_layer_effects(self):
        param_pg = PGModel(properties=[
            _make_named_prop("param1", _make_animated_prop(value=10.0)),
        ])
        ei = EffectInstance(name="Blur", parameters=param_pg)
        effect_parade = PGModel(properties=[
            _make_named_prop("ADBE Blur", ei),
        ])
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Effect Parade", effect_parade),
        ])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.num_effects == 1
        eff = layer.effect(1)
        assert eff.name == "Blur"
        assert layer.effect("Blur").name == "Blur"

    def test_layer_masks(self):
        mask_props = PGModel(name="Mask 1", properties=[
            _make_named_prop("ADBE Mask Opacity", _make_animated_prop(value=100.0)),
        ])
        md = MaskData(index=0, mode=1, properties=mask_props)
        mask_parade = PGModel(properties=[
            _make_named_prop("ADBE Mask Atom", md),
        ])
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Mask Parade", mask_parade),
        ])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.num_masks == 1
        m = layer.mask(1)
        assert m.name == "Mask 1"

    def test_layer_call_raises_on_missing(self):
        lm = _make_layer_model(properties=[])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        with pytest.raises(KeyError):
            layer("Nonexistent")


# Layer subclass factory tests


class TestLayerSubclasses:
    def test_av_layer(self):
        lm = _make_layer_model(layer_type=0, asset_id=42)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, AVLayer)

    def test_text_layer(self):
        lm = _make_layer_model(layer_type=3)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, TextLayer)

    def test_shape_layer(self):
        lm = _make_layer_model(layer_type=4)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, ShapeLayer)

    def test_camera_layer(self):
        lm = _make_layer_model(layer_type=2)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, CameraLayer)

    def test_light_layer(self):
        lm = _make_layer_model(layer_type=1)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, LightLayer)

    def test_text_layer_source_text(self):
        doc = TextDocument(text="Hello")
        doc_prop = AnimatedProperty(value=doc)
        tp = TextPropertyModel(fonts=[Font(family="Helvetica")], documents=doc_prop)
        text_group = PGModel(properties=[
            _make_named_prop("ADBE Text Document", tp),
        ])
        lm = _make_layer_model(layer_type=3, properties=[
            _make_named_prop("ADBE Text Properties", text_group),
        ])
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert isinstance(layer, TextLayer)
        assert layer.source_text is not None
        assert layer.source_text.text == "Hello"
        assert layer.source_text.fonts == ["Helvetica"]


# CompItem tests


class TestCompItem:
    def test_comp_basics(self):
        comp_model = _make_comp_model(
            name="Test Comp", width=1920, height=1080,
            framerate=24.0, duration=5.0,
        )
        ci = CompItem(comp_model)
        assert ci.name == "Test Comp"
        assert ci.width == 1920
        assert ci.height == 1080
        assert ci.frame_rate == 24.0
        assert ci.duration == 5.0
        assert ci.frame_duration == pytest.approx(1.0 / 24.0)
        assert ci.type_name == "Composition"

    def test_comp_layer_by_index(self):
        lm1 = _make_layer_model(name="Layer A")
        lm2 = _make_layer_model(name="Layer B")
        comp_model = _make_comp_model(layers=[lm1, lm2])
        ci = CompItem(comp_model)
        assert ci.num_layers == 2
        assert ci.layer(1).name == "Layer A"
        assert ci.layer(2).name == "Layer B"

    def test_comp_layer_by_name(self):
        lm = _make_layer_model(name="Background")
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer("Background")
        assert layer is not None
        assert layer.name == "Background"

    def test_comp_layer_not_found(self):
        comp_model = _make_comp_model(layers=[])
        ci = CompItem(comp_model)
        assert ci.layer(1) is None
        assert ci.layer("Nope") is None

    def test_comp_layers_collection(self):
        lm1 = _make_layer_model(name="A")
        lm2 = _make_layer_model(name="B")
        comp_model = _make_comp_model(layers=[lm1, lm2])
        ci = CompItem(comp_model)
        layers = ci.layers
        assert len(layers) == 2
        assert layers[1].name == "A"
        assert layers[2].name == "B"
        with pytest.raises(IndexError):
            layers[0]
        with pytest.raises(IndexError):
            layers[3]

    def test_comp_layers_iter(self):
        lm1 = _make_layer_model(name="A")
        lm2 = _make_layer_model(name="B")
        comp_model = _make_comp_model(layers=[lm1, lm2])
        ci = CompItem(comp_model)
        names = [l.name for l in ci.layers]
        assert names == ["A", "B"]

    def test_comp_bg_color(self):
        comp_model = _make_comp_model(color=Color(0.2, 0.3, 0.4))
        ci = CompItem(comp_model)
        assert ci.bg_color == [0.2, 0.3, 0.4]

    def test_comp_work_area(self):
        comp_model = _make_comp_model(in_time=2.0, out_time=8.0)
        ci = CompItem(comp_model)
        assert ci.work_area_start == 2.0
        assert ci.work_area_duration == 6.0

    def test_comp_markers(self):
        marker_kfs = [
            Keyframe(time=1.0, value=Marker(name="Start", duration=0.0, label_color=1)),
            Keyframe(time=5.0, value=Marker(name="End", duration=0.5, label_color=2)),
        ]
        marker_prop = _make_animated_prop(keyframes=marker_kfs)
        markers_layer = LayerModel(
            properties=PGModel(properties=[
                _make_named_prop("ADBE Marker", marker_prop),
            ]),
        )
        comp_model = _make_comp_model(markers=markers_layer)
        ci = CompItem(comp_model)
        mp = ci.marker_property
        assert mp is not None
        assert mp.num_keys == 2
        mv = mp.key_value(1)
        assert mv.comment == "Start"


# Project tests


class TestProject:
    def test_project_comps(self):
        comp1 = _make_comp_model(name="Comp A", id=1)
        comp2 = _make_comp_model(name="Comp B", id=2)
        pm = _make_project_model(compositions=[comp1, comp2])
        proj = load_project(pm)
        assert len(proj.compositions) == 2
        assert proj.comp("Comp A").name == "Comp A"
        assert proj.comp("Comp B").name == "Comp B"
        assert proj.comp(1).name == "Comp A"
        assert proj.comp(2).name == "Comp B"

    def test_project_comp_not_found(self):
        pm = _make_project_model(compositions=[])
        proj = load_project(pm)
        assert proj.comp("Nope") is None
        assert proj.comp(1) is None

    def test_project_file(self):
        pm = _make_project_model()
        proj = load_project(pm)
        assert proj.file is None

    def test_project_render_queue(self):
        rqi = RQItemModel(comp_name="Test", status=1,
                          output_modules=[OutputModule(format="MooV")])
        pm = _make_project_model(render_queue=[rqi])
        proj = load_project(pm)
        rq = proj.render_queue
        assert rq.num_items == 1
        item = rq.item(1)
        assert item.comp_name == "Test"
        assert item.num_output_modules == 1
        om = item.output_module(1)
        assert om.format == "MooV"

    def test_project_items(self):
        comp = _make_comp_model(name="My Comp", id=10)
        pm = _make_project_model(compositions=[comp])
        proj = load_project(pm)
        # Items come from folder.items
        assert proj.num_items == 1

    def test_project_repr(self):
        pm = _make_project_model()
        proj = load_project(pm)
        assert "Project" in repr(proj)

    def test_project_color_management_ocio(self):
        pm = _make_project_model()
        pm.color_management_settings = {"ocioConfigurationFile": "ACES 1.2"}
        proj = load_project(pm)
        assert proj.color_management_settings == {"ocioConfigurationFile": "ACES 1.2"}
        assert proj.ocio_config == "ACES 1.2"
        assert proj.color_space == "ACES 1.2"

    def test_project_color_management_classic_srgb(self):
        pm = _make_project_model()
        pm.working_color_space = {
            "baseColorProfile": {"colorProfileName": "sRGB IEC61966-2.1"}}
        proj = load_project(pm)
        assert proj.working_color_space_name == "sRGB IEC61966-2.1"
        assert proj.color_space == "sRGB IEC61966-2.1"

    def test_project_color_management_default_none(self):
        proj = load_project(_make_project_model())
        assert proj.color_management_settings == {}
        assert proj.ocio_config == ""
        assert proj.color_space == "None"


# Layer parent lookup


class TestLayerParent:
    def test_parent_found(self):
        lm_parent = _make_layer_model(name="Parent", id=10)
        lm_child = _make_layer_model(name="Child", id=20, parent_id=10)
        comp_model = _make_comp_model(layers=[lm_parent, lm_child])
        ci = CompItem(comp_model)
        child = ci.layer(2)
        assert child.parent is not None
        assert child.parent.name == "Parent"

    def test_parent_not_found(self):
        lm = _make_layer_model(name="Orphan", parent_id=0)
        comp_model = _make_comp_model(layers=[lm])
        ci = CompItem(comp_model)
        layer = ci.layer(1)
        assert layer.parent is None


# Chaining integration test


class TestChaining:
    def test_full_chain(self):
        """Test layer("Transform")("Position").value style chaining."""
        pos_prop = _make_animated_prop(value=Vector(960, 540))
        transform = _make_transform_group(position=pos_prop)
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Transform Group", transform),
        ])
        comp_model = _make_comp_model(layers=[lm])
        pm = _make_project_model(compositions=[comp_model])
        proj = load_project(pm)
        comp = proj.comp("Main Comp")
        layer = comp.layer(1)
        # AE-style chaining
        val = layer("Transform")("Position").value
        assert val == [960, 540]
        # Shortcut
        assert layer.position.value == [960, 540]

    def test_chain_with_keyframes(self):
        kfs = [
            Keyframe(time=0.0, value=Vector(0, 0), transition_type=1),
            Keyframe(time=1.0, value=Vector(100, 200), transition_type=1),
        ]
        pos_prop = _make_animated_prop(keyframes=kfs, animated=True)
        transform = _make_transform_group(position=pos_prop)
        lm = _make_layer_model(properties=[
            _make_named_prop("ADBE Transform Group", transform),
        ])
        comp_model = _make_comp_model(layers=[lm])
        pm = _make_project_model(compositions=[comp_model])
        proj = load_project(pm)
        layer = proj.comp(1).layer(1)
        pos = layer("Transform")("Position")
        assert pos.num_keys == 2
        assert pos.key_value(1) == [0, 0]
        assert pos.value_at_time(0.5) == [50.0, 100.0]
