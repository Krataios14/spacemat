"""Flatten materials and outgassing entries to plain dicts and CSV.

No pandas dependency; ``to_records`` output feeds ``pandas.DataFrame``
directly if you have it.
"""

from __future__ import annotations

import csv
import io
from typing import Iterable, Optional, Sequence, Union

from .db import load_all
from .outgassing import OutgassingEntry
from .schema import Material
from .units import as_kelvin


def to_records(materials: Optional[Sequence[Material]] = None,
               T_service=None) -> list[dict]:
    """One flat dict per material. Temperature-dependent curves are sampled
    at ``T_service`` (columns suffixed with the temperature), otherwise the
    curve range is reported so you know what exists."""
    t_k = as_kelvin(T_service) if T_service is not None else None
    records = []
    for m in (materials if materials is not None else load_all()):
        rec: dict = {
            "name": m.name,
            "category": m.category,
            "subcategory": m.subcategory,
            "condition": m.condition,
            "density_kg_m3": m.density_kg_m3,
            "tml_pct": m.outgassing.tml if m.outgassing else None,
            "cvcm_pct": m.outgassing.cvcm if m.outgassing else None,
            "wvr_pct": m.outgassing.wvr if m.outgassing else None,
            "flammability": m.flammability,
        }
        for key, curve in sorted(m.curves.items()):
            if t_k is not None:
                rec[f"{key}_at_{t_k:g}K"] = curve.at(t_k)
            else:
                rec[f"{key}_range_K"] = f"{curve.t_min:g}-{curve.t_max:g}"
        records.append(rec)
    return records


def outgassing_to_records(entries: Iterable[OutgassingEntry]) -> list[dict]:
    """Flatten NASA database entries (e.g. from ``outgassing.screen``)."""
    return [{
        "material": e.material,
        "data_ref": e.data_ref,
        "manufacturer": e.manufacturer,
        "tml_pct": e.tml,
        "cvcm_pct": e.cvcm,
        "wvr_pct": e.wvr,
        "application": e.application,
        "cure": "; ".join(str(c) for c in e.cure),
        "year": e.year,
    } for e in entries]


def to_csv(records: Sequence[dict], path: Optional[str] = None) -> Optional[str]:
    """Write records to ``path``, or return CSV text when path is None.
    Columns are the union across records, in first-seen order."""
    if not records:
        raise ValueError("nothing to export")
    fields: list[str] = []
    for r in records:
        for k in r:
            if k not in fields:
                fields.append(k)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    if path is None:
        return buf.getvalue()
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(buf.getvalue())
    return None
