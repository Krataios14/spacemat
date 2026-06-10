"""Load the bundled dataset into Material objects."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from .schema import Material, Outgassing, PropertyCurve


def _parse_material(raw: dict) -> Material:
    out = None
    if raw.get("outgassing"):
        o = raw["outgassing"]
        out = Outgassing(tml=o["tml"], cvcm=o["cvcm"], wvr=o.get("wvr"), source=o.get("source", ""))
    curves = {}
    for key, c in raw.get("curves", {}).items():
        curves[key] = PropertyCurve(
            name=key,
            unit=c["unit"],
            temps_k=tuple(c["temps_k"]),
            values=tuple(c["values"]),
            source=c.get("source", ""),
        )
    return Material(
        name=raw["name"],
        category=raw["category"],
        subcategory=raw.get("subcategory", ""),
        condition=raw.get("condition", ""),
        density_kg_m3=raw.get("density_kg_m3"),
        outgassing=out,
        curves=curves,
        yield_strength_rt_mpa=raw.get("yield_strength_rt_mpa"),
        ultimate_strength_rt_mpa=raw.get("ultimate_strength_rt_mpa"),
        modulus_rt_gpa=raw.get("modulus_rt_gpa"),
        flammability=raw.get("flammability", "untested"),
        notes=raw.get("notes", ""),
        references=tuple(raw.get("references", ())),
    )


@lru_cache(maxsize=1)
def load_all() -> tuple[Material, ...]:
    text = resources.files("spacemat.data").joinpath("materials.json").read_text(encoding="utf-8")
    raw = json.loads(text)
    return tuple(_parse_material(m) for m in raw["materials"])


def get(name: str) -> Material:
    """Look up a material by exact or case-insensitive substring match."""
    mats = load_all()
    for m in mats:
        if m.name == name:
            return m
    needle = name.lower()
    hits = [m for m in mats if needle in m.name.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise KeyError(f"no material matching {name!r}")
    raise KeyError(f"ambiguous name {name!r}: {[m.name for m in hits]}")
