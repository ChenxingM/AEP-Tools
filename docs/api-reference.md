# aep-tools API Reference

> 所有集合索引均为 **1-based**。R = 只读，R/W = 可读写。

---

## Project

```python
proj = Project.open("file.aep")     # 自动识别 .aep/.aepx
proj = open_aep("file.aep")         # 仅 .aep
proj = open_aepx("file.aepx")       # 仅 .aepx
```

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `file` | `str \| None` | R | 源文件路径 |
| `ae_version` | `str \| None` | R | AE 版本号，如 `"25.6"` |
| `ae_version_info` | `dict \| None` | R | 完整版本信息 `{major, minor, patch, build, os, beta}` |
| `writable` | `bool` | R | 是否支持写入（仅 .aep） |
| `num_items` | `int` | R | 顶层项目数 |
| `items` | `ItemCollection` | R | 顶层项目集合 |
| `active_item` | `CompItem \| None` | R | 当前活动合成 |
| `compositions` | `list[CompItem]` | R | 所有合成 |
| `render_queue` | `RenderQueue` | R | 渲染队列 |
| `bits_per_channel` | `int` | R/W | 色深：8 / 16 / 32 |
| `working_gamma` | `float` | R/W | 工作 gamma |
| `linearize_working_space` | `bool` | R/W | 线性化工作色彩空间 |
| `compensate_scene_referred` | `bool` | R/W | 补偿场景参照配置文件 |
| `audio_sample_rate` | `float` | R/W | 音频采样率 (Hz) |

| 方法 | 返回 | 说明 |
|------|------|------|
| `item(index)` | `Any` | 按 1-based 索引获取项目 |
| `comp(name_or_index)` | `CompItem \| None` | 按名称或索引查找合成 |
| `save(path=None)` | `None` | 保存。path=None 覆盖原文件 |

---

## CompItem

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `id` | `int` | R | 内部 ID |
| `name` | `str` | R/W | 合成名称 |
| `type_name` | `str` | R | 固定 `"Composition"` |
| `width` | `int` | R/W | 宽度 (px) |
| `height` | `int` | R/W | 高度 (px) |
| `duration` | `float` | R/W | 时长 (秒) |
| `frame_rate` | `float` | R/W | 帧率 |
| `frame_duration` | `float` | R | 单帧时长 = 1/frame_rate |
| `bg_color` | `list[float]` | R/W | 背景色 [r, g, b] |
| `pixel_aspect` | `float` | R/W | 像素宽高比 |
| `work_area_start` | `float` | R/W | 工作区起点 (秒) |
| `work_area_duration` | `float` | R/W | 工作区时长 (秒) |
| `display_start_time` | `float` | R/W | 显示起始时间 |
| `drop_frame` | `bool` | R/W | 丢帧时间码 |
| `draft3d` | `bool` | R/W | 草图 3D |
| `motion_blur` | `bool` | R/W | 运动模糊 |
| `shutter_angle` | `int` | R/W | 快门角度 |
| `shutter_phase` | `int` | R/W | 快门相位 |
| `motion_blur_samples_per_frame` | `int` | R/W | 每帧运动模糊采样数 |
| `motion_blur_adaptive_sample_limit` | `int` | R/W | 自适应采样上限 |
| `frame_blending` | `bool` | R/W | 帧混合 |
| `hide_shy_layers` | `bool` | R/W | 隐藏害羞图层 |
| `preserve_nested_resolution` | `bool` | R/W | 保持嵌套分辨率 |
| `preserve_nested_frame_rate` | `bool` | R/W | 保持嵌套帧率 |
| `num_layers` | `int` | R | 图层数 |
| `layers` | `LayerCollection` | R | 图层集合 |
| `marker_property` | `MarkerProperty \| None` | R | 合成标记 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `layer(name_or_index)` | `Layer \| None` | 按名称或 1-based 索引查找图层 |

### 图层 CRUD

| 方法 | 返回 | 说明 |
|------|------|------|
| `add_solid(name, color, width, height)` | `int` | 添加纯色图层，返回 layer_id。color=(r,g,b) 0.0-1.0，width/height 默认合成尺寸 |
| `add_null(name)` | `int` | 添加空对象图层 |
| `add_adjustment(name, width, height)` | `int` | 添加调整图层 |
| `add_shape(name)` | `int` | 添加形状图层 |
| `add_text(name)` | `int` | 添加文字图层 |
| `add_camera(name)` | `int` | 添加摄像机图层 |
| `add_light(name)` | `int` | 添加灯光图层 |
| `remove_layer(index_or_layer)` | `None` | 删除图层（按 1-based 索引或 Layer 对象） |
| `duplicate_layer(index_or_layer)` | `Layer` | 复制图层，返回新图层 |
| `move_layer(index_or_layer, new_index)` | `None` | 移动图层到指定位置 |
| `precompose(layer_ids, new_comp_name)` | `(int, int)` | 预合成，返回 (new_comp_id, precomp_layer_id) |

