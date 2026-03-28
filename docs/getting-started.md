# aep-tools 测试版使用指南

> 版本: 0.1.0a1 | Python >= 3.10 | Windows x64

## 安装

```bash
pip install aep_tools-0.1.0a1-cp313-cp313-win_amd64.whl
```

如需 GUI 功能（查看器/编辑器），额外安装 PySide6：

```bash
pip install PySide6
```

验证安装：

```bash
python -c "import aep_tools; print('OK')"
```

---

## 快速上手

### 打开项目

```python
from aep_tools import Project

# 自动识别 .aep / .aepx
proj = Project.open("my_project.aep")

print(proj.ae_version)       # "25.6"
print(proj.bits_per_channel)  # 8 / 16 / 32
print(len(proj.compositions)) # 合成数量
```

### 遍历合成和图层

```python
for comp in proj.compositions:
    print(f"Comp: {comp.name}  {comp.width}x{comp.height}  {comp.frame_rate}fps  {comp.duration}s")
    for layer in comp.layers:
        print(f"  [{layer.index}] {layer.name}  ({layer.in_point:.2f}s - {layer.out_point:.2f}s)")
```

### 读取属性值

```python
comp = proj.comp("Main Comp")   # 按名称查找
layer = comp.layer(1)            # 1-based 索引

# 快捷属性
print(layer.position.value)      # [960.0, 540.0]
print(layer.scale.value)         # [100.0, 100.0, 100.0]
print(layer.rotation.value)      # 0.0
print(layer.opacity.value)       # 1.0

# 按 matchName 或显示名查找
transform = layer.property("ADBE Transform Group")
pos = transform.property("ADBE Position")
print(pos.value)  # 同 layer.position.value
```

### 读取关键帧

```python
prop = layer.position

if prop.is_time_varying:
    print(f"关键帧数: {prop.num_keys}")
    for i in range(1, prop.num_keys + 1):  # 1-based
        kf = prop.key(i)
        print(f"  [{i}] time={kf.time:.2f}s  value={kf.value}")

    # 关键帧详情
    print(prop.key_in_interpolation_type(1))   # LINEAR / BEZIER / HOLD
    print(prop.key_in_temporal_ease(1))         # [{"speed": 0.0, "influence": 16.67}]
    print(prop.key_in_spatial_tangent(1))       # [0.0, 0.0] 或 None

    # 按时间查找最近关键帧
    idx = prop.nearest_key_index(2.5)
    print(prop.key_value(idx))
```

---

## 修改和保存

> 仅 `.aep` 文件支持写入，`.aepx` 为只读。可通过 `proj.writable` 检查。

### 图层增删复制移动

```python
comp = proj.compositions[0]

# 添加各种图层
comp.add_solid("Red Solid", color=(1.0, 0.0, 0.0))      # 纯色
comp.add_null("Null Object")                              # 空对象
comp.add_adjustment("Adjustment")                         # 调整图层
comp.add_shape("Shape Layer")                             # 形状图层
comp.add_text("Text Layer")                               # 文字图层
comp.add_camera("Camera")                                 # 摄像机
comp.add_light("Light")                                   # 灯光

# 删除
comp.layers[1].remove()           # 删除第 1 个图层
comp.remove_layer(2)              # 按索引删除

# 复制
comp.layers[1].duplicate()        # 复制第 1 个图层（副本在原图层下方）

# 移动
comp.layers[3].move_to(1)         # 移到最上层
comp.layers[1].move_to_beginning()  # 同上
comp.layers[1].move_to_end()      # 移到最下层

# 预合成（将指定图层移入新合成）
lid1 = comp.add_solid("A", color=(1,0,0))
lid2 = comp.add_solid("B", color=(0,1,0))
new_comp_id, precomp_layer_id = comp.precompose([lid1, lid2], "PreComp AB")

proj.save("output.aep")
```

### 修改图层属性

