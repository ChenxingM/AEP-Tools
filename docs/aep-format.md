# AEP/AEPX Binary Data Structure Specification

This document describes the internal data structure of Adobe After Effects project files
(`.aep` binary and `.aepx` XML formats), based on reverse-engineering analysis.

---

## Table of Contents

1. [File Container Format](#1-file-container-format)
2. [RIFF Chunk Layout](#2-riff-chunk-layout)
3. [Chunk Type Reference](#3-chunk-type-reference)
4. [Project Hierarchy](#4-project-hierarchy)
5. [Project Version (head / svap)](#5-project-version-head--svap)
6. [Item Data (idta)](#6-item-data-idta)
7. [Composition Data (cdta)](#7-composition-data-cdta)
8. [Layer Data (ldta)](#8-layer-data-ldta)
9. [Property System](#9-property-system)
10. [Animated Property (tdbs)](#10-animated-property-tdbs)
11. [Keyframe Format](#11-keyframe-format)
12. [Asset Data](#12-asset-data)
13. [Effect Definitions](#13-effect-definitions)
14. [Mask Data (mkif)](#14-mask-data-mkif)
15. [Bezier Shape (shph)](#15-bezier-shape-shph)
16. [Gradient Data (GCst)](#16-gradient-data-gcst)
17. [Text Data (btdk / COS Format)](#17-text-data-btdk--cos-format)
18. [Marker Data (Nmrd)](#18-marker-data-nmrd)
19. [Layer Styles](#19-layer-styles)
20. [AEPX XML Format](#20-aepx-xml-format)
21. [Constants and Enumerations](#21-constants-and-enumerations)
22. [Match Name Reference](#22-match-name-reference)
23. [Write-Back / RIFF Serialization](#23-write-back--riff-serialization)

---

## 1. File Container Format

AEP files use the **RIFF** (Resource Interchange File Format) container.

### File Header (12 bytes)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       4     magic           char[4]   "RIFX" (big-endian) or "RIFF" (little-endian)
4       4     file_size       uint32    Total file size minus 8 bytes
8       4     file_type       char[4]   "Egg!" — After Effects identifier
```

- **RIFX** = Big-endian byte order (most common for AEP files)
- **RIFF** = Little-endian byte order
- All multi-byte integers and floats in the file follow this byte order

### Trailing Data (XMP Metadata)

AEP files may contain **XMP metadata** appended after the RIFX chunk. This data is not part of the RIFF structure and must be preserved during round-trip save operations.

```
[RIFX chunk (8 + file_size bytes)] [XMP metadata (variable, typically ~14KB)]
```

The RIFX chunk boundary is at offset `8 + file_size` (where `file_size` is the uint32 at offset 4). Any bytes beyond this offset are trailing data.

### AEPX Detection

AEPX files are XML-based. They begin with `<?xml` or `<AfterEffectsProject` instead of
RIFF/RIFX magic bytes. See [Section 19](#19-aepx-xml-format) for XML format details.

---

## 2. RIFF Chunk Layout

Every data unit in the file is a **chunk**:

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       4     header          char[4]   Chunk type identifier (ASCII)
4       4     size            uint32    Byte count of data following this field
8       size  data            varies    Chunk payload
```

- Chunks are padded to **2-byte boundaries** (1 padding byte if `size` is odd)
- **LIST chunks** contain a 4-byte sub-type followed by child chunks:

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       4     header          char[4]   "LIST"
4       4     size            uint32    Total size of sub-type + children
8       4     list_type       char[4]   List sub-type (e.g., "Fold", "Item", "Layr")
12      ...   children        Chunk[]   Sequence of child chunks
```

---

## 3. Chunk Type Reference

### Container Chunks (LIST sub-types)

| Sub-type | Description |
|----------|-------------|
| `Fold` | Project root folder |
| `Item` | Project item (composition, folder, or asset) |
| `Sfdr` | Sub-folder |
| `Layr` | Layer in a composition |
| `SecL` | Section layer (composition markers) |
| `Pin ` | Asset pin (container for asset data) |
| `EfdG` | Effect definitions group |
| `EfDf` | Single effect definition |
| `parT` | Effect parameter template list |
| `tdgp` | Property group |
| `tdbs` | Animated property data |
| `tdsn` | Property display name wrapper (contains Utf8) |
| `fnam` | File/effect name wrapper (contains Utf8) |
| `pdnm` | Parameter display name wrapper (contains Utf8) |
| `Als2` | File alias container (contains alas) |
| `om-s` | Animated shape property |
| `omks` | Shape keyframe collection |
| `shap` | Single shape definition |
| `GCst` | Animated gradient property |
| `GCky` | Gradient keyframe collection |
| `otst` | Animated orientation property |
| `otky` | Orientation keyframe collection |
| `mrst` | Animated marker property |
| `mrky` | Marker keyframe collection |
| `Nmrd` | Named record (single marker) |
| `btds` | Animated text property |
| `sspc` | Source parameters / effect instance |
| `list` | Generic keyframe list container |

### Data Chunks (leaf-level binary)

| Header | Size | Description |
|--------|------|-------------|
| `Utf8` | var | UTF-8 encoded string |
| `wsnm` | var | UTF-16 encoded workspace name |
| `tdmn` | var | Match name string (ADBE identifier) |
| `head` | 20 | Project header (format level, version) |
| `svap` | 4 | Last-save AE version identifier |
| `idta` | ~20 | Item metadata (type, ID) |
| `cdta` | ~142 | Composition metadata (size, framerate, duration) |
| `ldta` | ~164 | Layer metadata (timing, flags, blend mode) |
| `tdsb` | 4 | Property visibility/split/enabled flags |
| `tdb4` | ~69 | Property type metadata (dimensions, type flags) |
| `cdat` | var | Static property value (float64 array) |
| `tdum` | 8 | Property minimum bound (float64) |
| `tduM` | 8 | Property maximum bound (float64) |
| `lhd3` | ~20 | Keyframe list header (count, item size) |
| `ldat` | var | Keyframe list data (binary array) |
| `opti` | var | Asset options (solid color or type code) |
| `sspc` | var | Source parameters (width, height, sequence info) |
| `alas` | var | File reference (JSON string) |
| `mkif` | 12 | Mask info (mode, inverted, locked) |
| `shph` | 20 | Shape header (bounding box, closed flag) |
| `btdk` | var | Text binary data (COS format) |
| `NmHd` | ~17 | Marker header (duration, flags) |
| `tdpi` | 4 | Layer reference target ID |
| `tdps` | 4 | Layer reference source |
| `tdli` | 4 | Unsigned integer reference |
| `otda` | 24 | Orientation data (3× float64) |

---

## 4. Project Hierarchy

The overall chunk tree structure:

```
RIFX "Egg!"
├── LIST Fold                       ← Project root folder
│   ├── LIST Item                   ← Folder item
│   │   ├── idta                    ← item_type=1 (folder)
│   │   ├── Utf8                    ← Folder name
│   │   └── LIST Sfdr              ← Sub-folder children
│   │       └── LIST Item ...
│   │
│   ├── LIST Item                   ← Composition item
│   │   ├── idta                    ← item_type=4 (composition)
│   │   ├── Utf8                    ← Composition name
│   │   ├── cdta                    ← Composition metadata
│   │   ├── LIST Layr              ← Layer 1
│   │   │   ├── ldta               ← Layer data
│   │   │   ├── Utf8               ← Layer name
│   │   │   └── LIST tdgp          ← Property tree root
│   │   │       ├── tdmn           ← "ADBE Transform Group"
│   │   │       ├── LIST tdgp      ← Transform group
│   │   │       │   ├── tdmn       ← "ADBE Position"
│   │   │       │   ├── LIST tdbs  ← Animated position
│   │   │       │   │   ├── tdsb   ← Flags
│   │   │       │   │   ├── tdb4   ← Type metadata
│   │   │       │   │   ├── cdat   ← Static value
│   │   │       │   │   ├── list   ← Keyframes (if animated)
│   │   │       │   │   └── Utf8   ← Expression (if any)
│   │   │       │   └── ...
│   │   │       └── ...
│   │   ├── LIST Layr              ← Layer 2
│   │   └── LIST SecL              ← Composition markers
│   │
│   └── LIST Item                   ← Asset item
│       ├── idta                    ← item_type=7 (asset)
│       ├── Utf8                    ← Asset name
│       └── LIST Pin               ← Asset container
│           ├── sspc               ← Source dimensions
│           ├── opti               ← Asset type/options
│           ├── LIST Als2          ← File reference (if file asset)
│           │   └── alas           ← JSON path data
│           └── Utf8               ← Name parts
│
└── LIST EfdG                       ← Effect definitions
    └── LIST EfDf                   ← Single effect
        ├── tdmn                    ← Effect match name
        └── LIST sspc              ← Effect template
            ├── LIST fnam          ← Display name
            └── LIST parT          ← Parameter definitions
```

---

## 5. Project Version (head / svap)

AE version information is stored in two top-level chunks directly under the RIFX root.

### head Chunk (20 bytes)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       2     format_level    uint16    File format level (encodes AE major version)
2       2     minor_version   uint16    AE minor version number
4       4     version_id      uint32    Internal version identifier (same as svap)
8       12    (reserved)      —         Timestamps, internal counters
```

**AE major version:** `ae_major = format_level - 71`

| format_level | AE Major Version |
|-------------|-----------------|
| 93 | AE 22 (CC 2022) |
| 94 | AE 23 (CC 2023) |
| 95 | AE 24 (CC 2024) |
| 96 | AE 25 (CC 2025) |
| 97 | AE 26 |

**AE minor version:** `head[2:4]` is a uint16 that directly gives the minor version (reliable for AE 23+). For example, format_level=96 and minor_version=6 → AE 25.6.

### svap Chunk (4 bytes)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       4     version_id      uint32    Internal AE build identifier
```

The 4-byte `svap` value is identical to `head[4:8]`. It encodes an internal build number but does **not** directly map to the marketing patch version (e.g., the `.4` in 25.6.4 is not reliably extractable).

### Hex Offsets for Manual Editing

In a typical AEP file:

| Chunk | Offset | Size | Description |
|-------|--------|------|-------------|
| `svap` | 0x14 | 4 | `version_id` — last-save AE build identifier |
| `head` format_level | 0x20 | 2 | uint16 — determines AE major version |
| `head` minor_version | 0x22 | 2 | uint16 — AE minor version |
| `head` version_id | 0x24 | 4 | Same value as svap |

> **Note:** These offsets assume standard AEP layout. The `svap` chunk is the first child of the RIFX root, followed by `head`.

---

## 6. Item Data (idta)

Identifies the type and ID of a project item.

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       2     item_type       uint16    Item type code
2       14    (reserved)      —         —
16      4     item_id         uint32    Unique item identifier
```

**Item Type Codes:**

| Value | Meaning |
|-------|---------|
| 1 | Folder |
| 4 | Composition |
| 7 | Asset (image, solid, video, audio) |

---

## 7. Composition Data (cdta)

Stores composition-level metadata. Time values use **rational number** encoding.

```
Offset  Size  Field               Type      Description
─────────────────────────────────────────────────────────
0       4     (reserved)          —         —
4       4     time_denom          uint32    Framerate denominator
8       4     time_num            uint32    Framerate numerator
                                            framerate = time_num / time_denom
12      9     (reserved)          —         —
21      2     playhead_raw        uint16    Playhead position (raw)
23      2     (reserved)          —         —
25      2     playhead_div        uint16    Playhead divisor
                                            playhead_time = playhead_raw / (playhead_div / fps)
27      2     (reserved)          —         —
29      2     in_time_raw         uint16    Work area in-point (raw)
31      2     (reserved)          —         —
33      2     in_time_div         uint16    In-point divisor
35      2     (reserved)          —         —
37      2     out_time_raw        uint16    Work area out-point (raw)
39      2     (reserved)          —         —
41      2     out_time_div        uint16    Out-point divisor
43      2     (reserved)          —         —
45      2     duration_raw        uint16    Duration (raw)
47      2     (reserved)          —         —
49      2     duration_div        uint16    Duration divisor
51      1     (reserved)          —         —
52      1     bg_red              uint8     Background color R (0–255)
53      1     bg_green            uint8     Background color G (0–255)
54      1     bg_blue             uint8     Background color B (0–255)
55      85    (reserved)          —         —
140     2     width               uint16    Composition width (pixels)
142     2     height              uint16    Composition height (pixels)
144     12    (reserved)          —         —
```

**Time Calculation Formula:**

```
divisor = raw_divisor / framerate
value   = raw_value / divisor
```

**Special Case:** If `out_time_raw == 65535`, the out-time equals the composition duration.

---

## 8. Layer Data (ldta)

Contains all core layer attributes.

### Binary Layout

```
Offset  Size  Field               Type      Description
─────────────────────────────────────────────────────────
0       4     layer_id            uint32    Unique layer identifier
4       2     quality             uint16    Render quality (1=Draft, 2=Best)
6       2     (reserved)          —         —
8       4     time_stretch_num    sint32    Time stretch numerator
12      4     start_time_num      sint32    Layer start time numerator
16      4     start_time_den      uint32    Layer start time denominator
20      4     in_time_num         sint32    In-point numerator
24      4     in_time_den         uint32    In-point denominator
28      4     out_time_num        sint32    Out-point numerator
32      4     out_time_den        uint32    Out-point denominator
36      4     flags               uint32    Layer flags (see below)
40      4     asset_id            uint32    Reference to source asset/composition
44      17    (reserved)          —         —
61      1     label_color         uint8     AE label color index (0–16)
62      2     (reserved)          —         —
64      32    (reserved)          —         —
96      4     blend_mode          uint32    Blend mode constant (see §20)
100     4     (reserved)          —         —
104     4     matte_mode          uint32    Track matte mode (see §20)
108     2     (reserved)          —         —
110     2     time_stretch_den    uint16    Time stretch denominator
112     19    (reserved)          —         —
131     1     layer_type          uint8     Layer type code (see below)
132     4     parent_id           uint32    Parent layer ID (0 = no parent)
136     24    (reserved)          —         —
160     4     matte_id            uint32    Track matte source layer ID
```

### Layer Type Codes

| Value | Type |
|-------|------|
| 0 | Asset (footage, solid, composition reference) |
| 1 | Light |
| 2 | Camera |
| 3 | Text |
| 4 | Shape |

### Layer Flags (4 bytes, bit-level)

```
Byte[0]:
  bit 1  is_guide              Layer is a guide layer
  bit 6  bicubic_sampling      Use bicubic sampling

Byte[1]:
  bit 0  auto_orient           Auto-orient to path
  bit 1  is_adjustment         Adjustment layer
  bit 2  threedimensional      3D layer
  bit 3  solo                  Solo switch enabled
  bit 7  is_null               Null object layer

Byte[2]:
  bit 0  visible               Layer visibility (eye icon)
  bit 2  effects_enabled       Effects switch on
  bit 3  motion_blur_enabled   Motion blur enabled
  bit 5  locked                Layer locked
  bit 6  shy                   Shy layer
  bit 7  continuously_rasterize  Collapse transformations / Continuously rasterize
```

### Time Value Calculation

```
start_time  = start_time_num  / start_time_den
in_time     = in_time_num     / in_time_den
out_time    = out_time_num    / out_time_den
time_stretch = time_stretch_num / time_stretch_den
```

### Layer Name Resolution

The layer name comes from the `Utf8` chunk in the `Layr` list. If the name is empty
(placeholder `"-_0_/-"`), the parser falls back to the **source asset or composition name**
referenced by `asset_id`.

---

## 9. Property System

After Effects stores all animatable properties in a **tree** of property groups.

### Property Group (tdgp)

A `LIST tdgp` chunk contains these children in sequence:

```
tdmn    → Match name identifying this child
tdsb    → Visibility/enabled flags for the group itself
tdsn    → Display name (LIST with inner Utf8)
tdmn    → Match name for first child property
<child> → Property data (tdgp, tdbs, om-s, GCst, etc.)
tdmn    → Match name for second child property
<child> → Property data
...
```

Each `tdmn` chunk is consumed by the **next** non-metadata chunk in the sequence.

### Property Visibility Flags (tdsb, 4 bytes)

```
Offset  Size  Field       Type      Description
─────────────────────────────────────────────────
0       4     flags       uint32    Bit flags
```

```
Byte[3]:
  bit 0  visible     Property is visible (or 'enabled' when split=true)
  bit 1  split       Indicates this is a Layer Styles sub-group
```

**Interpretation:**
- `split=false`: `bit 0` → `visible` field (normal property visibility)
- `split=true`:  `bit 0` → `enabled` field (Layer Styles on/off toggle)

### Property Types

Properties manifest as different chunk types based on what they represent:

| Chunk Type | Resulting Object | Usage |
|------------|-----------------|-------|
| `tdgp` | PropertyGroup | Container for sub-properties |
| `tdbs` | AnimatedProperty | Standard animatable value |
| `om-s` | AnimatedProperty (shape) | Bezier path data |
| `GCst` | AnimatedProperty (gradient) | Color gradient |
| `otst` | AnimatedProperty (orientation) | 3D orientation |
| `mrst` | AnimatedProperty (marker) | Composition markers |
| `btds` | TextProperty | Text document with styling |
| `sspc` | EffectInstance | Applied effect with parameters |

---

## 10. Animated Property (tdbs)

A `LIST tdbs` contains the full definition of an animated property.

### Children

```
tdsb    → Visibility flags
tdb4    → Property type metadata
cdat    → Static value (when not animated)
list    → Keyframe list (when animated)
Utf8    → Expression string (optional)
tdpi    → Layer reference target (for layer ref properties)
tdps    → Layer reference source (for layer ref properties)
tdli    → Unsigned int reference (for uint ref properties)
```

### Property Metadata (tdb4)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       2     (reserved)      —         —
2       2     components      uint16    Number of value components (1–4)
4       2     type_flags      uint16    Spatial flag (see below)
6       7     (reserved)      —         —
13      4     time_scale      uint32    Keyframe time divisor
17      39    (reserved)      —         —
56      4     prop_flags      uint32    Property type indicators
60      8     (reserved)      —         —
68      1     animated        uint8     1 = has keyframes, 0 = static
```

**type_flags (offset 4):**

```
Byte[1]:
  bit 3  is_spatial    Property has spatial bezier tangents (position, anchor point)
```

**prop_flags (offset 56):**

```
Byte[0]:
  bit 0  is_color      RGBA color property

Byte[2]:
  bit 0  is_bool       Boolean/checkbox property
  bit 2  is_ref        Layer or value reference
```

### Property Type Resolution

Priority order (first match wins):

| Condition | prop_type | Name | Example Properties |
|-----------|-----------|------|--------------------|
| `is_spatial` | 2 | Spatial | Position, Anchor Point |
| `is_bool` | 0 | Color* | Opacity, enable toggles |
| `is_color` | 1 | Scalar | Fill Color, Stroke Color |
| `is_ref` + `tdpi` exists | 4 | Layer Reference | Set Matte source |
| `is_ref` + `tdli` exists | 6 | Uint Reference | Dropdown selections |
| (default) | 3 | Multidimensional | Scale, Rotation |

*Note: In the original JS code, prop_type 0 maps to boolean/simple and prop_type 1 to scalar
despite the names. The naming is a historical artifact.*

### Static Value (cdat)

The `cdat` chunk stores the property's static value followed by tangent/velocity slots. Its total size depends on the property type:

**Non-spatial properties** (Scale, Rotation, Opacity): `components × 5` float64s

```
[value₁..valueₙ] [ease_in₁..ease_inₙ] [ease_out₁..ease_outₙ] [influence_in₁..ₙ] [influence_out₁..ₙ]
```

**Spatial properties** (Position, Anchor Point): `components × 3 + 3` float64s

```
[value₁..valueₙ] [spatial_in₁..ₙ] [spatial_out₁..ₙ] [temporal_ease × 3]
```

**Examples of cdat sizes:**

| Property | Components | Spatial | float64 count | Byte size |
|----------|-----------|---------|--------------|-----------|
| Opacity | 1 | No | 1×5 = 5 | 40 |
| Rotation Z | 1 | No | 1×5 = 5 | 40 |
| Position (2D) | 2 | Yes | 2×3+3 = 9 | 72 |
| Anchor Point (2D) | 2 | Yes | 2×3+3 = 9 | 72 |
| Scale (3D) | 3 | No | 3×5 = 15 | 120 |

> **Important:** When modifying cdat values, only overwrite the first `components` float64s (the actual value). The remaining tangent/velocity data must be preserved to avoid corrupting the project file.

**Value interpretation by prop_type:**

| prop_type | Layout | Description |
|-----------|--------|-------------|
| 0 (Color) | `[alpha, R, G, B]` | R/G/B in 0–255, alpha in 0–1 |
| 1 (Scalar) | Not in cdat | Value comes from `extra_values` list |
| 2 (Spatial) | `[x, y]` or `[x, y, z]` | Position coordinates |
| 3 (Multi) | `[v₁, v₂, …]` | Scale, rotation, etc. |
| 4 (LayerRef) | Not in cdat | See tdpi/tdps chunks |
| 6 (Uint) | Not in cdat | See tdli chunk |

> **Note:** AE stores Scale and Opacity as 0–1 fractions internally (1.0 = 100%). The AE UI displays them as percentages.

### Property Bounds (tdum / tduM)

The `tdum` and `tduM` chunks define the minimum and maximum allowed values for a property. Each contains a single float64.

```
tdum: 8 bytes → float64 minimum value
tduM: 8 bytes → float64 maximum value
```

These chunks are **always present** in real AEP files, even when both values are 0.0. For example, Opacity has tdum=0.0 and tduM=100.0.

---

## 11. Keyframe Format

### Keyframe List Container (list)

Contains `lhd3` (header) and `ldat` (data).

**List Header (lhd3):**

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       10    (reserved)      —         —
10      2     count           uint16    Number of keyframes
12      6     (reserved)      —         —
18      2     item_size       uint16    Bytes per keyframe record
```

**List Data (ldat):** `count × item_size` bytes, divided into fixed-size records.

### Keyframe Record — Common Header (8 bytes)

All keyframe types share this prefix:

```
Offset  Size  Field               Type      Description
─────────────────────────────────────────────────────────
0       1     (reserved)          —         —
1       4     time_raw            sint32    Keyframe time (divide by time_scale)
5       1     transition_type     uint8     Interpolation type
6       1     label_color         uint8     Label color index
7       1     flags               uint8     Bezier mode flags
```

**Transition Types:**

| Value | Name | Description |
|-------|------|-------------|
| 1 | Linear | Linear interpolation |
| 2 | Bezier | Bezier curve interpolation |
| 3 | Hold | Step/hold (no interpolation) |

**Flags byte (offset 7):**

```
bit 3  continuous_bezier    Continuous bezier handles
bit 4  auto_bezier          Auto bezier mode
bit 5  roving               Roving keyframe (smooth motion)
```

Bezier mode: `continuous_bezier` → mode 1, `auto_bezier` → mode 2, neither → mode 0.

### Keyframe Record — Type-Specific Data

**Spatial (prop_type=2) — Position/Anchor Point:**

```
Offset  Size             Field           Description
───────────────────────────────────────────────────────
8       16               (reserved)      —
24      8                in_speed        float64
32      8                in_influence    float64
40      8                out_speed       float64
48      8                out_influence   float64
56      C×8              value           [x, y, z] coordinates
56+C×8  C×8              in_tangent      Bezier in-tangent [x, y, z]
56+C×16 C×8              out_tangent     Bezier out-tangent [x, y, z]
```

*(C = components count)*

**Scalar (prop_type=1) — Opacity, Rotation, etc.:**

```
Offset  Size  Field           Description
──────────────────────────────────────────
8       16    (reserved)      —
24      8     in_speed        float64
32      8     in_influence    float64
40      8     out_speed       float64
48      8     out_influence   float64
```

Value comes from `extra_values[index]`, not from the keyframe data itself.

**Multidimensional (prop_type=3,5) — Scale, etc.:**

```
Offset  Size    Field           Description
─────────────────────────────────────────────
8       C×8     value           [v₁, v₂, …] float64 array
8+C×8   C×8     in_speed        float64 per component
8+C×16  C×8     in_influence    float64 per component
8+C×24  C×8     out_speed       float64 per component
8+C×32  C×8     out_influence   float64 per component
```

**Color (prop_type=0):**

```
Offset  Size  Field           Description
──────────────────────────────────────────
8       16    (reserved)      —
24      8     in_speed        float64
32      8     in_influence    float64
40      8     out_speed       float64
48      8     out_influence   float64
56      C×8   value           [alpha, R, G, B] — R/G/B in 0–255
```

### Short Keyframes (Markers)

Marker keyframes may have `item_size` as small as 16 bytes, containing only the
common header (8 bytes) + 8 bytes of basic data. The parser checks
`reader.remaining()` before attempting to read speed/influence values.

### Speed Value Processing

`NaN` float64 values in speed fields are replaced with `0.0`.

---

## 12. Asset Data

Assets are stored under `LIST Item` with `item_type=7`, containing a `LIST Pin`.

### Source Parameters (sspc in Pin)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       32    (reserved)      —         —
32      2     width           uint16    Asset width (pixels)
34      2     (reserved)      —         —
36      2     height          uint16    Asset height (pixels)
38      2     (reserved)      —         —
40      2     seq_count       uint16    Sequence frame count
42      132   (reserved)      —         —
174     2     seq_start       uint16    Sequence start frame
176     2     (reserved)      —         —
178     2     seq_end         uint16    Sequence end frame
180     2     (reserved)      —         —
182     2     seq_max_len     uint16    Max frame name digit length
```

### Asset Options (opti)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       4     type_code       char[4]   Asset type identifier
4       2     (reserved)      —         —
6       4     (reserved)      —         —
```

**If type_code == `"Soli"` (Solid Color):**

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
10      4     alpha           float32   Alpha (0.0–1.0)
14      4     red             float32   Red component
18      4     green           float32   Green component
22      4     blue            float32   Blue component
26      256   name            char[256] Null-terminated solid name (UTF-8)
```

Color component encoding: value `== 255` → use as-is, otherwise `value × 255`.

**If type_code != `"Soli"` (File Reference):**

The file path is stored in `LIST Als2 → alas` as a JSON string:

```json
{
  "fullpath": "C:\\Users\\...\\image.png",
  "target_is_folder": false
}
```

When `target_is_folder` is `true`, the asset is an **image sequence** and the
`seq_count`, `seq_start`, `seq_end`, `seq_max_len` fields in sspc are valid.

---

## 13. Effect Definitions

Global effect templates are stored in `LIST EfdG`.

### Structure per Effect (LIST EfDf)

```
tdmn              → Effect match name (e.g., "ADBE Gaussian Blur 2")
LIST sspc         → Effect template
  LIST fnam       → Display name
    Utf8          → "Gaussian Blur"
  LIST parT       → Parameter definitions
    tdmn          → Parameter 1 match name
    <param_data>  → Parameter 1 binary metadata
    pdnm          → Parameter 1 display name (optional)
    tdmn          → Parameter 2 match name
    <param_data>  → Parameter 2 binary metadata
    ...
```

### Parameter Binary Metadata

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       14    (reserved)      —         —
14      2     param_type      uint16    Parameter type code
16      32    name            char[32]  Null-terminated parameter name (UTF-8)
48      8     (varies)        —         Default/last values (type-dependent)
```

### Parameter Type Codes

| Code | Type | Value Format |
|------|------|-------------|
| 0 | Layer Reference | LayerRef object |
| 2 | Angle | `sint32 / 65536` (radians, fixed-point) |
| 3 | Percent | `sint32 / 65536` (fixed-point) |
| 4 | Dropdown | `uint32` (selected index) + `uint8` (default) |
| 5 | Color (RGB) | `[alpha/255, R, G, B]` as uint8 |
| 6 | 2D Point | `[sint32/128, sint32/128]` (fixed-point) |
| 7 | Popup | `uint32` (selected) + skip(2) + `uint16` (default) |
| 10 | Float | `float64` |
| 18 | 3D Color | `[float64×512, float64×512, float64×512]` |

### Effect Instance (sspc in property tree)

When an effect is applied to a layer, it appears as `LIST sspc` inside the property
tree under `"ADBE Effect Parade"`. Contains `fnam` (instance name) and `tdgp`
(parameter values).

---

## 14. Mask Data (mkif)

Mask metadata chunk, found in property groups under `"ADBE Mask Parade"`.

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       1     inverted        uint8     1 = mask inverted
1       1     locked          uint8     1 = mask locked
2       4     (reserved)      —         —
6       2     mode            uint16    Mask operation mode
8       3     (reserved)      —         —
11      1     index           uint8     Mask order index
```

**Mask Modes:**

| Value | Mode |
|-------|------|
| 0 | None |
| 1 | Add |
| 2 | Subtract |
| 3 | Intersect |
| 4 | Darken |
| 5 | Lighten |
| 6 | Difference |

The `mkif` chunk is followed by a property group (`tdgp`) containing the mask's
shape, feather, opacity, and expansion properties.

---

## 15. Bezier Shape (shph)

Shape path data for vector masks and shape layers.

### Shape Header (shph)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       3     (reserved)      —         —
3       1     flags           uint8     Shape flags
4       4     min_x           float32   Bounding box left
8       4     min_y           float32   Bounding box top
12      4     max_x           float32   Bounding box right
16      4     max_y           float32   Bounding box bottom
```

**Flags byte:**

```
bit 3  open_path    0 = closed path, 1 = open path
```

Note: The `closed` property is the **inverse** of bit 3: `closed = !flags.bit(0, 3)`.

### Shape Points

Stored in a `list` chunk (same format as keyframe lists). Each point record:

```
Offset  Size  Field   Type      Description
──────────────────────────────────────────
0       4     x       float32   X coordinate
4       4     y       float32   Y coordinate
```

Points with `NaN` coordinates are skipped.

Points are organized in **triplets**: `[in_tangent, vertex, out_tangent]`.
Total vertex count = `len(points) / 3`.

### Shape in Animated Property

Animated shapes use `LIST om-s`:

```
LIST om-s
  LIST omks          ← Shape keyframe collection
    LIST shap        ← Shape at keyframe 0
      shph           ← Shape header
      list           ← Shape points
    LIST shap        ← Shape at keyframe 1
    ...
  LIST tdbs          ← Animation timing (scalar keyframes)
```

Group info is attached to each shape: `maxVertexCount` (maximum vertex count across
all keyframes) and `bezierCount` (total number of shape keyframes).

---

## 16. Gradient Data (GCst)

Animated gradient property.

### Structure

```
LIST GCst
  LIST GCky          ← Gradient keyframe collection
    Utf8             ← XML string for gradient 0
    Utf8             ← XML string for gradient 1
    ...
  LIST tdbs          ← Animation timing
```

### Gradient XML Format

Each keyframe's gradient is an XML string using After Effects' property XML format:

```xml
<prop.map>
  <prop.list>
    <prop.pair>
      <key>Gradient Color Data</key>
      <prop.list>
        <prop.pair>
          <key>Color Stops</key>
          <prop.list>
            <prop.pair>
              <key>Stops List</key>
              <prop.list>
                <prop.pair>
                  <key>0</key>
                  <prop.list>
                    <prop.pair>
                      <key>Stops Color</key>
                      <array>
                        <array.type><float/></array.type>
                        <float>0.0</float>      <!-- position (0-1) -->
                        <float>0.5</float>      <!-- midpoint (0-1) -->
                        <float>1.0</float>      <!-- R (0-1) -->
                        <float>0.0</float>      <!-- G (0-1) -->
                        <float>0.0</float>      <!-- B (0-1) -->
                        <float>1.0</float>      <!-- alpha (0-1) -->
                      </array>
                    </prop.pair>
                  </prop.list>
                </prop.pair>
                ...
              </prop.list>
            </prop.pair>
          </prop.list>
        </prop.pair>
        <prop.pair>
          <key>Alpha Stops</key>
          <prop.list>
            <prop.pair>
              <key>Stops List</key>
              <prop.list>
                <prop.pair>
                  <key>0</key>
                  <prop.list>
                    <prop.pair>
                      <key>Stops Alpha</key>
                      <array>
                        <array.type><float/></array.type>
                        <float>0.0</float>      <!-- position -->
                        <float>0.5</float>      <!-- midpoint -->
                        <float>1.0</float>      <!-- alpha value -->
                      </array>
                    </prop.pair>
                  </prop.list>
                </prop.pair>
              </prop.list>
            </prop.pair>
          </prop.list>
        </prop.pair>
      </prop.list>
    </prop.pair>
  </prop.list>
</prop.map>
```

---

## 17. Text Data (btdk / COS Format)

Text documents use the **COS** (Carousel Object System) binary format,
a PDF-like token stream.

### COS Token Types

| Syntax | Type | Example |
|--------|------|---------|
| `123`, `3.14` | Number | Integer or float |
| `(Hello World)` | String | Escaped parenthesized string |
| `<48656C6C6F>` | Hex String | Hex-encoded bytes |
| `/key` | Name | Dictionary key |
| `true`, `false` | Boolean | — |
| `null` | Null | — |
| `<< ... >>` | Dictionary | Key-value pairs |
| `[ ... ]` | Array | Ordered list |
| `% ...` | Comment | To end of line |

### String Escape Sequences

| Sequence | Meaning |
|----------|---------|
| `\\` | Backslash |
| `\(` | Left parenthesis |
| `\)` | Right parenthesis |
| `\n` | Line feed |
| `\r` | Carriage return |
| `\t` | Tab |
| `\NNN` | Octal character code |

Nested parentheses within strings are tracked by depth counter.

### Text Document Structure

The parsed COS object has this hierarchy (using integer string keys):

```
Root dict
├── "0": Font and metadata
│   └── "1"
│       └── "0": Array of font entries
│           └── [i]
│               └── "0"
│                   └── "0"
│                       └── "0": Font family name (string)
│
└── "1": Text documents
    └── "1": Array of document entries
        └── [i]: Single text document
            ├── "0"
            │   ├── "0": Text content (string)
            │   ├── "5"
            │   │   └── "0": Line styles array
            │   │       └── [j]
            │   │           ├── "0"
            │   │           │   └── "0"
            │   │           │       └── "5": Justify data
            │   │           │           └── [0]: Text justify mode
            │   │           └── "1": Character count
            │   └── "6"
            │       └── "0": Character styles array
            │           └── [j]
            │               ├── "0"
            │               │   └── "0"
            │               │       └── "6": Style data
            │               │           ├── [0]:  Font index
            │               │           ├── [1]:  Font size
            │               │           ├── [2]:  Faux bold (bool)
            │               │           ├── [3]:  Faux italic (bool)
            │               │           ├── [4]:  Auto leading (bool)
            │               │           ├── [5]:  Leading
            │               │           ├── [8]:  Tracking
            │               │           ├── [12]: Text transform
            │               │           ├── [13]: Vertical alignment
            │               │           ├── [53]: Fill color [a, r, g, b]
            │               │           ├── [54]: Stroke color [a, r, g, b]
            │               │           ├── [56]: Fill enabled (bool)
            │               │           ├── [57]: Stroke enabled (bool)
            │               │           ├── [58]: Stroke over fill (bool)
            │               │           └── [63]: Stroke width
            │               └── "1": Character count
            └── "1"
                └── "2": Paragraph styles array
                    └── [j]
                        └── "6": Array of paragraph rects
                            └── [k]
                                ├── "0"
                                │   └── "0": Position [x, y]
                                └── "1": Size [?, ?, width, height]
```

### Animated Text Property (btds)

```
LIST btds
  btdk             ← COS binary data (fonts + document styles)
  LIST tdbs        ← Animation keyframes for text values
```

---

## 18. Marker Data (Nmrd)

Composition markers (chapter points, cue marks).

### Named Record (Nmrd)

```
LIST Nmrd
  NmHd             ← Marker header
  Utf8             ← Marker name (optional)
```

### Marker Header (NmHd)

```
Offset  Size  Field           Type      Description
─────────────────────────────────────────────────────
0       3     (reserved)      —         —
3       1     flags           uint8     Marker flags
4       4     (reserved)      —         —
8       4     duration_num    uint32    Duration numerator
12      4     duration_den    uint32    Duration denominator
16      1     label_color     uint8     Label color index
```

**Flags:**

```
bit 1  is_protected    Marker is protected/locked
```

**Duration:** `duration = duration_num / duration_den` (0 for instantaneous markers).

### Animated Markers (mrst)

```
LIST mrst
  LIST mrky        ← Marker data collection
    LIST Nmrd      ← Marker 0
    LIST Nmrd      ← Marker 1
    ...
  LIST tdbs        ← Timing (keyframe times = marker positions)
```

---

## 19. Layer Styles

Layer Styles (Drop Shadow, Inner Glow, Bevel, Stroke, etc.) have special handling.

### Structure

```
ADBE Layer Styles (tdgp)
├── tdsb                        ← Root flags (split=true, visible=true — UNRELIABLE)
├── ADBE Blend Options Group    ← Always present, always "enabled"
├── dropShadow/enabled          ← Drop Shadow toggle + properties
├── innerShadow/enabled         ← Inner Shadow toggle + properties
├── outerGlow/enabled           ← Outer Glow toggle + properties
├── innerGlow/enabled           ← Inner Glow toggle + properties
├── bevelEmboss/enabled         ← Bevel and Emboss toggle + properties
├── chromeFX/enabled            ← Satin toggle + properties
├── solidFill/enabled           ← Color Overlay toggle + properties
├── gradientFill/enabled        ← Gradient Overlay toggle + properties
├── patternFill/enabled         ← Pattern Overlay toggle + properties
└── frameFX/enabled             ← Stroke toggle + properties
```

### Enabled State Detection

The root `tdsb` flag for `ADBE Layer Styles` is **always** `0x00000003`
(`split=true, visible=true`) when the section exists, regardless of whether
any style is actually enabled. This flag is **unreliable**.

**Correct logic:**

1. For each `*/enabled` sub-group:
   - If `split=true` in tdsb: use `bit(3,0)` as the enabled state
   - If `split=false` in tdsb: infer enabled from whether the group has child properties
     (has properties → enabled, empty → disabled)
2. Root enabled = `any(sub_style.enabled for sub_style in */enabled groups)`

### Sub-style Match Names

Layer Styles use **non-ADBE** match names for sub-groups:

| Match Name | AE Layer Style |
|-----------|----------------|
| `dropShadow/enabled` | Drop Shadow |
| `innerShadow/enabled` | Inner Shadow |
| `outerGlow/enabled` | Outer Glow |
| `innerGlow/enabled` | Inner Glow |
| `bevelEmboss/enabled` | Bevel and Emboss |
| `chromeFX/enabled` | Satin |
| `solidFill/enabled` | Color Overlay |
| `gradientFill/enabled` | Gradient Overlay |
| `patternFill/enabled` | Pattern Overlay |
| `frameFX/enabled` | Stroke |

Within each sub-style, property match names use the same prefix:

```
innerShadow/color
innerShadow/opacity
innerShadow/distance
innerShadow/blur
```

---

## 20. AEPX XML Format

AEPX files encode the same chunk tree as XML.

### Root Element

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AfterEffectsProject ...>
  <!-- Child elements represent chunks -->
</AfterEffectsProject>
```

### Chunk → XML Mapping

| AEP (Binary) | AEPX (XML) |
|--------------|------------|
| Chunk header | Element tag name |
| LIST chunk | Element with child elements |
| Binary data | `bdata="hex..."` attribute |
| Utf8 string | `<string>text</string>` child |
| File reference | `<fileReference>` child |

### Example

Binary:
```
LIST Fold
  LIST Item
    idta [binary data]
    Utf8 "My Comp"
```

XML:
```xml
<Fold>
  <Item>
    <idta bdata="0004000000000000000000000000000000000001"/>
    <Utf8>
      <string>My Comp</string>
    </Utf8>
  </Item>
</Fold>
```

### Endianness

AEPX files include a `byteOrder` attribute or can be detected from the XML content.
The parser defaults to big-endian for binary data within `bdata` attributes.

---

## 21. Constants and Enumerations

### Blend Modes

| Value | Mode | Value | Mode |
|-------|------|-------|------|
| 1 | Normal | 17 | Hard Light |
| 3 | Darken | 18 | Linear Light |
| 4 | Multiply | 19 | Vivid Light |
| 5 | Color Burn | 20 | Pin Light |
| 6 | Linear Burn | 21 | Hard Mix |
| 7 | Darker Color | 23 | Difference |
| 9 | Lighten | 24 | Exclusion |
| 10 | Screen | 26 | Hue |
| 11 | Color Dodge | 27 | Saturation |
| 12 | Linear Dodge (Add) | 28 | Color |
| 13 | Lighter Color | 29 | Luminosity |
| 15 | Overlay | | |
| 16 | Soft Light | | |

### Track Matte Modes

| Value | Mode |
|-------|------|
| 0 | None |
| 1 | Alpha Matte |
| 2 | Alpha Inverted Matte |
| 3 | Luma Matte |
| 4 | Luma Inverted Matte |

### Layer Types

| Value | Type |
|-------|------|
| 0 | Asset (footage/solid/precomp) |
| 1 | Light |
| 2 | Camera |
| 3 | Text |
| 4 | Shape |

### Transition Types (Keyframe Interpolation)

| Value | Type |
|-------|------|
| 1 | Linear |
| 2 | Bezier |
| 3 | Hold |

### Bezier Modes

| Value | Mode |
|-------|------|
| 0 | Normal |
| 1 | Continuous |
| 2 | Auto |

### Mask Modes

| Value | Mode |
|-------|------|
| 0 | None |
| 1 | Add |
| 2 | Subtract |
| 3 | Intersect |
| 4 | Darken |
| 5 | Lighten |
| 6 | Difference |

---

## 22. Match Name Reference

Match names (`tdmn` chunks) identify standard After Effects properties. The parser
maps these to human-readable names.

### Transform

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Transform Group` | Transform |
| `ADBE Anchor Point` | Anchor Point |
| `ADBE Position` | Position |
| `ADBE Position_0` | X Position |
| `ADBE Position_1` | Y Position |
| `ADBE Position_2` | Z Position |
| `ADBE Scale` | Scale |
| `ADBE Rotate X` | X Rotation |
| `ADBE Rotate Y` | Y Rotation |
| `ADBE Rotate Z` | Z Rotation |
| `ADBE Rotation` | Rotation |
| `ADBE Opacity` | Opacity |
| `ADBE Orientation` | Orientation |
| `ADBE Skew` | Skew |
| `ADBE Skew Axis` | Skew Axis |

### Shape Layer

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Root Vectors Group` | Contents |
| `ADBE Vector Group` | Group |
| `ADBE Vectors Group` | Contents |
| `ADBE Vector Transform Group` | Transform |
| `ADBE Vector Shape - Rect` | Rectangle |
| `ADBE Vector Rect Position` | Position |
| `ADBE Vector Rect Size` | Size |
| `ADBE Vector Rect Roundness` | Roundness |
| `ADBE Vector Shape - Ellipse` | Ellipse |
| `ADBE Vector Ellipse Position` | Position |
| `ADBE Vector Ellipse Size` | Size |
| `ADBE Vector Shape - Star` | Polystar |
| `ADBE Vector Shape - Group` | Path |
| `ADBE Vector Shape` | Path |
| `ADBE Vector Graphic - Fill` | Fill |
| `ADBE Vector Fill Color` | Color |
| `ADBE Vector Fill Opacity` | Opacity |
| `ADBE Vector Fill Rule` | Fill Rule |
| `ADBE Vector Graphic - Stroke` | Stroke |
| `ADBE Vector Stroke Color` | Color |
| `ADBE Vector Stroke Opacity` | Opacity |
| `ADBE Vector Stroke Width` | Stroke Width |
| `ADBE Vector Stroke Line Cap` | Line Cap |
| `ADBE Vector Stroke Line Join` | Line Join |
| `ADBE Vector Stroke Miter Limit` | Miter Limit |
| `ADBE Vector Stroke Dashes` | Dashes |
| `ADBE Vector Graphic - G-Fill` | Gradient Fill |
| `ADBE Vector Graphic - G-Stroke` | Gradient Stroke |
| `ADBE Vector Grad Start Pt` | Start Point |
| `ADBE Vector Grad End Pt` | End Point |
| `ADBE Vector Grad Colors` | Colors |
| `ADBE Vector Grad Type` | Type |
| `ADBE Vector Filter - Trim` | Trim Paths |
| `ADBE Vector Trim Start` | Start |
| `ADBE Vector Trim End` | End |
| `ADBE Vector Trim Offset` | Offset |
| `ADBE Vector Filter - Merge` | Merge Paths |
| `ADBE Vector Filter - Offset` | Offset Paths |
| `ADBE Vector Filter - PB` | Pucker & Bloat |
| `ADBE Vector Filter - Repeater` | Repeater |
| `ADBE Vector Repeater Copies` | Copies |
| `ADBE Vector Repeater Offset` | Offset |
| `ADBE Vector Repeater Transform` | Transform |
| `ADBE Vector Filter - RC` | Round Corners |
| `ADBE Vector RoundCorner Radius` | Radius |
| `ADBE Vector Filter - Twist` | Twist |
| `ADBE Vector Filter - Zigzag` | Zig Zag |
| `ADBE Vector Blend Mode` | Blend Mode |
| `ADBE Vector Group Opacity` | Opacity |

### Effects & Masks

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Effect Parade` | Effects |
| `ADBE Mask Parade` | Masks |
| `ADBE Mask Atom` | Mask |
| `ADBE Mask Shape` | Mask Path |
| `ADBE Mask Feather` | Mask Feather |
| `ADBE Mask Opacity` | Mask Opacity |
| `ADBE Mask Offset` | Mask Expansion |

### Text

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Text Properties` | Text |
| `ADBE Text Document` | Source Text |
| `ADBE Text Animators` | Animators |
| `ADBE Text Animator` | Animator |
| `ADBE Text Selectors` | Selectors |
| `ADBE Text Selector` | Range Selector |
| `ADBE Text Percent Start` | Start |
| `ADBE Text Percent End` | End |
| `ADBE Text Animator Properties` | Properties |
| `ADBE Text Path Options` | Path Options |
| `ADBE Text More Options` | More Options |

### Other

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Time Remapping` | Time Remap |
| `ADBE Layer Styles` | Layer Styles |
| `ADBE Marker` | Markers |
| `ADBE Camera Options Group` | Camera Options |
| `ADBE Camera Aperture` | Aperture |
| `ADBE Camera Zoom` | Zoom |

### Common Effects

| Match Name | Display Name |
|-----------|-------------|
| `ADBE Gaussian Blur 2` | Gaussian Blur |
| `ADBE Drop Shadow` | Drop Shadow |
| `ADBE Fill` | Fill |
| `ADBE Stroke` | Stroke |
| `ADBE Tint` | Tint |
| `ADBE Tritone` | Tritone |
| `ADBE Pro Levels2` | Levels |
| `ADBE Displacement Map` | Displacement Map |
| `ADBE Set Matte3` | Set Matte |
| `ADBE Twirl` | Twirl |
| `ADBE Spherize` | Spherize |
| `ADBE Radial Wipe` | Radial Wipe |

---

## 23. Write-Back / RIFF Serialization

This section documents how modified chunk trees are serialized back to valid `.aep` binary files.

### Overview

The write-back process operates on the in-memory chunk tree: values are modified by patching individual chunk data, then the entire tree is re-serialized. **Chunk sizes are recalculated during serialization** — the original `chunk.length` is not trusted for container chunks.

### Serialization by Chunk Type

#### Root Chunk (RIFX/RIFF)

```
[magic 4B] [size 4B] [file_type 4B "Egg!"] [children...]
```

- `magic`: preserved from parse (`"RIFX"` or `"RIFF"`)
- `size`: **recalculated** as `4 (file_type) + total children bytes`
- Written as a placeholder `0x00000000`, then patched after all children are written

#### LIST Chunks

```
"LIST" [size 4B] [list_type 4B] [children...]
```

- `size`: **recalculated** as `4 (list_type) + total children bytes`
- Same placeholder-then-patch approach as root

#### Non-LIST Container Chunks (tdsn, fnam, pdnm)

```
[header 4B] [size 4B] [children...]
```

- These have `ChunkList` data with `type=""` — **no type prefix** written (unlike LIST which writes a 4-byte type)
- `size`: recalculated from children

#### String Chunks (Utf8, alas, tdmn, wsnm)

```
[header 4B] [size 4B] [encoded_bytes...]
```

- `Utf8` / `alas`: UTF-8 encoded
- `wsnm`: UTF-16-LE encoded
- `tdmn`: UTF-8 + null terminator, **padded to original `chunk.length`** (typically 32 bytes) with zero bytes. This preserves fixed-size alignment expected by AE.
- `size`: length of the encoded byte string (after padding for tdmn)

#### Raw Binary Chunks (idta, cdta, ldta, tdb4, etc.)

```
[header 4B] [size 4B] [data...]
```

- `size`: `len(data)` — uses the current byte length of `chunk.data`
- Data written as-is

#### Special Case: btdk (Text Data)

The parser stores `btdk` chunks with `header="btdk"` and `data=bytes`, but in the binary format btdk is actually a LIST subtype:

```
"LIST" [size 4B] "btdk" [data...]
```

- `size`: `4 (type "btdk") + len(data)`
- The serializer detects `header == "btdk"` and wraps it in a LIST envelope

### 2-Byte Alignment

All chunks are aligned to 2-byte boundaries. If a chunk's data size is odd, **1 padding byte** (`0x00`) is appended after the data. This padding byte is **not** included in the chunk's `size` field.

```
[header 4B] [size 4B] [data (size bytes)] [0x00 if size is odd]
```

### Size Recalculation Formula

For container chunks (root, LIST, non-LIST containers), the total child byte count is:

```
child_bytes = sum(
    8 + child.data_size + (child.data_size % 2)    # header(4) + size(4) + data + padding
    for child in children
)
```

Container `size` field:
- **LIST**: `4 (list_type) + child_bytes`
- **Non-LIST container** (tdsn, fnam, pdnm): `child_bytes` (no type prefix)
- **Root** (RIFX/RIFF): `4 (file_type) + child_bytes`

### XMP Trailing Data

AEP files may have XMP metadata appended **after** the RIFF container boundary (`offset 8 + file_size`). This data is not part of the chunk tree.

During save, the trailing data is preserved by:
1. On load: store bytes beyond `8 + file_size` as `trailing_data`
2. On save: `write(serialized_chunks + trailing_data)`

### Modifying Layer Names

1. Navigate to `Fold → Item (comp_id) → Layr (layer_id)`
2. Find the `Utf8` chunk in the `Layr` LIST
3. Replace `chunk.data` with the new name string
4. If no `Utf8` exists, create one and insert after `ldta`
5. Chunk sizes are recalculated automatically on serialization

### Modifying Property Values (cdat In-Place Patching)

1. Navigate to `Layr → tdgp → [match_name_path] → tdbs → cdat`
2. Read the first `components` float64 values (the actual property value)
3. Overwrite only those bytes, **preserving the remaining tangent/velocity data**

```
cdat layout (non-spatial, e.g. Opacity):
[value × N] [ease_in × N] [ease_out × N] [influence_in × N] [influence_out × N]
 ↑ patch     ↑ preserve...

cdat layout (spatial, e.g. Position):
[value × N] [spatial_in × N] [spatial_out × N] [temporal × 3]
 ↑ patch     ↑ preserve...
```

The `cdat.data` size is **not changed** — only the value portion at the start is overwritten.

### Creating Missing Property Chunks

When a Transform property (Anchor Point, Position, Scale, Rotation, Opacity) has no chunk in the binary (AE omits unmodified defaults), a new `tdbs` subtree is created from templates:

```
LIST tdbs
├── tdsb    4B    flags = 0x00000001 (visible)
├── tdsn    LIST  display name placeholder "-_0_/-"
├── tdb4    124B  property metadata (from template)
├── cdat    var   value + zero tangents
├── tdum    8B    float64 minimum bound
└── tduM    8B    float64 maximum bound
```

**Template tdb4 selection** by match name:

| Match Name | Components | Spatial | cdat float64 count |
|---|---|---|---|
| `ADBE Opacity` | 1 | No | 1×5 = 5 (40 bytes) |
| `ADBE Rotate Z` | 1 | No | 1×5 = 5 (40 bytes) |
| `ADBE Scale` | 3 | No | 3×5 = 15 (120 bytes) |
| `ADBE Anchor Point` | 2 | Yes | 2×3+3 = 9 (72 bytes) |
| `ADBE Position` | 2 | Yes | 2×3+3 = 9 (72 bytes) |

**Insertion**: the new `tdmn` + `LIST tdbs` pair is inserted into the parent `tdgp` before the `"ADBE Group End"` tdmn sentinel.

**tdmn padding**: new tdmn chunks are null-terminated and padded to 32 bytes with `0x00`.

### Modifying Keyframe Values (ldat In-Place Patching)

1. Navigate to `tdbs → list → lhd3 + ldat`
2. Read `count` and `item_size` from `lhd3` (offsets 10 and 18)
3. Calculate value offset within each keyframe record:
   - Common header: 8 bytes `[1B skip][4B time][1B transition][1B label][1B flags]`
   - Spatial properties: +16 bytes skip, then `components × 8` bytes for values
   - Non-spatial multi-dim: values start at offset 8
4. Patch: `ldat[idx × item_size + value_offset : +packed_size]`

### Modifying Keyframe Time (ldat In-Place Patching)

1. Navigate to the property's `ldat` (same as value patching above)
2. Read `time_scale` from `tdb4` at offset 11 (uint32)
3. Compute: `time_raw = round(new_time_seconds × time_scale)`
4. Patch 4 bytes (signed int32) at offset `idx × item_size + 1` (after 1 skip byte)

### Modifying Keyframe Interpolation (ldat In-Place Patching)

1. Navigate to the property's `ldat`
2. Patch 1 byte at offset `idx × item_size + 5` (after 1 skip + 4 time bytes)
3. Values: `1` = linear, `2` = bezier, `3` = hold

**Note:** This byte controls the **outgoing** interpolation. To change a keyframe's incoming interpolation, modify the **previous** keyframe's transition byte.

### Modifying Keyframe Temporal Ease (ldat In-Place Patching)

Ease data layout depends on property type:

**Scalar / Spatial (components=1 or is_spatial):**
```
Record: [8B header][16B skip][in_speed f64][in_influence f64][out_speed f64][out_influence f64]
                              ↑ ease starts at offset 24
```

**Multi-dimensional (components > 1, non-spatial):**
```
Record: [8B header][value: C×8B][in_speed: C×8B][in_influence: C×8B][out_speed: C×8B][out_influence: C×8B]
                                 ↑ ease starts after value block
```

Where `C` = number of components (e.g. 2 for 2D position, 3 for scale).

### Modifying Asset File Paths (alas JSON Patching)

Footage asset file paths are stored in JSON within the `alas` chunk:

1. Navigate to `Fold → Item (asset_id) → Pin  → Als2 → alas`
2. Parse the `alas` data as UTF-8 JSON
3. Update the `"fullpath"` key
4. Re-serialize JSON and replace `alas.data`

Item lookup traverses the folder hierarchy recursively, matching by `idta` item ID (offset 16, uint32).

### Endianness

All multi-byte integers and floats follow the file's byte order:
- `RIFX` → big-endian (`>`)
- `RIFF` → little-endian (`<`)

The `big_endian` flag determined at parse time is threaded through all serialization functions.
