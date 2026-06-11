"""Property tokens with comparison operators: TML < 1.0 builds a Criterion."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Callable, Optional

from .schema import Material

_OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge}


@dataclass(frozen=True)
class Criterion:
    label: str
    op: str
    threshold: float
    getter: Callable[[Material, Optional[float]], Optional[float]]

    def evaluate(self, material: Material, t_kelvin: Optional[float] = None) -> Optional[bool]:
        # None means the material has no data for this, not a pass
        value = self.getter(material, t_kelvin)
        if value is None:
            return None
        return _OPS[self.op](value, self.threshold)

    def __repr__(self) -> str:
        return f"{self.label} {self.op} {self.threshold}"


class Property:
    """Screenable quantity; comparing it returns a Criterion."""

    def __init__(self, label: str, getter: Callable[[Material, Optional[float]], Optional[float]]):
        self.label = label
        self.getter = getter

    def _make(self, op: str, threshold: float) -> Criterion:
        return Criterion(self.label, op, float(threshold), self.getter)

    def __lt__(self, other): return self._make("<", other)
    def __le__(self, other): return self._make("<=", other)
    def __gt__(self, other): return self._make(">", other)
    def __ge__(self, other): return self._make(">=", other)


def _outgassing_field(field: str):
    def getter(m: Material, _t):
        return getattr(m.outgassing, field) if m.outgassing else None
    return getter


def _curve_at_t(curve_name: str, rt_fallback: Optional[str] = None):
    def getter(m: Material, t_kelvin: Optional[float]):
        if t_kelvin is not None:
            return m.property_at(curve_name, t_kelvin)
        if rt_fallback is not None:
            return getattr(m, rt_fallback)
        return None
    return getter


TML = Property("TML [%]", _outgassing_field("tml"))
CVCM = Property("CVCM [%]", _outgassing_field("cvcm"))
WVR = Property("WVR [%]", _outgassing_field("wvr"))
DENSITY = Property("density [kg/m^3]", lambda m, _t: m.density_kg_m3)
YIELD_STRENGTH = Property("yield strength [MPa]",
                          _curve_at_t("yield_strength_mpa", "yield_strength_rt_mpa"))
ULTIMATE_STRENGTH = Property("ultimate strength [MPa]",
                             _curve_at_t("ultimate_strength_mpa", "ultimate_strength_rt_mpa"))
THERMAL_CONDUCTIVITY = Property("thermal conductivity [W/(m*K)]",
                                _curve_at_t("thermal_conductivity_w_mk"))
CONTRACTION = Property("thermal contraction from 293 K [%]",
                       _curve_at_t("thermal_contraction_pct"))
ELONGATION = Property("elongation [%]", _curve_at_t("elongation_pct"))
