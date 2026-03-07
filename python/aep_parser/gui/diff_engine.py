"""Pure-logic diff engine for comparing two AEP project dicts.

No Qt dependencies — can be tested independently.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .theme import ADBE_NAMES, fmt_val


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class DiffStatus(Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class DiffNode:
    path: str                              # e.g. "compositions/Main Comp/layers/Shape Layer 1"
    label: str                             # display name
    status: DiffStatus
    value_a: Any = None                    # A-side value (None when ADDED)
    value_b: Any = None                    # B-side value (None when REMOVED)
    node_type: str = ""                    # composition / layer / property / asset / setting …
    children: list[DiffNode] = field(default_factory=list)
    match_name: str = ""                   # AE matchName (property nodes)
    has_changes: bool = False              # True if self or any descendant has a diff

    def __post_init__(self):
        self._update_has_changes()

    def _update_has_changes(self):
        if self.status is not DiffStatus.UNCHANGED:
            self.has_changes = True
        else:
            self.has_changes = any(c.has_changes for c in self.children)

    def to_dict(self, changes_only: bool = True) -> dict | None:
        """Serialize to a JSON-friendly dict.

        If *changes_only* is True, unchanged leaf nodes and empty
        unchanged branches are omitted to keep output compact.
        """
        if changes_only and not self.has_changes:
            return None

        d: dict[str, Any] = {"label": self.label}

        if self.status is not DiffStatus.UNCHANGED or not changes_only:
            d["status"] = self.status.value

        if self.node_type:
            d["type"] = self.node_type

        # Values — only for leaf / modified / added / removed
        if self.status is not DiffStatus.UNCHANGED:
            if self.value_a is not None:
                d["valueA"] = _compact_val(self.value_a)
            if self.value_b is not None:
                d["valueB"] = _compact_val(self.value_b)

        if self.children:
            kids = []
            for c in self.children:
                cd = c.to_dict(changes_only=changes_only)
                if cd is not None:
                    kids.append(cd)
            if kids:
                d["children"] = kids

        return d


@dataclass
class DiffSummary:
    added: int = 0
    removed: int = 0
    modified: int = 0
    unchanged: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _prop_display_name(match_name: str) -> str:
    """Translate an AE matchName to a human-readable name."""
    return ADBE_NAMES.get(match_name, match_name)


def _match_by_keys(items_a: list[dict], items_b: list[dict],
                   primary_key, fallback_key=None):
    """Match two lists of dicts, returning (matched, only_a, only_b).

    *primary_key* can be a str or a callable(dict)->hashable.
    *fallback_key* is tried when primary_key yields None / missing.
    Returns:
        matched  — list of (key, dict_a, dict_b)
        only_a   — list of (key, dict_a)
        only_b   — list of (key, dict_b)
    """
    def _key(item, keyfn):
        if callable(keyfn):
            return keyfn(item)
        return item.get(keyfn)

    idx_b: dict[Any, dict] = {}
    for item in items_b:
        k = _key(item, primary_key)
        if k is None and fallback_key:
            k = _key(item, fallback_key)
        if k is not None:
            idx_b[k] = item

    matched: list[tuple[Any, dict, dict]] = []
    only_a: list[tuple[Any, dict]] = []
    used_b_keys: set = set()

    for item in items_a:
        k = _key(item, primary_key)
        if k is None and fallback_key:
            k = _key(item, fallback_key)
        if k is not None and k in idx_b:
            matched.append((k, item, idx_b[k]))
            used_b_keys.add(k)
        else:
            only_a.append((k, item))

    only_b: list[tuple[Any, dict]] = []
    for item in items_b:
        k = _key(item, primary_key)
        if k is None and fallback_key:
            k = _key(item, fallback_key)
        if k not in used_b_keys:
            only_b.append((k, item))

    return matched, only_a, only_b


def _values_equal(a: Any, b: Any) -> bool:
    """Deep equality with tolerance for floats."""
    if type(a) is not type(b):
        # int vs float comparison
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < 1e-9
        return False
    if isinstance(a, float):
        return abs(a - b) < 1e-9
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    return a == b


def _make_leaf(path: str, label: str, node_type: str,
               val_a: Any, val_b: Any, match_name: str = "") -> DiffNode:
    """Create a leaf DiffNode by comparing two values."""
    if val_a is None and val_b is not None:
        status = DiffStatus.ADDED
    elif val_a is not None and val_b is None:
        status = DiffStatus.REMOVED
    elif _values_equal(val_a, val_b):
        status = DiffStatus.UNCHANGED
    else:
        status = DiffStatus.MODIFIED
    return DiffNode(path=path, label=label, status=status,
                    value_a=val_a, value_b=val_b,
                    node_type=node_type, match_name=match_name)


def _format_value(v: Any) -> str:
    """Format a value for display using the existing theme formatter."""
    return fmt_val(v)


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def diff_projects(dict_a: dict, dict_b: dict) -> DiffNode:
    """Compare two ``Project.to_dict()`` outputs. Returns a DiffNode tree."""
    children: list[DiffNode] = []

    # Settings
    settings_node = _diff_settings(
        dict_a.get("settings", {}),
        dict_b.get("settings", {}),
    )
    children.append(settings_node)

    # Compositions
    comps_node = _diff_compositions(
        dict_a.get("compositions", []),
        dict_b.get("compositions", []),
    )
    children.append(comps_node)

    # Assets
    assets_node = _diff_assets(
        dict_a.get("assets", {}),
        dict_b.get("assets", {}),
    )
    children.append(assets_node)

    # Effects
    effects_node = _diff_effects(
        dict_a.get("effects", {}),
        dict_b.get("effects", {}),
    )
    children.append(effects_node)

    # Render Queue
    rq_node = _diff_render_queue(
        dict_a.get("renderQueue", []),
        dict_b.get("renderQueue", []),
    )
    children.append(rq_node)

    # Determine root status
    any_changes = any(c.has_changes for c in children)
    root = DiffNode(
        path="",
        label="Project",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="project",
        children=children,
        has_changes=any_changes,
    )
    return root


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def _diff_settings(settings_a: dict, settings_b: dict) -> DiffNode:
    all_keys = sorted(set(list(settings_a.keys()) + list(settings_b.keys())))
    children: list[DiffNode] = []
    for key in all_keys:
        va = settings_a.get(key)
        vb = settings_b.get(key)
        child = _make_leaf(f"settings/{key}", key, "setting", va, vb)
        children.append(child)

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path="settings",
        label="Settings",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="settings",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Compositions
# ---------------------------------------------------------------------------

def _diff_compositions(comps_a: list, comps_b: list) -> DiffNode:
    matched, only_a, only_b = _match_by_keys(comps_a, comps_b, "name", "id")
    children: list[DiffNode] = []

    for name, ca, cb in matched:
        children.append(_diff_single_comp(str(name), ca, cb))

    for name, ca in only_a:
        label = str(name or ca.get("name", "?"))
        children.append(DiffNode(
            path=f"compositions/{label}",
            label=label,
            status=DiffStatus.REMOVED,
            value_a=ca,
            node_type="composition",
            has_changes=True,
        ))

    for name, cb in only_b:
        label = str(name or cb.get("name", "?"))
        children.append(DiffNode(
            path=f"compositions/{label}",
            label=label,
            status=DiffStatus.ADDED,
            value_b=cb,
            node_type="composition",
            has_changes=True,
        ))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path="compositions",
        label="Compositions",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="compositions",
        children=children,
        has_changes=any_changes,
    )


def _diff_single_comp(name: str, ca: dict, cb: dict) -> DiffNode:
    base = f"compositions/{name}"
    children: list[DiffNode] = []

    # Comp-level scalar fields
    _COMP_FIELDS = [
        "id", "width", "height", "framerate", "duration",
        "inTime", "outTime", "pixelAspect", "displayStartTime",
        "shutterAngle", "shutterPhase",
        "motionBlurSamplesPerFrame", "motionBlurAdaptiveSampleLimit",
    ]
    for fld in _COMP_FIELDS:
        va = ca.get(fld)
        vb = cb.get(fld)
        if va is not None or vb is not None:
            child = _make_leaf(f"{base}/{fld}", fld, "setting", va, vb)
            children.append(child)

    # Background color
    bg_a = ca.get("backgroundColor")
    bg_b = cb.get("backgroundColor")
    if bg_a is not None or bg_b is not None:
        children.append(_make_leaf(
            f"{base}/backgroundColor", "backgroundColor", "setting", bg_a, bg_b))

    # Comp flags
    flags_a = ca.get("flags", {})
    flags_b = cb.get("flags", {})
    flags_node = _diff_dict(f"{base}/flags", "flags", flags_a, flags_b, "setting")
    if flags_node.children:
        children.append(flags_node)

    # Layers
    layers_node = _diff_layers(name, ca.get("layers", []), cb.get("layers", []))
    children.append(layers_node)

    # Markers
    markers_a = ca.get("markers")
    markers_b = cb.get("markers")
    if markers_a is not None or markers_b is not None:
        children.append(_diff_dict(
            f"{base}/markers", "Markers", markers_a or {}, markers_b or {}, "setting"))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=base,
        label=name,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="composition",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Layers
# ---------------------------------------------------------------------------

def _diff_layers(comp_name: str, layers_a: list, layers_b: list) -> DiffNode:
    base = f"compositions/{comp_name}/layers"

    def _layer_key(layer: dict):
        return (layer.get("name", ""), layer.get("id", 0))

    matched, only_a, only_b = _match_by_keys(layers_a, layers_b, _layer_key, "name")
    children: list[DiffNode] = []

    for key, la, lb in matched:
        label = la.get("name", str(key))
        children.append(_diff_single_layer(comp_name, label, la, lb))

    for key, la in only_a:
        label = la.get("name", str(key))
        children.append(DiffNode(
            path=f"{base}/{label}",
            label=label,
            status=DiffStatus.REMOVED,
            value_a=la,
            node_type="layer",
            has_changes=True,
        ))

    for key, lb in only_b:
        label = lb.get("name", str(key))
        children.append(DiffNode(
            path=f"{base}/{label}",
            label=label,
            status=DiffStatus.ADDED,
            value_b=lb,
            node_type="layer",
            has_changes=True,
        ))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=base,
        label="Layers",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="layers",
        children=children,
        has_changes=any_changes,
    )


def _diff_single_layer(comp_name: str, layer_name: str,
                       la: dict, lb: dict) -> DiffNode:
    base = f"compositions/{comp_name}/layers/{layer_name}"
    children: list[DiffNode] = []

    # Scalar fields
    _LAYER_FIELDS = [
        "id", "type", "inTime", "outTime", "startTime",
        "quality", "timeStretch", "assetId", "parentId",
        "blendMode", "matteMode", "matteId", "autoOrient", "lightType",
    ]
    for fld in _LAYER_FIELDS:
        va = la.get(fld)
        vb = lb.get(fld)
        if va is not None or vb is not None:
            children.append(_make_leaf(f"{base}/{fld}", fld, "setting", va, vb))

    # Layer flags
    flags_a = la.get("flags", {})
    flags_b = lb.get("flags", {})
    flags_node = _diff_dict(f"{base}/flags", "flags", flags_a, flags_b, "setting")
    if flags_node.children:
        children.append(flags_node)

    # Properties
    props_a = la.get("properties", {})
    props_b = lb.get("properties", {})
    if props_a or props_b:
        props_node = _diff_property_groups(base, "Properties", props_a, props_b)
        children.append(props_node)

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=base,
        label=layer_name,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="layer",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

def _diff_property_groups(base_path: str, label: str,
                          group_a: dict, group_b: dict) -> DiffNode:
    """Diff a PropertyGroup.to_dict() — has 'properties' list of NamedProperty."""
    path = f"{base_path}/{label}"
    children: list[DiffNode] = []

    # Group-level fields (name, enabled, visible, splitPosition)
    for fld in ("name", "enabled", "visible", "splitPosition"):
        va = group_a.get(fld)
        vb = group_b.get(fld)
        if va is not None or vb is not None:
            if not _values_equal(va, vb):
                children.append(_make_leaf(f"{path}/{fld}", fld, "setting", va, vb))

    props_a = group_a.get("properties", [])
    props_b = group_b.get("properties", [])

    # Guard: properties must be a list of NamedProperty dicts
    if not isinstance(props_a, list):
        props_a = []
    if not isinstance(props_b, list):
        props_b = []
    props_a = [p for p in props_a if isinstance(p, dict)]
    props_b = [p for p in props_b if isinstance(p, dict)]

    # Match by matchName
    matched, only_a, only_b = _match_by_keys(props_a, props_b, "matchName")

    for mn, pa, pb in matched:
        mn_str = str(mn)
        display = _prop_display_name(mn_str)
        va = pa.get("value")
        vb = pb.get("value")
        children.append(_diff_property_value(f"{path}/{mn_str}", display, mn_str, va, vb))

    for mn, pa in only_a:
        mn_str = str(mn)
        display = _prop_display_name(mn_str)
        children.append(DiffNode(
            path=f"{path}/{mn_str}",
            label=display,
            status=DiffStatus.REMOVED,
            value_a=pa.get("value"),
            node_type="property",
            match_name=mn_str,
            has_changes=True,
        ))

    for mn, pb in only_b:
        mn_str = str(mn)
        display = _prop_display_name(mn_str)
        children.append(DiffNode(
            path=f"{path}/{mn_str}",
            label=display,
            status=DiffStatus.ADDED,
            value_b=pb.get("value"),
            node_type="property",
            match_name=mn_str,
            has_changes=True,
        ))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=path,
        label=label,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="property_group",
        children=children,
        has_changes=any_changes,
    )


def _is_property_group(v: Any) -> bool:
    """True if *v* looks like a PropertyGroup.to_dict() (has a 'properties' list)."""
    return isinstance(v, dict) and isinstance(v.get("properties"), list)


def _diff_property_value(path: str, label: str, match_name: str,
                         val_a: Any, val_b: Any) -> DiffNode:
    """Diff the 'value' of a NamedProperty — could be a scalar, PropertyGroup, or AnimatedProperty."""
    # PropertyGroup (has "properties" list — not a dict like MaskData.properties)
    if _is_property_group(val_a):
        if _is_property_group(val_b):
            return _diff_property_groups(path, label, val_a, val_b)
        # A is group, B is not (or None) — structural change
        return _make_leaf(path, label, "property", val_a, val_b, match_name)

    if _is_property_group(val_b):
        return _make_leaf(path, label, "property", val_a, val_b, match_name)

    # AnimatedProperty (has "animated" key)
    if isinstance(val_a, dict) and "animated" in val_a:
        if isinstance(val_b, dict) and "animated" in val_b:
            return _diff_animated_property(path, label, match_name, val_a, val_b)
        return _make_leaf(path, label, "property", val_a, val_b, match_name)

    if isinstance(val_b, dict) and "animated" in val_b:
        return _make_leaf(path, label, "property", val_a, val_b, match_name)

    # Scalar / dict / other
    return _make_leaf(path, label, "property", val_a, val_b, match_name)


def _diff_animated_property(path: str, label: str, match_name: str,
                            ap_a: dict, ap_b: dict) -> DiffNode:
    """Diff two AnimatedProperty dicts."""
    children: list[DiffNode] = []

    # Compare static value
    v_a = ap_a.get("value")
    v_b = ap_b.get("value")
    if v_a is not None or v_b is not None:
        children.append(_make_leaf(f"{path}/value", "value", "property", v_a, v_b, match_name))

    # Compare expression
    expr_a = ap_a.get("expression")
    expr_b = ap_b.get("expression")
    if expr_a is not None or expr_b is not None:
        children.append(_make_leaf(f"{path}/expression", "expression", "property", expr_a, expr_b))

    # Compare animated flag and components
    for fld in ("animated", "components", "split", "type"):
        fa = ap_a.get(fld)
        fb = ap_b.get(fld)
        if fa is not None or fb is not None:
            if not _values_equal(fa, fb):
                children.append(_make_leaf(f"{path}/{fld}", fld, "setting", fa, fb))

    # Compare keyframes
    kfs_a = ap_a.get("keyframes", [])
    kfs_b = ap_b.get("keyframes", [])
    if kfs_a or kfs_b:
        kf_node = _diff_keyframes(path, kfs_a, kfs_b)
        children.append(kf_node)

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=path,
        label=label,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="property",
        match_name=match_name,
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Keyframes
# ---------------------------------------------------------------------------

def _diff_keyframes(path: str, kfs_a: list, kfs_b: list) -> DiffNode:
    """Diff two keyframe lists by index (positional matching)."""
    kf_path = f"{path}/keyframes"
    children: list[DiffNode] = []
    max_len = max(len(kfs_a), len(kfs_b))

    for i in range(max_len):
        ka = kfs_a[i] if i < len(kfs_a) else None
        kb = kfs_b[i] if i < len(kfs_b) else None
        label = f"Keyframe {i + 1}"
        p = f"{kf_path}/{i}"

        if ka is None:
            children.append(DiffNode(
                path=p, label=label, status=DiffStatus.ADDED,
                value_b=kb, node_type="keyframe", has_changes=True))
        elif kb is None:
            children.append(DiffNode(
                path=p, label=label, status=DiffStatus.REMOVED,
                value_a=ka, node_type="keyframe", has_changes=True))
        elif _values_equal(ka, kb):
            children.append(DiffNode(
                path=p, label=label, status=DiffStatus.UNCHANGED,
                value_a=ka, value_b=kb, node_type="keyframe"))
        else:
            # Diff individual keyframe fields
            kf_children: list[DiffNode] = []
            all_keys = sorted(set(list(ka.keys()) + list(kb.keys())))
            for fld in all_keys:
                fva = ka.get(fld)
                fvb = kb.get(fld)
                if fva is not None or fvb is not None:
                    kf_children.append(_make_leaf(
                        f"{p}/{fld}", fld, "keyframe_field", fva, fvb))
            any_ch = any(c.has_changes for c in kf_children)
            children.append(DiffNode(
                path=p, label=label,
                status=DiffStatus.MODIFIED if any_ch else DiffStatus.UNCHANGED,
                value_a=ka, value_b=kb,
                node_type="keyframe",
                children=kf_children,
                has_changes=any_ch,
            ))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=kf_path,
        label=f"Keyframes ({len(kfs_a)} -> {len(kfs_b)})",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="keyframes",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def _is_comp_asset(v: Any) -> bool:
    """True if the asset dict is actually a Composition (has 'layers')."""
    return isinstance(v, dict) and "layers" in v


def _diff_assets(assets_a: dict, assets_b: dict) -> DiffNode:
    all_keys = sorted(set(list(assets_a.keys()) + list(assets_b.keys())))
    children: list[DiffNode] = []

    for key in all_keys:
        aa = assets_a.get(key)
        ab = assets_b.get(key)

        # Skip composition assets — already covered in Compositions section
        if _is_comp_asset(aa) or _is_comp_asset(ab):
            continue
        label = key
        if isinstance(aa, dict):
            label = aa.get("name", key)
        elif isinstance(ab, dict):
            label = ab.get("name", key)
        path = f"assets/{key}"

        if aa is None:
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.ADDED,
                value_b=ab, node_type="asset", has_changes=True))
        elif ab is None:
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.REMOVED,
                value_a=aa, node_type="asset", has_changes=True))
        elif _values_equal(aa, ab):
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.UNCHANGED,
                value_a=aa, value_b=ab, node_type="asset"))
        else:
            node = _diff_dict(path, str(label), aa, ab, "asset")
            children.append(node)

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path="assets",
        label="Assets",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="assets",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Effects (global definitions)
# ---------------------------------------------------------------------------

def _diff_effects(effects_a: dict, effects_b: dict) -> DiffNode:
    all_keys = sorted(set(list(effects_a.keys()) + list(effects_b.keys())))
    children: list[DiffNode] = []

    for key in all_keys:
        ea = effects_a.get(key)
        eb = effects_b.get(key)
        label = key
        if isinstance(ea, dict):
            label = ea.get("name", key)
        elif isinstance(eb, dict):
            label = eb.get("name", key)
        path = f"effects/{key}"

        if ea is None:
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.ADDED,
                value_b=eb, node_type="effect", has_changes=True))
        elif eb is None:
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.REMOVED,
                value_a=ea, node_type="effect", has_changes=True))
        elif _values_equal(ea, eb):
            children.append(DiffNode(
                path=path, label=str(label), status=DiffStatus.UNCHANGED,
                value_a=ea, value_b=eb, node_type="effect"))
        else:
            node = _diff_dict(path, str(label), ea, eb, "effect")
            children.append(node)

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path="effects",
        label="Effects",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="effects",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Render Queue
# ---------------------------------------------------------------------------

def _diff_render_queue(rq_a: list, rq_b: list) -> DiffNode:
    def _rq_key(item: dict):
        return (item.get("compName", ""), item.get("compId", 0))

    matched, only_a, only_b = _match_by_keys(rq_a, rq_b, _rq_key)
    children: list[DiffNode] = []

    for key, ra, rb in matched:
        label = ra.get("compName", str(key))
        path = f"renderQueue/{label}"
        if _values_equal(ra, rb):
            children.append(DiffNode(
                path=path, label=label, status=DiffStatus.UNCHANGED,
                value_a=ra, value_b=rb, node_type="renderQueueItem"))
        else:
            node = _diff_dict(path, label, ra, rb, "renderQueueItem")
            children.append(node)

    for key, ra in only_a:
        label = ra.get("compName", str(key))
        children.append(DiffNode(
            path=f"renderQueue/{label}", label=label, status=DiffStatus.REMOVED,
            value_a=ra, node_type="renderQueueItem", has_changes=True))

    for key, rb in only_b:
        label = rb.get("compName", str(key))
        children.append(DiffNode(
            path=f"renderQueue/{label}", label=label, status=DiffStatus.ADDED,
            value_b=rb, node_type="renderQueueItem", has_changes=True))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path="renderQueue",
        label="Render Queue",
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type="renderQueue",
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Generic dict diff
# ---------------------------------------------------------------------------

def _diff_dict(path: str, label: str,
               dict_a: dict | None, dict_b: dict | None,
               node_type: str = "setting") -> DiffNode:
    """Recursively diff two dicts (or scalars). Returns a DiffNode."""
    if dict_a is None:
        dict_a = {}
    if dict_b is None:
        dict_b = {}

    if not isinstance(dict_a, dict) or not isinstance(dict_b, dict):
        return _make_leaf(path, label, node_type, dict_a, dict_b)

    all_keys = sorted(set(list(dict_a.keys()) + list(dict_b.keys())))
    children: list[DiffNode] = []

    for key in all_keys:
        va = dict_a.get(key)
        vb = dict_b.get(key)
        p = f"{path}/{key}"

        if isinstance(va, dict) and isinstance(vb, dict):
            children.append(_diff_dict(p, str(key), va, vb, node_type))
        elif isinstance(va, list) and isinstance(vb, list):
            children.append(_diff_list(p, str(key), va, vb, node_type))
        else:
            children.append(_make_leaf(p, str(key), node_type, va, vb))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=path,
        label=label,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type=node_type,
        children=children,
        has_changes=any_changes,
    )


def _diff_list(path: str, label: str,
               list_a: list, list_b: list,
               node_type: str = "setting") -> DiffNode:
    """Diff two lists positionally."""
    children: list[DiffNode] = []
    max_len = max(len(list_a), len(list_b))

    for i in range(max_len):
        va = list_a[i] if i < len(list_a) else None
        vb = list_b[i] if i < len(list_b) else None
        p = f"{path}/{i}"
        item_label = f"[{i}]"

        if isinstance(va, dict) and isinstance(vb, dict):
            children.append(_diff_dict(p, item_label, va, vb, node_type))
        else:
            children.append(_make_leaf(p, item_label, node_type, va, vb))

    any_changes = any(c.has_changes for c in children)
    return DiffNode(
        path=path,
        label=label,
        status=DiffStatus.MODIFIED if any_changes else DiffStatus.UNCHANGED,
        node_type=node_type,
        children=children,
        has_changes=any_changes,
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def compute_summary(root: DiffNode) -> DiffSummary:
    """Walk the DiffNode tree and count leaf-node statuses."""
    summary = DiffSummary()
    _walk_summary(root, summary)
    return summary


def _walk_summary(node: DiffNode, summary: DiffSummary):
    if node.children:
        for child in node.children:
            _walk_summary(child, summary)
    else:
        # Leaf node — count it
        if node.status is DiffStatus.ADDED:
            summary.added += 1
        elif node.status is DiffStatus.REMOVED:
            summary.removed += 1
        elif node.status is DiffStatus.MODIFIED:
            summary.modified += 1
        else:
            summary.unchanged += 1


# ---------------------------------------------------------------------------
# Value compaction (for JSON export)
# ---------------------------------------------------------------------------

def _compact_val(v: Any) -> Any:
    """Produce a compact JSON-safe representation of a property value."""
    if v is None:
        return None
    if isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, dict):
        # Animated property — compact form
        if "animated" in v and "keyframes" in v:
            kfs = v["keyframes"]
            out: dict[str, Any] = {}
            if v.get("value") is not None:
                out["value"] = _compact_val(v["value"])
            if v.get("expression"):
                out["expression"] = v["expression"]
            if kfs:
                out["keyframes"] = [
                    {k: _compact_val(val) for k, val in kf.items()}
                    for kf in kfs
                ]
            return out
        return {k: _compact_val(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_compact_val(x) for x in v]
    return str(v)


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

_LLM_PROMPT_TEMPLATE = """\
以下是两个 After Effects 工程文件的差异列表，每行一条变更。
格式: [状态] 路径: 旧值 -> 新值
- 新增的项只有新值，删除的项只有旧值。

