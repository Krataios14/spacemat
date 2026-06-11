# spacemat

Python tools for spaceflight materials selection.

The core of the package is a bundled snapshot of the **complete NASA GSFC
outgassing database**: 13,582 ASTM E595 test entries fetched straight from
the source at outgassing.nasa.gov. Not a curated subset, the whole thing,
queryable offline. On top of that sits a smaller curated layer of cryogenic
property curves (strength, conductivity, contraction down to 4 K) for the
alloys and insulators that cryo tank work runs on.

```
pip install -e .
spacemat summary "scotchweld 2216"
```
```
64 test(s) matching 'scotchweld 2216': 18 pass, 46 fail, 0 incomplete
TML  min 0.10  median 1.10  max 2.85
CVCM min 0.00  median 0.03  max 1.50
```

That output is the point of the project. A single datasheet number says
EC-2216 passes outgassing. The full test history says it failed E595 in 46
of 64 tests depending on lot and cure. You want the spread, not the cherry
picked row.

## The outgassing database

13,582 entries, every test NASA publishes: material, manufacturer, TML,
CVCM, WVR, application, cure schedule, data reference, year. NASA data is a
US Government work, so redistributing the snapshot is fine. Refresh it any
time with `python scripts/fetch_nasa_outgassing.py`.

```python
from spacemat import outgassing

outgassing.search("RTV 566")                # every test of a product
outgassing.screen(tml_max=1.0, cvcm_max=0.1, contains="epoxy")
outgassing.summarize("braycote")            # spread across tests
outgassing.snapshot_info()                  # provenance and retrieval date
```

Or from the shell:

```
spacemat search "rtv 566"
spacemat screen --tml 1.0 --cvcm 0.1 --application adhesive --csv passing.csv
spacemat info
```

Numeric screens drop entries with missing values rather than passing them.
No data never reads as passes.

## Cryogenic property curves

The curated layer has full property curves for 304L, 301 cold rolled,
Al-Li 2195, and Inconel 718 (yield, ultimate, conductivity, contraction,
4 to 295 K) plus PTFE, polyimide, and G-10 for standoffs. Curves
interpolate linearly and refuse to extrapolate: out of range returns
`None`, and the thermal tools raise.

```python
from spacemat import screen, TML, CVCM, YIELD_STRENGTH, CONTRACTION, K

screen(TML < 1.0, CVCM < 0.1, YIELD_STRENGTH > 1000, T_service=90*K)
screen(CONTRACTION < 0.3, T_service=77*K)
```

These values are representative public data (NIST cryogenic properties,
NASA reports), not design allowables. They are for trades and budgets, not
margins of safety.

## Thermal tools

Heat leak through a support needs the integral of k dT, not k at one
temperature. The curves are piecewise linear so the integral is exact:

```python
from spacemat import K
from spacemat.thermal import heat_leak, contraction_mismatch

heat_leak("G-10", area_m2=1.1e-4, length_m=0.3, T_cold=90*K, T_hot=295*K)
contraction_mismatch("PTFE", "304L", 77*K)   # differential strain, percent
```

`examples/strut_heat_leak.py` runs the classic eight-strut tank support
trade end to end.

## Compliance reports

```
spacemat report 304L "RTV 566" "Vespel SP-1" --temp 90 -o compliance.md
```

Markdown report with E595 pass/fail, flammability flags, properties at the
service temperature, and a crosscheck of every non-metal against the full
NASA database showing how many tests exist upstream and their spread.
Materials over the TML limit only from absorbed water (TML minus WVR
passes) are marked CONDITIONAL, the usual bakeout case.

`examples/vet_bom.py` does the same in bulk for a bill of materials.

## Also in the box

* `compare(["304L", "Al-Li 2195"], T_service=90*K)` comparison tables
* `ashby_plot(DENSITY, YIELD_STRENGTH, T_service=90*K)` trade plots
  (needs `pip install spacemat[plot]`)
* `spacemat.export` to CSV or dict records for pandas
* Data integrity tests: every value carries a source string, enforced in CI

## Development

```
pip install -e .[dev]
pytest
```

MIT licensed. Contributions welcome, with sources.
