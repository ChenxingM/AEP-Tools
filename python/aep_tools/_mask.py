"""Mask wrapper mirroring AE scripting MaskPropertyGroup object."""

from __future__ import annotations

from typing import Any

from aep_parser.models import MaskData, NamedProperty

from ._constants import MaskMode
from ._property import Property, _wrap_named_property


class Mask:
    """Wraps a MaskData model."""

    def __init__(self, model: MaskData, match_name: str = "") -> None:
        self._model = model
        self._match_name = match_name
        self._props: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        if self._model.properties and self._model.properties.name:
            return self._model.properties.name
        return f"Mask {self._model.index + 1}"

    @property
    def match_name(self) -> str:
        return self._match_name

    @property
    def mode(self) -> MaskMode:
        return MaskMode(self._model.mode)

    @property
    def inverted(self) -> bool:
        return self._model.inverted

    @property
    def locked(self) -> bool:
        return self._model.locked

    @property
    def index(self) -> int:
        """1-based index."""
        return self._model.index + 1

    def _ensure_props(self) -> dict[str, Any]:
        if self._props is not None:
            return self._props
        self._props = {}
        if self._model.properties:
            for np in self._model.properties.properties:
                wrapped = _wrap_named_property(np)
                self._props[np.match_name] = wrapped
        return self._props

    @property
    def mask_path(self) -> Property | None:
        return self._ensure_props().get("ADBE Mask Shape")

    @property
    def mask_feather(self) -> Property | None:
        return self._ensure_props().get("ADBE Mask Feather")

    @property
    def mask_opacity(self) -> Property | None:
        return self._ensure_props().get("ADBE Mask Opacity")

    @property
    def mask_expansion(self) -> Property | None:
        return self._ensure_props().get("ADBE Mask Offset")

    def __repr__(self) -> str:
        return f"Mask({self.name!r}, mode={self.mode.name})"
