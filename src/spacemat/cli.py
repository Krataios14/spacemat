"""Command line interface.

    spacemat search "rtv 566"            search the NASA outgassing database
    spacemat summary "scotchweld 2216"   TML/CVCM spread across all tests
    spacemat screen --tml 1.0 --cvcm 0.1 --contains epoxy
    spacemat materials --category metal --temp 90
    spacemat show 304L --temp 90
    spacemat report 304L "RTV 566" --temp 90 -o compliance.md
    spacemat info                        snapshot provenance
"""

from __future__ import annotations

import argparse
import sys

from . import export, outgassing
from .compare import compare
from .db import get, load_all
from .report import compliance_report


def _print_table(rows: list[list[str]], headers: list[str]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        print(fmt.format(*r))


def _fmt(v, nd=2) -> str:
    return "" if v is None else f"{v:.{nd}f}"


def _entries_table(entries, limit: int) -> None:
    shown = entries[:limit]
    rows = [[e.material[:55], _fmt(e.tml), _fmt(e.cvcm), _fmt(e.wvr),
             e.application[:24], e.data_ref, str(e.year or "")] for e in shown]
    _print_table(rows, ["material", "TML%", "CVCM%", "WVR%", "application", "ref", "year"])
    if len(entries) > limit:
        print(f"... {len(entries) - limit} more (use --limit, or --csv to export all)")


def cmd_search(args) -> int:
    entries = outgassing.search(args.text, field=args.field)
    if not entries:
        print(f"no entries matching {args.text!r}")
        return 1
    if args.csv:
        export.to_csv(export.outgassing_to_records(entries), args.csv)
        print(f"wrote {len(entries)} entries to {args.csv}")
    else:
        _entries_table(entries, args.limit)
    return 0


def cmd_summary(args) -> int:
    s = outgassing.summarize(args.text)
    if s is None:
        print(f"no entries matching {args.text!r}")
        return 1
    print(f"{s['n_tests']} test(s) matching {args.text!r}: "
          f"{s['n_pass']} pass, {s['n_fail']} fail, {s['n_no_data']} incomplete")
    print(f"TML  min {_fmt(s['tml_min'])}  median {_fmt(s['tml_median'])}  max {_fmt(s['tml_max'])}")
    print(f"CVCM min {_fmt(s['cvcm_min'])}  median {_fmt(s['cvcm_median'])}  max {_fmt(s['cvcm_max'])}")
    return 0


def cmd_screen(args) -> int:
    entries = outgassing.screen(tml_max=args.tml, cvcm_max=args.cvcm, wvr_max=args.wvr,
                                contains=args.contains, application=args.application,
                                manufacturer=args.manufacturer, year_min=args.year_min)
    print(f"{len(entries)} entries pass")
    if args.csv:
        export.to_csv(export.outgassing_to_records(entries), args.csv)
        print(f"wrote {args.csv}")
    elif entries:
        _entries_table(entries, args.limit)
    return 0


def cmd_materials(args) -> int:
    mats = [m for m in load_all() if not args.category or m.category == args.category]
    rows = []
    for m in mats:
        o = m.outgassing
        extra = ""
        if args.temp is not None:
            v = m.property_at("yield_strength_mpa", args.temp)
            extra = f"{v:.0f}" if v is not None else ""
        rows.append([m.name, m.category, m.condition,
                     _fmt(o.tml if o else None), _fmt(o.cvcm if o else None),
                     m.flammability, extra])
    headers = ["name", "category", "condition", "TML%", "CVCM%", "flam",
               f"yield@{args.temp}K" if args.temp is not None else ""]
    _print_table(rows, headers)
    return 0


def cmd_show(args) -> int:
    print(compare([args.name], T_service=args.temp))
    m = get(args.name)
    if m.notes:
        print(f"\n{m.notes}")
    for key, c in sorted(m.curves.items()):
        print(f"\n{key} [{c.unit}], {c.t_min:g}-{c.t_max:g} K ({c.source})")
        print("  T[K]: " + "  ".join(f"{t:g}" for t in c.temps_k))
        print("  val:  " + "  ".join(f"{v:g}" for v in c.values))
    return 0


def cmd_report(args) -> int:
    text = compliance_report(args.names, T_service=args.temp, project=args.project)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.output}")
    else:
        print(text)
    return 0


def cmd_info(_args) -> int:
    for k, v in outgassing.snapshot_info().items():
        print(f"{k}: {v}")
    print(f"curated materials: {len(load_all())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spacemat",
                                description="Spaceflight materials screening")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("search", help="search the NASA outgassing database")
    s.add_argument("text")
    s.add_argument("--field", default="material",
                   choices=["material", "application", "manufacturer", "data_ref"])
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--csv", help="export all matches to a CSV file")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("summary", help="TML/CVCM spread across all tests of a product")
    s.add_argument("text")
    s.set_defaults(func=cmd_summary)

    s = sub.add_parser("screen", help="filter the NASA database by E595 limits")
    s.add_argument("--tml", type=float, help="max TML percent")
    s.add_argument("--cvcm", type=float, help="max CVCM percent")
    s.add_argument("--wvr", type=float, help="max WVR percent")
    s.add_argument("--contains", help="material name substring")
    s.add_argument("--application", help="application substring")
    s.add_argument("--manufacturer", help="manufacturer substring")
    s.add_argument("--year-min", type=int, dest="year_min")
    s.add_argument("--limit", type=int, default=25)
    s.add_argument("--csv", help="export all matches to a CSV file")
    s.set_defaults(func=cmd_screen)

    s = sub.add_parser("materials", help="list curated materials with property curves")
    s.add_argument("--category")
    s.add_argument("--temp", type=float, help="service temperature in K")
    s.set_defaults(func=cmd_materials)

    s = sub.add_parser("show", help="all data for one curated material")
    s.add_argument("name")
    s.add_argument("--temp", type=float, help="service temperature in K")
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("report", help="generate a Markdown compliance report")
    s.add_argument("names", nargs="+")
    s.add_argument("--temp", type=float, help="service temperature in K")
    s.add_argument("--project", default="")
    s.add_argument("-o", "--output")
    s.set_defaults(func=cmd_report)

    s = sub.add_parser("info", help="dataset provenance and counts")
    s.set_defaults(func=cmd_info)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyError as e:
        print(f"error: {e.args[0]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
