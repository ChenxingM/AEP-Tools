"""示例：加载 .aep/.aepx 文件并读取项目属性。

用法:
    python examples/read_project.py path/to/project.aep
    python examples/read_project.py path/to/project.aepx
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import Project, AVLayer, TextLayer, ShapeLayer, CameraLayer, LightLayer



path = Path(r"C:\Users\cmp094\Desktop\MHYA2_238_V1.aep")

proj = Project.open(path)
comp = next((c for c in proj.compositions if c.name == "_LO_238"), None)
if comp:
    print(f"合成: {comp.name} ({comp.width}x{comp.height})")
    print(f"默认位置（合成中心）: [{comp.width/2}, {comp.height/2}]\n")

    for layer in comp.layers:
        print(f"图层 {layer.index}: {layer.name}")
        print(f"  入点={layer.in_point:.2f}s  出点={layer.out_point:.2f}s")

        # Position
        if layer.position:
            p = layer.position
            print(f"  位置: {p.value}  (keys={p.num_keys})")
        elif layer.position_x or layer.position_y:
            px = layer.position_x
            py = layer.position_y
            xv = px.value if px else comp.width / 2
            yv = py.value if py else comp.height / 2
            # 0.0 = 默认值，实际位置是合成中心
            x_keys = px.num_keys if px else 0
            y_keys = py.num_keys if py else 0
            print(f"  位置(分离): X={xv} (keys={x_keys})  Y={yv} (keys={y_keys})")

        if layer.scale:
            print(f"  缩放: {layer.scale.value}")
        if layer.opacity:
            print(f"  不透明度: {layer.opacity.value}")
        if layer.rotation:
            print(f"  旋转: {layer.rotation.value}")

        if layer.num_effects > 0:
            print(f"  效果: {layer.num_effects} 个")
            for i in range(1, layer.num_effects + 1):
                print(f"    [{i}] {layer.effect(i).name}")

        if layer.num_masks > 0:
            print(f"  蒙版: {layer.num_masks} 个")
            for i in range(1, layer.num_masks + 1):
                m = layer.mask(i)
                print(f"    [{i}] {m.name}  模式={m.mode.name}")
        print()