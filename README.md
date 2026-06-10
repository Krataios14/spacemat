# spacemat

Programmatic access and screening engine for spaceflight materials data.

NASA's outgassing database, NIST-style cryogenic property curves, and handbook
design properties all exist — publicly — but in three different places and three
different formats. `spacemat` unifies them into one queryable schema with an API
that reads like the spec sheet:

```python
from spacemat import screen, TML, CVCM, YIELD_STRENGTH, K

# Materials that pass ASTM E595 outgassing screening and hold
# >1000 MPa yield at 90 K (LOX-temperature cryo tank service):
for r in screen(TML < 1.0, CVCM < 0.1, YIELD_STRENGTH > 1000, T_service=90*K):
    print(r.material.name, r.material.property_at("yield_strength_mpa", 90))
# Stainless Steel 301  1120.0
# Inconel 718          1170.0
```

## What's in the database (v0.1)

- **Outgassing (ASTM E595)** — TML / CVCM / WVR for ~20 common spacecraft
  materials, in the style of the NASA GSFC outgassing database
  ([outgassing.nasa.gov](https://outgassing.nasa.gov)).
- **Cryogenic property curves (20–295 K)** — yield/ultimate strength and thermal
  conductivity vs. temperature for the alloys a stainless cryo-tank program
  cares about: **304L**, **301 (cold rolled)**, **Al-Li 2195-T8**, **Inconel 718**
  — plus PTFE, polyimide, and G-10 conductivities for thermal standoffs.
  Curves are point data with linear interpolation and **no silent
  extrapolation**: a query outside the measured range returns `None`.
- **Flammability flags** — NASA-STD-6001-sense pass/fail/review flags.

> ⚠️ All values are *representative public data*, not design allowables.
> Outgassing depends on lot, cure, and bakeout — verify the exact product
> against outgassing.nasa.gov before flight use.

## Screening

Criteria are built from comparable property tokens:

```python
from spacemat import screen, TML, CVCM, DENSITY, THERMAL_CONDUCTIVITY, K

screen(TML < 1.0, CVCM < 0.1)                      # outgassing only
screen(DENSITY < 5000, category="metal")           # lightweight metals
screen(THERMAL_CONDUCTIVITY < 0.5, T_service=20*K) # cryo thermal isolators
screen(TML < 1.0, require_flammability_pass=True)  # crewed-vehicle screen
```

Materials missing the data a criterion needs are excluded by default; pass
`include_data_gaps=True` to see them with the gap flagged (`r.data_gaps`).

## Ashby-style trade plots

```python
from spacemat import ashby_plot, DENSITY, YIELD_STRENGTH, K
ax = ashby_plot(DENSITY, YIELD_STRENGTH, T_service=90*K, logy=True)
ax.figure.savefig("trade.png")   # requires: pip install spacemat[plot]
```

## Compliance reports

```python
from spacemat import compliance_report, K
print(compliance_report(
    ["Stainless Steel 304L", "Vespel SP-1", "RTV 566", "Apiezon N"],
    T_service=90*K, project="Demo cryo tank"))
```

Produces a Markdown report with ASTM E595 pass/fail (including the
water-dominated **CONDITIONAL** case where TML−WVR passes), flammability
flags, and properties evaluated at the service temperature with data-coverage
warnings.

## Install & test

```
pip install -e .[dev]
pytest
```

## Data provenance

| Family | Source |
|---|---|
| Outgassing | NASA GSFC Outgassing Database (ASTM E595) |
| Cryogenic curves | NIST Cryogenic Material Properties; NASA technical reports |
| Flammability | NASA-STD-6001 ratings where on record |

MIT licensed. Contributions of additional vetted records welcome — each entry
carries a `source` string; keep it that way.
