"""Query interface to the full NASA GSFC outgassing database.

The package bundles a snapshot of the complete database (all test entries,
not a curated subset) built by ``scripts/fetch_nasa_outgassing.py``. Each
entry is one ASTM E595 test of one material sample: the same product often
appears several times with different cure schedules or test campaigns, and
that is exactly what you want to see when deciding whether a value is robust.

Typical use::

    from spacemat import outgassing

    outgassing.search("RTV 566")              # every test of RTV 566
    outgassing.screen(tml_max=1.0, cvcm_max=0.1, contains="epoxy")
    outgassing.summarize("EC-2216")           # min/max/median across tests
"""

from __future__ import annotations

import gzip
import json
import statistics
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Optional

SNAPSHOT = "nasa_outgassing.json.gz"


@dataclass(frozen=True)
class CureStep:
    time: str
    temp: str
    atm: str

    def __str__(self) -> str:
        return "/".join(p for p in (self.time, self.temp, self.atm) if p)


@dataclass(frozen=True)
class OutgassingEntry:
    """One ASTM E595 test record from the NASA GSFC database."""

    material: str
    data_ref: str
    manufacturer: str
    tml: Optional[float]
    cvcm: Optional[float]
    wvr: Optional[float]
    application: str
    cure: tuple[CureStep, ...]
    year: Optional[int]

    def passes_e595(self, tml_max: float = 1.0, cvcm_max: float = 0.10) -> Optional[bool]:
        """Pass/fail against screening limits; None if TML or CVCM is missing."""
        if self.tml is None or self.cvcm is None:
            return None
        return self.tml <= tml_max and self.cvcm <= cvcm_max


@lru_cache(maxsize=1)
def _snapshot() -> dict:
    path = resources.files("spacemat.data").joinpath(SNAPSHOT)
    with path.open("rb") as fb, gzip.open(fb, "rt", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load() -> tuple[OutgassingEntry, ...]:
    """All entries in the bundled snapshot."""
    return tuple(
        OutgassingEntry(
            material=e["material"],
            data_ref=e["data_ref"],
            manufacturer=e["manufacturer"],
            tml=e["tml"],
            cvcm=e["cvcm"],
            wvr=e["wvr"],
            application=e["application"],
            cure=tuple(CureStep(c["time"], c["temp"], c["atm"]) for c in e["cure"]),
            year=e["year"],
        )
        for e in _snapshot()["entries"]
    )


def snapshot_info() -> dict:
    """Provenance of the bundled snapshot (source, retrieval date, row count)."""
    return dict(_snapshot()["meta"])


def search(text: str, field: str = "material") -> list[OutgassingEntry]:
    """Case-insensitive substring search. ``field`` is one of
    material / application / manufacturer / data_ref."""
    if field not in ("material", "application", "manufacturer", "data_ref"):
        raise ValueError(f"unknown search field {field!r}")
    needle = text.lower()
    return [e for e in load() if needle in getattr(e, field).lower()]


def screen(tml_max: Optional[float] = None,
           cvcm_max: Optional[float] = None,
           wvr_max: Optional[float] = None,
           contains: Optional[str] = None,
           application: Optional[str] = None,
           manufacturer: Optional[str] = None,
           year_min: Optional[int] = None) -> list[OutgassingEntry]:
    """Filter the full database. Numeric limits drop entries with missing values,
    since "no data" must never read as "passes"."""
    results = []
    for e in load():
        if tml_max is not None and (e.tml is None or e.tml > tml_max):
            continue
        if cvcm_max is not None and (e.cvcm is None or e.cvcm > cvcm_max):
            continue
        if wvr_max is not None and (e.wvr is None or e.wvr > wvr_max):
            continue
        if contains is not None and contains.lower() not in e.material.lower():
            continue
        if application is not None and application.lower() not in e.application.lower():
            continue
        if manufacturer is not None and manufacturer.lower() not in e.manufacturer.lower():
            continue
        if year_min is not None and (e.year is None or e.year < year_min):
            continue
        results.append(e)
    return results


def summarize(text: str) -> Optional[dict]:
    """Spread of TML/CVCM across every test matching ``text``.

    A material with one clean test and three dirty ones is a different risk
    than four clean tests; this shows that at a glance. Returns None when
    nothing matches.
    """
    entries = search(text)
    if not entries:
        return None
    tmls = [e.tml for e in entries if e.tml is not None]
    cvcms = [e.cvcm for e in entries if e.cvcm is not None]
    verdicts = [e.passes_e595() for e in entries]
    return {
        "query": text,
        "n_tests": len(entries),
        "n_pass": sum(1 for v in verdicts if v is True),
        "n_fail": sum(1 for v in verdicts if v is False),
        "n_no_data": sum(1 for v in verdicts if v is None),
        "tml_min": min(tmls) if tmls else None,
        "tml_median": statistics.median(tmls) if tmls else None,
        "tml_max": max(tmls) if tmls else None,
        "cvcm_min": min(cvcms) if cvcms else None,
        "cvcm_median": statistics.median(cvcms) if cvcms else None,
        "cvcm_max": max(cvcms) if cvcms else None,
    }
