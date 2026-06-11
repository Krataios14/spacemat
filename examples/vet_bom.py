"""Vet a bill of materials against the NASA outgassing database.

Input: a text file with one product name per line (# for comments).
Output: a CSV with the test-count and TML/CVCM spread for each item, plus
a console summary of anything that looks risky.

Usage: python examples/vet_bom.py bom.txt vetted.csv
"""

import csv
import sys

from spacemat import outgassing


def vet(names):
    rows = []
    for name in names:
        s = outgassing.summarize(name)
        if s is None:
            rows.append({"item": name, "n_tests": 0, "verdict": "NOT FOUND"})
            continue
        if s["n_fail"] == 0 and s["n_tests"] >= 3:
            verdict = "CLEAN"
        elif s["n_pass"] == 0:
            verdict = "FAILS"
        else:
            verdict = "MIXED"
        rows.append({"item": name, "n_tests": s["n_tests"], "n_pass": s["n_pass"],
                     "n_fail": s["n_fail"], "tml_min": s["tml_min"],
                     "tml_max": s["tml_max"], "cvcm_max": s["cvcm_max"],
                     "verdict": verdict})
    return rows


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        names = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    rows = vet(names)
    fields = ["item", "n_tests", "n_pass", "n_fail", "tml_min", "tml_max",
              "cvcm_max", "verdict"]
    with open(sys.argv[2], "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        if r["verdict"] != "CLEAN":
            print(f"{r['verdict']:>9}  {r['item']}  ({r.get('n_tests', 0)} tests)")
    print(f"\nwrote {sys.argv[2]} ({len(rows)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
