# AEP Parser

Parse After Effects project files (`.aep` binary / `.aepx` XML) into structured JSON.

## Features

- Full RIFF/RIFX binary `.aep` parser (big-endian & little-endian)
- XML `.aepx` parser
- Rust-accelerated RIFF parsing (~15x faster than pure Python)
- Extracts: compositions, layers, properties, keyframes, effects, masks, text, markers, render queue
- **Write-back**: modify and save back to `.aep`:
  - Layer names, composition names
  - Property static values (position, scale, opacity, etc.)
  - Keyframe values, times, interpolation types, and temporal ease
  - Footage asset file paths
- AE scripting-style API (`aep_tools`) with 1-based indexing
- PySide6 GUI viewer/editor with AE-like dark theme
- CLI tool for batch processing

## Installation

Requires Python >= 3.10 and Rust toolchain (for building the native extension).

```bash
# Build and install (includes Rust extension)
pip install maturin
maturin build --release
pip install target/wheels/aep_parser-*.whl

# With GUI support
pip install "target/wheels/aep_parser-*.whl[gui]"
```

### Development

```bash
# Editable install (recompiles Rust on install)
maturin develop --release

# Run tests
pytest
```

## Usage

### Python API (aep_tools)

```python
from aep_tools import Project

proj = Project.open("input.aep")
print(proj.ae_version)          # "25.6"

comp = proj.comp("Main Comp")
layer = comp.layer(1)
print(layer.position.value)     # [960, 540]
print(layer.opacity.value)      # 1.0

# Modify via property setters
layer.position.value = [500.0, 300.0]
layer.position.set_value_at_key(1, [0.0, 0.0])
comp.name = "Renamed Comp"

# Change footage path
footage = proj.item(3)
footage.file = "/new/path/to/file.mov"

proj.save("output.aep")
```

See [docs/api.md](docs/api.md) for full API reference (read/write annotations, keyframe editing, interpolation, etc.).

### Low-level Parser API (aep_parser)

```python
from aep_parser import parse_aep, parse_aepx

# Binary .aep
project = parse_aep(open("input.aep", "rb").read())

# XML .aepx
project = parse_aepx(open("input.aepx").read())

# Access structured data
for comp in project.compositions:
    print(f"{comp.name}: {comp.width}x{comp.height} @ {comp.framerate}fps")
    for layer in comp.layers:
        print(f"  Layer: {layer.name} ({layer.in_time:.2f}s - {layer.out_time:.2f}s)")

# Export to dict/JSON
import json
print(json.dumps(project.to_dict(), indent=2, ensure_ascii=False))
```

### CLI

```bash
aep-parser input.aep                  # Print JSON to stdout
aep-parser input.aep -o output.json   # Write to file
aep-parser input.aep --compact        # Compact output
aep-parser input.aep --comp "Main"    # Filter by composition name
python -m aep_parser input.aep        # Run as module
```

### GUI

```bash
aep-viewer                # Launch viewer
aep-viewer input.aep      # Open file directly
python -m aep_parser.gui  # Run as module
```

GUI features:
- Dark theme mimicking After Effects
- Project panel with folder structure, footage paths, compositions
- Layer tree with properties, keyframes (expandable with time/type/value/ease)
- Right-click editing: layer names, property values, keyframe values/time/interpolation/ease, footage paths
- Save modified `.aep` files

## Project Structure

```
aep-parser/
+-- Cargo.toml                    # Rust crate (PyO3 RIFF parser)
+-- pyproject.toml                # maturin build system
+-- rust/
|   +-- lib.rs                    # Rust RIFF parser -> aep_parser._core
+-- python/
|   +-- aep_parser/               # Low-level parser
|   |   +-- __init__.py           # Public API: parse_aep(), parse_aepx()
|   |   +-- __main__.py           # CLI: python -m aep_parser
|   |   +-- _core.pyi             # Type stubs for Rust extension
|   |   +-- models.py             # Data models (Project, Composition, Layer, ...)
|   |   +-- _parser/              # Internal parsing modules
|   |   |   +-- project.py        # Chunk tree -> Project model
|   |   |   +-- riff.py           # Pure Python RIFF parser (fallback)
|   |   |   +-- aepx.py           # XML AEPX -> chunk tree
|   |   |   +-- binary_reader.py  # Low-level binary reader
|   |   |   +-- chunk.py          # Chunk/ChunkList types
|   |   |   +-- cos.py            # COS text format parser
|   |   +-- gui/                  # GUI viewer/editor (optional, needs PySide6)
|   |       +-- __init__.py       # Entry: python -m aep_parser.gui
|   |       +-- app.py            # MainWindow
|   |       +-- widgets.py        # CompWidget, ProjectPanel
|   |       +-- theme.py          # Colors, styles, ADBE names
|   +-- aep_tools/                # High-level scripting API
|       +-- __init__.py           # Public API: Project, open_aep, open_aepx
|       +-- _project.py           # Project wrapper (items, comps, version, save)
|       +-- _comp.py              # CompItem, LayerCollection
|       +-- _layer.py             # Layer, AVLayer, TextLayer, ShapeLayer, ...
|       +-- _property.py          # Property, PropertyGroup, KeyframeValue, ...
|       +-- _effect.py            # Effect wrapper
|       +-- _mask.py              # Mask wrapper
|       +-- _constants.py         # Enums, match name maps
|       +-- _writer.py            # Binary write-back (RIFX serializer)
+-- tests/
|   +-- test_parser.py            # Parser tests (16)
|   +-- test_tools.py             # aep_tools API tests (83)
|   +-- test_writer.py            # Writer tests (28)
+-- docs/
    +-- api.md                    # aep_tools API reference (English)
    +-- api-zh.md                 # aep_tools API reference (Chinese)
    +-- aep-format.md             # AEP format specification (English)
    +-- aep-format-zh.md          # AEP format specification (Chinese)
```

## Architecture

```
.aep (binary)  -->  Rust _core (fast)  -->  Chunk tree  -->  ProjectParser  -->  Project
                     or Python riff_parser (fallback)

.aepx (XML)    -->  Python aepx_parser -->  Chunk tree  -->  ProjectParser  -->  Project
```

The Rust extension (`_core`) accelerates RIFF binary parsing by ~15x. If not available, the pure Python parser is used as fallback. Both produce the same Chunk/ChunkList tree that `ProjectParser` consumes.

## Documentation

- [API Reference](docs/api.md) — `aep_tools` classes, properties (R/W annotations), methods
- [API 参考文档](docs/api-zh.md) — 同上，中文版
- [AEP Format Spec (EN)](docs/aep-format.md) — Binary format reverse-engineering documentation
- [AEP Format Spec (ZH)](docs/aep-format-zh.md) — Same in Chinese
