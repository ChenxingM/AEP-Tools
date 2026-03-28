"""Layer CRUD operations — add, remove, duplicate, move layers in compositions."""

from __future__ import annotations

import struct
from pathlib import Path

from aep_parser._parser.chunk import Chunk, ChunkList

from ._common import _is_chunk_list
from ._navigate import find_comp_chunklist

# ── Constants ────────────────────────────────────────────────────────────────

_LAYER_BLOCK_SIZE = 16  # Layr + Ewst + 14 view state chunks
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "tests" / "layers"

# Default view state chunk values
_FVDV = b"\x00\x00\x00\x03"
_FIOP = b"\x00"
_FTTS = b"\x00\x00\x00\x00"
_FOAC = b"\x00"
_FIAC = b"\x00"
_FIPC = b"\x00\x00"
_FIFL = b"\x00\x00\x00\x00"

# Cached template data (loaded on first use)
_template_cache: dict | None = None


def _load_templates() -> dict:
    """Load and parse template AEP files, caching all reusable chunks."""
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    from aep_parser._parser.riff import AepChunkParser

    # ── black_solid_one.aep: solid layer + Solids folder templates ──
    path = _TEMPLATE_DIR / "black_solid_one.aep"
    with open(path, "rb") as f:
        data = f.read()
    parser = AepChunkParser(data, 0, True)
    root = parser.parse()
    fold = root.data.find("Fold")

    comp_item = _find_first_comp(fold)
    layr, layr_idx = _find_first_layr(comp_item)
    view_state_chunks = comp_item.data.children[layr_idx + 1:layr_idx + _LAYER_BLOCK_SIZE]

    solids_item = _find_solids_folder(fold)
    sfdr = solids_item.data.find("Sfdr")
    footage_item, footage_view = _extract_footage_from_sfdr(sfdr)

    # ── all_layers.aep: templates for each layer type ──
    path2 = _TEMPLATE_DIR / "all_layers.aep"
    with open(path2, "rb") as f:
        data2 = f.read()
    parser2 = AepChunkParser(data2, 0, True)
    root2 = parser2.parse()
    fold2 = root2.data.find("Fold")

    comp2 = _find_comp_by_name(fold2, "Comp 1")
    layer_templates = _extract_layer_templates(comp2)

    _template_cache = {
        "layr": layr,
        "view_state": view_state_chunks,
        "solids_folder": solids_item,
        "footage_item": footage_item,
        "footage_view": footage_view,
        **layer_templates,
    }
    return _template_cache


def _find_first_comp(fold: Chunk) -> Chunk:
    for c in fold.data.children:
        if c.name == "Item":
            idta = c.data.find_optional("idta")
            if idta and isinstance(idta.data, bytes) and len(idta.data) >= 2:
                if struct.unpack(">H", idta.data[0:2])[0] == 4:
                    return c
    raise ValueError("No composition found")


def _find_comp_by_name(fold: Chunk, name: str) -> Chunk:
    for c in fold.data.children:
        if c.name == "Item":
            idta = c.data.find_optional("idta")
            if idta and isinstance(idta.data, bytes) and len(idta.data) >= 2:
                if struct.unpack(">H", idta.data[0:2])[0] == 4:
                    utf8 = c.data.find_optional("Utf8")
                    if utf8 and isinstance(utf8.data, str) and utf8.data == name:
                        return c
    raise ValueError(f"Composition '{name}' not found")


def _find_first_layr(comp: Chunk) -> tuple[Chunk, int]:
    for i, c in enumerate(comp.data.children):
        if c.name == "Layr":
            return c, i
    raise ValueError("No Layr found")


def _find_solids_folder(fold: Chunk) -> Chunk:
    for c in fold.data.children:
        if c.name == "Item":
            utf8 = c.data.find_optional("Utf8")
            if utf8 and isinstance(utf8.data, str) and utf8.data == "Solids":
                return c
    raise ValueError("No Solids folder found")


