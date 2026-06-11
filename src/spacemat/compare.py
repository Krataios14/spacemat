"""Side-by-side comparison tables for candidate materials."""

from __future__ import annotations

from typing import Sequence, Union

from .db import get
from .schema import Material
from .units import as_kelvin

_ROWS = (
    ("density_kg_m3", "density [kg/m^3]", None),
    ("yield_strength_mpa", "yield [MPa]", "curve"),
    ("ultimate_strength_mpa", "ultimate [MPa]", "curve"),
    ("thermal_conductivity_w_mk", "k [W/(m*K)]", "curve"),
    ("thermal_contraction_pct", "contraction from 293 K [%]", "curve"),
    ("tml", "TML [%]", "outgassing"),
    ("cvcm", "CVCM [%]", "outgassing"),
    ("flammability", "flammability", "attr"),
)


def compare(names: Sequence[Union[Material, str]], T_service=None) -> str:
    """Markdown table of the properties that drive a typical trade,
    evaluated at ``T_service`` where temperature-dependent."""
    mats = [m if isinstance(m, Material) else get(m) for m in names]
    t_k = as_kelvin(T_service) if T_service is not None else None

    header = "| property | " + " | ".join(m.name for m in mats) + " |"
    sep = "|---" * (len(mats) + 1) + "|"
    lines = [header, sep]
    if t_k is not None:
        lines.insert(0, f"At {t_k:g} K:\n")

    for key, label, kind in _ROWS:
        cells = []
        for m in mats:
            if kind == "curve":
                if t_k is None:
                    cells.append("(need T)")
                    continue
                v = m.property_at(key, t_k)
                cells.append(f"{v:.3g}" if v is not None else "no data")
            elif kind == "outgassing":
                v = getattr(m.outgassing, key, None) if m.outgassing else None
                cells.append(f"{v:.2f}" if v is not None else "no data")
            elif kind == "attr":
                cells.append(str(getattr(m, key)))
            else:
                v = getattr(m, key)
                cells.append(f"{v:g}" if v is not None else "no data")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)
