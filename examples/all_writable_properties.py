"""展示 aep_tools 所有可写属性和方法的完整示例。

用法:
    python examples/all_writable_properties.py input.aep output.aep
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from aep_tools import (
    Project, CompItem, Layer, AVLayer, LightLayer,
    BlendingMode, TrackMatteType, LayerQuality, KeyframeInterpolationType,
)


def main():
    if len(sys.argv) < 3:
        print("用法: python examples/all_writable_properties.py input.aep output.aep")
        sys.exit(1)

    proj = Project.open(sys.argv[1])  # 打开 .aep 文件，返回 Project 对象

    # ================================================================
    # 1. Project 级别属性 (项目设置)
    # ================================================================

    proj.bits_per_channel = 16          # 位深: 8, 16, 32
    proj.working_gamma = 2.2            # 工作 Gamma 值
    proj.linearize_working_space = True # 线性化工作空间
    proj.compensate_scene_referred = False  # 补偿场景参照
    proj.audio_sample_rate = 48000.0    # 音频采样率 (Hz)

    # ================================================================
    # 2. CompItem 级别属性 (合成设置)
    # ================================================================

    comp = proj.comp(1)  # 按 1-based 索引取合成, 也可 proj.comp("合成名")

    # --- 基本属性 ---
    comp.name = "My Composition"        # 合成名称
    comp.width = 1920                   # 宽度 (像素)
    comp.height = 1080                  # 高度 (像素)
    comp.frame_rate = 30.0              # 帧率 (fps)
    comp.duration = 10.0                # 时长 (秒)
    comp.bg_color = [0, 0, 0]           # 背景色 [R, G, B] 0-255
    comp.pixel_aspect = 1.0             # 像素宽高比
    comp.display_start_time = 0.0       # 显示起始时间 (秒)

    # --- 工作区 ---
    comp.work_area_start = 1.0          # 工作区起点 (秒)
    comp.work_area_duration = 5.0       # 工作区长度 (秒)

    # --- 合成开关 ---
    comp.draft3d = False                # Draft 3D 模式
    comp.motion_blur = True             # 启用运动模糊
    comp.frame_blending = True          # 启用帧混合
    comp.hide_shy_layers = False        # 隐藏害羞图层
    comp.preserve_nested_resolution = True   # 保持嵌套合成分辨率
    comp.preserve_nested_frame_rate = False  # 保持嵌套合成帧率
    comp.drop_frame = False             # Drop Frame 时间码

    # --- 快门 / 运动模糊参数 ---
    comp.shutter_angle = 180            # 快门角度 (度)
    comp.shutter_phase = -90            # 快门相位 (度)
    comp.motion_blur_samples_per_frame = 16      # 每帧运动模糊采样数
    comp.motion_blur_adaptive_sample_limit = 128 # 自适应采样上限

    # ================================================================
    # 3. Layer 级别属性 (图层设置)
    # ================================================================

    layer = comp.layer(1)  # 按 1-based 索引取图层, 也可 comp.layer("图层名")

    # --- 名称 ---
    layer.name = "My Layer"             # 图层名称

    # --- 显示开关 ---
    layer.enabled = True                # 可见 (眼睛图标)
    layer.solo = False                  # Solo
    layer.shy = False                   # 害羞
    layer.locked = False                # 锁定

    # --- 图层类型开关 ---
    layer.three_d_layer = True          # 3D 图层 (注意: False→True 需属性已是3分量)
    layer.guide_layer = False           # 参考线图层
    layer.adjustment_layer = False      # 调整图层
    layer.null_layer = False            # 空对象图层
    layer.environment_layer = False     # 环境图层

    # --- 渲染开关 ---
    layer.effects_active = True         # 特效启用
    layer.motion_blur = True            # 运动模糊
    layer.collapse_transformation = False  # 折叠变换 / 连续光栅化
    layer.auto_orient = False           # 自动朝向
    layer.sampling_quality = True       # 双三次采样 (Bicubic)
    layer.frame_blending = True         # 帧混合
    layer.frame_blending_type = 1       # 帧混合类型: 0=Frame Mix, 1=Pixel Motion
    layer.audio_enabled = True          # 音频启用
    layer.preserve_transparency = False # 保持透明度

    # --- 混合 / 遮罩 / 质量 ---
    layer.blending_mode = BlendingMode.NORMAL       # 混合模式 (枚举或 int)
    layer.track_matte_type = TrackMatteType.NONE    # 轨道遮罩类型
    layer.quality = LayerQuality.BEST               # 质量: WIREFRAME=0, DRAFT=1, BEST=2
    layer.label = 1                                 # 标签颜色索引 (0-16)

    # --- 时间 ---
    layer.in_point = 0.0                # 入点 (秒)
    layer.out_point = 10.0              # 出点 (秒)
    layer.start_time = 0.0              # 起始时间 (秒)
    layer.stretch = 1.0                 # 时间拉伸 (1.0=100%)

    # --- LightLayer 专属 ---
    for lyr in comp.layers:
        if isinstance(lyr, LightLayer):
            lyr.light_type = 2          # 灯光类型: 0=Parallel, 1=Spot, 2=Point, 3=Ambient
            break

    # ================================================================
    # 4. Property 级别 (属性值 / 关键帧)
    # ================================================================

    # --- 静态属性值 ---
    if layer.position is not None:
        layer.position.value = [960.0, 540.0, 0.0]  # 位置 [X, Y, Z]
    if layer.scale is not None:
        layer.scale.value = [1.0, 1.0, 1.0]         # 缩放 [X, Y, Z] (1.0=100%)
    if layer.rotation is not None:
        layer.rotation.value = 0.0                   # Z 旋转 (度)
    if layer.opacity is not None:
        layer.opacity.value = 1.0                    # 不透明度 (0.0-1.0)
    if layer.anchor_point is not None:
        layer.anchor_point.value = [960.0, 540.0, 0.0]  # 锚点

    # 分离 XYZ 维度时:
    if layer.position_x is not None:
        layer.position_x.value = 960.0               # X 位置
    if layer.position_y is not None:
        layer.position_y.value = 540.0               # Y 位置
    if layer.position_z is not None:
        layer.position_z.value = 0.0                 # Z 位置

    # 3D 旋转:
    if layer.rotation_x is not None:
        layer.rotation_x.value = 0.0                 # X 旋转
    if layer.rotation_y is not None:
        layer.rotation_y.value = 0.0                 # Y 旋转

    # 通过 match name 路径访问任意属性:
    # layer.property("ADBE Transform Group").property("ADBE Opacity").value = 0.5

    # --- 关键帧值 ---
    prop = layer.position  # 取一个有关键帧的属性
    if prop is not None and prop.num_keys > 0:
        # 按索引设值 (1-based)
        prop.set_value_at_key(1, [100.0, 200.0, 0.0])

        # 按时间设值 (找最近的关键帧)
        prop.set_value_at_time(2.0, [500.0, 300.0, 0.0])

        # 设置插值类型
        prop.set_interpolation_type_at_key(
            1,
            in_type=KeyframeInterpolationType.BEZIER,   # 入: LINEAR=1, BEZIER=2, HOLD=3
            out_type=KeyframeInterpolationType.BEZIER,   # 出
        )

        # 设置缓动 (temporal ease)
        prop.set_temporal_ease_at_key(
            1,
            in_ease=[{"speed": 0.0, "influence": 16.67}],   # 入缓动
            out_ease=[{"speed": 100.0, "influence": 33.33}], # 出缓动
        )

    # ================================================================
    # 5. FootageItem (素材路径)
    # ================================================================

    for i in range(1, proj.num_items + 1):
        item = proj.item(i)
        if hasattr(item, 'file') and item.file is not None:
            item.file = "/new/path/to/footage.mov"  # 修改素材文件路径
            break

    # ================================================================
    # 6. 低级 Project.change_*() 方法 (不经过对象包装, 直接按 ID 操作)
    # ================================================================
    

    comp_id = comp.id
    layer_id = layer.id

    # --- 合成 ---
    proj.change_comp_name(comp_id, "New Name")                   # 改合成名
    proj.change_comp_dimensions(comp_id, 1920, 1080)             # 改尺寸
    proj.change_comp_framerate(comp_id, 24.0)                    # 改帧率
    proj.change_comp_duration(comp_id, 15.0)                     # 改时长
    proj.change_comp_bgcolor(comp_id, 30, 30, 30)               # 改背景色 R,G,B (0-255)
    proj.change_comp_pixel_aspect(comp_id, 1.0)                  # 改像素宽高比
    proj.change_comp_display_start_time(comp_id, 0.0)            # 改显示起始时间
    proj.change_comp_work_area_start(comp_id, 0.0)               # 改工作区起点
    proj.change_comp_work_area_end(comp_id, 10.0)                # 改工作区终点
    proj.change_comp_flag(comp_id, "draft3d", False)             # 合成开关
    proj.change_comp_flag(comp_id, "motion_blur", True)          #   可用: draft3d, motion_blur,
    proj.change_comp_flag(comp_id, "frame_blending", True)       #         frame_blending, hide_shy_layers,
    proj.change_comp_flag(comp_id, "hide_shy_layers", False)     #         preserve_nested_resolution,
    proj.change_comp_flag(comp_id, "preserve_nested_resolution", True)   # preserve_nested_frame_rate
    proj.change_comp_flag(comp_id, "preserve_nested_frame_rate", False)
    proj.change_comp_drop_frame(comp_id, False)                  # Drop Frame (独立方法)
    proj.change_comp_shutter_angle(comp_id, 180)                 # 快门角度
    proj.change_comp_shutter_phase(comp_id, -90)                 # 快门相位
    proj.change_comp_motion_blur_samples(comp_id, 16, 128)       # 运动模糊采样 (每帧, 自适应上限)

    # --- 图层 ---
    proj.change_layer_name(comp_id, layer_id, "New Layer Name")  # 改图层名
    proj.change_layer_flag(comp_id, layer_id, "visible", True)   # 图层开关
    proj.change_layer_flag(comp_id, layer_id, "solo", False)     #   可用: visible, solo, shy, locked,
    proj.change_layer_flag(comp_id, layer_id, "shy", False)      #         threedimensional, is_guide,
    proj.change_layer_flag(comp_id, layer_id, "locked", False)   #         is_adjustment, is_null,
    proj.change_layer_flag(comp_id, layer_id, "threedimensional", True)  # continuously_rasterize,
    proj.change_layer_flag(comp_id, layer_id, "is_guide", False)         # motion_blur_enabled,
    proj.change_layer_flag(comp_id, layer_id, "is_adjustment", False)    # effects_enabled, auto_orient,
    proj.change_layer_flag(comp_id, layer_id, "is_null", False)          # bicubic_sampling,
    proj.change_layer_flag(comp_id, layer_id, "continuously_rasterize", False)  # frame_blending,
    proj.change_layer_flag(comp_id, layer_id, "motion_blur_enabled", True)      # frame_blending_type,
    proj.change_layer_flag(comp_id, layer_id, "effects_enabled", True)          # audio_enabled,
    proj.change_layer_flag(comp_id, layer_id, "auto_orient", False)             # environment_layer
    proj.change_layer_flag(comp_id, layer_id, "bicubic_sampling", True)
    proj.change_layer_flag(comp_id, layer_id, "frame_blending", True)
    proj.change_layer_flag(comp_id, layer_id, "frame_blending_type", True)
    proj.change_layer_flag(comp_id, layer_id, "audio_enabled", True)
    proj.change_layer_flag(comp_id, layer_id, "environment_layer", False)
    proj.change_layer_label(comp_id, layer_id, 1)                # 标签颜色 (0-16)
    proj.change_layer_blend_mode(comp_id, layer_id, 2)           # 混合模式 (int, 见 BlendingMode 枚举)
    proj.change_layer_track_matte(comp_id, layer_id, 0)          # 轨道遮罩 (int, 见 TrackMatteType 枚举)
    proj.change_layer_quality(comp_id, layer_id, 2)              # 质量: 0=Wireframe, 1=Draft, 2=Best
    proj.change_layer_preserve_transparency(comp_id, layer_id, False)  # 保持透明度
    proj.change_layer_light_type(comp_id, layer_id, 2)           # 灯光类型: 0=Parallel,1=Spot,2=Point,3=Ambient
    proj.change_layer_time_field(comp_id, layer_id, "in_time", 0.0)       # 入点
    proj.change_layer_time_field(comp_id, layer_id, "out_time", 10.0)     # 出点
    proj.change_layer_time_field(comp_id, layer_id, "start_time", 0.0)    # 起始时间
    proj.change_layer_time_field(comp_id, layer_id, "time_stretch", 1.0)  # 时间拉伸

    # --- 属性值 ---
    match_path = ["ADBE Transform Group", "ADBE Position"]       # match name 路径
    proj.change_property_value(comp_id, layer_id, match_path, [960.0, 540.0, 0.0])  # 改属性静态值

    # --- 关键帧 ---
    proj.change_keyframe_value(comp_id, layer_id, match_path, 0, [100.0, 200.0, 0.0])  # 改关键帧值 (0-based index)
    proj.change_keyframe_time(comp_id, layer_id, match_path, 0, 1.0)                    # 改关键帧时间
    proj.change_keyframe_interpolation(comp_id, layer_id, match_path, 0, 2)              # 改插值: 1=Linear,2=Bezier,3=Hold
    proj.change_keyframe_ease(                                    # 改缓动
        comp_id, layer_id, match_path, 0,
        in_speed=[0.0], in_influence=[16.67],                    # 入缓动 (每维度一个值)
        out_speed=[100.0], out_influence=[33.33],                # 出缓动
    )

    # --- 素材 ---
    proj.change_asset_path(1, "/new/path.mov")                   # 按素材 ID 改路径

    # ================================================================
    # 7. 保存
    # ================================================================

    proj.save(sys.argv[2])  # 另存为新文件, 也可 proj.save() 覆盖原文件
    print(f"已保存: {sys.argv[2]}")


if __name__ == "__main__":
    main()