---

## Layer

> 子类: `AVLayer` `TextLayer` `ShapeLayer` `CameraLayer` `LightLayer`

### 基本信息

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `id` | `int` | R | 内部 ID |
| `index` | `int` | R | 1-based 索引 |
| `name` | `str` | R/W | 图层名称 |
| `containing_comp` | `CompItem \| None` | R | 所属合成 |
| `parent` | `Layer \| None` | R | 父图层 |

### 标志

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `enabled` | `bool` | R/W | 可见性 (眼睛图标) |
| `solo` | `bool` | R/W | 独奏 |
| `shy` | `bool` | R/W | 害羞 |
| `locked` | `bool` | R/W | 锁定 |
| `three_d_layer` | `bool` | R/W | 3D 图层 |
| `auto_orient` | `bool` | R/W | 自动朝向 |
| `null_layer` | `bool` | R/W | 空对象 |
| `guide_layer` | `bool` | R/W | 参考线图层 |
| `adjustment_layer` | `bool` | R/W | 调整图层 |
| `effects_active` | `bool` | R/W | 效果开关 |
| `motion_blur` | `bool` | R/W | 运动模糊 |
| `collapse_transformation` | `bool` | R/W | 折叠变换/连续栅格化 |
| `frame_blending` | `bool` | R/W | 帧混合 |
| `frame_blending_type` | `int` | R/W | 帧混合类型 |
| `audio_enabled` | `bool` | R/W | 音频开关 |
| `environment_layer` | `bool` | R/W | 环境图层 |
| `preserve_transparency` | `bool` | R/W | 保持透明度 |
| `sampling_quality` | `bool` | R/W | 双三次采样 |

### 时间

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `in_point` | `float` | R/W | 入点 (秒) |
| `out_point` | `float` | R/W | 出点 (秒) |
| `start_time` | `float` | R/W | 起始时间 (秒) |
| `stretch` | `float` | R/W | 时间拉伸 (%) |

### 外观

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `blending_mode` | `BlendingMode \| int` | R/W | 混合模式 |
| `track_matte_type` | `TrackMatteType \| int` | R/W | 轨道遮罩类型 |
| `quality` | `LayerQuality` | R/W | 图层质量 |
| `label` | `int` | R/W | 标签颜色 (0-15) |

### 变换快捷属性

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `transform` | `PropertyGroup \| None` | R | 变换组 |
| `position` | `Property \| None` | R | 位置 |
| `scale` | `Property \| None` | R | 缩放 |
| `rotation` | `Property \| None` | R | Z 旋转 |
| `opacity` | `Property \| None` | R | 不透明度 |
| `anchor_point` | `Property \| None` | R | 锚点 |
| `orientation` | `Property \| None` | R | 方向 (3D) |
| `rotation_x` | `Property \| None` | R | X 旋转 (3D) |
| `rotation_y` | `Property \| None` | R | Y 旋转 (3D) |
| `rotation_z` | `Property \| None` | R | Z 旋转 (3D) |
| `position_x` | `Property \| None` | R | X 位置 (分离维度) |
| `position_y` | `Property \| None` | R | Y 位置 (分离维度) |
| `position_z` | `Property \| None` | R | Z 位置 (分离维度) |

### 时间重映射

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `time_remap_enabled` | `bool` | R | 是否启用时间重映射 |
| `time_remap` | `Property \| None` | R | 时间重映射属性 |

### 标记

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `marker_property` | `MarkerProperty \| None` | R | 图层标记 |

### 效果和遮罩

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `num_effects` | `int` | R | 效果数量 |
| `num_masks` | `int` | R | 遮罩数量 |
| `num_properties` | `int` | R | 属性数量 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `property(name_or_index)` | `Any` | 按 matchName/显示名/索引查找属性 |
| `layer["name"]` | `Any` | 同上，支持 `[]` 和 `()` 语法 |
| `effect(name_or_index)` | `Effect \| None` | 按名称或索引查找效果 |
| `mask(index)` | `Mask \| None` | 按 1-based 索引查找遮罩 |
| `remove()` | `None` | 从所属合成中删除此图层 |
| `duplicate()` | `Layer` | 复制此图层，返回副本 |
| `move_to(index)` | `None` | 移动到指定位置 (1-based) |
| `move_to_beginning()` | `None` | 移到最上层 |
| `move_to_end()` | `None` | 移到最下层 |

### 子类额外属性