def _extract_footage_from_sfdr(sfdr: Chunk) -> tuple[Chunk, list[Chunk]]:
    for i, c in enumerate(sfdr.data.children):
        if c.name == "Item":
            view = [ch for ch in sfdr.data.children[i + 1:]
                    if ch.header != "LIST"]
            return c, view
    raise ValueError("No footage Item in Sfdr")


def _extract_layer_templates(comp: Chunk) -> dict:
    """Extract typed layer templates from all_layers.aep Comp 1."""
    templates = {}
    for c in comp.data.children:
        if c.name != "Layr":
            continue
        ldta = c.data.find("ldta").data
        utf8 = c.data.find("Utf8")
        name = utf8.data if isinstance(utf8.data, str) else ""
        asset_id = struct.unpack(">I", ldta[40:44])[0]
        flags = ldta[36:40]
        is_null = bool(flags[2] & (1 << 7))
        is_adjustment = bool(flags[2] & (1 << 1))

        # Identify by name (Chinese names from the test file)
        tdgp = c.data.find("tdgp")
        has_tdmn = lambda mn: any(
            tc.header == "tdmn" and isinstance(tc.data, str) and tc.data == mn
            for tc in tdgp.data.children
        )

        if has_tdmn("ADBE Light Options Group"):
            templates["layr_light"] = c
        elif has_tdmn("ADBE Camera Options Group"):
            templates["layr_camera"] = c
        elif has_tdmn("ADBE Root Vectors Group"):
            templates["layr_shape"] = c
        elif has_tdmn("ADBE Text Properties"):
            templates["layr_text"] = c
        elif is_null:
            templates["layr_null"] = c
        elif is_adjustment:
            templates["layr_adjustment"] = c
        elif asset_id != 0 and asset_id != 0xFFFFFFFF and not is_null:
            # Precomp or normal solid — check if asset is a comp
            if "layr_precomp" not in templates:
                # First non-special solid-like layer with an asset reference
                # In all_layers.aep, 预合成图层 comes first
                templates["layr_precomp"] = c

    return templates


# ── Deep Copy ────────────────────────────────────────────────────────────────

def _deep_copy_chunk(chunk: Chunk) -> Chunk:
    """Recursively deep-copy a chunk tree."""
    if _is_chunk_list(chunk.data):
        new_children = [_deep_copy_chunk(c) for c in chunk.data.children]
        new_cl = ChunkList(chunk.data.type, new_children)
        return Chunk(chunk.header, chunk.length, new_cl)
    elif isinstance(chunk.data, (bytes, bytearray)):
        return Chunk(chunk.header, chunk.length, bytes(chunk.data))
    elif isinstance(chunk.data, str):
        return Chunk(chunk.header, chunk.length, chunk.data)
    else:
        import copy
        return copy.deepcopy(chunk)


# ── ID / Navigation Helpers ──────────────────────────────────────────────────

def _scan_max_id(chunk: Chunk) -> int:
    """Scan all idta and ldta chunks to find the maximum ID."""
    max_id = 0
    if isinstance(chunk.data, (bytes, bytearray)):
        if chunk.header == "idta" and len(chunk.data) >= 20:
            max_id = struct.unpack(">I", chunk.data[16:20])[0]
        elif chunk.header == "ldta" and len(chunk.data) >= 4:
            max_id = struct.unpack(">I", chunk.data[0:4])[0]
    elif _is_chunk_list(chunk.data):
        for child in chunk.data.children:
            max_id = max(max_id, _scan_max_id(child))
    return max_id


def _find_dlay_index(comp_cl: ChunkList) -> int:
    """Find the index of the first DLay chunk."""
    for i, c in enumerate(comp_cl.children):
        if c.name == "DLay":
            return i
    raise ValueError("No DLay found in composition")


def _find_layer_block_start(comp_cl: ChunkList, layer_id: int) -> int | None:
    """Find the start index of a layer's 16-chunk block."""
    for i, c in enumerate(comp_cl.children):
        if c.name == "Layr":
            ldta = c.data.find_optional("ldta")
            if ldta and isinstance(ldta.data, (bytes, bytearray)) and len(ldta.data) >= 4:
                if struct.unpack(">I", ldta.data[0:4])[0] == layer_id:
                    return i
    return None


