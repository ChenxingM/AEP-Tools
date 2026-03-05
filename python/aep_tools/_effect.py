"""Effect wrapper mirroring AE scripting Effect object."""

from __future__ import annotations

from typing import Any

from aep_parser.models import (
    AnimatedProperty,
    EffectInstance,
    NamedProperty,
    PropertyGroup as PGModel,
)

from ._constants import MATCH_NAMES
from ._property import Property, PropertyGroup, _wrap_named_property


class Effect:
    """Wraps an EffectInstance model."""

    def __init__(self, model: EffectInstance, match_name: str = "") -> None:
        self._model = model
        self._match_name = match_name
        self._params: list[tuple[str, str, Any]] | None = None

    @property
    def name(self) -> str:
        return self._model.name or self._match_name

    @property
    def match_name(self) -> str:
        return self._match_name

    @property
    def enabled(self) -> bool:
        pg = self._model.parameters
        if pg.enabled is not None:
            return pg.enabled
        return pg.visible

    def _ensure_params(self) -> list[tuple[str, str, Any]]:
        if self._params is not None:
            return self._params
        self._params = []
        for np in self._model.parameters.properties:
            wrapped = _wrap_named_property(np)
            mn = np.match_name
            dn = MATCH_NAMES.get(mn, mn)
            if isinstance(wrapped, (Property, PropertyGroup)):
                dn = wrapped.name
            self._params.append((mn, dn, wrapped))
        return self._params

    @property
    def num_params(self) -> int:
        return len(self._ensure_params())

    def param(self, name_or_index: str | int) -> Any:
        """Lookup parameter by 1-based index or name."""
        params = self._ensure_params()
        if isinstance(name_or_index, int):
            idx = name_or_index - 1
            if 0 <= idx < len(params):
                return params[idx][2]
            return None
        name_lower = name_or_index.lower()
        for mn, dn, wrapped in params:
            if mn == name_or_index or dn.lower() == name_lower:
                return wrapped
        return None

    def __call__(self, name_or_index: str | int) -> Any:
        result = self.param(name_or_index)
        if result is None:
            raise KeyError(f"Effect parameter {name_or_index!r} not found in {self.name!r}")
        return result

    def __getitem__(self, name_or_index: str | int) -> Any:
        return self.__call__(name_or_index)

    def __repr__(self) -> str:
        return f"Effect({self.name!r}, num_params={self.num_params})"
