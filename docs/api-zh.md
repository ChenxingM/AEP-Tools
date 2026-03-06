# aep_tools API 参考文档

所有集合索引均为 **1-based**。

---

## Project

表示一个 After Effects 工程。由 `Project.open()` 返回。

### 类方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `Project.open(path)` | `Project` | 打开 `.aep` 或 `.aepx` 文件 |

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `file` | `str \| None` | R | 源文件路径 |
| `ae_version` | `str \| None` | R | 保存此工程的 AE 版本（如 `"25.6"`） |
| `writable` | `bool` | R | 是否支持保存/修改（仅 `.aep`） |
| `num_items` | `int` | R | 顶层元素数量 |
| `items` | `ItemCollection` | R | 顶层元素（1-based） |
| `compositions` | `list[CompItem]` | R | 所有合成 |
| `active_item` | `CompItem \| None` | R | 活动合成 |
| `render_queue` | `RenderQueue` | R | 渲染队列 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `item(index)` | `Any \| None` | 按 1-based 索引获取元素 |
| `comp(name_or_index)` | `CompItem \| None` | 按名称或 1-based 索引获取合成 |
| `save(path=None)` | `None` | 保存为 `.aep`。path 为 None 时覆盖原文件 |
| `change_layer_name(comp_id, layer_id, name)` | `bool` | 重命名图层 |
| `change_property_value(comp_id, layer_id, match_path, value)` | `bool` | 设置属性静态值 |
| `change_keyframe_value(comp_id, layer_id, match_path, key_index, value)` | `bool` | 设置关键帧值 |
| `change_keyframe_time(comp_id, layer_id, match_path, key_index, time)` | `bool` | 设置关键帧时间（秒） |
| `change_keyframe_interpolation(comp_id, layer_id, match_path, key_index, type)` | `bool` | 设置插值（1=线性, 2=贝塞尔, 3=定格） |
| `change_keyframe_ease(comp_id, layer_id, match_path, key_index, ...)` | `bool` | 设置缓动 |
| `change_asset_path(asset_id, new_path)` | `bool` | 设置素材文件路径 |

### 示例

```python
from aep_tools import Project

proj = Project.open("input.aep")
print(proj.ae_version)            # "25.6"
comp = proj.comp("Main Comp")     # 按名称
comp = proj.comp(1)               # 按索引
proj.save("output.aep")
```

---

## CompItem

表示一个合成。

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `name` | `str` | R/W | 合成名称 |
| `id` | `int` | R | 内部 ID |
| `type_name` | `str` | R | 固定为 `"Composition"` |
| `width` | `int` | R | 宽度（像素） |
| `height` | `int` | R | 高度（像素） |
| `duration` | `float` | R | 时长（秒） |
| `frame_rate` | `float` | R | 帧率 |
| `frame_duration` | `float` | R | 单帧时长（`1/frame_rate`） |
| `work_area_start` | `float` | R | 工作区起始（秒） |
| `work_area_duration` | `float` | R | 工作区时长（秒） |
| `bg_color` | `list[float]` | R | 背景颜色 `[r, g, b]` |
| `num_layers` | `int` | R | 图层数量 |
| `layers` | `LayerCollection` | R | 所有图层（1-based） |
| `marker_property` | `MarkerProperty \| None` | R | 合成标记 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `layer(name_or_index)` | `Layer \| None` | 按名称或 1-based 索引获取图层 |

### 示例

```python
comp = proj.comp("Main Comp")
comp.name = "重命名合成"
print(f"{comp.width}x{comp.height} @ {comp.frame_rate}fps")

for layer in comp.layers:
    print(layer.name)
```

---

## Layer