```python
# 图层名称
layer.name = "New Name"

# 图层标志
layer.enabled = False        # 隐藏
layer.solo = True
layer.shy = True
layer.locked = True
layer.three_d_layer = True   # 3D 图层
layer.adjustment_layer = True
layer.guide_layer = True
layer.motion_blur = True
layer.effects_active = False

# 图层时间
layer.in_point = 1.0         # 入点（秒）
layer.out_point = 5.0        # 出点
layer.start_time = -0.5      # 起始时间
layer.stretch = 50.0         # 时间拉伸 (%)

# 混合模式
from aep_tools import BlendingMode
layer.blending_mode = BlendingMode.MULTIPLY

# 轨道遮罩
from aep_tools import TrackMatteType
layer.track_matte_type = TrackMatteType.ALPHA

# 图层质量
from aep_tools import LayerQuality
layer.quality = LayerQuality.BEST

# 标签颜色 (0-15)
layer.label = 5
```

### 修改属性静态值

```python
layer.position.value = [500.0, 300.0]
layer.scale.value = [50.0, 50.0, 100.0]
layer.opacity.value = 0.5
layer.rotation.value = 45.0
```

### 修改关键帧

```python
from aep_tools import KeyframeInterpolationType

prop = layer.position

# 修改关键帧值 (1-based 索引)
prop.set_value_at_key(1, [0.0, 0.0])
prop.set_value_at_key(2, [1920.0, 1080.0])

# 修改插值类型
prop.set_interpolation_type_at_key(1,
    in_type=KeyframeInterpolationType.BEZIER,
    out_type=KeyframeInterpolationType.BEZIER)

# 修改缓动
prop.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 0.0, "influence": 33.33}])

# 按时间设置（找最近的关键帧修改）
prop.set_value_at_time(2.0, [960.0, 540.0])
```

### 修改合成设置

```python
comp.name = "Renamed Comp"
comp.width = 1920
comp.height = 1080
comp.frame_rate = 30.0
comp.duration = 10.0
comp.bg_color = [0.0, 0.0, 0.0]  # 黑色背景

# 工作区域
comp.work_area_start = 0.0
comp.work_area_duration = 5.0

# 运动模糊
comp.motion_blur = True
comp.shutter_angle = 180
comp.shutter_phase = -90

# 其他标志
comp.draft3d = False
comp.frame_blending = True
comp.hide_shy_layers = True
comp.drop_frame = False
```

### 修改项目设置

```python
proj.bits_per_channel = 16
proj.working_gamma = 2.2
proj.linearize_working_space = True
proj.audio_sample_rate = 48000.0
```

### 修改素材路径

```python
footage = proj.item(3)  # 1-based 索引
if footage.type_name == "Footage":
    footage.file = "/new/path/to/file.mov"
```

### 保存

```python
proj.save()                    # 覆盖原文件
proj.save("output.aep")       # 另存为
```

---

## 效果和遮罩

### 效果

```python
print(layer.num_effects)

effect = layer.effect(1)          # 按索引
effect = layer.effect("Gaussian Blur")  # 按名称

print(effect.name)                # "Gaussian Blur"
print(effect.match_name)          # "ADBE Gaussian Blur"
print(effect.enabled)
print(effect.num_params)

# 效果参数
param = effect.param(1)           # 按索引
param = effect.param("Blurriness") # 按名称
print(param.value)
```

### 遮罩

```python
from aep_tools import MaskMode

print(layer.num_masks)

mask = layer.mask(1)              # 1-based
print(mask.name)
print(mask.mode)                  # MaskMode.ADD
print(mask.inverted)

# 遮罩属性
if mask.mask_opacity:
    print(mask.mask_opacity.value)
if mask.mask_feather:
    print(mask.mask_feather.value)
if mask.mask_expansion:
    print(mask.mask_expansion.value)
```

---

## 文本图层

```python
from aep_tools import TextLayer

layer = comp.layer("Title")
if isinstance(layer, TextLayer):
    text_prop = layer.source_text
    print(text_prop.text)          # 当前文本内容
    print(text_prop.fonts)         # 字体列表

    # 带关键帧的文本
    if text_prop.num_keys > 0:
        for i in range(1, text_prop.num_keys + 1):
            doc = text_prop.key_value(i)
            print(f"  [{i}] {text_prop.key_time(i):.2f}s: {doc.text}")
```

