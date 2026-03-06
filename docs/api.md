# aep_tools API Reference

AE scripting-style API for After Effects project files. Mirrors [After Effects Scripting Guide](https://ae-scripting.docsforadobe.dev/).

All collection indices are **1-based**.

---

## Project

Represents an After Effects project. Returned by `Project.open()`.

### Class Method

| Method | Returns | Description |
|---|---|---|
| `Project.open(path)` | `Project` | Open a `.aep` or `.aepx` file |

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `file` | `str \| None` | R | Source file path |
| `ae_version` | `str \| None` | R | AE version that saved this project (e.g. `"25.6"`) |
| `writable` | `bool` | R | Whether save/modify is supported (`.aep` only) |
| `num_items` | `int` | R | Number of top-level items |
| `items` | `ItemCollection` | R | Top-level items (1-based) |
| `compositions` | `list[CompItem]` | R | All compositions |
| `active_item` | `CompItem \| None` | R | Active composition |
| `render_queue` | `RenderQueue` | R | Render queue |

### Methods

| Method | Returns | Description |
|---|---|---|
| `item(index)` | `Any \| None` | Get item by 1-based index |
| `comp(name_or_index)` | `CompItem \| None` | Get composition by name or 1-based index |
| `save(path=None)` | `None` | Save to `.aep`. If path is None, overwrite original |
| `change_layer_name(comp_id, layer_id, name)` | `bool` | Rename a layer |
| `change_property_value(comp_id, layer_id, match_path, value)` | `bool` | Set property static value |
| `change_keyframe_value(comp_id, layer_id, match_path, key_index, value)` | `bool` | Set keyframe value |
| `change_keyframe_time(comp_id, layer_id, match_path, key_index, time)` | `bool` | Set keyframe time (seconds) |
| `change_keyframe_interpolation(comp_id, layer_id, match_path, key_index, type)` | `bool` | Set interpolation (1=linear, 2=bezier, 3=hold) |
| `change_keyframe_ease(comp_id, layer_id, match_path, key_index, ...)` | `bool` | Set temporal ease |
| `change_asset_path(asset_id, new_path)` | `bool` | Set footage file path |

### Example

```python
from aep_tools import Project

proj = Project.open("input.aep")
print(proj.ae_version)            # "25.6"
comp = proj.comp("Main Comp")     # by name
comp = proj.comp(1)               # by index
proj.save("output.aep")
```

---

## CompItem

Represents a composition.

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `name` | `str` | R/W | Composition name |
| `id` | `int` | R | Internal ID |
| `type_name` | `str` | R | Always `"Composition"` |
| `width` | `int` | R/W | Width in pixels |
| `height` | `int` | R/W | Height in pixels |
| `duration` | `float` | R/W | Duration (seconds) |
| `frame_rate` | `float` | R/W | Frames per second |
| `frame_duration` | `float` | R | Duration of one frame (`1/frame_rate`) |
| `work_area_start` | `float` | R | Work area start (seconds) |
| `work_area_duration` | `float` | R | Work area duration (seconds) |
| `bg_color` | `list[float]` | R/W | Background color `[r, g, b]` |
| `num_layers` | `int` | R | Number of layers |
| `layers` | `LayerCollection` | R | All layers (1-based) |
| `marker_property` | `MarkerProperty \| None` | R | Composition markers |

### Methods

| Method | Returns | Description |
|---|---|---|
| `layer(name_or_index)` | `Layer \| None` | Get layer by name or 1-based index |

### Example

```python
comp = proj.comp("Main Comp")
comp.name = "Renamed"
comp.width = 3840
comp.height = 2160
comp.frame_rate = 60.0
comp.bg_color = [0, 0, 0]

for layer in comp.layers:
    print(layer.name)
```

---

## Layer

Base class for all layers. Subtypes: `AVLayer`, `TextLayer`, `ShapeLayer`, `CameraLayer`, `LightLayer` (auto-selected).

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `index` | `int` | R | 1-based index in composition |
| `name` | `str` | R/W | Layer name |
| `containing_comp` | `CompItem \| None` | R | Parent composition |
| `label` | `int` | R/W | Label color index |
| `enabled` | `bool` | R/W | Visibility (eye icon) |
| `solo` | `bool` | R/W | Solo |
| `shy` | `bool` | R/W | Shy |
| `locked` | `bool` | R/W | Locked |
| `null_layer` | `bool` | R/W | Is null object |
| `guide_layer` | `bool` | R/W | Is guide layer |
| `adjustment_layer` | `bool` | R/W | Is adjustment layer |
| `three_d_layer` | `bool` | R/W | 3D layer |
| `auto_orient` | `bool` | R/W | Auto-orient |
| `effects_active` | `bool` | R/W | Effects enabled |
| `motion_blur` | `bool` | R/W | Motion blur |
| `collapse_transformation` | `bool` | R/W | Collapse / Continuously rasterize |
| `sampling_quality` | `bool` | R/W | Bicubic sampling |
| `in_point` | `float` | R/W | In point (seconds) |
| `out_point` | `float` | R/W | Out point (seconds) |
| `start_time` | `float` | R/W | Start time (seconds) |
| `stretch` | `float` | R/W | Time stretch factor |
| `blending_mode` | `BlendingMode` | R/W | Blending mode |
| `track_matte_type` | `TrackMatteType` | R/W | Track matte type |
| `quality` | `LayerQuality` | R/W | Render quality |
| `parent` | `Layer \| None` | R | Parent layer |
| `num_properties` | `int` | R | Number of top-level property groups |
| `num_effects` | `int` | R | Number of effects |
| `num_masks` | `int` | R | Number of masks |
| `time_remap_enabled` | `bool` | R | Whether time remap exists |
| `time_remap` | `Property \| None` | R | Time remap property |
| `marker_property` | `MarkerProperty \| None` | R | Layer markers |

#### Transform Shortcuts

| Property | Type | Access | Match Name |
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

> These return `Property` objects whose `.value` is R/W. Returns `None` if the property doesn't exist in the project. When Position is separated, use `position_x`/`position_y` instead of `position`.

### Methods

| Method | Returns | Description |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | Get property by match name, display name, or 1-based index |
| `effect(name_or_index)` | `Effect \| None` | Get effect by name or 1-based index |
| `mask(index)` | `Mask \| None` | Get mask by 1-based index |

### Property Access (3 equivalent forms)

```python
layer.property("Transform")     # returns None if not found
layer("Transform")              # raises KeyError if not found
layer["Transform"]              # raises KeyError if not found
```

**Name resolution order:** exact match_name > display name > case-insensitive > model `.name`

### Example

```python
layer = comp.layer(1)
layer.name = "Background"
print(layer.position.value)       # [960, 540]
print(layer.opacity.value)        # 1.0

# Flags & timing
layer.enabled = False
layer.three_d_layer = True
layer.in_point = 1.0
layer.blending_mode = BlendingMode.MULTIPLY

# Chaining
layer("Transform")("Position").value
```

---

## AVLayer (extends Layer)

Asset-based layer (footage, solid, precomp).

| Property | Type | Access | Description |
|---|---|---|---|
| `source` | `Any \| None` | R | Source item (ImageAsset, SolidAsset, Composition) |

---

## TextLayer (extends Layer)

| Property | Type | Access | Description |
|---|---|---|---|
| `source_text` | `TextSourceProperty \| None` | R | Text source property |

```python
layer.source_text.text     # "Hello World"
layer.source_text.fonts    # ["Arial"]
```

---

## ShapeLayer (extends Layer)

| Property | Type | Access | Description |
|---|---|---|---|
| `contents` | `PropertyGroup \| None` | R | Shape contents group (`ADBE Root Vectors Group`) |

---

## CameraLayer (extends Layer)

| Property | Type | Access | Description |
|---|---|---|---|
| `camera_options` | `PropertyGroup \| None` | R | Camera options group |

---

## LightLayer (extends Layer)

No additional properties.

---

## Property

Wraps a single animatable property (position, opacity, scale, etc.).

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `name` | `str` | R | Display name |
| `match_name` | `str` | R | AE internal match name |
| `value` | `Any` | R/W | Static value (or value at first keyframe) |
| `num_keys` | `int` | R | Number of keyframes (0 = not animated) |
| `is_time_varying` | `bool` | R | Has multiple keyframes |
| `expression` | `str \| None` | R | Expression string |
| `expression_enabled` | `bool` | R | Whether expression is set |
| `dimensions_separated` | `bool` | R | Position is split into X/Y/Z |
| `is_spatial` | `bool` | R | Is spatial property |
| `property_value_type` | `PropertyValueType` | R | Value type enum |
| `keys` | `list[KeyframeValue]` | R | All keyframes |

### Keyframe Read Methods

| Method | Returns | Description |
|---|---|---|
| `key(index)` | `KeyframeValue` | Keyframe at 1-based index |
| `key_value(index)` | `Any` | Value at keyframe |
| `key_time(index)` | `float` | Time at keyframe (seconds) |
| `key_in_interpolation_type(index)` | `KeyframeInterpolationType` | Incoming interpolation |
| `key_out_interpolation_type(index)` | `KeyframeInterpolationType` | Outgoing interpolation |
| `key_in_temporal_ease(index)` | `list[dict]` | Incoming ease `[{"speed", "influence"}]` |
| `key_out_temporal_ease(index)` | `list[dict]` | Outgoing ease `[{"speed", "influence"}]` |
| `key_in_spatial_tangent(index)` | `list[float] \| None` | Incoming spatial tangent |
| `key_out_spatial_tangent(index)` | `list[float] \| None` | Outgoing spatial tangent |
| `key_roving(index)` | `bool` | Is roving keyframe |
| `nearest_key_index(t)` | `int` | Index of nearest keyframe to time `t` |
| `value_at_time(t)` | `Any` | Interpolated value at time `t` |

### Keyframe Write Methods

| Method | Returns | Description |
|---|---|---|
| `set_value_at_key(index, value)` | `None` | Set keyframe value |
| `set_value_at_time(time, value)` | `None` | Set value at nearest keyframe to `time` |
| `set_interpolation_type_at_key(index, in_type, out_type=None)` | `None` | Set in/out interpolation type |
| `set_temporal_ease_at_key(index, in_ease=None, out_ease=None)` | `None` | Set temporal ease |

### Value Types

| AE Type | Python Type |
|---|---|
| 2D position / vector | `[x, y]` |
| 3D position / vector | `[x, y, z]` |
| Color | `[r, g, b, a]` |
| Scalar (opacity, rotation...) | `float` |
| Layer reference | `int` (layer ID) |

> Scale and Opacity are stored as 0-1 fractions (1.0 = 100%).

### Example

```python
pos = layer.position

# Read
pos.value                     # [960, 540]
pos.num_keys                  # 2
pos.key_value(1)              # [0, 0]
pos.key_time(2)               # 1.0
pos.value_at_time(0.5)        # [480, 270]

# Write static value
pos.value = [500.0, 300.0]

# Write keyframe
pos.set_value_at_key(1, [100.0, 200.0])

# Write interpolation
from aep_tools import KeyframeInterpolationType as KIT
pos.set_interpolation_type_at_key(1, in_type=KIT.BEZIER, out_type=KIT.HOLD)

# Write ease
pos.set_temporal_ease_at_key(1,
    in_ease=[{"speed": 0.0, "influence": 33.33}],
    out_ease=[{"speed": 0.0, "influence": 33.33}],
)
```

---

## PropertyGroup

Wraps a group of properties. Supports chaining.

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `name` | `str` | R | Group name |
| `match_name` | `str` | R | AE match name |
| `enabled` | `bool \| None` | R | Enabled state |
| `num_properties` | `int` | R | Number of children |

### Methods

| Method | Returns | Description |
|---|---|---|
| `property(name_or_index)` | `Any \| None` | Get child by name or 1-based index |

Supports `__call__`, `__getitem__`, `__len__`, `__iter__`.

### Example

```python
transform = layer("Transform")
transform("Position").value         # [960, 540]
transform.property(1).value         # anchor point
len(transform)                      # number of children

for prop in transform:
    print(prop.name)
```

---

## Effect

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `name` | `str` | R | Effect name |
| `match_name` | `str` | R | AE match name |
| `enabled` | `bool` | R | Enabled state |
| `num_params` | `int` | R | Number of parameters |

### Methods

| Method | Returns | Description |
|---|---|---|
| `param(name_or_index)` | `Any \| None` | Get parameter by name or 1-based index |

Supports `__call__` and `__getitem__`.

### Example

```python
eff = layer.effect(1)
eff = layer.effect("Gaussian Blur")
eff.param(1).value                   # first parameter
eff("Blurriness").value              # by name
```

---

## Mask

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `name` | `str` | R | Mask name |
| `match_name` | `str` | R | AE match name |
| `mode` | `MaskMode` | R | Mask mode |
| `inverted` | `bool` | R | Inverted |
| `locked` | `bool` | R | Locked |
| `index` | `int` | R | 1-based index |
| `mask_path` | `Property \| None` | R | Mask path shape |
| `mask_feather` | `Property \| None` | R | Feather |
| `mask_opacity` | `Property \| None` | R | Opacity |
| `mask_expansion` | `Property \| None` | R | Expansion |

### Example

```python
m = layer.mask(1)
m.mode                    # MaskMode.ADD
m.mask_opacity.value      # 100.0
```

---

## MarkerProperty

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `num_keys` | `int` | R | Number of markers |

### Methods

| Method | Returns | Description |
|---|---|---|
| `key_value(index)` | `MarkerValue` | Marker at 1-based index |
| `key_time(index)` | `float` | Time of marker (seconds) |
| `nearest_key_index(t)` | `int` | Nearest marker to time `t` |

---

## MarkerValue

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `comment` | `str` | R | Comment text |
| `duration` | `float` | R | Duration (seconds) |
| `label` | `int` | R | Label color index |
| `time` | `float` | R | Time (seconds) |

### Example

```python
mp = comp.marker_property
mv = mp.key_value(1)
print(mv.comment, mv.time)    # "Intro" 1.0
```

---

## TextSourceProperty

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `text` | `str` | R | Current text string |
| `value` | `TextDocument \| None` | R | Full TextDocument |
| `fonts` | `list[str]` | R | Font family names |
| `num_keys` | `int` | R | Number of text keyframes |

### Methods

| Method | Returns | Description |
|---|---|---|
| `key_value(index)` | `TextDocument \| None` | TextDocument at keyframe |
| `key_time(index)` | `float` | Time at keyframe (seconds) |

---

## KeyframeValue

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `index` | `int` | R | 1-based index |
| `time` | `float` | R | Time (seconds) |
| `value` | `Any` | R | Value |

---

## FolderItem

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `type_name` | `str` | R | `"Folder"` |
| `name` | `str` | R | Folder name |
| `id` | `int` | R | Internal ID |
| `num_items` | `int` | R | Child count |
| `items` | `ItemCollection` | R | Children (1-based) |

---

## FootageItem

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `type_name` | `str` | R | `"Footage"` or `"Solid"` |
| `name` | `str` | R | Item name |
| `id` | `int` | R | Internal ID |
| `width` | `int` | R | Width in pixels |
| `height` | `int` | R | Height in pixels |
| `file` | `str \| None` | R/W | File path (footage only) |
| `color` | `list[float] \| None` | R | `[r, g, b, a]` (solid only) |

### Example

```python
item = proj.item(1)
print(item.file)                     # "/path/to/footage.mov"
item.file = "/new/path.mov"          # update path
proj.save("output.aep")
```

---

## RenderQueue

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `num_items` | `int` | R | Number of items |

### Methods

| Method | Returns | Description |
|---|---|---|
| `item(index)` | `RenderQueueItem \| None` | Get by 1-based index |

---

## RenderQueueItem

### Properties

| Property | Type | Access | Description |
|---|---|---|---|
| `comp_name` | `str` | R | Composition name |
| `status` | `int` | R | Render status |
| `num_output_modules` | `int` | R | Number of output modules |

### Methods

| Method | Returns | Description |
|---|---|---|
| `output_module(index)` | `OutputModule \| None` | Get by 1-based index |

---

## Enums

### BlendingMode

| Value | Name |
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

| Value | Name |
|---|---|
| 0 | NONE |
| 1 | ALPHA |
| 2 | ALPHA_INVERTED |
| 3 | LUMA |
| 4 | LUMA_INVERTED |

### MaskMode

| Value | Name |
|---|---|
| 0 | NONE |
| 1 | ADD |
| 2 | SUBTRACT |
| 3 | INTERSECT |
| 4 | DARKEN |
| 5 | LIGHTEN |
| 6 | DIFFERENCE |

### KeyframeInterpolationType

| Value | Name |
|---|---|
| 1 | LINEAR |
| 2 | BEZIER |
| 3 | HOLD |

### LayerQuality

| Value | Name |
|---|---|
| 0 | WIREFRAME |
| 1 | DRAFT |
| 2 | BEST |

### LayerType

| Value | Name |
|---|---|
| 0 | ASSET |
| 1 | LIGHT |
| 2 | CAMERA |
| 3 | TEXT |
| 4 | SHAPE |

### PropertyValueType

| Value | Name |
|---|---|
| 0 | COLOR |
| 1 | SCALAR |
| 2 | SPATIAL |
| 3 | MULTIDIMENSIONAL |
| 4 | LAYER_REF |
| 5 | CUSTOM |
| 6 | UINT |

### AutoOrientType

| Value | Name |
|---|---|
| 0 | NO_AUTO_ORIENT |
| 1 | ALONG_PATH |
| 2 | CAMERA_OR_POINT_OF_INTEREST |
| 3 | CHARACTERS_TOWARD_CAMERA |

---

## Match Name Reference

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
| `ADBE Mask Shape` | Mask Path |
| `ADBE Mask Feather` | Mask Feather |
| `ADBE Mask Opacity` | Mask Opacity |
| `ADBE Mask Offset` | Mask Expansion |

Both match names and display names can be used for property lookup.
