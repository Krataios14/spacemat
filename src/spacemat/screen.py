"""The screening engine: filter the database against engineering criteria."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .criteria import Criterion
from .db import load_all
from .schema import Material
from .units import as_kelvin


@dataclass(frozen=True)
class ScreenResult:
    material: Material
    t_service_k: Optional[float]
    verdicts: dict   # criterion repr -> True/False/None

    @property
    def passed(self) -> bool:
        return all(v is True for v in self.verdicts.values())

    @property
    def data_gaps(self) -> list[str]:
        return [k for k, v in self.verdicts.items() if v is None]


def screen(*criteria: Criterion,
           T_service=None,
           category: Optional[str] = None,
           require_flammability_pass: bool = False,
           require_temperature_coverage: bool = False,
           include_data_gaps: bool = False) -> list[ScreenResult]:
    """Screen the database against criteria built from property tokens.

    Example::

        from spacemat import screen, TML, CVCM, K
        passing = screen(TML < 1.0, CVCM < 0.1, T_service=90*K)

    Criteria with temperature-dependent properties (e.g. ``YIELD_STRENGTH``)
    are evaluated at ``T_service`` when given. A material missing the data a
    criterion needs is excluded unless ``include_data_gaps=True``, in which
    case it is returned with the gap noted (verdict ``None``).
    """
    t_k = as_kelvin(T_service) if T_service is not None else None
    results = []
    for m in load_all():
        if category and m.category != category:
            continue
        if require_flammability_pass and m.flammability != "pass":
            continue
        if require_temperature_coverage and t_k is not None and not m.covers_temperature(t_k):
            continue
        verdicts = {repr(c): c.evaluate(m, t_k) for c in criteria}
        if any(v is False for v in verdicts.values()):
            continue
        if not include_data_gaps and any(v is None for v in verdicts.values()):
            continue
        results.append(ScreenResult(material=m, t_service_k=t_k, verdicts=verdicts))
    return results