---

## 标记

```python
# 合成标记
marker_prop = comp.marker_property
if marker_prop:
    for i in range(1, marker_prop.num_keys + 1):
        m = marker_prop.key_value(i)
        print(f"  {marker_prop.key_time(i):.2f}s: {m.comment} (dur={m.duration}s)")

# 图层标记
layer_markers = layer.marker_property
if layer_markers:
    for i in range(1, layer_markers.num_keys + 1):
        m = layer_markers.key_value(i)
        print(f"  {layer_markers.key_time(i):.2f}s: {m.comment}")
```

---

## 项目结构浏览

### 文件夹和素材

```python
def print_items(items, indent=0):
    for i in range(1, len(items) + 1):
        item = items[i]
        prefix = "  " * indent
        if item.type_name == "Folder":
            print(f"{prefix}[Folder] {item.name}")
            print_items(item.items, indent + 1)
        elif item.type_name == "Composition":
            print(f"{prefix}[Comp] {item.name}")
        elif item.type_name == "Footage":
            print(f"{prefix}[Footage] {item.name} -> {item.file}")
        elif item.type_name == "Solid":
            print(f"{prefix}[Solid] {item.name} {item.width}x{item.height}")

print_items(proj.items)
```

### 渲染队列

```python
rq = proj.render_queue
for i in range(1, rq.num_items + 1):
    item = rq.item(i)
    print(f"  [{i}] {item.comp_name} (status={item.status})")
    for j in range(1, item.num_output_modules + 1):
        om = item.output_module(j)
        print(f"      Output: {om.format} -> {om.output_path}")
```

---

## 导出 JSON

### 高级 API 导出

```python
import json

proj = Project.open("input.aep")
comp = proj.comp("Main Comp")

# 导出单个合成的 dict
data = comp._model.to_dict()
print(json.dumps(data, indent=2, ensure_ascii=False))
```

### 低级 API 导出整个项目

```python
from aep_parser import parse_aep

project_model = parse_aep(open("input.aep", "rb").read())

# 完整项目 JSON
data = project_model.to_dict()
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
```

---

## CLI 命令

安装后可直接使用 `aep-tools` 命令：

```bash
# 输出完整 JSON 到终端
aep-tools input.aep

# 写入 JSON 文件
aep-tools input.aep -o output.json

# 紧凑格式
aep-tools input.aep --compact

# 只输出指定合成
aep-tools input.aep --comp "Main Comp"
aep-tools input.aep --comp-id 1

# 查看 AE 版本信息（不解析全文件，很快）
aep-tools input.aep -V

# 也可以作为模块运行
python -m aep_parser input.aep
```

---

## GUI 查看器

需要安装 PySide6：

```bash
# 启动查看器
aep-vieweraep-viewer
aep-viewer input.aep

# 或作为模块运行
python -m aep_parser.gui
```

GUI 功能：
- AE 风格深色主题
- 项目面板：文件夹结构、素材路径、合成列表
- 图层树：属性、关键帧（可展开查看时间/类型/值/缓动）
- 右键编辑：图层名/标志/混合模式/时间、属性值、关键帧、素材路径
- 合成编辑：名称、尺寸、帧率、时长、背景色、标志、工作区域
- 项目设置编辑：色深、gamma、线性化、音频采样率
- 保存修改后的 `.aep` 文件

---

## 图层类型

| 类型 | 类 | 说明 |
|------|-----|------|
| 素材/预合成/固态 | `AVLayer` | `layer.source` 返回关联资产 |
| 文本 | `TextLayer` | `layer.source_text` 获取文本内容 |
| 形状 | `ShapeLayer` | `layer.contents` 获取形状组 |
| 摄像机 | `CameraLayer` | `layer.camera_options` 获取摄像机参数 |
| 灯光 | `LightLayer` | `layer.light_type` 读写灯光类型 |
| 空对象 | `Layer` | `layer.null_layer == True` |

