"""示例：加载 .aep/.aepx 文件并读取项目属性。

用法:
    python examples/read_project.py path/to/project.aep
    python examples/read_project.py path/to/project.aepx
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
from aep_tools import Project, AVLayer, TextLayer, ShapeLayer, CameraLayer, LightLayer


def main():
    path = Path(r"C:\Users\cmp094\Desktop\MHYA2_238_V1.aep")
    if not path.exists():
        print(f"文件不存在: {path}")
        sys.exit(1)

    # ── 打开项目 ────────────────────────────────────────────────────────
    proj = Project.open(path)
    print(f"项目: {proj.file}")
    print(f"合成数量: {len(proj.compositions)}")
    print()

    # ── 遍历所有合成 ────────────────────────────────────────────────────
    for comp in proj.compositions:
        print(f"{'='*60}")
        print(f"合成: {comp.name}")
        print(f"  尺寸: {comp.width}x{comp.height}")
        print(f"  帧率: {comp.frame_rate} fps")
        print(f"  时长: {comp.duration:.2f}s")
        print(f"  工作区: {comp.work_area_start:.2f}s - "
              f"{comp.work_area_start + comp.work_area_duration:.2f}s")
        print(f"  背景色: {comp.bg_color}")
        print(f"  图层数: {comp.num_layers}")

        # 合成标记
        mp = comp.marker_property
        if mp and mp.num_keys > 0:
            print(f"  标记数: {mp.num_keys}")
            for i in range(1, mp.num_keys + 1):
                mv = mp.key_value(i)
                print(f"    [{i}] t={mv.time:.2f}s  \"{mv.comment}\"  "
                      f"duration={mv.duration:.2f}s")

        # ── 遍历图层 ────────────────────────────────────────────────────
        for layer in comp.layers:
            layer_type = type(layer).__name__
            print(f"\n  图层 {layer.index}: {layer.name}  ({layer_type})")
            print(f"    启用={layer.enabled}  3D={layer.three_d_layer}  "
                  f"混合={getattr(layer.blending_mode, 'name', layer.blending_mode)}")
            print(f"    入点={layer.in_point:.2f}s  出点={layer.out_point:.2f}s  "
                  f"起始={layer.start_time:.2f}s")

            if layer.parent:
                print(f"    父级: {layer.parent.name}")

            # Transform 属性
            if layer.position:
                pos = layer.position
                print(f"    位置: {pos.value}  "
                      f"(关键帧={pos.num_keys}, 动画={pos.is_time_varying})")
            if layer.scale:
                print(f"    缩放: {layer.scale.value}")
            if layer.rotation:
                print(f"    旋转: {layer.rotation.value}")
            if layer.opacity:
                opa = layer.opacity
                print(f"    不透明度: {opa.value}")
                if opa.num_keys > 0:
                    for i in range(1, opa.num_keys + 1):
                        print(f"      关键帧[{i}] t={opa.key_time(i):.2f}s  "
                              f"v={opa.key_value(i)}")
            if layer.anchor_point:
                print(f"    锚点: {layer.anchor_point.value}")

            # 表达式
            if layer.position and layer.position.expression:
                print(f"    位置表达式: {layer.position.expression}")

            # 时间重映射
            if layer.time_remap_enabled:
                tr = layer.time_remap
                print(f"    时间重映射: 关键帧={tr.num_keys}")

            # 文本图层
            if isinstance(layer, TextLayer) and layer.source_text:
                st = layer.source_text
                print(f"    文本: \"{st.text}\"")
                if st.fonts:
                    print(f"    字体: {st.fonts}")

            # 形状图层
            if isinstance(layer, ShapeLayer) and layer.contents:
                print(f"    形状内容: {layer.contents.num_properties} 个子属性")

            # 摄像机图层
            if isinstance(layer, CameraLayer) and layer.camera_options:
                cam = layer.camera_options
                print(f"    摄像机选项: {cam.num_properties} 个参数")

            # 效果
            if layer.num_effects > 0:
                print(f"    效果数: {layer.num_effects}")
                for i in range(1, layer.num_effects + 1):
                    eff = layer.effect(i)
                    print(f"      [{i}] {eff.name}  ({eff.match_name})  "
                          f"参数={eff.num_params}")

            # 蒙版
            if layer.num_masks > 0:
                print(f"    蒙版数: {layer.num_masks}")
                for i in range(1, layer.num_masks + 1):
                    m = layer.mask(i)
                    print(f"      [{i}] {m.name}  模式={m.mode.name}  "
                          f"反转={m.inverted}")

        print()

    # ── 渲染队列 ────────────────────────────────────────────────────────
    rq = proj.render_queue
    if rq.num_items > 0:
        print(f"{'='*60}")
        print(f"渲染队列: {rq.num_items} 项")
        for i in range(1, rq.num_items + 1):
            item = rq.item(i)
            print(f"  [{i}] {item.comp_name}  状态={item.status}  "
                  f"输出模块={item.num_output_modules}")


if __name__ == "__main__":
    main()
