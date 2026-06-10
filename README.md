# spacemat

Python tools for spaceflight materials selection. Pulls together public
outgassing data (ASTM E595), cryogenic property curves, and handbook
mechanical properties into one schema you can actually query.

I built this because the data exists but lives in three different places with
three different formats: the NASA outgassing database is a website, the NIST
cryogenic property data is scattered across pages and papers, and strength
data is in handbooks. If you want "passes outgassing AND holds 1000 MPa at
90 K" you end up with browser tabs and a spreadsheet. Now it's one call:

```python
from spacemat import screen, TML, CVCM, YIELD_STRENGTH, K

for r in screen(TML < 1.0, CVCM < 0.1, YIELD_STRENGTH > 1000, T_service=90*K):
    print(r.material.name)
# Stainless Steel 301
# Inconel 718
```

## What's in the database

* ASTM E595 outgassing values (TML, CVCM, WVR) for common spacecraft
  materials, in the style of the NASA GSFC database at outgassing.nasa.gov
* Property curves over 4 to 295 K for the alloys cryo tank work cares about:
  304L, 301 cold rolled, Al-Li 2195, Inconel 718, plus polymer and composite
  conductivities for standoffs and isolators
* Flammability flags in the NASA-STD-6001 sense (pass / fail / needs review)

Curves are point data with linear interpolation. Queries outside the measured
range return `None` instead of extrapolating, on purpose. If you ask for
yield strength at 4 K and the data stops at 20 K, you should know that.

Important: these are representative public values, not design allowables.
Outgassing in particular depends on lot, cure, and bakeout. Verify the exact
product against outgassing.nasa.gov before you fly anything.

## Screening

Criteria are built from property tokens that support comparison operators:

```python
from spacemat import screen, TML, CVCM, DENSITY, THERMAL_CONDUCTIVITY, K

screen(TML < 1.0, CVCM < 0.1)                       # outgassing only
screen(DENSITY < 5000, category="metal")            # light metals
screen(THERMAL_CONDUCTIVITY < 0.5, T_service=20*K)  # cryo isolators
screen(TML < 1.0, require_flammability_pass=True)   # crewed vehicle screen
```

Materials missing the data a criterion needs are dropped by default. Pass
`include_data_gaps=True` to keep them, with the gap listed in `r.data_gaps`.

## Trade plots

```python
from spacemat import ashby_plot, DENSITY, YIELD_STRENGTH, K
ax = ashby_plot(DENSITY, YIELD_STRENGTH, T_service=90*K, logy=True)
ax.figure.savefig("trade.png")
```

Plotting needs matplotlib: `pip install spacemat[plot]`

## Compliance reports

```python
from spacemat import compliance_report, K
print(compliance_report(
    ["Stainless Steel 304L", "Vespel SP-1", "RTV 566", "Apiezon N"],
    T_service=90*K, project="Demo cryo tank"))
```

Generates a Markdown report with E595 pass/fail per material, flammability
flags, and properties at the service temperature. Materials that exceed the
TML limit only because of absorbed water (TML minus WVR under the limit) are
marked CONDITIONAL, since those are usually accepted after bakeout.

## Install and test

```
pip install -e .[dev]
pytest
```

## Data sources

| Family | Source |
|---|---|
| Outgassing | NASA GSFC Outgassing Database (ASTM E595) |
| Cryogenic curves | NIST Cryogenic Material Properties, NASA technical reports |
| Flammability | NASA-STD-6001 ratings where on record |

Every record carries a source string. If you contribute data, keep it that
way. MIT licensed.