图层类型检查：

```python
from aep_tools import AVLayer, TextLayer, ShapeLayer, CameraLayer, LightLayer

layer = comp.layer(1)
if isinstance(layer, TextLayer):
    print("这是文本图层")
elif isinstance(layer, ShapeLayer):
    print("这是形状图层")
elif isinstance(layer, AVLayer):
    print("这是素材/预合成图层")
```

---

## 枚举参考

### BlendingMode

| 值 | 名称 | 值 | 名称 |
|----|------|----|------|
| 2 | NORMAL | 3 | DISSOLVE |
| 4 | ADD | 5 | MULTIPLY |
| 6 | SCREEN | 7 | OVERLAY |
| 8 | SOFT_LIGHT | 9 | HARD_LIGHT |
| 10 | DARKEN | 11 | LIGHTEN |
| 12 | CLASSIC_DIFFERENCE | 25 | EXCLUSION |
| 26 | DIFFERENCE | 27 | COLOR_DODGE |
| 28 | COLOR_BURN | 29 | LINEAR_DODGE |
| 30 | LINEAR_BURN | 31 | LINEAR_LIGHT |
| 32 | VIVID_LIGHT | 33 | PIN_LIGHT |
| 34 | HARD_MIX | 37 | SUBTRACT |
| 38 | DIVIDE | | |

### TrackMatteType

| 值 | 名称 |
|----|------|
| 0 | NONE |
| 1 | ALPHA |
| 2 | ALPHA_INVERTED |
| 3 | LUMA |
| 4 | LUMA_INVERTED |

### KeyframeInterpolationType

| 值 | 名称 |
|----|------|
| 1 | LINEAR |
| 2 | BEZIER |
| 3 | HOLD |

### LayerQuality

| 值 | 名称 |
|----|------|
| 0 | WIREFRAME |
| 1 | DRAFT |
| 2 | BEST |

### MaskMode

| 值 | 名称 |
|----|------|
| 0 | NONE |
| 1 | ADD |
| 2 | SUBTRACT |
| 3 | INTERSECT |
| 4 | DARKEN |
| 5 | LIGHTEN |
| 6 | DIFFERENCE |

---

## 完整示例：批量替换素材路径

```python
from aep_tools import Project

proj = Project.open("template.aep")

# 遍历所有素材项，替换路径前缀
for i in range(1, proj.num_items + 1):
    item = proj.item(i)
    if hasattr(item, 'file') and item.file:
        old = item.file
        if old.startswith("D:/old_assets/"):
            item.file = old.replace("D:/old_assets/", "E:/new_assets/")
            print(f"  {old} -> {item.file}")

proj.save("updated.aep")
```

## 完整示例：读取所有合成的关键帧统计

```python
from aep_tools import Project, Property

proj = Project.open("input.aep")

for comp in proj.compositions:
    total_keys = 0
    for layer in comp.layers:
        for i in range(1, layer.num_properties + 1):
            prop = layer.property(i)
            if isinstance(prop, Property) and prop.is_time_varying:
                total_keys += prop.num_keys
    print(f"{comp.name}: {comp.num_layers} layers, {total_keys} keyframes")
```

## 完整示例：导出合成信息到 CSV

```python
import csv
from aep_tools import Project

proj = Project.open("input.aep")

with open("compositions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Name", "Width", "Height", "FPS", "Duration", "Layers"])
    for comp in proj.compositions:
        writer.writerow([
            comp.name, comp.width, comp.height,
            comp.frame_rate, f"{comp.duration:.2f}", comp.num_layers
        ])
```

---

## 已知限制

- **写入仅支持 `.aep`**：`.aepx` 文件为只读
- **不支持创建新元素**：不能新建图层、合成、关键帧，只能修改已有的
- **表达式为只读**：可以读取表达式内容，但不能修改
- **wheel 平台限定**：当前 wheel 仅适用于 CPython 3.13 + Windows x64，其他环境需从源码构建
