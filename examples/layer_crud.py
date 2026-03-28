"""展示 aep_tools 图层增删复制移动和预合成的完整示例。

用法:
    python examples/layer_crud.py input.aep output.aep
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import Project, CompItem


def main():
    if len(sys.argv) < 3:
        print("用法: python examples/layer_crud.py input.aep output.aep")
        sys.exit(1)

    proj = Project.open(sys.argv[1])  # 打开 .aep 文件，返回 Project 对象
    comp = proj.comp(1)  # 按 1-based 索引取合成, 也可 proj.comp("合成名")

    # ================================================================
    # 1. 添加图层 — 所有类型
    # ================================================================

    # --- 纯色图层 ---
    comp.add_solid(
        "Red Solid",                     # 图层名/素材名
        color=(1.0, 0.0, 0.0),           # RGB 颜色 (0.0-1.0)
        width=1920,                      # 宽度 (默认=合成宽度)
        height=1080,                     # 高度 (默认=合成高度)
    )  # 返回 layer_id (int)

    # --- 空对象图层 ---
    comp.add_null("My Null")             # 100x100 空对象

    # --- 调整图层 ---
    comp.add_adjustment(
        "My Adjustment",
        width=1920,                      # 默认=合成宽度
        height=1080,                     # 默认=合成高度
    )

    # --- 形状图层 ---
    comp.add_shape("My Shape")           # 空形状图层

    # --- 文字图层 ---
    comp.add_text("My Text")             # 空文字图层

    # --- 摄像机图层 ---
    comp.add_camera("My Camera")         # 摄像机

    # --- 灯光图层 ---
    comp.add_light("My Light")           # 灯光

    # ================================================================
    # 2. 删除图层
    # ================================================================

    # 方式一: 通过图层对象
    comp.layers[1].remove()              # 删除最顶层图层

    # 方式二: 通过索引
    comp.remove_layer(1)                 # 删除当前第 1 个图层 (1-based)

    # ================================================================
    # 3. 复制图层
    # ================================================================

    # 方式一: 通过图层对象
    comp.layers[1].duplicate()           # 复制，副本出现在原图层下方

    # 方式二: 通过索引
    comp.duplicate_layer(1)              # 同上

    # ================================================================
    # 4. 移动图层
    # ================================================================

    # 移到指定位置
    comp.layers[3].move_to(1)            # 将第 3 层移到最上面

    # 快捷方法
    comp.layers[2].move_to_beginning()   # 移到最上层 (= move_to(1))
    comp.layers[1].move_to_end()         # 移到最下层

    # 通过 CompItem 方法
    comp.move_layer(2, 1)               # 将第 2 层移到第 1 位

    # ================================================================
    # 5. 预合成 (Precompose)
    # ================================================================

    # 先创建几个图层
    lid_a = comp.add_solid("Solid A", color=(1.0, 0.0, 0.0))
    lid_b = comp.add_solid("Solid B", color=(0.0, 1.0, 0.0))
    lid_c = comp.add_solid("Solid C", color=(0.0, 0.0, 1.0))

    # 将 A 和 B 预合成到新合成 "PreComp AB"
    new_comp_id, precomp_layer_id = comp.precompose(
        [lid_a, lid_b],                  # 要预合成的图层 ID 列表
        "PreComp AB",                    # 新合成名称
    )  # 返回 (新合成 ID, 预合成图层 ID)

    # ================================================================
    # 6. 保存
    # ================================================================

    proj.save(sys.argv[2])  # 另存为新文件, 也可 proj.save() 覆盖原文件
    print(f"已保存: {sys.argv[2]}")


if __name__ == "__main__":
    main()
