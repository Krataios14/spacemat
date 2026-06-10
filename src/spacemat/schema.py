"""Unified schema for spaceflight materials records.

One :class:`Material` joins three data families that normally live in three
different places:

* outgassing per ASTM E595 (NASA GSFC outgassing database style: TML, CVCM, WVR)
* temperature-dependent property curves (cryogenic range, NIST-style point data)
* room-temperature design properties (MMPDS-style where publicly available)
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Outgassing:
    """ASTM E595 screening values, percent by mass."""

    tml: float            # Total Mass Loss, %
    cvcm: float           # Collected Volatile Condensable Material, %
    wvr: Optional[float] = None  # Water Vapor Regained, %
    source: str = ""

    def passes_e595(self, tml_max: float = 1.0, cvcm_max: float = 0.10) -> bool:
        return self.tml <= tml_max and self.cvcm <= cvcm_max


@dataclass(frozen=True)
class PropertyCurve:
    """A property sampled at discrete temperatures, linearly interpolated.

    Temperatures in kelvin, ascending. Queries outside the sampled range
    return None rather than extrapolating — cryogenic data must not be
    extrapolated silently.
    """

    name: str
    unit: str
    temps_k: tuple[float, ...]
    values: tuple[float, ...]
    source: str = ""

    def __post_init__(self):
        if len(self.temps_k) != len(self.values) or len(self.temps_k) < 2:
            raise ValueError(f"curve {self.name!r}: need >=2 matched (T, value) points")
        if list(self.temps_k) != sorted(self.temps_k):
            raise ValueError(f"curve {self.name!r}: temperatures must be ascending")

    @property
    def t_min(self) -> float:
        return self.temps_k[0]

    @property
    def t_max(self) -> float:
        return self.temps_k[-1]

    def at(self, t_kelvin: float) -> Optional[float]:
        if not (self.t_min <= t_kelvin <= self.t_max):
            return None
        i = bisect.bisect_left(self.temps_k, t_kelvin)
        if i < len(self.temps_k) and self.temps_k[i] == t_kelvin:
            return self.values[i]
        t0, t1 = self.temps_k[i - 1], self.temps_k[i]
        v0, v1 = self.values[i - 1], self.values[i]
        return v0 + (v1 - v0) * (t_kelvin - t0) / (t1 - t0)


@dataclass(frozen=True)
class Material:
    name: str
    category: str                 # "metal", "polymer", "adhesive", "coating", ...
    subcategory: str = ""
    condition: str = ""           # temper / cure / form, e.g. "annealed sheet", "T8"
    density_kg_m3: Optional[float] = None
    outgassing: Optional[Outgassing] = None
    curves: dict[str, PropertyCurve] = field(default_factory=dict)
    # Room-temperature design-allowable-style values (MPa unless noted).
    yield_strength_rt_mpa: Optional[float] = None
    ultimate_strength_rt_mpa: Optional[float] = None
    modulus_rt_gpa: Optional[float] = None
    flammability: str = "untested"  # "pass" | "fail" | "untested" (NASA-STD-6001 sense)
    notes: str = ""
    references: tuple[str, ...] = ()

    def property_at(self, curve_name: str, t_kelvin: float) -> Optional[float]:
        curve = self.curves.get(curve_name)
        return curve.at(t_kelvin) if curve else None

    def covers_temperature(self, t_kelvin: float) -> bool:
        """True if at least one mechanical-strength curve spans this temperature."""
        for key in ("yield_strength_mpa", "ultimate_strength_mpa"):
            c = self.curves.get(key)
            if c and c.t_min <= t_kelvin <= c.t_max:
                return True
        return False
