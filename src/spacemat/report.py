"""Compliance report generator: ASTM E595 outgassing + NASA-STD-6001 flammability flags."""

from __future__ import annotations

import re
from typing import Optional, Sequence

from . import outgassing
from .db import get
from .schema import Material
from .units import as_kelvin

E595_TML_LIMIT = 1.0
E595_CVCM_LIMIT = 0.10


def _e595_line(m: Material) -> tuple[str, str]:
    """Return (status, detail) for the outgassing assessment."""
    o = m.outgassing
    if o is None:
        return "NO DATA", "no E595 record; test per ASTM E595 or locate a database entry"
    parts = [f"TML {o.tml:.2f}% (limit {E595_TML_LIMIT:.2f}%)",
             f"CVCM {o.cvcm:.2f}% (limit {E595_CVCM_LIMIT:.2f}%)"]
    if o.wvr is not None:
        parts.append(f"WVR {o.wvr:.2f}%")
    detail = ", ".join(parts)
    if o.passes_e595(E595_TML_LIMIT, E595_CVCM_LIMIT):
        return "PASS", detail
    if o.cvcm <= E595_CVCM_LIMIT and o.wvr is not None and (o.tml - o.wvr) <= E595_TML_LIMIT:
        return "CONDITIONAL", detail + "; TML exceeds limit but TML-WVR passes (water-dominated, bakeout typically accepted)"
    return "FAIL", detail


_FLAM_TEXT = {
    "pass": ("PASS", "self-extinguishing / acceptable per NASA-STD-6001 screening"),
    "fail": ("FAIL", "flammable; requires waiver or configuration control per NASA-STD-6001"),
    "untested": ("REVIEW", "no flammability rating on record; assess per NASA-STD-6001 Test 1"),
}


def _nasa_query(m: Material) -> str:
    """Best-effort search string for the NASA database: strip parentheticals
    and generic prefixes from the curated name."""
    name = re.sub(r"\s*\(.*?\)", "", m.name)
    name = re.sub(r"^(Stainless Steel|Scotch-Weld|Hysol)\s+", "", name, flags=re.I)
    return name.strip()


def _nasa_crosscheck(m: Material) -> Optional[dict]:
    if m.category == "metal":
        return None  # metals are non-outgassing; the database covers organics
    return outgassing.summarize(_nasa_query(m))


def compliance_report(names: Sequence[str], T_service=None, project: str = "",
                      crosscheck: bool = True) -> str:
    """Build a Markdown compliance report for the named materials.

    Covers ASTM E595 outgassing (TML <= 1.0%, CVCM <= 0.10%), flammability
    flags, and (when ``T_service`` is given) mechanical/thermal properties
    at the service temperature with data-coverage warnings.
    """
    t_k = as_kelvin(T_service) if T_service is not None else None
    lines = ["# Materials Compliance Report"]
    if project:
        lines.append(f"**Project:** {project}")
    if t_k is not None:
        lines.append(f"**Service temperature:** {t_k:g} K")
    lines += [
        "",
        "Limits applied: ASTM E595 screening (TML ≤ 1.0%, CVCM ≤ 0.10%); "
        "flammability per NASA-STD-6001 flags on record.",
        "",
        "| Material | Condition | E595 | Outgassing detail | Flammability |",
        "|---|---|---|---|---|",
    ]
    materials = [get(n) for n in names]
    for m in materials:
        e_status, e_detail = _e595_line(m)
        f_status, _ = _FLAM_TEXT[m.flammability]
        lines.append(f"| {m.name} | {m.condition} | **{e_status}** | {e_detail} | {f_status} |")

    lines += ["", "## Per-material notes", ""]
    for m in materials:
        lines.append(f"### {m.name}")
        e_status, e_detail = _e595_line(m)
        f_status, f_detail = _FLAM_TEXT[m.flammability]
        lines.append(f"- Outgassing: **{e_status}**: {e_detail}")
        if m.outgassing and m.outgassing.source:
            lines.append(f"  - source: {m.outgassing.source}")
        if crosscheck:
            s = _nasa_crosscheck(m)
            if s:
                lines.append(
                    f"  - NASA database: {s['n_tests']} test(s) matching "
                    f"{_nasa_query(m)!r}: {s['n_pass']} pass, {s['n_fail']} fail; "
                    f"TML {s['tml_min']:.2f} to {s['tml_max']:.2f}%, "
                    f"CVCM {s['cvcm_min']:.2f} to {s['cvcm_max']:.2f}%")
            elif m.category != "metal":
                lines.append(
                    f"  - NASA database: no entries matching {_nasa_query(m)!r}; "
                    "search outgassing.nasa.gov manually")
        lines.append(f"- Flammability: **{f_status}**: {f_detail}")
        if t_k is not None:
            props = []
            for key, label in (("yield_strength_mpa", "yield strength"),
                               ("ultimate_strength_mpa", "ultimate strength"),
                               ("thermal_conductivity_w_mk", "thermal conductivity")):
                c = m.curves.get(key)
                if not c:
                    continue
                v = c.at(t_k)
                if v is None:
                    props.append(f"{label}: NO DATA at {t_k:g} K (curve covers {c.t_min:g}-{c.t_max:g} K)")
                else:
                    props.append(f"{label}: {v:.3g} {c.unit}")
            if props:
                lines.append(f"- Properties at {t_k:g} K: " + "; ".join(props))
            else:
                lines.append(f"- Properties at {t_k:g} K: no temperature-dependent data on record")
        if m.notes:
            lines.append(f"- Notes: {m.notes}")
        lines.append("")

    lines += [
        "---",
        "*Outgassing values are representative database entries; verify the exact "
        "product/lot/cure against outgassing.nasa.gov before flight use. Property "
        "curves are typical values, not design allowables.*",
    ]
    return "\n".join(lines)
