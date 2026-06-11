"""Size the conducted heat leak for cryo tank support struts.

Eight hollow struts carry a 90 K tank shell from a 295 K skirt. Compare
candidate strut materials on conducted heat and on strength at temperature.
"""

from spacemat import K, get
from spacemat.thermal import compare_heat_leak, heat_leak

# Strut geometry: 25 mm OD, 1.5 mm wall, 300 mm long
import math
OD, WALL, LENGTH = 0.025, 0.0015, 0.30
AREA = math.pi / 4 * (OD**2 - (OD - 2 * WALL)**2)
N_STRUTS = 8

CANDIDATES = ["304L", "Stainless Steel 301", "Inconel 718", "G-10"]

print(f"strut cross section: {AREA * 1e6:.1f} mm^2, length {LENGTH * 1e3:.0f} mm")
print(f"{'material':<28} {'Q per strut [W]':>16} {'total [W]':>10} {'yield@90K [MPa]':>16}")
for name, q in compare_heat_leak(CANDIDATES, AREA, LENGTH, T_cold=90 * K, T_hot=295 * K):
    y = get(name).property_at("yield_strength_mpa", 90)
    y_txt = f"{y:.0f}" if y is not None else "n/a"
    print(f"{name:<28} {q:>16.2f} {q * N_STRUTS:>10.1f} {y_txt:>16}")

# A single number for the budget spreadsheet:
q_g10 = heat_leak("G-10", AREA, LENGTH, T_cold=90 * K, T_hot=295 * K)
print(f"\nbaseline G-10 design: {q_g10 * N_STRUTS:.2f} W total conducted")
