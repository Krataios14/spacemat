"""Fetch NIST cryogenic property curve fits and write data/nist_fits.json.

NIST publishes each property as a curve-fit equation (log10 polynomial for
conductivity/specific heat/modulus tables, quartic for linear expansion)
with coefficients in an HTML table. We parse those coefficients verbatim,
so evaluation in spacemat is exact NIST, not a re-fit.

Usage: python scripts/fetch_nist_fits.py
"""

from __future__ import annotations

import html as htmllib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://trc.nist.gov/cryogenics/materials/"
OUT = Path(__file__).resolve().parents[1] / "src" / "spacemat" / "data" / "nist_fits.json"

# page path -> (our material name, ordered curve names per table as they
# appear on the page; None skips a column we don't carry)
PAGES = {
    "304LStainless/304LStainless_rev.htm": ("Stainless Steel 304L", [
        ["thermal_conductivity_w_mk", "specific_heat_lowT_j_kgk"],
        ["thermal_contraction_pct"],
    ]),
    # 304's modulus comes as two fit segments; we keep the wide one and skip
    # the 5-57 K piece rather than invent a stitched curve
    "304Stainless/304Stainless_rev.htm": ("__304__", [
        ["thermal_conductivity_w_mk", "specific_heat_j_kgk"],
        [None, "youngs_modulus_gpa", "thermal_contraction_pct"],
    ]),
    # 316's specific heat is two fit segments; keep the high-T one
    "316Stainless/316Stainless_rev.htm": ("Stainless Steel 316", [
        ["thermal_conductivity_w_mk", None, "specific_heat_j_kgk"],
        [None, "youngs_modulus_gpa", "thermal_contraction_pct"],
    ]),
    "6061 Aluminum/6061_T6Aluminum_rev.htm": ("Aluminum 6061-T6", [
        ["thermal_conductivity_w_mk", "specific_heat_j_kgk"],
        ["youngs_modulus_gpa", "thermal_contraction_pct"],
    ]),
    "Iconel 718/Inconel718_rev.htm": ("Inconel 718", [
        ["thermal_conductivity_w_mk"],
        ["thermal_contraction_pct"],
    ]),
    "G-10 CR Fiberglass Epoxy/G10CRFiberglassEpoxy_rev.htm": ("G-10/FR-4 glass epoxy", [
        ["thermal_conductivity_w_mk", "thermal_conductivity_warp_w_mk", "specific_heat_j_kgk"],
        ["thermal_contraction_pct", "thermal_contraction_warp_pct"],
    ]),
    "Teflon/Teflon_rev.htm": ("PTFE (Teflon)", [
        ["thermal_conductivity_w_mk", "specific_heat_j_kgk"],
        ["thermal_contraction_pct"],
    ]),
    "Polyimide Kapton/PolyimideKapton_rev.htm": ("Kapton H film", [
        ["thermal_conductivity_w_mk", "specific_heat_j_kgk"],
    ]),
    "Ti6Al4V/Ti6Al4V_rev.htm": ("Ti-6Al-4V", [
        ["thermal_conductivity_w_mk"],
        ["thermal_contraction_pct"],
    ]),
    "Invar(Fe-36Ni)/Invar_rev.htm": ("Invar 36", [
        ["thermal_conductivity_w_mk", "specific_heat_j_kgk"],
        ["youngs_modulus_gpa", "thermal_contraction_pct"],
    ]),
}

UNITS = {
    "thermal_conductivity_w_mk": "W/(m*K)",
    "thermal_conductivity_warp_w_mk": "W/(m*K)",
    "specific_heat_j_kgk": "J/(kg*K)",
    "specific_heat_lowT_j_kgk": "J/(kg*K)",
    "youngs_modulus_gpa": "GPa",
    "thermal_contraction_pct": "% (shrinkage from 293 K)",
    "thermal_contraction_warp_pct": "% (shrinkage from 293 K)",
}