所有图层的基类。子类型：`AVLayer`、`TextLayer`、`ShapeLayer`、`CameraLayer`、`LightLayer`（自动选择）。

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `index` | `int` | R | 合成中的 1-based 索引 |
| `name` | `str` | R/W | 图层名称 |
| `containing_comp` | `CompItem \| None` | R | 所属合成 |
| `label` | `int` | R | 标签颜色索引 |
| `enabled` | `bool` | R | 可见性（眼睛图标） |
| `solo` | `bool` | R | 独奏 |
| `shy` | `bool` | R | 害羞 |
| `locked` | `bool` | R | 锁定 |
| `null_layer` | `bool` | R | 是否空对象 |
| `guide_layer` | `bool` | R | 是否参考线图层 |
| `adjustment_layer` | `bool` | R | 是否调整图层 |
| `three_d_layer` | `bool` | R | 3D 图层 |
| `auto_orient` | `bool` | R | 自动朝向 |
| `effects_active` | `bool` | R | 效果启用 |
| `motion_blur` | `bool` | R | 运动模糊 |
| `collapse_transformation` | `bool` | R | 折叠变换 / 连续光栅化 |
| `sampling_quality` | `bool` | R | 双立方采样 |
| `in_point` | `float` | R | 入点（秒） |
| `out_point` | `float` | R | 出点（秒） |
| `start_time` | `float` | R | 起始时间（秒） |
| `stretch` | `float` | R | 时间拉伸因子 |
| `blending_mode` | `BlendingMode` | R | 混合模式 |
| `track_matte_type` | `TrackMatteType` | R | 轨道遮罩类型 |
| `quality` | `LayerQuality` | R | 渲染质量 |
| `parent` | `Layer \| None` | R | 父图层 |
| `num_properties` | `int` | R | 顶层属性组数量 |
| `num_effects` | `int` | R | 效果数量 |
| `num_masks` | `int` | R | 遮罩数量 |
| `time_remap_enabled` | `bool` | R | 是否存在时间重映射 |
| `time_remap` | `Property \| None` | R | 时间重映射属性 |
| `marker_property` | `MarkerProperty \| None` | R | 图层标记 |

#### Transform 快捷属性

| 属性 | 类型 | 访问 | Match Name |
|---|---|---|---|
| `transform` | `PropertyGroup \| None` | R | `ADBE Transform Group` |
| `position` | `Property \| None` | R | `ADBE Position` |
| `position_x` | `Property \| None` | R | `ADBE Position_0` |
| `position_y` | `Property \| None` | R | `ADBE Position_1` |
| `position_z` | `Property \| None` | R | `ADBE Position_2` |
| `scale` | `Property \| None` | R | `ADBE Scale` |
| `rotation` | `Property \| None` | R | `ADBE Rotate Z` |
| `rotation_x` | `Property \| None` | R | `ADBE Rotate X` |
| `rotation_y` | `Property \| None` | R | `ADBE Rotate Y` |
| `rotation_z` | `Property \| None` | R | `ADBE Rotate Z` |
| `opacity` | `Property \| None` | R | `ADBE Opacity` |
| `anchor_point` | `Property \| None` | R | `ADBE Anchor Point` |
| `orientation` | `Property \| None` | R | `ADBE Orientation` |

> 返回 `Property` 对象，其 `.value` 支持读写。位置分离时请使用 `position_x`/`position_y` 代替 `position`。不存在的属性返回 `None`。

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | 按 match name、显示名或 1-based 索引获取属性 |
| `effect(name_or_index)` | `Effect \| None` | 按名称或 1-based 索引获取效果 |
| `mask(index)` | `Mask \| None` | 按 1-based 索引获取遮罩 |

### 属性访问（三种等效方式）

```python
layer.property("Transform")     # 未找到返回 None
layer("Transform")              # 未找到抛出 KeyError
layer["Transform"]              # 未找到抛出 KeyError
```

**名称解析顺序：** 精确 match_name > 显示名 > 不区分大小写 > 模型 `.name`

### 示例

```python
layer = comp.layer(1)
layer.name = "背景"
print(layer.position.value)       # [960, 540]
print(layer.opacity.value)        # 1.0
print(layer.in_point)             # 0.0

# 链式访问
layer("Transform")("Position").value
```

---

## AVLayer（继承 Layer）

素材图层（footage、solid、预合成）。

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `source` | `Any \| None` | R | 来源素材（ImageAsset、SolidAsset、Composition） |

---

## TextLayer（继承 Layer）

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `source_text` | `TextSourceProperty \| None` | R | 文字源属性 |

```python
layer.source_text.text     # "Hello World"
layer.source_text.fonts    # ["Arial"]
```