文件 A (旧): {name_a}
文件 B (新): {name_b}
统计: 新增 {added} / 删除 {removed} / 修改 {modified} / 未变更 {unchanged}

<diff>
{diff_lines}
</diff>

请逐条用中文总结以上差异，只输出有变更的内容，不要总结或概述。\
"""


def _flatten_diff(node: DiffNode, lines: list[str], path_parts: list[str]):
    """Recursively collect one-liner change descriptions."""
    current = path_parts + ([node.label] if node.label else [])

    # Leaf node with a real change
    if not node.children and node.status is not DiffStatus.UNCHANGED:
        path_str = "/".join(current)
        tag = {"added": "+", "removed": "-", "modified": "~"}[node.status.value]
        va = fmt_val(node.value_a) if node.value_a is not None else ""
        vb = fmt_val(node.value_b) if node.value_b is not None else ""

        if node.status is DiffStatus.MODIFIED:
            lines.append(f"[{tag}] {path_str}: {va} -> {vb}")
        elif node.status is DiffStatus.ADDED:
            # For large added blobs, summarize instead of dumping raw value
            vb = _summarize_blob(node.value_b) if isinstance(node.value_b, dict) else vb
            lines.append(f"[{tag}] {path_str}: {vb}")
        else:  # REMOVED
            va = _summarize_blob(node.value_a) if isinstance(node.value_a, dict) else va
            lines.append(f"[{tag}] {path_str}: {va}")
        return

    # Container with added/removed status but no children detail
    # (entire comp/layer/asset added or removed wholesale)
    if node.status in (DiffStatus.ADDED, DiffStatus.REMOVED) and not node.children:
        path_str = "/".join(current)
        tag = "+" if node.status is DiffStatus.ADDED else "-"
        blob = node.value_b if node.status is DiffStatus.ADDED else node.value_a
        desc = _summarize_blob(blob) if isinstance(blob, dict) else fmt_val(blob)
        lines.append(f"[{tag}] {path_str}: {desc}")
        return

    # Recurse into children
    for child in node.children:
        if child.has_changes:
            _flatten_diff(child, lines, current)


def _summarize_blob(d: dict) -> str:
    """One-line summary for a large added/removed dict (layer, asset, etc.)."""
    parts: list[str] = []
    if "type" in d:
        parts.append(d["type"])
    if "name" in d:
        parts.append(f'"{d["name"]}"')
    if "layers" in d:
        parts.append(f"{len(d['layers'])} layers")
    if "width" in d and "height" in d:
        parts.append(f"{d['width']}x{d['height']}")
    if "framerate" in d:
        parts.append(f"{d['framerate']}fps")
    if "fullPath" in d:
        parts.append(d["fullPath"])
    return "(" + ", ".join(parts) + ")" if parts else str(d)[:80]


def export_diff_json(root: DiffNode, summary: DiffSummary,
                     name_a: str = "", name_b: str = "",
                     path: str | Path | None = None,
                     include_prompt: bool = True) -> str:
    """Export the diff as flat change lines (compact) or raw JSON.

    Returns the output string. If *path* is given, also writes to file.
    If *include_prompt* is True, produces a compact LLM prompt with
    one-liner diff lines instead of nested JSON.
    """
    if include_prompt:
        lines: list[str] = []
        _flatten_diff(root, lines, [])
        diff_lines = "\n".join(lines)

        output = _LLM_PROMPT_TEMPLATE.format(
            name_a=name_a or "File A",
            name_b=name_b or "File B",
            added=summary.added,
            removed=summary.removed,
            modified=summary.modified,
            unchanged=summary.unchanged,
            diff_lines=diff_lines,
        )
    else:
        diff_dict = root.to_dict(changes_only=True) or {}
        output = json.dumps(diff_dict, ensure_ascii=False, indent=2)

    if path is not None:
        Path(path).write_text(output, encoding="utf-8")

    return output