def _count_user_layers(comp_cl: ChunkList) -> int:
    """Count user Layr chunks before DLay."""
    count = 0
    for c in comp_cl.children:
        if c.name == "DLay":
            break
        if c.name == "Layr":
            count += 1
    return count


def _layer_insert_point(comp_cl: ChunkList, index: int | None) -> int:
    """Calculate the children list index to insert a new layer block."""
    dlay_idx = _find_dlay_index(comp_cl)

    # Find where user layers start
    first_layr_idx = dlay_idx
    for i, c in enumerate(comp_cl.children):
        if c.name == "Layr":
            first_layr_idx = i
            break

    if index is None or index <= 1:
        return first_layr_idx  # top

    num_layers = _count_user_layers(comp_cl)
    target = min(index, num_layers + 1)
    return first_layr_idx + (target - 1) * _LAYER_BLOCK_SIZE


# ── Chunk Modification Helpers ───────────────────────────────────────────────

def _build_view_state_block_simple() -> list[Chunk]:
    """Build 7 simple view state chunks (used at Fold level after comp Items)."""
    return [
        Chunk("fvdv", 4, _FVDV),
        Chunk("fiop", 1, _FIOP),
        Chunk("ftts", 4, _FTTS),
        Chunk("foac", 1, _FOAC),
        Chunk("fiac", 1, _FIAC),
        Chunk("fipc", 2, _FIPC),
        Chunk("fifl", 4, _FIFL),
    ]


def _set_chunk_id(chunk: Chunk, field: str, new_id: int) -> None:
    """Set an ID in a binary chunk's data."""
    if not isinstance(chunk.data, (bytes, bytearray)):
        return
    data = bytearray(chunk.data)
    if field == "idta_id" and len(data) >= 20:
        struct.pack_into(">I", data, 16, new_id)
    elif field == "iide" and len(data) >= 4:
        struct.pack_into("<I", data, 0, new_id)  # iide is always little-endian
    elif field == "ldta_layer_id" and len(data) >= 4:
        struct.pack_into(">I", data, 0, new_id)
    elif field == "ldta_asset_id" and len(data) >= 44:
        struct.pack_into(">I", data, 40, new_id)
    elif field == "ewin_layer_id" and len(data) >= 24:
        struct.pack_into(">I", data, 20, new_id)
    chunk.data = bytes(data)


def _set_ldta_times(ldta_chunk: Chunk, duration_num: int, duration_den: int) -> None:
    """Set layer time fields to match composition duration."""
    data = bytearray(ldta_chunk.data)
    # start_time = 0
    struct.pack_into(">i", data, 12, 0)
    struct.pack_into(">I", data, 16, duration_den)
    # in_time = 0
    struct.pack_into(">i", data, 20, 0)
    struct.pack_into(">I", data, 24, duration_den)
    # out_time = duration
    struct.pack_into(">i", data, 28, duration_num)
    struct.pack_into(">I", data, 32, duration_den)
    ldta_chunk.data = bytes(data)


def _set_opti_color_name(opti_chunk: Chunk, name: str,
                         r: float, g: float, b: float) -> None:
    """Set solid color and name in opti chunk."""
    data = bytearray(opti_chunk.data)
    struct.pack_into(">f", data, 14, r)
    struct.pack_into(">f", data, 18, g)
    struct.pack_into(">f", data, 22, b)
    # Name at offset 26 (NUL-terminated, 256 bytes max)
    name_bytes = name.encode("utf-8")[:255]
    data[26:282] = b"\x00" * 256
    data[26:26 + len(name_bytes)] = name_bytes
    opti_chunk.data = bytes(data)


def _set_sspc_dimensions(sspc_chunk: Chunk, width: int, height: int) -> None:
    """Set dimensions in sspc chunk."""
    data = bytearray(sspc_chunk.data)
    struct.pack_into(">H", data, 32, width)
    struct.pack_into(">H", data, 36, height)
    sspc_chunk.data = bytes(data)


