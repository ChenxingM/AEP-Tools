# aep_tools API Reference

AE scripting-style API for After Effects project files (`.aep` / `.aepx`).

API design mirrors [After Effects ExtendScript](https://ae-scripting.docsforadobe.dev/), using 1-based indexing and chain-style property access.

> **Read/Write Legend:** Properties marked **RW** are read-write (modify + save back to `.aep`). All others are **read-only**. Write support requires the project to be opened from a binary `.aep` file (`proj.writable == True`).

---

## Quick Start

```python
from aep_tools import Project

proj = Project.open("my_project.aep")
comp = proj.comp("Main Comp")
layer = comp.layer(1)

# Read properties
print(layer.position.value)        # [960, 540]
print(layer.opacity.num_keys)      # 3

# AE-style chaining
layer("Transform")("Position").key_value(1)

# Modify and save
layer.position.value = [500.0, 300.0]
layer.position.set_value_at_key(1, [0.0, 0.0])
proj.save("output.aep")
```

---

## Opening Projects

### `Project.open(path)`

Auto-detect `.aep` / `.aepx` by extension.

```python
proj = Project.open("path/to/project.aep")
proj = Project.open("path/to/project.aepx")
```

### `open_aep(path)` / `open_aepx(path)`

Open a specific format directly.

```python
from aep_tools import open_aep, open_aepx
proj = open_aep("binary.aep")
proj = open_aepx("xml.aepx")
```

### `load_project(model)`

Wrap an already-parsed `aep_parser.models.Project` model.

```python
from aep_parser import parse_aep
from aep_tools import load_project
model = parse_aep(data)
proj = load_project(model)
```

---

## Project

| Property / Method | Type | R/W | Description |
|---|---|---|---|
| `file` | `str \| None` | R | File path (if opened from file) |
| `ae_version` | `str \| None` | R | AE version that last saved this file (e.g. `"25.6"`) |
| `writable` | `bool` | R | `True` if loaded from binary `.aep` (supports save/modify) |
| `compositions` | `list[CompItem]` | R | All compositions |
| `comp(name_or_index)` | `CompItem \| None` | R | Lookup by name or 1-based index |
| `num_items` | `int` | R | Number of top-level project items |
| `items` | `ItemCollection` | R | All top-level items (1-based) |
| `item(index)` | `Any \| None` | R | Get item by 1-based index |
| `active_item` | `CompItem \| None` | R | Active composition (if available) |
| `render_queue` | `RenderQueue` | R | Render queue |
| `save(path)` | `None` | — | Save to `.aep` file (requires `writable`) |

### Low-Level Write Methods

These operate directly on the chunk tree. For most use cases, prefer the property-level setters (e.g. `layer.position.value = ...`).

| Method | Return | Description |
|---|---|---|
| `change_layer_name(comp_id, layer_id, new_name)` | `bool` | Rename a layer |
| `change_property_value(comp_id, layer_id, match_path, value)` | `bool` | Change a property's static value |
| `change_keyframe_value(comp_id, layer_id, match_path, key_index, value)` | `bool` | Change a keyframe's value |
| `change_keyframe_time(comp_id, layer_id, match_path, key_index, time)` | `bool` | Change a keyframe's time |
| `change_keyframe_interpolation(comp_id, layer_id, match_path, key_index, type)` | `bool` | Change interpolation (1=linear, 2=bezier, 3=hold) |
| `change_keyframe_ease(comp_id, layer_id, match_path, key_index, ...)` | `bool` | Change temporal ease (speed/influence) |
| `change_asset_path(asset_id, new_path)` | `bool` | Change a footage asset's file path |

```python
proj.comp("Main Comp")    # by name
proj.comp(1)              # by 1-based index
proj.ae_version           # "25.6"
```

---

## CompItem

| Property / Method | Type | R/W | Description |
|---|---|---|---|
| `name` | `str` | **RW** | Composition name |
| `id` | `int` | R | Internal ID |
| `width` | `int` | R | Width in pixels |
| `height` | `int` | R | Height in pixels |
| `duration` | `float` | R | Duration in seconds |
| `frame_rate` | `float` | R | Frames per second |
| `frame_duration` | `float` | R | `1.0 / frame_rate` |
| `work_area_start` | `float` | R | Work area start (seconds) |
| `work_area_duration` | `float` | R | Work area duration (seconds) |
| `bg_color` | `list[float]` | R | Background color `[r, g, b]` |
| `num_layers` | `int` | R | Number of layers |
| `layers` | `LayerCollection` | R | All layers (1-based) |
| `layer(name_or_index)` | `Layer \| None` | R | Lookup by name or 1-based index |
| `marker_property` | `MarkerProperty \| None` | R | Composition markers |

```python
comp = proj.comp("Main Comp")
comp.name = "Renamed Comp"    # write-back to .aep
comp.layer(1)                  # first layer
comp.layer("Background")      # by name
for layer in comp.layers:
    print(layer.name)
```

---

## Layer

Base class. Actual layers are subclassed as `AVLayer`, `TextLayer`, `ShapeLayer`, `CameraLayer`, `LightLayer` (selected automatically by the factory).

### Identity

| Property | Type | R/W | Description |
|---|---|---|---|
| `index` | `int` | R | 1-based index in composition |
| `name` | `str` | **RW** | Layer name |
| `containing_comp` | `CompItem \| None` | R | Parent composition |
| `label` | `int` | R | Label color index |

### Flags (all read-only)

| Property | Type | Description |
|---|---|---|
| `enabled` | `bool` | Visibility (eye icon) |
| `solo` | `bool` | Solo switch |
| `shy` | `bool` | Shy flag |
| `locked` | `bool` | Lock flag |
| `null_layer` | `bool` | Is null object |
| `guide_layer` | `bool` | Is guide layer |
| `adjustment_layer` | `bool` | Is adjustment layer |
| `three_d_layer` | `bool` | 3D layer enabled |
| `auto_orient` | `bool` | Auto-orient |
| `effects_active` | `bool` | Effects enabled |
| `motion_blur` | `bool` | Motion blur enabled |
| `collapse_transformation` | `bool` | Collapse / Continuously rasterize |
| `sampling_quality` | `bool` | Bicubic sampling |

### Timing (all read-only)

| Property | Type | Description |
|---|---|---|
| `in_point` | `float` | In point (seconds) |
| `out_point` | `float` | Out point (seconds) |
| `start_time` | `float` | Start time (seconds) |
| `stretch` | `float` | Time stretch factor |

### Blend / Matte (all read-only)

| Property | Type | Description |
|---|---|---|
| `blending_mode` | `BlendingMode \| int` | Blending mode enum (raw int for unknown values) |
| `track_matte_type` | `TrackMatteType \| int` | Track matte type |
| `quality` | `LayerQuality` | Render quality |

### Parenting

| Property | Type | Description |
|---|---|---|
| `parent` | `Layer \| None` | Parent layer (auto-resolved by ID) |

### Property Access

Three equivalent ways to access the property tree:

```python
layer.property("Transform")        # method
layer("Transform")                 # __call__ (raises KeyError if missing)
layer["Transform"]                 # __getitem__ (raises KeyError if missing)
```

| Method | Type | Description |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | Lookup property by match_name, display name, or 1-based index |
| `num_properties` | `int` | Number of top-level property groups |

**Name resolution order:**
1. Exact `match_name` (e.g. `"ADBE Transform Group"`)
2. Display name via `DISPLAY_NAMES` reverse map (e.g. `"Transform"`)
3. Case-insensitive display name comparison
4. Model `.name` attribute (user-defined names)

### Transform Shortcuts

Direct access to common transform properties. Each returns a `Property` (read-write via `.value` setter) or `None` if not present:

| Property | Match Name | Description |
|---|---|---|
| `transform` | `ADBE Transform Group` | Transform group |
| `position` | `ADBE Position` | Position (combined) |
| `position_x` | `ADBE Position_0` | X Position (when separated) |
| `position_y` | `ADBE Position_1` | Y Position (when separated) |
| `position_z` | `ADBE Position_2` | Z Position (when separated) |
| `scale` | `ADBE Scale` | Scale |
| `rotation` | `ADBE Rotate Z` | Rotation (2D / Z Rotation) |
| `rotation_x` | `ADBE Rotate X` | X Rotation |
| `rotation_y` | `ADBE Rotate Y` | Y Rotation |
| `rotation_z` | `ADBE Rotate Z` | Z Rotation |
| `opacity` | `ADBE Opacity` | Opacity |
| `anchor_point` | `ADBE Anchor Point` | Anchor Point |
| `orientation` | `ADBE Orientation` | Orientation (3D) |

> **Note:** When Position is separated into dimensions, `layer.position` returns `None`. Use `layer.position_x` / `layer.position_y` instead. Properties that haven't been modified from their default value may not be present in the parsed data.

### Time Remap

| Property | Type | Description |
|---|---|---|
| `time_remap_enabled` | `bool` | Whether time remap exists |
| `time_remap` | `Property \| None` | Time remap property |

### Effects

| Property / Method | Type | Description |
|---|---|---|
| `num_effects` | `int` | Number of effects |
| `effect(name_or_index)` | `Effect \| None` | Get effect by 1-based index or name |

### Masks

| Property / Method | Type | Description |
|---|---|---|
| `num_masks` | `int` | Number of masks |
| `mask(index)` | `Mask \| None` | Get mask by 1-based index |

### Markers

| Property | Type | Description |
|---|---|---|
| `marker_property` | `MarkerProperty \| None` | Layer markers |

---

## Layer Subclasses

### AVLayer

Asset-based layer (footage, solid, precomp). Inherits all `Layer` properties.

| Property | Type | Description |
|---|---|---|
| `source` | `Any \| None` | Source asset from project (ImageAsset, SolidAsset, Composition) |

### TextLayer

| Property | Type | Description |
|---|---|---|
| `source_text` | `TextSourceProperty \| None` | Text source property |

```python
layer.source_text.text     # "Hello World"
layer.source_text.fonts    # ["Arial"]
```

### ShapeLayer

| Property | Type | Description |
|---|---|---|
| `contents` | `PropertyGroup \| None` | Shape contents group |

### CameraLayer

| Property | Type | Description |
|---|---|---|
| `camera_options` | `PropertyGroup \| None` | Camera options group |

### LightLayer

Placeholder for future expansion. Inherits all `Layer` properties.

---

## Property

Wraps a single animated property value.

### Read Properties

| Property | Type | Description |
|---|---|---|
| `name` | `str` | Display name |
| `match_name` | `str` | AE internal match name |
| `value` | `Any` | **RW** — Current value (static or first keyframe) |
| `num_keys` | `int` | Number of keyframes |
| `is_time_varying` | `bool` | Has multiple keyframes |
| `expression` | `str \| None` | Expression string |
| `expression_enabled` | `bool` | Whether expression exists |
| `dimensions_separated` | `bool` | Position split into X/Y/Z |
| `is_spatial` | `bool` | Is spatial property |
| `property_value_type` | `PropertyValueType` | Value type enum |
| `keys` | `list[KeyframeValue]` | All keyframes (1-based index) |

### Value Types

Values are returned as plain Python types:

| Model Type | Python Type |
|---|---|
| `Vector(x, y)` | `[x, y]` |
| `Vector(x, y, z)` | `[x, y, z]` |
| `Color(r, g, b, a)` | `[r, g, b, a]` |
| `float` | `float` |
| `LayerRef` | `int` (layer ID) |

### Setting Static Values

```python
layer.position.value = [500.0, 300.0]     # set position
layer.opacity.value = 0.5                  # set opacity to 50%
layer.scale.value = [1.2, 1.2, 1.2]       # set scale to 120%
```

> **Note:** AE stores Scale and Opacity as 0-1 fractions internally (1.0 = 100%).

### Keyframe Read Methods

All keyframe indices are **1-based**.

| Method | Return | Description |
|---|---|---|
| `key(index)` | `KeyframeValue` | Keyframe at index |
| `key_value(index)` | `Any` | Value at keyframe |
| `key_time(index)` | `float` | Time at keyframe (seconds) |
| `key_in_interpolation_type(index)` | `KeyframeInterpolationType` | Incoming interpolation |
| `key_out_interpolation_type(index)` | `KeyframeInterpolationType` | Outgoing interpolation |
| `key_in_temporal_ease(index)` | `list[dict]` | `[{"speed": ..., "influence": ...}]` |
| `key_out_temporal_ease(index)` | `list[dict]` | `[{"speed": ..., "influence": ...}]` |
| `key_in_spatial_tangent(index)` | `list[float] \| None` | Incoming spatial tangent |
| `key_out_spatial_tangent(index)` | `list[float] \| None` | Outgoing spatial tangent |
| `key_roving(index)` | `bool` | Is roving keyframe |
| `nearest_key_index(t)` | `int` | 1-based index of nearest key to time `t` |

### Keyframe Write Methods

| Method | Description |
|---|---|
| `set_value_at_key(key_index, value)` | Set keyframe value (1-based index) |
| `set_value_at_time(time, value)` | Set value at nearest keyframe to `time` |
| `set_interpolation_type_at_key(key_index, in_type, out_type=None)` | Set in/out interpolation |
| `set_temporal_ease_at_key(key_index, in_ease=None, out_ease=None)` | Set temporal ease |

```python
pos = layer.position

# Read
pos.value                      # [960, 540]
pos.num_keys                   # 2
pos.key_value(1)               # [0, 0]
pos.key_time(2)                # 1.0
pos.value_at_time(0.5)         # [480, 270]

# Write keyframe value
pos.set_value_at_key(1, [100.0, 200.0])

# Write interpolation
from aep_tools import KeyframeInterpolationType
pos.set_interpolation_type_at_key(
    1,
    in_type=KeyframeInterpolationType.BEZIER,
    out_type=KeyframeInterpolationType.HOLD,
)

# Write temporal ease
pos.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 0.0, "influence": 33.33}],
)
```

#### Interpolation Semantics

In AEP binary, each keyframe stores one `transition_type` that controls the **outgoing** curve. So:
- `out_type` sets this keyframe's transition_type
- `in_type` sets the **previous** keyframe's transition_type (key_index - 1)

If `out_type` is `None`, it defaults to `in_type` (same as AE behavior when only one type is specified).

### Interpolation

| Method | Return | Description |
|---|---|---|
| `value_at_time(t)` | `Any` | Evaluate at time `t` (linear + hold interpolation) |

---

## PropertyGroup

Wraps a group of properties. Supports chaining, indexing, and iteration. All properties are **read-only**.

| Property / Method | Type | Description |
|---|---|---|
| `name` | `str` | Group name |
| `match_name` | `str` | AE match name |
| `enabled` | `bool \| None` | Enabled state (for toggleable groups) |
| `num_properties` | `int` | Number of children |
| `property(name_or_index)` | `Any \| None` | Lookup child |

### Access Patterns

```python
group.property("Opacity")    # by name
group.property(1)            # by 1-based index
group("Opacity")             # __call__ (raises KeyError)
group["Opacity"]             # __getitem__ (raises KeyError)
len(group)                   # num_properties
for prop in group:           # iterate children
    print(prop.name)
```

---

## Effect

All properties are **read-only**.

| Property / Method | Type | Description |
|---|---|---|
| `name` | `str` | Effect display name |
| `match_name` | `str` | AE match name |
| `enabled` | `bool` | Enabled state |
| `num_params` | `int` | Number of parameters |
| `param(name_or_index)` | `Any \| None` | Get parameter by name or 1-based index |

Supports `__call__` and `__getitem__`:

```python
layer.effect(1)                 # first effect
layer.effect("Gaussian Blur")   # by name
eff = layer.effect(1)
eff.param(1).value              # first parameter value
eff("Blurriness").value         # by parameter name
```

---

## Mask

All properties are **read-only**.

| Property | Type | Description |
|---|---|---|
| `name` | `str` | Mask name |
| `match_name` | `str` | AE match name |
| `mode` | `MaskMode` | Mask mode (ADD, SUBTRACT, etc.) |
| `inverted` | `bool` | Inverted |
| `locked` | `bool` | Locked |
| `index` | `int` | 1-based index |
| `mask_path` | `Property \| None` | Mask path shape |
| `mask_feather` | `Property \| None` | Feather |
| `mask_opacity` | `Property \| None` | Opacity |
| `mask_expansion` | `Property \| None` | Expansion |

```python
m = layer.mask(1)
m.mode                    # MaskMode.ADD
m.mask_opacity.value      # 100.0
```

---

## MarkerProperty / MarkerValue

All properties are **read-only**.

### MarkerProperty

| Property / Method | Type | Description |
|---|---|---|
| `num_keys` | `int` | Number of markers |
| `key_value(index)` | `MarkerValue` | Marker at 1-based index |
| `key_time(index)` | `float` | Time at marker |
| `nearest_key_index(t)` | `int` | Nearest marker to time `t` |

### MarkerValue

| Property | Type | Description |
|---|---|---|
| `comment` | `str` | Marker comment text |
| `duration` | `float` | Duration (seconds) |
| `label` | `int` | Label color index |
| `time` | `float` | Time (seconds) |

```python
mp = comp.marker_property
mv = mp.key_value(1)
print(mv.comment, mv.time)    # "Intro" 1.0
```

---

## TextSourceProperty

All properties are **read-only**.

| Property / Method | Type | Description |
|---|---|---|
| `text` | `str` | Current text string |
| `value` | `TextDocument \| None` | Full TextDocument object |
| `fonts` | `list[str]` | Font family names |
| `num_keys` | `int` | Number of text keyframes |
| `key_value(index)` | `TextDocument \| None` | TextDocument at keyframe |
| `key_time(index)` | `float` | Time at keyframe |

---

## KeyframeValue

All properties are **read-only**.

| Property | Type | Description |
|---|---|---|
| `index` | `int` | 1-based index |
| `time` | `float` | Time (seconds) |
| `value` | `Any` | Converted value |

---

## Project Items

### FolderItem

All properties are **read-only**.

| Property | Type | Description |
|---|---|---|
| `type_name` | `str` | `"Folder"` |
| `name` | `str` | Folder name |
| `id` | `int` | Internal ID |
| `num_items` | `int` | Child count |
| `items` | `ItemCollection` | Children (1-based) |

### FootageItem

| Property | Type | R/W | Description |
|---|---|---|---|
| `type_name` | `str` | R | `"Footage"` or `"Solid"` |
| `name` | `str` | R | Item name |
| `id` | `int` | R | Internal ID |
| `width` | `int` | R | Width in pixels |
| `height` | `int` | R | Height in pixels |
| `file` | `str \| None` | **RW** | File path (footage only, raises `TypeError` on solids) |
| `color` | `list[float] \| None` | R | `[r, g, b, a]` (solid only) |

```python
# Read footage path
item = proj.item(1)
print(item.file)              # "/path/to/footage.mov"

# Change footage path
item.file = "/new/path/to/footage.mov"
proj.save("output.aep")
```

### RenderQueue

| Property / Method | Type | Description |
|---|---|---|
| `num_items` | `int` | Number of render queue items |
| `item(index)` | `RenderQueueItem \| None` | Get by 1-based index |

### RenderQueueItem

| Property / Method | Type | Description |
|---|---|---|
| `comp_name` | `str` | Composition name |
| `status` | `int` | Render status code |
| `num_output_modules` | `int` | Number of output modules |
| `output_module(index)` | `OutputModule \| None` | Get by 1-based index |

---

## Write-Back (Binary .aep Only)

Projects opened from binary `.aep` files support modification and saving. The `writable` property indicates availability.

### Saving

```python
proj = Project.open("input.aep")
assert proj.writable  # True for .aep, False for .aepx

# Save to a new file
proj.save("output.aep")

# Overwrite original
proj.save()
```

### Property-Level Write (Recommended)

The simplest way to modify values — use property setters directly:

```python
comp = proj.comp("Main Comp")
layer = comp.layer(1)

# Static value
layer.position.value = [500.0, 300.0]
layer.opacity.value = 0.5

# Keyframe value
layer.position.set_value_at_key(1, [100.0, 200.0])

# Keyframe interpolation
from aep_tools import KeyframeInterpolationType
layer.position.set_interpolation_type_at_key(1,
    in_type=KeyframeInterpolationType.LINEAR,
    out_type=KeyframeInterpolationType.BEZIER,
)

# Keyframe temporal ease
layer.position.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 100.0, "influence": 33.33}],
)

# Composition name
comp.name = "New Comp Name"

# Footage file path
footage = proj.item(3)  # a FootageItem
footage.file = "/new/path/to/file.mov"

proj.save("output.aep")
```

### Low-Level Write (Project Methods)

For cases where you need direct control using IDs and match name paths:

```python
# Rename layer
proj.change_layer_name(comp.id, layer._model.id, "New Name")

# Change static property value
proj.change_property_value(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    [500.0, 300.0]
)

# Change keyframe value (1-based index)
proj.change_keyframe_value(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, [100.0, 200.0]
)

# Change keyframe time
proj.change_keyframe_time(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, 2.5  # new time in seconds
)

# Change keyframe interpolation (1=linear, 2=bezier, 3=hold)
proj.change_keyframe_interpolation(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1, 3  # hold
)

# Change keyframe temporal ease
proj.change_keyframe_ease(
    comp.id, layer._model.id,
    ["ADBE Transform Group", "ADBE Position"],
    1,
    in_speed=[0.0], in_influence=[33.33],
    out_speed=[0.0], out_influence=[33.33],
)

# Change footage asset path
proj.change_asset_path(asset_id, "/new/path/to/file.mov")

proj.save("output.aep")
```

> **Note:** AE stores Scale and Opacity as 0-1 fractions internally (1.0 = 100%). When writing values, use fractions, not percentages. If a Transform property (Anchor Point, Position, Scale, Rotation, Opacity) doesn't exist in the binary, it will be created automatically with the correct chunk structure.

### Version Info

```python
proj.ae_version    # "25.6" -- AE version that last saved this file (None for .aepx)
```

---

## Read/Write Summary

| What | Read | Write (property-level) | Write (low-level) |
|---|---|---|---|
| Comp name | `comp.name` | `comp.name = "..."` | — |
| Layer name | `layer.name` | `layer.name = "..."` | `proj.change_layer_name(...)` |
| Property static value | `prop.value` | `prop.value = ...` | `proj.change_property_value(...)` |
| Keyframe value | `prop.key_value(i)` | `prop.set_value_at_key(i, v)` | `proj.change_keyframe_value(...)` |
| Keyframe time | `prop.key_time(i)` | — | `proj.change_keyframe_time(...)` |
| Keyframe interpolation | `prop.key_in/out_interpolation_type(i)` | `prop.set_interpolation_type_at_key(i, in, out)` | `proj.change_keyframe_interpolation(...)` |
| Keyframe ease | `prop.key_in/out_temporal_ease(i)` | `prop.set_temporal_ease_at_key(i, in, out)` | `proj.change_keyframe_ease(...)` |
| Footage file path | `item.file` | `item.file = "..."` | `proj.change_asset_path(...)` |

---

## Enums

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

## AE Match Name Reference

Common match names used for property lookup:

| Match Name | Display Name |
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
| `ADBE Light Options Group` | Light Options |
| `ADBE Material Options Group` | Material Options |
| `ADBE Mask Shape` | Mask Path |
| `ADBE Mask Feather` | Mask Feather |
| `ADBE Mask Opacity` | Mask Opacity |
| `ADBE Mask Offset` | Mask Expansion |

You can use either the match name or the display name when looking up properties.
