# aep_tools API 参考文档

用于 After Effects 工程文件（`.aep` / `.aepx`）的 AE 脚本风格 API。

API 设计参照 [After Effects ExtendScript](https://ae-scripting.docsforadobe.dev/)，使用 1-based 索引和链式属性访问。

> **读写标注：** 标记 **RW** 的属性支持读写（可修改并保存回 `.aep`）。其余属性为**只读**。写入功能需要从二进制 `.aep` 文件打开项目（`proj.writable == True`）。

---

## 快速开始

```python
from aep_tools import Project

proj = Project.open("my_project.aep")
comp = proj.comp("Main Comp")
layer = comp.layer(1)

# 读取属性
print(layer.position.value)        # [960, 540]
print(layer.opacity.num_keys)      # 3

# AE 风格链式访问
layer("Transform")("Position").key_value(1)

# 修改并保存
layer.position.value = [500.0, 300.0]
layer.position.set_value_at_key(1, [0.0, 0.0])
proj.save("output.aep")
```

---

## 打开项目

### `Project.open(path)`

根据扩展名自动检测 `.aep` / `.aepx`。

```python
proj = Project.open("path/to/project.aep")
proj = Project.open("path/to/project.aepx")
```

### `open_aep(path)` / `open_aepx(path)`

直接打开指定格式。

```python
from aep_tools import open_aep, open_aepx
proj = open_aep("binary.aep")
proj = open_aepx("xml.aepx")
```

### `load_project(model)`

包装已解析的 `aep_parser.models.Project` 模型。

```python
from aep_parser import parse_aep
from aep_tools import load_project
model = parse_aep(data)
proj = load_project(model)
```

---

## Project

| 属性 / 方法 | 类型 | 读写 | 说明 |
|---|---|---|---|
| `file` | `str \| None` | R | 文件路径（从文件打开时） |
| `ae_version` | `str \| None` | R | 上次保存此文件的 AE 版本（如 `"25.6"`） |
| `writable` | `bool` | R | 从二进制 `.aep` 加载时为 `True`（支持保存/修改） |
| `compositions` | `list[CompItem]` | R | 所有合成 |
| `comp(name_or_index)` | `CompItem \| None` | R | 按名称或 1-based 索引查找 |
| `num_items` | `int` | R | 顶层项目元素数量 |
| `items` | `ItemCollection` | R | 所有顶层元素（1-based） |
| `item(index)` | `Any \| None` | R | 按 1-based 索引获取元素 |
| `active_item` | `CompItem \| None` | R | 活动合成（如果可用） |
| `render_queue` | `RenderQueue` | R | 渲染队列 |
| `save(path)` | `None` | — | 保存为 `.aep` 文件（需要 `writable`） |

### 底层写入方法

直接操作 chunk tree。大多数场景建议使用属性级别的 setter（如 `layer.position.value = ...`）。

| 方法 | 返回 | 说明 |
|---|---|---|
| `change_layer_name(comp_id, layer_id, new_name)` | `bool` | 重命名图层 |
| `change_property_value(comp_id, layer_id, match_path, value)` | `bool` | 修改属性静态值 |
| `change_keyframe_value(comp_id, layer_id, match_path, key_index, value)` | `bool` | 修改关键帧值 |
| `change_keyframe_time(comp_id, layer_id, match_path, key_index, time)` | `bool` | 修改关键帧时间 |
| `change_keyframe_interpolation(comp_id, layer_id, match_path, key_index, type)` | `bool` | 修改插值类型（1=线性, 2=贝塞尔, 3=定格） |
| `change_keyframe_ease(comp_id, layer_id, match_path, key_index, ...)` | `bool` | 修改缓动（速度/影响） |
| `change_asset_path(asset_id, new_path)` | `bool` | 修改素材资产文件路径 |

---

## CompItem

| 属性 / 方法 | 类型 | 读写 | 说明 |
|---|---|---|---|
| `name` | `str` | **RW** | 合成名称 |
| `id` | `int` | R | 内部 ID |
| `width` | `int` | R | 宽度（像素） |
| `height` | `int` | R | 高度（像素） |
| `duration` | `float` | R | 时长（秒） |
| `frame_rate` | `float` | R | 帧率 |
| `frame_duration` | `float` | R | `1.0 / frame_rate` |
| `work_area_start` | `float` | R | 工作区起始（秒） |
| `work_area_duration` | `float` | R | 工作区时长（秒） |
| `bg_color` | `list[float]` | R | 背景颜色 `[r, g, b]` |
| `num_layers` | `int` | R | 图层数量 |
| `layers` | `LayerCollection` | R | 所有图层（1-based） |
| `layer(name_or_index)` | `Layer \| None` | R | 按名称或 1-based 索引查找 |
| `marker_property` | `MarkerProperty \| None` | R | 合成标记 |

```python
comp = proj.comp("Main Comp")
comp.name = "重命名合成"       # 写回 .aep
comp.layer(1)                   # 第一个图层
comp.layer("Background")        # 按名称
for layer in comp.layers:
    print(layer.name)
```

---

## Layer

基类。实际图层会自动选择为子类：`AVLayer`、`TextLayer`、`ShapeLayer`、`CameraLayer`、`LightLayer`。

### 标识

| 属性 | 类型 | 读写 | 说明 |
|---|---|---|---|
| `index` | `int` | R | 合成中的 1-based 索引 |
| `name` | `str` | **RW** | 图层名称 |
| `containing_comp` | `CompItem \| None` | R | 父合成 |
| `label` | `int` | R | 标签颜色索引 |

### 标志（全部只读）

| 属性 | 类型 | 说明 |
|---|---|---|
| `enabled` | `bool` | 可见性（眼睛图标） |
| `solo` | `bool` | 独奏 |
| `shy` | `bool` | 害羞 |
| `locked` | `bool` | 锁定 |
| `null_layer` | `bool` | 是否空对象 |
| `guide_layer` | `bool` | 是否参考线图层 |
| `adjustment_layer` | `bool` | 是否调整图层 |
| `three_d_layer` | `bool` | 3D 图层 |
| `auto_orient` | `bool` | 自动朝向 |
| `effects_active` | `bool` | 效果启用 |
| `motion_blur` | `bool` | 运动模糊 |
| `collapse_transformation` | `bool` | 折叠变换 / 连续光栅化 |
| `sampling_quality` | `bool` | 双立方采样 |

### 时间（全部只读）

| 属性 | 类型 | 说明 |
|---|---|---|
| `in_point` | `float` | 入点（秒） |
| `out_point` | `float` | 出点（秒） |
| `start_time` | `float` | 起始时间（秒） |
| `stretch` | `float` | 时间拉伸因子 |

### 混合 / 遮罩（全部只读）

| 属性 | 类型 | 说明 |
|---|---|---|
| `blending_mode` | `BlendingMode \| int` | 混合模式枚举 |
| `track_matte_type` | `TrackMatteType \| int` | 轨道遮罩类型 |
| `quality` | `LayerQuality` | 渲染质量 |

### 父级

| 属性 | 类型 | 说明 |
|---|---|---|
| `parent` | `Layer \| None` | 父图层（按 ID 自动解析） |

### 属性访问

三种等效方式访问属性树：

```python
layer.property("Transform")        # 方法
layer("Transform")                 # __call__（未找到抛出 KeyError）
layer["Transform"]                 # __getitem__（未找到抛出 KeyError）
```

| 方法 | 类型 | 说明 |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | 按 match_name、显示名或 1-based 索引查找 |
| `num_properties` | `int` | 顶层属性组数量 |

**名称解析顺序：**
1. 精确 `match_name`（如 `"ADBE Transform Group"`）
2. 显示名通过 `DISPLAY_NAMES` 反向映射（如 `"Transform"`）
3. 不区分大小写的显示名比较
4. 模型 `.name` 属性（用户自定义名称）

### Transform 快捷属性

直接访问常用变换属性。每个返回 `Property`（可通过 `.value` setter 读写）或 `None`：

| 属性 | Match Name | 说明 |
|---|---|---|
| `transform` | `ADBE Transform Group` | 变换组 |
| `position` | `ADBE Position` | 位置（合并） |
| `position_x` | `ADBE Position_0` | X 位置（分离时） |
| `position_y` | `ADBE Position_1` | Y 位置（分离时） |
| `position_z` | `ADBE Position_2` | Z 位置（分离时） |
| `scale` | `ADBE Scale` | 缩放 |
| `rotation` | `ADBE Rotate Z` | 旋转（2D / Z 旋转） |
| `rotation_x` | `ADBE Rotate X` | X 旋转 |
| `rotation_y` | `ADBE Rotate Y` | Y 旋转 |
| `rotation_z` | `ADBE Rotate Z` | Z 旋转 |
| `opacity` | `ADBE Opacity` | 不透明度 |
| `anchor_point` | `ADBE Anchor Point` | 锚点 |
| `orientation` | `ADBE Orientation` | 方向（3D） |

> **注意：** 当位置被分离为维度时，`layer.position` 返回 `None`。请改用 `layer.position_x` / `layer.position_y`。未从默认值修改的属性可能不在解析数据中。

### 时间重映射

| 属性 | 类型 | 说明 |
|---|---|---|
| `time_remap_enabled` | `bool` | 是否存在时间重映射 |
| `time_remap` | `Property \| None` | 时间重映射属性 |

### 效果

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `num_effects` | `int` | 效果数量 |
| `effect(name_or_index)` | `Effect \| None` | 按 1-based 索引或名称获取 |

### 遮罩

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `num_masks` | `int` | 遮罩数量 |
| `mask(index)` | `Mask \| None` | 按 1-based 索引获取 |

### 标记

| 属性 | 类型 | 说明 |
|---|---|---|
| `marker_property` | `MarkerProperty \| None` | 图层标记 |

---

## Layer 子类

### AVLayer

素材图层（footage、solid、预合成）。继承所有 `Layer` 属性。

| 属性 | 类型 | 说明 |
|---|---|---|
| `source` | `Any \| None` | 来源素材 |

### TextLayer

| 属性 | 类型 | 说明 |
|---|---|---|
| `source_text` | `TextSourceProperty \| None` | 文字源属性 |

```python
layer.source_text.text     # "Hello World"
layer.source_text.fonts    # ["Arial"]
```

### ShapeLayer

| 属性 | 类型 | 说明 |
|---|---|---|
| `contents` | `PropertyGroup \| None` | 形状内容组 |

### CameraLayer

| 属性 | 类型 | 说明 |
|---|---|---|
| `camera_options` | `PropertyGroup \| None` | 摄像机选项组 |

### LightLayer

未来扩展。继承所有 `Layer` 属性。

---

## Property

封装单个动画属性值。

### 读取属性

| 属性 | 类型 | 说明 |
|---|---|---|
| `name` | `str` | 显示名称 |
| `match_name` | `str` | AE 内部 match name |
| `value` | `Any` | **RW** — 当前值（静态值或第一个关键帧） |
| `num_keys` | `int` | 关键帧数量 |
| `is_time_varying` | `bool` | 是否有多个关键帧 |
| `expression` | `str \| None` | 表达式字符串 |
| `expression_enabled` | `bool` | 是否存在表达式 |
| `dimensions_separated` | `bool` | 位置是否分离为 X/Y/Z |
| `is_spatial` | `bool` | 是否空间属性 |
| `property_value_type` | `PropertyValueType` | 值类型枚举 |
| `keys` | `list[KeyframeValue]` | 所有关键帧（1-based 索引） |

### 值类型

值以纯 Python 类型返回：

| 模型类型 | Python 类型 |
|---|---|
| `Vector(x, y)` | `[x, y]` |
| `Vector(x, y, z)` | `[x, y, z]` |
| `Color(r, g, b, a)` | `[r, g, b, a]` |
| `float` | `float` |
| `LayerRef` | `int`（图层 ID） |

### 设置静态值

```python
layer.position.value = [500.0, 300.0]     # 设置位置
layer.opacity.value = 0.5                  # 设置不透明度为 50%
layer.scale.value = [1.2, 1.2, 1.2]       # 设置缩放为 120%
```

> **注意：** AE 内部以 0-1 分数存储缩放和不透明度（1.0 = 100%）。

### 关键帧读取方法

所有关键帧索引为 **1-based**。

| 方法 | 返回 | 说明 |
|---|---|---|
| `key(index)` | `KeyframeValue` | 指定索引的关键帧 |
| `key_value(index)` | `Any` | 关键帧的值 |
| `key_time(index)` | `float` | 关键帧时间（秒） |
| `key_in_interpolation_type(index)` | `KeyframeInterpolationType` | 入方向插值 |
| `key_out_interpolation_type(index)` | `KeyframeInterpolationType` | 出方向插值 |
| `key_in_temporal_ease(index)` | `list[dict]` | `[{"speed": ..., "influence": ...}]` |
| `key_out_temporal_ease(index)` | `list[dict]` | `[{"speed": ..., "influence": ...}]` |
| `key_in_spatial_tangent(index)` | `list[float] \| None` | 入方向空间切线 |
| `key_out_spatial_tangent(index)` | `list[float] \| None` | 出方向空间切线 |
| `key_roving(index)` | `bool` | 是否漫游关键帧 |
| `nearest_key_index(t)` | `int` | 最近关键帧的 1-based 索引 |

### 关键帧写入方法

| 方法 | 说明 |
|---|---|
| `set_value_at_key(key_index, value)` | 设置关键帧值（1-based 索引） |
| `set_value_at_time(time, value)` | 设置最近时间关键帧的值 |
| `set_interpolation_type_at_key(key_index, in_type, out_type=None)` | 设置入/出插值 |
| `set_temporal_ease_at_key(key_index, in_ease=None, out_ease=None)` | 设置缓动 |

```python
pos = layer.position

# 读取
pos.value                      # [960, 540]
pos.num_keys                   # 2
pos.key_value(1)               # [0, 0]
pos.key_time(2)                # 1.0
pos.value_at_time(0.5)         # [480, 270]

# 写入关键帧值
pos.set_value_at_key(1, [100.0, 200.0])

# 写入插值类型
from aep_tools import KeyframeInterpolationType
pos.set_interpolation_type_at_key(
    1,
    in_type=KeyframeInterpolationType.BEZIER,
    out_type=KeyframeInterpolationType.HOLD,
)

# 写入缓动
pos.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 0.0, "influence": 33.33}],
)
```

#### 插值语义

在 AEP 二进制中，每个关键帧存储一个 `transition_type` 控制**出方向**曲线。因此：
- `out_type` 设置当前关键帧的 transition_type
- `in_type` 设置**前一个**关键帧的 transition_type（key_index - 1）

如果 `out_type` 为 `None`，默认与 `in_type` 相同（与 AE 只指定一个类型时的行为一致）。

### 插值计算

| 方法 | 返回 | 说明 |
|---|---|---|
| `value_at_time(t)` | `Any` | 在时间 `t` 求值（线性 + 定格插值） |

---

## PropertyGroup

封装属性组。支持链式访问、索引和迭代。所有属性**只读**。

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `name` | `str` | 组名称 |
| `match_name` | `str` | AE match name |
| `enabled` | `bool \| None` | 启用状态（可切换的组） |
| `num_properties` | `int` | 子属性数量 |
| `property(name_or_index)` | `Any \| None` | 查找子属性 |

### 访问模式

```python
group.property("Opacity")    # 按名称
group.property(1)            # 按 1-based 索引
group("Opacity")             # __call__（抛出 KeyError）
group["Opacity"]             # __getitem__（抛出 KeyError）
len(group)                   # num_properties
for prop in group:           # 迭代子属性
    print(prop.name)
```

---

## Effect

所有属性**只读**。

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `name` | `str` | 效果显示名称 |
| `match_name` | `str` | AE match name |
| `enabled` | `bool` | 启用状态 |
| `num_params` | `int` | 参数数量 |
| `param(name_or_index)` | `Any \| None` | 按名称或 1-based 索引获取参数 |

支持 `__call__` 和 `__getitem__`：

```python
layer.effect(1)                 # 第一个效果
layer.effect("Gaussian Blur")   # 按名称
eff = layer.effect(1)
eff.param(1).value              # 第一个参数值
eff("Blurriness").value         # 按参数名
```

---

## Mask

所有属性**只读**。

| 属性 | 类型 | 说明 |
|---|---|---|
| `name` | `str` | 遮罩名称 |
| `match_name` | `str` | AE match name |
| `mode` | `MaskMode` | 遮罩模式（ADD, SUBTRACT 等） |
| `inverted` | `bool` | 是否反转 |
| `locked` | `bool` | 是否锁定 |
| `index` | `int` | 1-based 索引 |
| `mask_path` | `Property \| None` | 遮罩路径形状 |
| `mask_feather` | `Property \| None` | 羽化 |
| `mask_opacity` | `Property \| None` | 不透明度 |
| `mask_expansion` | `Property \| None` | 扩展 |

```python
m = layer.mask(1)
m.mode                    # MaskMode.ADD
m.mask_opacity.value      # 100.0
```

---

## MarkerProperty / MarkerValue

所有属性**只读**。

### MarkerProperty

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `num_keys` | `int` | 标记数量 |
| `key_value(index)` | `MarkerValue` | 1-based 索引的标记 |
| `key_time(index)` | `float` | 标记时间 |
| `nearest_key_index(t)` | `int` | 最近标记索引 |

### MarkerValue

| 属性 | 类型 | 说明 |
|---|---|---|
| `comment` | `str` | 标记注释文本 |
| `duration` | `float` | 时长（秒） |
| `label` | `int` | 标签颜色索引 |
| `time` | `float` | 时间（秒） |

```python
mp = comp.marker_property
mv = mp.key_value(1)
print(mv.comment, mv.time)    # "Intro" 1.0
```

---

## TextSourceProperty

所有属性**只读**。

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `text` | `str` | 当前文本字符串 |
| `value` | `TextDocument \| None` | 完整 TextDocument 对象 |
| `fonts` | `list[str]` | 字体名称列表 |
| `num_keys` | `int` | 文本关键帧数量 |
| `key_value(index)` | `TextDocument \| None` | 关键帧处的 TextDocument |
| `key_time(index)` | `float` | 关键帧时间 |

---

## KeyframeValue

所有属性**只读**。

| 属性 | 类型 | 说明 |
|---|---|---|
| `index` | `int` | 1-based 索引 |
| `time` | `float` | 时间（秒） |
| `value` | `Any` | 转换后的值 |

---

## 项目元素

### FolderItem

所有属性**只读**。

| 属性 | 类型 | 说明 |
|---|---|---|
| `type_name` | `str` | `"Folder"` |
| `name` | `str` | 文件夹名称 |
| `id` | `int` | 内部 ID |
| `num_items` | `int` | 子元素数量 |
| `items` | `ItemCollection` | 子元素（1-based） |

### FootageItem

| 属性 | 类型 | 读写 | 说明 |
|---|---|---|---|
| `type_name` | `str` | R | `"Footage"` 或 `"Solid"` |
| `name` | `str` | R | 元素名称 |
| `id` | `int` | R | 内部 ID |
| `width` | `int` | R | 宽度（像素） |
| `height` | `int` | R | 高度（像素） |
| `file` | `str \| None` | **RW** | 文件路径（仅 footage，对 solid 抛出 `TypeError`） |
| `color` | `list[float] \| None` | R | `[r, g, b, a]`（仅 solid） |

```python
# 读取素材路径
item = proj.item(1)
print(item.file)              # "/path/to/footage.mov"

# 修改素材路径
item.file = "/new/path/to/footage.mov"
proj.save("output.aep")
```

### RenderQueue

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `num_items` | `int` | 渲染队列项数量 |
| `item(index)` | `RenderQueueItem \| None` | 按 1-based 索引获取 |

### RenderQueueItem

| 属性 / 方法 | 类型 | 说明 |
|---|---|---|
| `comp_name` | `str` | 合成名称 |
| `status` | `int` | 渲染状态码 |
| `num_output_modules` | `int` | 输出模块数量 |
| `output_module(index)` | `OutputModule \| None` | 按 1-based 索引获取 |

---

## 写回（仅限二进制 .aep）

从二进制 `.aep` 文件打开的项目支持修改和保存。`writable` 属性指示是否可用。

### 保存

```python
proj = Project.open("input.aep")
assert proj.writable  # .aep 为 True，.aepx 为 False

# 保存到新文件
proj.save("output.aep")

# 覆盖原文件
proj.save()
```

### 属性级别写入（推荐）

最简单的修改方式 — 直接使用属性 setter：

```python
comp = proj.comp("Main Comp")
layer = comp.layer(1)

# 静态值
layer.position.value = [500.0, 300.0]
layer.opacity.value = 0.5

# 关键帧值
layer.position.set_value_at_key(1, [100.0, 200.0])

# 关键帧插值
from aep_tools import KeyframeInterpolationType
layer.position.set_interpolation_type_at_key(1,
    in_type=KeyframeInterpolationType.LINEAR,
    out_type=KeyframeInterpolationType.BEZIER,
)

# 关键帧缓动
layer.position.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 100.0, "influence": 33.33}],
)

# 合成名称
comp.name = "新合成名称"

# 素材文件路径
footage = proj.item(3)  # FootageItem
footage.file = "/new/path/to/file.mov"

proj.save("output.aep")
```

### 底层写入（Project 方法）

需要直接控制 ID 和 match name 路径时使用：

```python
# 重命名图层
proj.change_layer_name(comp.id, layer._model.id, "新名称")

# 修改静态属性值
proj.change_property_value(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    [500.0, 300.0]
)

# 修改关键帧值（1-based 索引）
proj.change_keyframe_value(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, [100.0, 200.0]
)

# 修改关键帧时间
proj.change_keyframe_time(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, 2.5  # 新时间（秒）
)

# 修改关键帧插值（1=线性, 2=贝塞尔, 3=定格）
proj.change_keyframe_interpolation(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, 3  # 定格
)

# 修改关键帧缓动
proj.change_keyframe_ease(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1,
    in_speed=[0.0], in_influence=[33.33],
    out_speed=[0.0], out_influence=[33.33],
)

# 修改素材路径
proj.change_asset_path(asset_id, "/new/path/to/file.mov")

proj.save("output.aep")
```

> **注意：** AE 内部以 0-1 分数存储缩放和不透明度（1.0 = 100%）。写入值时请使用分数而非百分比。如果 Transform 属性（锚点、位置、缩放、旋转、不透明度）在二进制中不存在，会自动以正确的 chunk 结构创建。

### 版本信息

```python
proj.ae_version    # "25.6" — 上次保存此文件的 AE 版本（.aepx 返回 None）
```

---

## 读写总结

| 内容 | 读取 | 写入（属性级别） | 写入（底层） |
|---|---|---|---|
| 合成名称 | `comp.name` | `comp.name = "..."` | — |
| 图层名称 | `layer.name` | `layer.name = "..."` | `proj.change_layer_name(...)` |
| 属性静态值 | `prop.value` | `prop.value = ...` | `proj.change_property_value(...)` |
| 关键帧值 | `prop.key_value(i)` | `prop.set_value_at_key(i, v)` | `proj.change_keyframe_value(...)` |
| 关键帧时间 | `prop.key_time(i)` | — | `proj.change_keyframe_time(...)` |
| 关键帧插值 | `prop.key_in/out_interpolation_type(i)` | `prop.set_interpolation_type_at_key(i, in, out)` | `proj.change_keyframe_interpolation(...)` |
| 关键帧缓动 | `prop.key_in/out_temporal_ease(i)` | `prop.set_temporal_ease_at_key(i, in, out)` | `proj.change_keyframe_ease(...)` |
| 素材文件路径 | `item.file` | `item.file = "..."` | `proj.change_asset_path(...)` |

---

## 枚举

### BlendingMode

`NORMAL(1)` `DARKEN(3)` `MULTIPLY(4)` `COLOR_BURN(5)` `LINEAR_BURN(6)` `DARKER_COLOR(7)` `LIGHTEN(9)` `SCREEN(10)` `COLOR_DODGE(11)` `LINEAR_DODGE(12)` `LIGHTER_COLOR(13)` `OVERLAY(15)` `SOFT_LIGHT(16)` `HARD_LIGHT(17)` `LINEAR_LIGHT(18)` `VIVID_LIGHT(19)` `PIN_LIGHT(20)` `HARD_MIX(21)` `DIFFERENCE(23)` `EXCLUSION(24)` `HUE(26)` `SATURATION(27)` `COLOR(28)` `LUMINOSITY(29)`

### TrackMatteType

`NONE(0)` `ALPHA(1)` `ALPHA_INVERTED(2)` `LUMA(3)` `LUMA_INVERTED(4)`

### MaskMode

`NONE(0)` `ADD(1)` `SUBTRACT(2)` `INTERSECT(3)` `DARKEN(4)` `LIGHTEN(5)` `DIFFERENCE(6)`

### KeyframeInterpolationType

`LINEAR(1)` `BEZIER(2)` `HOLD(3)`

### LayerQuality

`WIREFRAME(0)` `DRAFT(1)` `BEST(2)`

### LayerType

`ASSET(0)` `LIGHT(1)` `CAMERA(2)` `TEXT(3)` `SHAPE(4)`

### PropertyValueType

`COLOR(0)` `SCALAR(1)` `SPATIAL(2)` `MULTIDIMENSIONAL(3)` `LAYER_REF(4)` `CUSTOM(5)` `UINT(6)`

### AutoOrientType

`NO_AUTO_ORIENT(0)` `ALONG_PATH(1)` `CAMERA_OR_POINT_OF_INTEREST(2)` `CHARACTERS_TOWARD_CAMERA(3)`

---

## AE Match Name 参考

属性查找常用 match name：

| Match Name | 显示名称 |
|---|---|
| `ADBE Transform Group` | Transform（变换） |
| `ADBE Anchor Point` | Anchor Point（锚点） |
| `ADBE Position` | Position（位置） |
| `ADBE Position_0` / `_1` / `_2` | X / Y / Z Position |
| `ADBE Scale` | Scale（缩放） |
| `ADBE Rotate X` / `Y` / `Z` | X / Y / Z Rotation |
| `ADBE Opacity` | Opacity（不透明度） |
| `ADBE Orientation` | Orientation（方向） |
| `ADBE Effect Parade` | Effects（效果） |
| `ADBE Mask Parade` | Masks（遮罩） |
| `ADBE Time Remapping` | Time Remap（时间重映射） |
| `ADBE Marker` | Marker（标记） |
| `ADBE Text Properties` | Text（文字） |
| `ADBE Text Document` | Source Text（源文本） |
| `ADBE Root Vectors Group` | Contents（内容） |
| `ADBE Camera Options Group` | Camera Options（摄像机选项） |
| `ADBE Light Options Group` | Light Options（灯光选项） |
| `ADBE Material Options Group` | Material Options（材质选项） |
| `ADBE Mask Shape` | Mask Path（遮罩路径） |
| `ADBE Mask Feather` | Mask Feather（遮罩羽化） |
| `ADBE Mask Opacity` | Mask Opacity（遮罩不透明度） |
| `ADBE Mask Offset` | Mask Expansion（遮罩扩展） |

可以使用 match name 或显示名称来查找属性。