---

## ShapeLayer（继承 Layer）

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `contents` | `PropertyGroup \| None` | R | 形状内容组（`ADBE Root Vectors Group`） |

---

## CameraLayer（继承 Layer）

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `camera_options` | `PropertyGroup \| None` | R | 摄像机选项组 |

---

## LightLayer（继承 Layer）

无额外属性。

---

## Property

封装单个动画属性（位置、不透明度、缩放等）。

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `name` | `str` | R | 显示名称 |
| `match_name` | `str` | R | AE 内部 match name |
| `value` | `Any` | R/W | 静态值（或第一个关键帧的值） |
| `num_keys` | `int` | R | 关键帧数量（0 = 无动画） |
| `is_time_varying` | `bool` | R | 是否有多个关键帧 |
| `expression` | `str \| None` | R | 表达式字符串 |
| `expression_enabled` | `bool` | R | 是否设置了表达式 |
| `dimensions_separated` | `bool` | R | 位置是否分离为 X/Y/Z |
| `is_spatial` | `bool` | R | 是否空间属性 |
| `property_value_type` | `PropertyValueType` | R | 值类型枚举 |
| `keys` | `list[KeyframeValue]` | R | 所有关键帧 |

### 关键帧读取方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `key(index)` | `KeyframeValue` | 1-based 索引的关键帧 |
| `key_value(index)` | `Any` | 关键帧的值 |
| `key_time(index)` | `float` | 关键帧时间（秒） |
| `key_in_interpolation_type(index)` | `KeyframeInterpolationType` | 入方向插值 |
| `key_out_interpolation_type(index)` | `KeyframeInterpolationType` | 出方向插值 |
| `key_in_temporal_ease(index)` | `list[dict]` | 入方向缓动 `[{"speed", "influence"}]` |
| `key_out_temporal_ease(index)` | `list[dict]` | 出方向缓动 `[{"speed", "influence"}]` |
| `key_in_spatial_tangent(index)` | `list[float] \| None` | 入方向空间切线 |
| `key_out_spatial_tangent(index)` | `list[float] \| None` | 出方向空间切线 |
| `key_roving(index)` | `bool` | 是否漫游关键帧 |
| `nearest_key_index(t)` | `int` | 最近关键帧的索引 |
| `value_at_time(t)` | `Any` | 时间 `t` 处的插值结果 |

### 关键帧写入方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `set_value_at_key(index, value)` | `None` | 设置关键帧值 |
| `set_value_at_time(time, value)` | `None` | 设置最近关键帧的值 |
| `set_interpolation_type_at_key(index, in_type, out_type=None)` | `None` | 设置入/出插值类型 |
| `set_temporal_ease_at_key(index, in_ease=None, out_ease=None)` | `None` | 设置缓动 |

### 值类型

| AE 类型 | Python 类型 |
|---|---|
| 2D 位置 / 向量 | `[x, y]` |
| 3D 位置 / 向量 | `[x, y, z]` |
| 颜色 | `[r, g, b, a]` |
| 标量（不透明度、旋转等） | `float` |
| 图层引用 | `int`（图层 ID） |

> 缩放和不透明度以 0-1 分数存储（1.0 = 100%）。

### 示例

```python
pos = layer.position

# 读取
pos.value                     # [960, 540]
pos.num_keys                  # 2
pos.key_value(1)              # [0, 0]
pos.key_time(2)               # 1.0
pos.value_at_time(0.5)        # [480, 270]

# 写入静态值
pos.value = [500.0, 300.0]

# 写入关键帧
pos.set_value_at_key(1, [100.0, 200.0])

# 写入插值
from aep_tools import KeyframeInterpolationType as KIT
pos.set_interpolation_type_at_key(1, in_type=KIT.BEZIER, out_type=KIT.HOLD)

# 写入缓动
pos.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 0.0, "influence": 33.33}],
)
```

---

## PropertyGroup

封装属性组。支持链式访问。

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `name` | `str` | R | 组名称 |
| `match_name` | `str` | R | AE match name |
| `enabled` | `bool \| None` | R | 启用状态 |
| `num_properties` | `int` | R | 子属性数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | 按名称或 1-based 索引获取子属性 |