| 子类 | 属性 | 类型 | 说明 |
|------|------|------|------|
| `AVLayer` | `source` | `Any` | 关联的资产对象 |
| `TextLayer` | `source_text` | `TextSourceProperty \| None` | 文本源属性 |
| `ShapeLayer` | `contents` | `PropertyGroup \| None` | 形状内容组 |
| `CameraLayer` | `camera_options` | `PropertyGroup \| None` | 摄像机选项组 |
| `LightLayer` | `light_type` | `int` | R/W，灯光类型: 0=平行 1=聚光 2=点 3=环境 |

---

## Property

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `name` | `str` | R | 显示名 |
| `match_name` | `str` | R | 内部 matchName |
| `value` | `Any` | R/W | 静态值或首帧值 |
| `num_keys` | `int` | R | 关键帧数 |
| `is_time_varying` | `bool` | R | 是否有多关键帧 |
| `expression` | `str \| None` | R | 表达式内容 |
| `expression_enabled` | `bool` | R | 表达式是否启用 |
| `dimensions_separated` | `bool` | R | 维度是否分离 |
| `is_spatial` | `bool` | R | 是否空间属性 |
| `property_value_type` | `PropertyValueType` | R | 值类型 |
| `keys` | `list[KeyframeValue]` | R | 所有关键帧列表 |

### 关键帧读取方法

| 方法 | 返回 | 说明 |
|------|------|------|
| `key(index)` | `KeyframeValue` | 关键帧对象 (1-based) |
| `key_value(index)` | `Any` | 关键帧值 |
| `key_time(index)` | `float` | 关键帧时间 (秒) |
| `key_in_interpolation_type(index)` | `KeyframeInterpolationType` | 入插值类型 |
| `key_out_interpolation_type(index)` | `KeyframeInterpolationType` | 出插值类型 |
| `key_in_temporal_ease(index)` | `list[dict]` | 入时间缓动 `[{speed, influence}]` |
| `key_out_temporal_ease(index)` | `list[dict]` | 出时间缓动 |
| `key_in_spatial_tangent(index)` | `list[float] \| None` | 入空间切线 |
| `key_out_spatial_tangent(index)` | `list[float] \| None` | 出空间切线 |
| `key_roving(index)` | `bool` | 是否为漫游关键帧 |
| `nearest_key_index(time)` | `int` | 最近关键帧索引 (1-based) |
| `value_at_time(time)` | `Any` | 在指定时间求值 (线性/保持插值) |

### 关键帧写入方法

| 方法 | 说明 |
|------|------|
| `set_value_at_key(index, value)` | 修改关键帧值 (1-based) |
| `set_interpolation_type_at_key(index, in_type, out_type=None)` | 修改插值类型 |
| `set_temporal_ease_at_key(index, in_ease=None, out_ease=None)` | 修改缓动，ease 格式: `[{speed, influence}]` |
| `set_value_at_time(time, value)` | 修改最近关键帧的值 |

---

## PropertyGroup

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `name` | `str` | R | 显示名 |
| `match_name` | `str` | R | 内部 matchName |
| `enabled` | `bool \| None` | R | 是否启用 |
| `num_properties` | `int` | R | 子属性数量 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `property(name_or_index)` | `Any` | 按名称或索引查找子属性 |
| `group["name"]` | `Any` | 同上，支持 `[]` 和 `()` 语法 |
| `len(group)` | `int` | 子属性数量 |
| `for p in group` | 迭代 | 遍历子属性 |

---

## KeyframeValue

| 属性 | 类型 | 说明 |
|------|------|------|
| `index` | `int` | 1-based 索引 |
| `time` | `float` | 时间 (秒) |
| `value` | `Any` | 值 |

---

## Effect

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `name` | `str` | R | 效果名称 |
| `match_name` | `str` | R | 内部 matchName |
| `enabled` | `bool` | R | 是否启用 |
| `num_params` | `int` | R | 参数数量 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `param(name_or_index)` | `Any` | 按名称或索引获取参数 |
| `effect["name"]` | `Any` | 同上，支持 `[]` 和 `()` 语法 |

---

## Mask

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `name` | `str` | R | 遮罩名称 |
| `match_name` | `str` | R | 内部 matchName |
| `mode` | `MaskMode` | R | 遮罩模式 |
| `inverted` | `bool` | R | 是否反转 |
| `locked` | `bool` | R | 是否锁定 |
| `index` | `int` | R | 1-based 索引 |
| `mask_path` | `Property \| None` | R | 路径属性 |
| `mask_feather` | `Property \| None` | R | 羽化属性 |
| `mask_opacity` | `Property \| None` | R | 不透明度属性 |
| `mask_expansion` | `Property \| None` | R | 扩展属性 |

---

## TextSourceProperty

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `text` | `str` | R | 当前文本内容 |
| `fonts` | `list` | R | 字体列表 |
| `value` | `TextDocument \| None` | R | 当前文本文档 |
| `num_keys` | `int` | R | 关键帧数 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `key_value(index)` | `TextDocument \| None` | 文本关键帧 (1-based) |
| `key_time(index)` | `float` | 关键帧时间 |