_NUM = re.compile(r"^-?\d+(\.\d+)?([Ee][+-]?\d+)?$")
_RANGE = re.compile(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$")


def _lines(html: str) -> list[str]:
    text = htmllib.unescape(re.sub(r"<[^>]+>", "\n", html))
    return [l.strip() for l in text.splitlines() if l.strip()]


def _is_value(s: str) -> bool:
    return bool(_NUM.match(s)) or s in (".", "NA")


def _to_float(s: str):
    return float(s) if _NUM.match(s) else None


def _read_values(lines, i, ncols):
    vals = []
    while len(vals) < ncols and i < len(lines) and _is_value(lines[i]):
        vals.append(_to_float(lines[i]))
        i += 1
    return vals, i


def _table_start(lines, i):
    return lines[i] == "a" and i + 1 < len(lines) and _is_value(lines[i + 1]) \
        and lines[i + 1] not in (".", "NA")


def parse_tables(lines: list[str]) -> list[list[dict]]:
    """Find every coefficient table; returns one list of column dicts each."""
    tables = []
    i = 0
    while i < len(lines):
        if not _table_start(lines, i):
            i += 1
            continue
        vals, j = _read_values(lines, i + 1, 99)
        ncols = len(vals)
        coeffs = {"a": vals}
        i = j
        for letter in "bcdefghi":
            if i < len(lines) and lines[i] == letter:
                coeffs[letter], i = _read_values(lines, i + 1, ncols)
        # trailer rows: T low / f> constants and the data+equation ranges.
        # labels get split across lines by the HTML, so scan token by token.
        t_low = below = None
        ranges = []
        pending = None
        while i < len(lines) and not _table_start(lines, i) and "form" not in lines[i]:
            tok = lines[i]
            m = _RANGE.match(tok)
            if m:
                ranges.append((float(m.group(1)), float(m.group(2))))
            elif "low" in tok.lower():
                pending = "t_low"
            elif tok.startswith("f>"):
                pending = "below"
            elif pending and _is_value(tok):
                run, i = _read_values(lines, i, ncols)
                if pending == "t_low":
                    t_low = run
                else:
                    below = run
                pending = None
                continue
            i += 1
        cols = []
        for c in range(ncols):
            col = {k: v[c] for k, v in coeffs.items() if c < len(v)}
            # second group of ranges is the equation range; that's what NIST
            # says the fit is valid over
            data_r = ranges[c] if c < len(ranges) else None
            eq_r = ranges[ncols + c] if ncols + c < len(ranges) else data_r
            cols.append({
                "coeffs": col,
                "form": "log10poly" if "i" in coeffs else "quartic",
                "t_min": eq_r[0] if eq_r else None,
                "t_max": eq_r[1] if eq_r else None,
                "data_range": list(data_r) if data_r else None,
                "t_low": t_low[c] if t_low else None,
                "below_value": below[c] if below else None,
            })
        tables.append(cols)
    return tables


def main() -> int:
    fits: dict[str, dict] = {}
    for path, (mat_name, table_specs) in PAGES.items():
        url = BASE + urllib.parse.quote(path)
        req = urllib.request.Request(url, headers={"User-Agent": "spacemat-fetch/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            html = r.read().decode("utf-8", errors="replace")
        tables = parse_tables(_lines(html))
        if len(tables) != len(table_specs):
            print(f"{path}: expected {len(table_specs)} tables, found {len(tables)}",
                  file=sys.stderr)
            return 1
        mat_fits = fits.setdefault(mat_name, {})
        for spec, cols in zip(table_specs, tables):
            if len(cols) != len(spec):
                print(f"{path}: column count mismatch {len(cols)} vs {spec}", file=sys.stderr)
                return 1
            for curve_name, col in zip(spec, cols):
                if curve_name is None:
                    continue
                col["unit"] = UNITS[curve_name]
                col["source"] = f"NIST cryogenic material properties curve fit, {url}"
                if curve_name.startswith("thermal_contraction"):
                    # NIST gives (L-L293)/L293 x 1e5; we store shrinkage in %
                    col["transform"] = "expansion_e5_to_contraction_pct"
                mat_fits[curve_name] = col
        print(f"{mat_name}: {', '.join(k for k in mat_fits)}")

    # 304L's own specific heat fit only covers 4-23 K and it has no modulus
    # fit; NIST treats 304/304L as the same base alloy for those, so borrow
    l304 = fits["Stainless Steel 304L"]
    for key in ("specific_heat_j_kgk", "youngs_modulus_gpa"):
        l304[key] = dict(fits["__304__"][key])
        l304[key]["source"] += " (304 fit, applied to 304L)"
    del fits["__304__"]

    OUT.write_text(json.dumps({"_meta": {
        "description": "Verbatim NIST cryogenic property curve-fit coefficients.",
        "source": "https://trc.nist.gov/cryogenics/materials/materialproperties.htm",
    }, "fits": fits}, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