支持 `__call__`、`__getitem__`、`__len__`、`__iter__`。

### 示例

```python
transform = layer("Transform")
transform("Position").value         # [960, 540]
transform.property(1).value         # 锚点
len(transform)                      # 子属性数量

for prop in transform:
    print(prop.name)
```

---

## Effect

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `name` | `str` | R | 效果名称 |
| `match_name` | `str` | R | AE match name |
| `enabled` | `bool` | R | 启用状态 |
| `num_params` | `int` | R | 参数数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `param(name_or_index)` | `Any \| None` | 按名称或 1-based 索引获取参数 |

支持 `__call__` 和 `__getitem__`。

### 示例

```python
eff = layer.effect(1)
eff = layer.effect("Gaussian Blur")
eff.param(1).value                   # 第一个参数
eff("Blurriness").value              # 按名称
```

---

## Mask

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `name` | `str` | R | 遮罩名称 |
| `match_name` | `str` | R | AE match name |
| `mode` | `MaskMode` | R | 遮罩模式 |
| `inverted` | `bool` | R | 是否反转 |
| `locked` | `bool` | R | 是否锁定 |
| `index` | `int` | R | 1-based 索引 |
| `mask_path` | `Property \| None` | R | 遮罩路径形状 |
| `mask_feather` | `Property \| None` | R | 羽化 |
| `mask_opacity` | `Property \| None` | R | 不透明度 |
| `mask_expansion` | `Property \| None` | R | 扩展 |

### 示例

```python
m = layer.mask(1)
m.mode                    # MaskMode.ADD
m.mask_opacity.value      # 100.0
```

---

## MarkerProperty

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `num_keys` | `int` | R | 标记数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `key_value(index)` | `MarkerValue` | 1-based 索引的标记 |
| `key_time(index)` | `float` | 标记时间（秒） |
| `nearest_key_index(t)` | `int` | 最近标记的索引 |

---

## MarkerValue

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `comment` | `str` | R | 注释文本 |
| `duration` | `float` | R | 时长（秒） |
| `label` | `int` | R | 标签颜色索引 |
| `time` | `float` | R | 时间（秒） |

### 示例

```python
mp = comp.marker_property
mv = mp.key_value(1)
print(mv.comment, mv.time)    # "Intro" 1.0
```

---

## TextSourceProperty

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `text` | `str` | R | 当前文本字符串 |
| `value` | `TextDocument \| None` | R | 完整 TextDocument |
| `fonts` | `list[str]` | R | 字体名称列表 |
| `num_keys` | `int` | R | 文本关键帧数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `key_value(index)` | `TextDocument \| None` | 关键帧处的 TextDocument |
| `key_time(index)` | `float` | 关键帧时间（秒） |

---

## KeyframeValue

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `index` | `int` | R | 1-based 索引 |
| `time` | `float` | R | 时间（秒） |
| `value` | `Any` | R | 值 |

---

## FolderItem

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `type_name` | `str` | R | `"Folder"` |
| `name` | `str` | R | 文件夹名称 |
| `id` | `int` | R | 内部 ID |
| `num_items` | `int` | R | 子元素数量 |
| `items` | `ItemCollection` | R | 子元素（1-based） |

---

## FootageItem

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `type_name` | `str` | R | `"Footage"` 或 `"Solid"` |
| `name` | `str` | R | 元素名称 |
| `id` | `int` | R | 内部 ID |
| `width` | `int` | R | 宽度（像素） |
| `height` | `int` | R | 高度（像素） |
| `file` | `str \| None` | R/W | 文件路径（仅 footage） |
| `color` | `list[float] \| None` | R | `[r, g, b, a]`（仅 solid） |

### 示例

```python
item = proj.item(1)
print(item.file)                     # "/path/to/footage.mov"
item.file = "/new/path.mov"          # 修改路径
proj.save("output.aep")
```

---

## RenderQueue

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `num_items` | `int` | R | 渲染队列项数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `item(index)` | `RenderQueueItem \| None` | 按 1-based 索引获取 |

---

## RenderQueueItem

### 属性