def _read_comp_duration(comp_cl: ChunkList) -> tuple[int, int]:
    """Read duration rational (num, den) from cdta chunk."""
    cdta = comp_cl.find_optional("cdta")
    if cdta and isinstance(cdta.data, (bytes, bytearray)) and len(cdta.data) >= 52:
        dur_num = struct.unpack(">i", cdta.data[44:48])[0]
        dur_den = struct.unpack(">I", cdta.data[48:52])[0]
        return dur_num, dur_den
    return 61440, 24576  # default 2.5s


# ── Solids Folder ────────────────────────────────────────────────────────────

def _ensure_solids_folder(root: Chunk, next_id: int) -> tuple[ChunkList, int]:
    """Find or create the Solids folder. Returns (Sfdr ChunkList, next_id)."""
    fold = root.list.find("Fold")

    for child in fold.list.children:
        if child.name == "Item":
            utf8 = child.list.find_optional("Utf8")
            if utf8 and isinstance(utf8.data, str) and utf8.data == "Solids":
                sfdr = child.list.find_optional("Sfdr")
                if sfdr:
                    return sfdr.list, next_id

    # Create from template
    templates = _load_templates()
    solids = _deep_copy_chunk(templates["solids_folder"])

    # Update folder ID
    folder_id = next_id
    next_id += 1
    _set_chunk_id(solids.data.find("iide"), "iide", folder_id)
    _set_chunk_id(solids.data.find("idta"), "idta_id", folder_id)

    # Clear the Sfdr (remove template footage item + view state)
    sfdr = solids.data.find("Sfdr")
    sfdr.data.children.clear()

    fold.list.children.append(solids)
    return sfdr.list, next_id


# ── Public API ───────────────────────────────────────────────────────────────

