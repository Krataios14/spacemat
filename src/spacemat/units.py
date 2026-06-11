"""Just enough units to write T_service=90*K. Everything converts to kelvin."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Quantity:
    magnitude: float
    unit: str

    def to_kelvin(self) -> float:
        if self.unit == "K":
            return self.magnitude
        if self.unit == "degC":
            return self.magnitude + 273.15
        if self.unit == "degF":
            return (self.magnitude - 32.0) * 5.0 / 9.0 + 459.67 * 5.0 / 9.0
        raise ValueError(f"cannot convert unit {self.unit!r} to kelvin")

    def __repr__(self) -> str:
        return f"{self.magnitude} {self.unit}"


@dataclass(frozen=True)
class Unit:
    symbol: str

    def __rmul__(self, value: float) -> Quantity:
        return Quantity(float(value), self.symbol)


K = Unit("K")
degC = Unit("degC")
degF = Unit("degF")


def as_kelvin(value) -> float:
    # bare numbers are taken as K
    if isinstance(value, Quantity):
        return value.to_kelvin()
    return float(value)
