"""Cryogenic thermal calculations on top of the conductivity curves.

The quantity that matters for a support strut or plumbing run between two
temperature stages is not k at a single temperature but the conductivity
integral over the span:

    Q = (A / L) * integral(k dT, T_cold..T_hot)

Curves are piecewise linear in T, so the integral here is exact, not a
numerical approximation.
"""

from __future__ import annotations

from typing import Union

from .db import get
from .schema import Material, PropertyCurve
from .units import as_kelvin

CURVE = "thermal_conductivity_w_mk"


def _resolve(material: Union[Material, str]) -> Material:
    return material if isinstance(material, Material) else get(material)


def conductivity_integral(material: Union[Material, str], T_cold, T_hot) -> float:
    """Integral of k dT from T_cold to T_hot, in W/m.

    Raises ValueError if the material has no conductivity curve or the span
    falls outside the measured range; extrapolating conductivity across a
    cryogenic span silently is how heat-leak budgets go wrong.
    """
    m = _resolve(material)
    curve = m.curves.get(CURVE)
    if curve is None:
        raise ValueError(f"{m.name} has no thermal conductivity curve")
    t0, t1 = as_kelvin(T_cold), as_kelvin(T_hot)
    if t0 >= t1:
        raise ValueError("T_cold must be below T_hot")
    if t0 < curve.t_min or t1 > curve.t_max:
        raise ValueError(
            f"{m.name}: requested span {t0:g}-{t1:g} K outside measured "
            f"range {curve.t_min:g}-{curve.t_max:g} K; refusing to extrapolate")
    if isinstance(curve, PropertyCurve):
        return _piecewise_linear_integral(curve, t0, t1)
    return _simpson(curve.at, t0, t1)


def _piecewise_linear_integral(curve: PropertyCurve, t0: float, t1: float) -> float:
    # trapezoid over the nodes inside the span; exact since segments are linear
    points = [(t0, curve.at(t0))]
    points += [(t, v) for t, v in zip(curve.temps_k, curve.values) if t0 < t < t1]
    points.append((t1, curve.at(t1)))
    total = 0.0
    for (ta, va), (tb, vb) in zip(points, points[1:]):
        total += 0.5 * (va + vb) * (tb - ta)
    return total


def _simpson(f, t0: float, t1: float, n: int = 512) -> float:
    # for NIST fit curves; n=512 puts the error way below the fit's own 1-5%
    h = (t1 - t0) / n
    total = f(t0) + f(t1)
    for i in range(1, n):
        total += f(t0 + i * h) * (4 if i % 2 else 2)
    return total * h / 3


def heat_leak(material: Union[Material, str], area_m2: float, length_m: float,
              T_cold, T_hot) -> float:
    """Steady-state conducted heat in watts through a prismatic member.

    One-dimensional conduction only: no radiation, no MLI, no contact
    resistance. Good for strut and tube budgets, which is what it is for.
    """
    if area_m2 <= 0 or length_m <= 0:
        raise ValueError("area and length must be positive")
    return (area_m2 / length_m) * conductivity_integral(material, T_cold, T_hot)


def contraction_mismatch(material_a: Union[Material, str],
                         material_b: Union[Material, str], T_cold) -> float:
    """Differential thermal strain in percent between two materials cooled
    from 293 K to T_cold. This is the number that cracks bonded joints and
    seizes clearance fits; positive means material_a shrinks more.
    """
    t = as_kelvin(T_cold)
    strains = []
    for mat in (material_a, material_b):
        m = _resolve(mat)
        c = m.curves.get("thermal_contraction_pct")
        if c is None:
            raise ValueError(f"{m.name} has no thermal contraction curve")
        v = c.at(t)
        if v is None:
            raise ValueError(
                f"{m.name}: {t:g} K outside contraction data range "
                f"{c.t_min:g}-{c.t_max:g} K")
        strains.append(v)
    return strains[0] - strains[1]


def compare_heat_leak(names: list[str], area_m2: float, length_m: float,
                      T_cold, T_hot) -> list[tuple[str, float]]:
    """Heat leak for several candidate materials, sorted best (lowest) first.
    Materials without coverage of the span are skipped."""
    rows = []
    for n in names:
        try:
            rows.append((_resolve(n).name, heat_leak(n, area_m2, length_m, T_cold, T_hot)))
        except ValueError:
            continue
    return sorted(rows, key=lambda r: r[1])