---

## MarkerProperty

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `num_keys` | `int` | R | 标记数量 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `key_value(index)` | `MarkerValue` | 标记值 (1-based) |
| `key_time(index)` | `float` | 标记时间 |
| `nearest_key_index(time)` | `int` | 最近标记索引 |

---

## MarkerValue

| 属性 | 类型 | 说明 |
|------|------|------|
| `comment` | `str` | 标记注释 |
| `duration` | `float` | 持续时间 (秒) |
| `label` | `int` | 标签颜色 |
| `time` | `float` | 时间 (秒) |

---

## FolderItem

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `type_name` | `str` | R | 固定 `"Folder"` |
| `name` | `str` | R | 文件夹名 |
| `id` | `int` | R | 内部 ID |
| `num_items` | `int` | R | 子项数 |
| `items` | `ItemCollection` | R | 子项集合 |

---

## FootageItem

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `type_name` | `str` | R | `"Footage"` 或 `"Solid"` |
| `name` | `str` | R | 素材名 |
| `id` | `int` | R | 内部 ID |
| `width` | `int` | R | 宽度 |
| `height` | `int` | R | 高度 |
| `file` | `str \| None` | R/W | 文件路径（写入会更新 chunk tree） |
| `color` | `list[float] \| None` | R | 固态层颜色 RGBA（仅 Solid） |

---

## RenderQueue

| 属性 | 类型 | 访问 | 说明 |
|------|------|------|------|
| `num_items` | `int` | R | 渲染项数量 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `item(index)` | `RenderQueueItemWrapper \| None` | 按 1-based 索引获取 |

### RenderQueueItemWrapper

| 属性 | 类型 | 说明 |
|------|------|------|
| `comp_name` | `str` | 合成名称 |
| `status` | `int` | 渲染状态 |
| `num_output_modules` | `int` | 输出模块数 |

| 方法 | 返回 | 说明 |
|------|------|------|
| `output_module(index)` | `OutputModule \| None` | 按 1-based 索引获取 |

### OutputModule

| 属性 | 类型 | 说明 |
|------|------|------|
| `format` | `str` | 格式 |
| `format_label` | `str` | 格式标签 |
| `template_name` | `str` | 模板名 |
| `file_template` | `str` | 文件模板 |
| `output_path` | `str` | 输出路径 |
| `width` | `int` | 宽度 |
| `height` | `int` | 高度 |

---

## ItemCollection / LayerCollection

| 操作 | 说明 |
|------|------|
| `collection[index]` | 1-based 索引访问 |
| `len(collection)` | 元素数量 |
| `for item in collection` | 遍历 |

---

## 枚举

### BlendingMode

```
NORMAL=2  DISSOLVE=3  ADD=4  MULTIPLY=5  SCREEN=6  OVERLAY=7
SOFT_LIGHT=8  HARD_LIGHT=9  DARKEN=10  LIGHTEN=11
CLASSIC_DIFFERENCE=12  HUE=13  SATURATION=14  COLOR=15  LUMINOSITY=16
STENCIL_ALPHA=17  STENCIL_LUMA=18  SILHOUETTE_ALPHA=19  SILHOUETTE_LUMA=20
LUMINESCENT_PREMUL=21  ALPHA_ADD=22
CLASSIC_COLOR_DODGE=23  CLASSIC_COLOR_BURN=24
EXCLUSION=25  DIFFERENCE=26  COLOR_DODGE=27  COLOR_BURN=28
LINEAR_DODGE=29  LINEAR_BURN=30  LINEAR_LIGHT=31  VIVID_LIGHT=32
PIN_LIGHT=33  HARD_MIX=34  LIGHTER_COLOR=35  DARKER_COLOR=36
SUBTRACT=37  DIVIDE=38
```

### TrackMatteType

```
NONE=0  ALPHA=1  ALPHA_INVERTED=2  LUMA=3  LUMA_INVERTED=4
```

### KeyframeInterpolationType

```
LINEAR=1  BEZIER=2  HOLD=3
```

### LayerQuality

```
WIREFRAME=0  DRAFT=1  BEST=2
```

### MaskMode

```
NONE=0  ADD=1  SUBTRACT=2  INTERSECT=3  DARKEN=4  LIGHTEN=5  DIFFERENCE=6
```

### PropertyValueType

```
COLOR=0  SCALAR=1  SPATIAL=2  MULTIDIMENSIONAL=3  LAYER_REF=4  CUSTOM=5  UINT=6
```

### LayerType

```
ASSET=0  LIGHT=1  CAMERA=2  TEXT=3  SHAPE=4
```

### AutoOrientType

```
NO_AUTO_ORIENT=0  ALONG_PATH=1  CAMERA_OR_POINT_OF_INTEREST=2  CHARACTERS_TOWARD_CAMERA=3
```
