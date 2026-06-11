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
    """Load every JSON file in the bundled data directory, sorted by name."""
    mats: list[Material] = []
    data_dir = resources.files("spacemat.data")
    for entry in sorted(data_dir.iterdir(), key=lambda e: e.name):
        if not entry.name.endswith(".json"):
            continue
        raw = json.loads(entry.read_text(encoding="utf-8"))
        mats.extend(_parse_material(m) for m in raw["materials"])
    names = [m.name for m in mats]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise ValueError(f"duplicate material names across data files: {sorted(dupes)}")
    return tuple(sorted(mats, key=lambda m: m.name))


def get(name: str) -> Material:
    """Look up a material by exact or case-insensitive substring match."""
    mats = load_all()
    needle = name.lower()
    for m in mats:
        if m.name.lower() == needle:
            return m
    hits = [m for m in mats if needle in m.name.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise KeyError(f"no material matching {name!r}")
    raise KeyError(f"ambiguous name {name!r}: {[m.name for m in hits]}")
