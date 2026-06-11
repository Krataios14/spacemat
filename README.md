# spacemat

[![PyPI](https://img.shields.io/pypi/v/spacemat)](https://pypi.org/project/spacemat/)
[![tests](https://github.com/Krataios14/spacemat/actions/workflows/test.yml/badge.svg)](https://github.com/Krataios14/spacemat/actions/workflows/test.yml)

Python tools for spaceflight materials selection.

The package bundles a snapshot of the NASA GSFC outgassing database (all
13,582 ASTM E595 test entries as of the retrieval date, fetched from
outgassing.nasa.gov) so it can be queried offline, plus cryogenic property
curves for the alloys and insulators commonly used in cryo tank and
instrument work.

```
pip install spacemat
spacemat summary "scotchweld 2216"
```
```
64 test(s) matching 'scotchweld 2216': 18 pass, 46 fail, 0 incomplete
TML  min 0.10  median 1.10  max 2.85
CVCM min 0.00  median 0.03  max 1.50
```

Keeping the per-test history matters: EC-2216 is usually quoted as passing
E595, but across 64 tests it failed 46 times depending on lot and cure
schedule. Single quoted values hide this spread.

## Outgassing database

Each entry has material, manufacturer, TML, CVCM, WVR, application, cure
schedule, data reference, and year. NASA data is a US Government work and
may be redistributed. `python scripts/fetch_nasa_outgassing.py` rebuilds
the snapshot from the live site.

```python
from spacemat import outgassing

outgassing.search("RTV 566")
outgassing.screen(tml_max=1.0, cvcm_max=0.1, contains="epoxy")
outgassing.summarize("braycote")
outgassing.snapshot_info()
```

The same things from the shell:

```
spacemat search "rtv 566"
spacemat screen --tml 1.0 --cvcm 0.1 --application adhesive --csv passing.csv
spacemat info
```

Numeric screens drop entries with missing values, so a screen result means
tested and passed, not no data found.

## Cryogenic property curves

Thermal conductivity, specific heat, thermal contraction, and Young's
modulus are evaluated from the curve-fit equations NIST publishes for
cryogenic materials, using NIST's own coefficients
(`scripts/fetch_nist_fits.py` parses them off the NIST pages). Materials
covered this way: 304L, 316, 6061-T6, Inconel 718, Ti-6Al-4V, Invar 36,
PTFE, polyimide, and G-10, most over 4 to 300 K.

NIST does not publish strength fits, so the yield and ultimate curves are
typical values from the open literature, with a source string on each
entry. They are suitable for trade studies, not design allowables. The same
applies to 301 cold rolled and Al-Li 2195 in general, which NIST does not
cover.

Queries outside a curve's measured range return `None`; the thermal tools
raise. Cryogenic data is never extrapolated.

```python
from spacemat import screen, TML, CVCM, YIELD_STRENGTH, CONTRACTION, K

screen(TML < 1.0, CVCM < 0.1, YIELD_STRENGTH > 1000, T_service=90*K)
screen(CONTRACTION < 0.3, T_service=77*K)
```

## Thermal tools

Heat leak through a support depends on the integral of k dT across the
temperature span. The integral is computed exactly for point curves and
numerically for the NIST fits:

```python
from spacemat import K
from spacemat.thermal import heat_leak, contraction_mismatch

heat_leak("G-10", area_m2=1.1e-4, length_m=0.3, T_cold=90*K, T_hot=295*K)
contraction_mismatch("PTFE", "304L", 77*K)   # differential strain, percent
```

`examples/strut_heat_leak.py` contains a worked strut-sizing example.

## Compliance reports

```
spacemat report 304L "RTV 566" "Vespel SP-1" --temp 90 -o compliance.md
```

Generates a Markdown report with E595 pass/fail, flammability flags, and
properties at the service temperature. Non-metals are also checked against
the bundled NASA database, reporting the number of upstream tests and their
TML/CVCM spread. Materials that exceed the TML limit only because of
absorbed water (TML minus WVR under the limit) are marked CONDITIONAL,
since these are normally accepted after bakeout.

`examples/vet_bom.py` runs the same check over a bill of materials.

## Other utilities

* `compare(["304L", "Al-Li 2195"], T_service=90*K)` prints a trade table
* `ashby_plot(DENSITY, YIELD_STRENGTH, T_service=90*K)` scatter plots,
  requires `pip install spacemat[plot]`
* `spacemat.export` flattens materials and database entries to CSV or
  dict records for pandas
* The test suite enforces that every data value carries a source string

## Contributing

For a development install:

```
pip install -e .[dev]
pytest
```

MIT licensed. Data contributions must include a source.