def add_solid_layer(root: Chunk, comp_id: int, name: str,
                    width: int, height: int,
                    r: float, g: float, b: float,
                    big_endian: bool,
                    index: int | None = None) -> int:
    """Add a solid layer to a composition. Returns the new layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    templates = _load_templates()
    duration_num, duration_den = _read_comp_duration(comp_cl)
    next_id = _scan_max_id(root) + 1

    # ── Create solid asset ──
    sfdr_cl, next_id = _ensure_solids_folder(root, next_id)
    asset_id = next_id
    next_id += 1

    # Deep copy footage item from template
    footage = _deep_copy_chunk(templates["footage_item"])
    _set_chunk_id(footage.data.find("iide"), "iide", asset_id)
    _set_chunk_id(footage.data.find("idta"), "idta_id", asset_id)

    # Update sspc dimensions and opti color/name
    pin = footage.data.find("Pin ")
    _set_sspc_dimensions(pin.data.find("sspc"), width, height)
    _set_opti_color_name(pin.data.find("opti"), name, r, g, b)

    # Add footage + view state to Sfdr
    sfdr_cl.children.append(footage)
    for vc in templates["footage_view"]:
        sfdr_cl.children.append(_deep_copy_chunk(vc))

    # ── Create layer ──
    layer_id = next_id

    # Deep copy Layr from template
    layr = _deep_copy_chunk(templates["layr"])
    ldta = layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", layer_id)
    _set_chunk_id(ldta, "ldta_asset_id", asset_id)
    _set_ldta_times(ldta, duration_num, duration_den)

    # Set layer name
    utf8 = layr.data.find("Utf8")
    utf8.data = name
    utf8.length = len(name.encode("utf-8"))

    # Build view state from template
    view_state = [_deep_copy_chunk(c) for c in templates["view_state"]]
    # Update ewin layer_id
    ewst = view_state[0]  # First chunk is Ewst
    ewin = ewst.data.find("ewin")
    _set_chunk_id(ewin, "ewin_layer_id", layer_id)

    # Assemble 16-chunk block
    block = [layr] + view_state

    # Insert into comp
    insert_at = _layer_insert_point(comp_cl, index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return layer_id


def _add_layer_from_template(root: Chunk, comp_id: int, template_key: str,
                             name: str, big_endian: bool,
                             asset_id: int = 0, ldta_flags: dict | None = None,
                             index: int | None = None) -> int:
    """Generic helper: add a layer from a named template. Returns layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    templates = _load_templates()
    duration_num, duration_den = _read_comp_duration(comp_cl)
    layer_id = _scan_max_id(root) + 1

    layr = _deep_copy_chunk(templates[template_key])
    ldta = layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", layer_id)

    # Set asset_id
    data = bytearray(ldta.data)
    struct.pack_into(">I", data, 40, asset_id)
    ldta.data = bytes(data)

    _set_ldta_times(ldta, duration_num, duration_den)

    # Apply custom flags
    if ldta_flags:
        data = bytearray(ldta.data)
        for offset, value in ldta_flags.items():
            data[offset] = value
        ldta.data = bytes(data)

    # Set name
    utf8 = layr.data.find("Utf8")
    utf8.data = name
    utf8.length = len(name.encode("utf-8"))

    # Build view state
    view_state = [_deep_copy_chunk(c) for c in templates["view_state"]]
    ewst = view_state[0]
    ewin = ewst.data.find("ewin")
    _set_chunk_id(ewin, "ewin_layer_id", layer_id)

    block = [layr] + view_state
    insert_at = _layer_insert_point(comp_cl, index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return layer_id


def _create_solid_asset(root: Chunk, name: str, width: int, height: int,
                        r: float, g: float, b: float,
                        big_endian: bool) -> tuple[int, int]:
    """Create a solid footage asset. Returns (asset_id, updated next_id)."""
    templates = _load_templates()
    next_id = _scan_max_id(root) + 1
    sfdr_cl, next_id = _ensure_solids_folder(root, next_id)
    asset_id = next_id
    next_id += 1

    footage = _deep_copy_chunk(templates["footage_item"])
    _set_chunk_id(footage.data.find("iide"), "iide", asset_id)
    _set_chunk_id(footage.data.find("idta"), "idta_id", asset_id)
    pin = footage.data.find("Pin ")
    _set_sspc_dimensions(pin.data.find("sspc"), width, height)
    _set_opti_color_name(pin.data.find("opti"), name, r, g, b)
    sfdr_cl.children.append(footage)
    for vc in templates["footage_view"]:
        sfdr_cl.children.append(_deep_copy_chunk(vc))
    return asset_id, next_id


def add_null_layer(root: Chunk, comp_id: int, name: str = "Null 1",
                   big_endian: bool = True,
                   index: int | None = None) -> int:
    """Add a null object layer. Returns layer_id."""
    asset_id, _ = _create_solid_asset(root, name, 100, 100, 0.0, 0.0, 0.0, big_endian)
    return _add_layer_from_template(
        root, comp_id, "layr_null", name, big_endian,
        asset_id=asset_id, index=index)


def add_adjustment_layer(root: Chunk, comp_id: int, name: str = "Adjustment Layer",
                         width: int | None = None, height: int | None = None,
                         big_endian: bool = True,
                         index: int | None = None) -> int:
    """Add an adjustment layer. Returns layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")
    cdta = comp_cl.find_optional("cdta")
    if cdta and isinstance(cdta.data, (bytes, bytearray)):
        cw = struct.unpack(">H", cdta.data[140:142])[0]
        ch = struct.unpack(">H", cdta.data[142:144])[0]
    else:
        cw, ch = 1920, 1080
    w = width if width is not None else cw
    h = height if height is not None else ch

    asset_id, _ = _create_solid_asset(root, name, w, h, 0.0, 0.0, 0.0, big_endian)
    return _add_layer_from_template(
        root, comp_id, "layr_adjustment", name, big_endian,
        asset_id=asset_id, index=index)


def add_shape_layer(root: Chunk, comp_id: int, name: str = "Shape Layer",
                    big_endian: bool = True,
                    index: int | None = None) -> int:
    """Add an empty shape layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_shape", name, big_endian,
        asset_id=0, index=index)