| 属性 | 类型 | 访问 | 说明 |
|---|---|---|---|
| `comp_name` | `str` | R | 合成名称 |
| `status` | `int` | R | 渲染状态 |
| `num_output_modules` | `int` | R | 输出模块数量 |

### 方法

| 方法 | 返回 | 说明 |
|---|---|---|
| `output_module(index)` | `OutputModule \| None` | 按 1-based 索引获取 |

---

## 枚举

### BlendingMode

| 值 | 名称 |
|---|---|
| 1 | NORMAL |
| 3 | DARKEN |
| 4 | MULTIPLY |
| 5 | COLOR_BURN |
| 6 | LINEAR_BURN |
| 7 | DARKER_COLOR |
| 9 | LIGHTEN |
| 10 | SCREEN |
| 11 | COLOR_DODGE |
| 12 | LINEAR_DODGE |
| 13 | LIGHTER_COLOR |
| 15 | OVERLAY |
| 16 | SOFT_LIGHT |
| 17 | HARD_LIGHT |
| 18 | LINEAR_LIGHT |
| 19 | VIVID_LIGHT |
| 20 | PIN_LIGHT |
| 21 | HARD_MIX |
| 23 | DIFFERENCE |
| 24 | EXCLUSION |
| 26 | HUE |
| 27 | SATURATION |
| 28 | COLOR |
| 29 | LUMINOSITY |

### TrackMatteType

| 值 | 名称 |
|---|---|
| 0 | NONE |
| 1 | ALPHA |
| 2 | ALPHA_INVERTED |
| 3 | LUMA |
| 4 | LUMA_INVERTED |

### MaskMode

| 值 | 名称 |
|---|---|
| 0 | NONE |
| 1 | ADD |
| 2 | SUBTRACT |
| 3 | INTERSECT |
| 4 | DARKEN |
| 5 | LIGHTEN |
| 6 | DIFFERENCE |

### KeyframeInterpolationType

| 值 | 名称 |
|---|---|
| 1 | LINEAR |
| 2 | BEZIER |
| 3 | HOLD |

### LayerQuality

| 值 | 名称 |
|---|---|
| 0 | WIREFRAME |
| 1 | DRAFT |
| 2 | BEST |

### LayerType

| 值 | 名称 |
|---|---|
| 0 | ASSET |
| 1 | LIGHT |
| 2 | CAMERA |
| 3 | TEXT |
| 4 | SHAPE |

### PropertyValueType

| 值 | 名称 |
|---|---|
| 0 | COLOR |
| 1 | SCALAR |
| 2 | SPATIAL |
| 3 | MULTIDIMENSIONAL |
| 4 | LAYER_REF |
| 5 | CUSTOM |
| 6 | UINT |

### AutoOrientType

| 值 | 名称 |
|---|---|
| 0 | NO_AUTO_ORIENT |
| 1 | ALONG_PATH |
| 2 | CAMERA_OR_POINT_OF_INTEREST |
| 3 | CHARACTERS_TOWARD_CAMERA |

---

## Match Name 参考

| Match Name | 显示名称 |
|---|---|
| `ADBE Transform Group` | Transform |
| `ADBE Anchor Point` | Anchor Point |
| `ADBE Position` | Position |
| `ADBE Position_0` / `_1` / `_2` | X / Y / Z Position |
| `ADBE Scale` | Scale |
| `ADBE Rotate X` / `Y` / `Z` | X / Y / Z Rotation |
| `ADBE Opacity` | Opacity |
| `ADBE Orientation` | Orientation |
| `ADBE Effect Parade` | Effects |
| `ADBE Mask Parade` | Masks |
| `ADBE Time Remapping` | Time Remap |
| `ADBE Marker` | Marker |
| `ADBE Text Properties` | Text |
| `ADBE Text Document` | Source Text |
| `ADBE Root Vectors Group` | Contents |
| `ADBE Camera Options Group` | Camera Options |
| `ADBE Mask Shape` | Mask Path |
| `ADBE Mask Feather` | Mask Feather |
| `ADBE Mask Opacity` | Mask Opacity |
| `ADBE Mask Offset` | Mask Expansion |

match name 和显示名称均可用于属性查找。
