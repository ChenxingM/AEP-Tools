"""测试所有可写属性 — 打开 .aep，修改全部可写属性，保存后重新读取验证。

用法:
    python examples/test_all_writable.py input.aep

会在同目录生成 input_modified.aep，然后重新读取对比。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import (
    Project, BlendingMode, TrackMatteType, LayerQuality,
    KeyframeInterpolationType,
)


def main():
    if len(sys.argv) < 2:
        print("用法: python examples/test_all_writable.py input.aep")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = input_path.with_stem(input_path.stem + "_modified1")

    proj = Project.open(input_path)
    assert proj.writable, "需要 .aep 文件（非 .aepx）"

    print(f"打开: {input_path}")
    print(f"AE 版本: {proj.ae_version}")
    print(f"合成数: {len(proj.compositions)}")
    print()

    # 选择第一个合成
    comp = proj.comp(1)
    if comp is None:
        print("没有找到合成")
        sys.exit(1)

    print(f"=== 合成: {comp.name} ===")
    print(f"  原始: {comp.width}x{comp.height} @ {comp.frame_rate}fps, "
          f"时长={comp.duration}s, 背景={comp.bg_color}")

    # CompItem 可写属性
    old_comp = {
        "name": comp.name,
        "width": comp.width,
        "height": comp.height,
        "frame_rate": comp.frame_rate,
        "duration": comp.duration,
        "bg_color": comp.bg_color[:],
    }

    comp.name = comp.name + "_MODIFIED"
    comp.width = 1280
    comp.height = 720

    comp.frame_rate = 24.0
    comp.duration = 10.0
    comp.bg_color = [128, 64, 32]

    print(f"  修改后: {comp.width}x{comp.height} @ {comp.frame_rate}fps, "
          f"时长={comp.duration}s, 背景={comp.bg_color}")
    print(f"  名称: {old_comp['name']} -> {comp.name}")
    print()

    # 选择第一个图层
    if comp.num_layers == 0:
        print("合成没有图层，跳过图层测试")
        proj.save(output_path)
        print(f"\n已保存: {output_path}")
        return

    layer = comp.layer(1)
    print(f"=== 图层 1: {layer.name} ===")

    # Layer 可写属性: 名称
    old_name = layer.name
    layer.name = "MODIFIED_LAYER"
    print(f"  名称: {old_name} -> {layer.name}")

    # Layer 可写属性: 标志
    # 注意: three_d_layer 和 null_layer 有结构性副作用，不能随意翻转。
    #   three_d_layer False→True: AE 要求 Anchor Point / Position 变为 3 分量，
    #   但 tdb4 元数据仍声明 2 分量 → AE 报错 "dimension 2, expected 3"。
    #   null_layer True 会改变图层的结构预期。
    # 因此这两个属性只测试"安全方向"的翻转。

    flags = {
        "enabled":                  layer.enabled,
        "solo":                     layer.solo,
        "shy":                      layer.shy,
        "locked":                   layer.locked,
        "guide_layer":              layer.guide_layer,
        "adjustment_layer":         layer.adjustment_layer,
        "auto_orient":              layer.auto_orient,
        "effects_active":           layer.effects_active,
        "motion_blur":              layer.motion_blur,
        "collapse_transformation":  layer.collapse_transformation,
        "sampling_quality":         layer.sampling_quality,
    }

    print(f"  标志 (修改前):")
    for k, v in flags.items():
        print(f"    {k}: {v}")
    print(f"    three_d_layer: {layer.three_d_layer}  (不翻转 False→True)")
    print(f"    null_layer: {layer.null_layer}  (不翻转 False→True)")

    # 安全翻转
    layer.enabled = not flags["enabled"]
    layer.solo = not flags["solo"]
    layer.shy = not flags["shy"]
    layer.locked = not flags["locked"]
    layer.guide_layer = not flags["guide_layer"]
    layer.adjustment_layer = not flags["adjustment_layer"]
    layer.auto_orient = not flags["auto_orient"]
    layer.effects_active = not flags["effects_active"]
    layer.motion_blur = not flags["motion_blur"]
    layer.collapse_transformation = not flags["collapse_transformation"]
    layer.sampling_quality = not flags["sampling_quality"]

    # three_d_layer: 只测试 True→False (安全), 不测试 False→True
    if layer.three_d_layer:
        layer.three_d_layer = False
        flags["three_d_layer"] = True  # 记录原值以便验证
    else:
        flags["three_d_layer"] = None  # 跳过

    # null_layer: 只测试 True→False (安全)
    if layer.null_layer:
        layer.null_layer = False
        flags["null_layer"] = True
    else:
        flags["null_layer"] = None

    print(f"  标志 (修改后):")
    print(f"    enabled: {layer.enabled}")
    print(f"    solo: {layer.solo}")
    print(f"    shy: {layer.shy}")
    print(f"    locked: {layer.locked}")
    print(f"    three_d_layer: {layer.three_d_layer}")
    print()

    # Layer 可写属性: 值
    old_label = layer.label
    old_blend = layer.blending_mode
    old_matte = layer.track_matte_type
    old_quality = layer.quality

    layer.label = 5
    layer.blending_mode = BlendingMode.MULTIPLY
    layer.track_matte_type = TrackMatteType.ALPHA
    layer.quality = LayerQuality.DRAFT

    print(f"  label: {old_label} -> {layer.label}")
    print(f"  blending_mode: {old_blend} -> {layer.blending_mode}")
    print(f"  track_matte_type: {old_matte} -> {layer.track_matte_type}")
    print(f"  quality: {old_quality} -> {layer.quality}")
    print()

    # Layer 可写属性: 时间
    old_in = layer.in_point
    old_out = layer.out_point
    old_start = layer.start_time
    old_stretch = layer.stretch

    layer.in_point = 1.0
    layer.out_point = 8.0
    layer.start_time = 0.5
    layer.stretch = 2.0

    print(f"  in_point: {old_in} -> {layer.in_point}")
    print(f"  out_point: {old_out} -> {layer.out_point}")
    print(f"  start_time: {old_start} -> {layer.start_time}")
    print(f"  stretch: {old_stretch} -> {layer.stretch}")
    print()

    # Property.value (Transform)
    print("  Transform 属性:")
    if layer.position is not None:
        old_pos = layer.position.value
        if isinstance(old_pos, list) and len(old_pos) == 3:
            layer.position.value = [100.0, 200.0, 0.0]
        else:
            layer.position.value = [100.0, 200.0]
        print(f"    position: {old_pos} -> {layer.position.value}")
    elif layer.position_x is not None:
        old_px = layer.position_x.value
        layer.position_x.value = 100.0
        print(f"    position_x: {old_px} -> {layer.position_x.value}")
    else:
        print("    position: (不存在)")

    if layer.scale is not None:
        old_scale = layer.scale.value
        layer.scale.value = [0.5, 0.5, 0.5] if len(old_scale) == 3 else [0.5, 0.5]
        print(f"    scale: {old_scale} -> {layer.scale.value}")

    if layer.opacity is not None:
        old_opacity = layer.opacity.value
        layer.opacity.value = 0.5
        print(f"    opacity: {old_opacity} -> {layer.opacity.value}")

    if layer.rotation is not None:
        old_rot = layer.rotation.value
        layer.rotation.value = 45.0
        print(f"    rotation: {old_rot} -> {layer.rotation.value}")

    if layer.anchor_point is not None:
        old_anchor = layer.anchor_point.value
        # 保持维度一致: 2D→[x,y], 3D→[x,y,z]
        if isinstance(old_anchor, list) and len(old_anchor) == 3:
            layer.anchor_point.value = [50.0, 50.0, 0.0]
        else:
            layer.anchor_point.value = [50.0, 50.0]
        print(f"    anchor_point: {old_anchor} -> {layer.anchor_point.value}")

    print()

    # 关键帧写入
    prop = layer.position or layer.opacity or layer.scale
    if prop is not None and prop.num_keys > 0:
        print(f"  关键帧测试 ({prop.match_name}, {prop.num_keys} keys):")
        old_kv = prop.key_value(1)
        old_kt = prop.key_time(1)
        old_in_interp = prop.key_in_interpolation_type(1)
        old_out_interp = prop.key_out_interpolation_type(1)

        print(f"    key(1) 原始: value={old_kv}, time={old_kt}s")
        print(f"    interp: in={old_in_interp}, out={old_out_interp}")

        # 修改关键帧值
        if isinstance(old_kv, list):
            new_kv = [v + 10.0 for v in old_kv]
        else:
            new_kv = old_kv + 10.0
        prop.set_value_at_key(1, new_kv)
        print(f"    key(1) 修改后: value={prop.key_value(1)}")

        # 修改插值
        prop.set_interpolation_type_at_key(1,
            in_type=KeyframeInterpolationType.BEZIER,
            out_type=KeyframeInterpolationType.HOLD)
        print(f"    interp 修改后: in={prop.key_in_interpolation_type(1)}, "
              f"out={prop.key_out_interpolation_type(1)}")

        # 修改缓动
        prop.set_temporal_ease_at_key(1,
            in_ease=[{"speed": 0.0, "influence": 16.67}],
            out_ease=[{"speed": 100.0, "influence": 50.0}])
        print(f"    ease 修改后: in={prop.key_in_temporal_ease(1)}, "
              f"out={prop.key_out_temporal_ease(1)}")
        print()
    else:
        print("  (没有关键帧，跳过关键帧测试)")
        print()

    # FootageItem.file
    print("=== 素材路径 ===")
    for i in range(1, proj.num_items + 1):
        item = proj.item(i)
        if hasattr(item, 'file') and item.file is not None:
            old_file = item.file
            item.file = "/test/modified/path.mov"
            print(f"  [{i}] {item.name}: {old_file} -> {item.file}")
            break
    else:
        print("  (没有找到 footage 素材)")
    print()

    # 保存
    proj.save(output_path)
    print(f"已保存: {output_path}")
    print()

    # 重新读取验证
    print("=" * 60)
    print("重新读取验证...")
    print("=" * 60)
    proj2 = Project.open(output_path)
    comp2 = proj2.comp(1)

    print(f"\n合成: {comp2.name}")
    print(f"  尺寸: {comp2.width}x{comp2.height}")
    print(f"  帧率: {comp2.frame_rate}")
    print(f"  时长: {comp2.duration}")
    print(f"  背景: {comp2.bg_color}")

    errors = []

    def check(name, got, expected):
        if got != expected:
            errors.append(f"  FAIL {name}: got {got}, expected {expected}")
            print(f"  FAIL {name}: {got} != {expected}")
        else:
            print(f"  OK   {name}: {got}")

    check("comp.name", comp2.name, comp.name)
    check("comp.width", comp2.width, 1280)
    check("comp.height", comp2.height, 720)
    check("comp.frame_rate", comp2.frame_rate, 24.0)

    if comp2.num_layers > 0:
        layer2 = comp2.layer(1)
        print(f"\n图层 1: {layer2.name}")

        check("layer.name", layer2.name, "MODIFIED_LAYER")
        check("layer.enabled", layer2.enabled, not flags["enabled"])
        check("layer.solo", layer2.solo, not flags["solo"])
        check("layer.shy", layer2.shy, not flags["shy"])
        check("layer.locked", layer2.locked, not flags["locked"])
        check("layer.adjustment_layer", layer2.adjustment_layer,
              not flags["adjustment_layer"])
        check("layer.guide_layer", layer2.guide_layer, not flags["guide_layer"])
        check("layer.auto_orient", layer2.auto_orient, not flags["auto_orient"])
        check("layer.effects_active", layer2.effects_active,
              not flags["effects_active"])
        check("layer.motion_blur", layer2.motion_blur, not flags["motion_blur"])
        check("layer.collapse_transformation", layer2.collapse_transformation,
              not flags["collapse_transformation"])
        check("layer.sampling_quality", layer2.sampling_quality,
              not flags["sampling_quality"])

        # three_d_layer / null_layer: 只在原值为 True 时验证翻转
        if flags.get("three_d_layer") is True:
            check("layer.three_d_layer", layer2.three_d_layer, False)
        if flags.get("null_layer") is True:
            check("layer.null_layer", layer2.null_layer, False)
        check("layer.label", layer2.label, 5)
        check("layer.blending_mode", int(layer2.blending_mode), BlendingMode.MULTIPLY)
        check("layer.track_matte_type", int(layer2.track_matte_type), TrackMatteType.ALPHA)
        check("layer.quality", int(layer2.quality), LayerQuality.DRAFT)

        # 时间验证 (允许小误差)
        def check_approx(name, got, expected, tol=0.05):
            if abs(got - expected) > tol:
                errors.append(f"  FAIL {name}: got {got}, expected {expected}")
                print(f"  FAIL {name}: {got} != {expected} (diff={abs(got-expected):.4f})")
            else:
                print(f"  OK   {name}: {got}")

        check_approx("layer.in_point", layer2.in_point, 1.0)
        check_approx("layer.out_point", layer2.out_point, 8.0)
        check_approx("layer.start_time", layer2.start_time, 0.5)
        check_approx("layer.stretch", layer2.stretch, 2.0)

        # Transform 验证
        if layer2.position is not None:
            pos_val = layer2.position.value
            if isinstance(pos_val, list) and len(pos_val) == 3:
                check("layer.position.value", pos_val, [100.0, 200.0, 0.0])
            else:
                check("layer.position.value", pos_val, [100.0, 200.0])
        if layer2.opacity is not None:
            check("layer.opacity.value", layer2.opacity.value, 0.5)
        if layer2.rotation is not None:
            check("layer.rotation.value", layer2.rotation.value, 45.0)

    print()
    if errors:
        print(f"{'=' * 60}")
        print(f"有 {len(errors)} 项验证失败:")
        for e in errors:
            print(e)
        sys.exit(1)
    else:
        print("全部验证通过!")


if __name__ == "__main__":
    main()