def add_text_layer(root: Chunk, comp_id: int, name: str = "Text Layer",
                   big_endian: bool = True,
                   index: int | None = None) -> int:
    """Add a text layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_text", name, big_endian,
        asset_id=0, index=index)


def add_camera_layer(root: Chunk, comp_id: int, name: str = "Camera",
                     big_endian: bool = True,
                     index: int | None = None) -> int:
    """Add a camera layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_camera", name, big_endian,
        asset_id=0, index=index)


def add_light_layer(root: Chunk, comp_id: int, name: str = "Light",
                    big_endian: bool = True,
                    index: int | None = None) -> int:
    """Add a light layer. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_light", name, big_endian,
        asset_id=0xFFFFFFFF, index=index)


def add_precomp_layer(root: Chunk, comp_id: int, source_comp_id: int,
                      name: str = "", big_endian: bool = True,
                      index: int | None = None) -> int:
    """Add a precomp layer referencing an existing composition. Returns layer_id."""
    return _add_layer_from_template(
        root, comp_id, "layr_precomp", name, big_endian,
        asset_id=source_comp_id, index=index)


def precompose_layers(root: Chunk, comp_id: int, layer_ids: list[int],
                      new_comp_name: str, big_endian: bool) -> tuple[int, int]:
    """Move layers into a new composition and replace with a precomp layer.

    Returns (new_comp_id, precomp_layer_id).
    """
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    if not layer_ids:
        raise ValueError("No layers specified for precompose")

    # Read comp properties from cdta
    cdta = comp_cl.find("cdta")
    cdta_data = cdta.data
    width = struct.unpack(">H", cdta_data[140:142])[0]
    height = struct.unpack(">H", cdta_data[142:144])[0]
    duration_num, duration_den = _read_comp_duration(comp_cl)

    # Find the insertion position (position of first selected layer)
    first_pos = None
    for layer_id in layer_ids:
        pos = _find_layer_block_start(comp_cl, layer_id)
        if pos is not None:
            if first_pos is None or pos < first_pos:
                first_pos = pos

    # Extract the selected layer blocks
    extracted_blocks: list[list[Chunk]] = []
    for layer_id in layer_ids:
        start = _find_layer_block_start(comp_cl, layer_id)
        if start is None:
            raise ValueError(f"Layer with id={layer_id} not found")
        block = comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
        extracted_blocks.append(block)

    # Remove selected layers from original comp (reverse order to preserve indices)
    for layer_id in reversed(layer_ids):
        start = _find_layer_block_start(comp_cl, layer_id)
        if start is not None:
            del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]

    # Create a new composition by deep-copying the source comp Item
    fold = root.list.find("Fold")
    source_comp_item = None
    for c in fold.list.children:
        if c.name == "Item":
            idta = c.list.find_optional("idta")
            if idta and isinstance(idta.data, bytes) and len(idta.data) >= 20:
                if struct.unpack(">H", idta.data[0:2])[0] == 4:
                    iid = struct.unpack(">I", idta.data[16:20])[0]
                    if iid == comp_id:
                        source_comp_item = c
                        break

    if source_comp_item is None:
        raise ValueError("Source composition Item not found")

    new_comp = _deep_copy_chunk(source_comp_item)
    next_id = _scan_max_id(root) + 1
    new_comp_id = next_id
    next_id += 1

    # Update new comp IDs
    _set_chunk_id(new_comp.list.find("iide"), "iide", new_comp_id)
    _set_chunk_id(new_comp.list.find("idta"), "idta_id", new_comp_id)

    # Set new comp name
    utf8 = new_comp.list.find("Utf8")
    utf8.data = new_comp_name
    utf8.length = len(new_comp_name.encode("utf-8"))

    # Remove all user Layr blocks from new comp (keep system layers DLay/SLay/CLay/SecL)
    new_comp_cl = new_comp.list
    while True:
        found = False
        for i, c in enumerate(new_comp_cl.children):
            if c.name == "Layr":
                del new_comp_cl.children[i:i + _LAYER_BLOCK_SIZE]
                found = True
                break
        if not found:
            break

    # Insert extracted layers into new comp (before DLay)
    dlay_idx = _find_dlay_index(new_comp_cl)
    insert_at = dlay_idx
    for block in extracted_blocks:
        for i, chunk in enumerate(block):
            new_comp_cl.children.insert(insert_at + i, chunk)
        insert_at += _LAYER_BLOCK_SIZE

    # Add new comp + FEE + view state to Fold
    fold.list.children.append(new_comp)
    # FEE (font/expression engine)
    ppSn_data = b"\x40\x62\xc0\x00\x00\x00\x00\x00"  # default ppSn
    fee = Chunk("LIST", 0, ChunkList("FEE ", [
        Chunk("ppSn", 8, ppSn_data),
    ]))
    fold.list.children.append(fee)
    # Fold-level view state (7 chunks)
    for vc in _build_view_state_block_simple():
        fold.list.children.append(vc)

    # Add precomp layer in original comp at the first layer's position
    precomp_layer_id = _add_layer_from_template(
        root, comp_id, "layr_precomp", new_comp_name, big_endian,
        asset_id=new_comp_id, index=None)

    # Move the precomp layer to the original position
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    precomp_start = _find_layer_block_start(comp_cl, precomp_layer_id)
    if precomp_start is not None and first_pos is not None:
        block = comp_cl.children[precomp_start:precomp_start + _LAYER_BLOCK_SIZE]
        del comp_cl.children[precomp_start:precomp_start + _LAYER_BLOCK_SIZE]
        # Recalculate position
        target_pos = _layer_insert_point(comp_cl, 1)
        # Find correct position based on remaining layers
        current_count = _count_user_layers(comp_cl)
        # Insert at beginning for now (user can move later)
        for i, chunk in enumerate(block):
            comp_cl.children.insert(target_pos + i, chunk)

    return new_comp_id, precomp_layer_id


def remove_layer(root: Chunk, comp_id: int, layer_id: int,
                 big_endian: bool) -> bool:
    """Remove a layer from a composition. Returns True if removed."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        return False

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        return False

    del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
    return True


