"""Rebuild data/nasa_outgassing.json.gz from the live NASA GSFC database.

The outgassing.nasa.gov front end serves the full table through a paged JSON
endpoint; walk it, normalize, gzip. NASA data is public domain. Re-run to
pick up new test entries.
"""

from __future__ import annotations

import datetime
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://etd.gsfc.nasa.gov/wp-admin/admin-ajax.php"
PAGE_SIZE = 500
OUT_PATH = Path(__file__).resolve().parents[1] / "src" / "spacemat" / "data" / "nasa_outgassing.json.gz"

EXPECTED_HEADERS = ["Material", "Data Ref", "Mfr.", "TML %", "CVCM", "WVR",
                    "Application", "Time 1", "Temp 1", "ATM 1", "Time 2", "Temp 2",
                    "ATM 2", "Time 3", "Temp 3", "ATM 3", "Time 4", "Temp 4",
                    "ATM 4", "Year"]


def fetch_page(page: int) -> dict:
    params = urllib.parse.urlencode({
        "action": "load_nasa_data",
        "items_per_page": PAGE_SIZE,
        "nasa_page": page,
        "sort_by": "material",
        "sort_order": "asc",
    })
    req = urllib.request.Request(f"{ENDPOINT}?{params}",
                                 headers={"User-Agent": "spacemat-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = json.load(resp)
    if not payload.get("success"):
        raise RuntimeError(f"page {page}: endpoint returned success=false")
    return payload["data"]


def parse_number(text: str):
    # blanks and junk become None; a few entries lead with < or >
    text = text.strip()
    if not text:
        return None
    if text[0] in "<>":
        text = text[1:]
    try:
        return float(text)
    except ValueError:
        return None


def normalize_row(row: list[str]) -> dict:
    (material, data_ref, mfr, tml, cvcm, wvr, application,
     t1, c1, a1, t2, c2, a2, t3, c3, a3, t4, c4, a4, year) = (s.strip() for s in row)
    cure = []
    for t, c, a in ((t1, c1, a1), (t2, c2, a2), (t3, c3, a3), (t4, c4, a4)):
        if t or c or a:
            cure.append({"time": t, "temp": c, "atm": a})
    try:
        year_val = int(year)
    except ValueError:
        year_val = None
    return {
        "material": material,
        "data_ref": data_ref,
        "manufacturer": mfr,
        "tml": parse_number(tml),
        "cvcm": parse_number(cvcm),
        "wvr": parse_number(wvr),
        "application": application,
        "cure": cure,
        "year": year_val,
    }


def main() -> int:
    first = fetch_page(1)
    if first["headers"] != EXPECTED_HEADERS:
        print("upstream column layout changed; update normalize_row before refetching:",
              first["headers"], file=sys.stderr)
        return 1
    total_pages = first["pagination"]["total_pages"]
    total_rows = first["pagination"]["total_rows"]
    rows = list(first["data"])
    for page in range(2, total_pages + 1):
        rows.extend(fetch_page(page)["data"])
        print(f"  page {page}/{total_pages} ({len(rows)} rows)")
        time.sleep(0.2)  # be polite to the WordPress backend
    if len(rows) != total_rows:
        print(f"warning: expected {total_rows} rows, got {len(rows)}", file=sys.stderr)

    entries = [normalize_row(r) for r in rows]
    snapshot = {
        "meta": {
            "source": "NASA GSFC Outgassing Database (outgassing.nasa.gov)",
            "endpoint": ENDPOINT,
            "retrieved": datetime.date.today().isoformat(),
            "total_rows": len(entries),
            "license": "U.S. Government work, not subject to copyright",
        },
        "entries": entries,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT_PATH, "wt", encoding="utf-8") as f:
        json.dump(snapshot, f, separators=(",", ":"))
    print(f"wrote {len(entries)} entries to {OUT_PATH} "
          f"({OUT_PATH.stat().st_size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