def duplicate_layer(root: Chunk, comp_id: int, layer_id: int,
                    big_endian: bool) -> int:
    """Duplicate a layer. Returns the new layer_id."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        raise ValueError(f"Layer with id={layer_id} not found")

    new_layer_id = _scan_max_id(root) + 1

    # Deep copy the entire 16-chunk block
    block = []
    for i in range(start, start + _LAYER_BLOCK_SIZE):
        block.append(_deep_copy_chunk(comp_cl.children[i]))

    # Update layer_id in ldta
    new_layr = block[0]
    ldta = new_layr.data.find("ldta")
    _set_chunk_id(ldta, "ldta_layer_id", new_layer_id)

    # Update ewin layer_id
    ewst = block[1]  # Ewst
    ewin = ewst.data.find_optional("ewin")
    if ewin:
        _set_chunk_id(ewin, "ewin_layer_id", new_layer_id)

    # Insert after the original block
    insert_at = start + _LAYER_BLOCK_SIZE
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)

    return new_layer_id


def move_layer(root: Chunk, comp_id: int, layer_id: int,
               new_index: int, big_endian: bool) -> None:
    """Move a layer to a new position (1-based index)."""
    comp_cl = find_comp_chunklist(root, comp_id, big_endian)
    if comp_cl is None:
        raise ValueError(f"Composition with id={comp_id} not found")

    start = _find_layer_block_start(comp_cl, layer_id)
    if start is None:
        raise ValueError(f"Layer with id={layer_id} not found")

    # Extract block
    block = comp_cl.children[start:start + _LAYER_BLOCK_SIZE]
    del comp_cl.children[start:start + _LAYER_BLOCK_SIZE]

    # Reinsert
    insert_at = _layer_insert_point(comp_cl, new_index)
    for i, chunk in enumerate(block):
        comp_cl.children.insert(insert_at + i, chunk)
