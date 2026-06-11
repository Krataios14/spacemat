import pytest

from spacemat import K, get
from spacemat.thermal import compare_heat_leak, conductivity_integral, heat_leak


def test_integral_exact_on_linear_segment():
    # 301 keeps a point curve: k(77)=7.7, k(90)=8.4, linear between, so the
    # integral over 77..90 is the trapezoid 0.5*(7.7+8.4)*13
    val = conductivity_integral("Stainless Steel 301", 77 * K, 90 * K)
    assert val == pytest.approx(0.5 * (7.7 + 8.4) * 13)


def test_integral_against_nist_fit():
    # 304L is now the NIST fit; the 77-90 K integral should land within a
    # few percent of the simple trapezoid of the fit endpoints
    val = conductivity_integral("304L", 77 * K, 90 * K)
    assert val == pytest.approx(0.5 * (7.92 + 8.70) * 13, rel=0.03)


def test_integral_spans_multiple_segments():
    a = conductivity_integral("304L", 20, 77)
    b = conductivity_integral("304L", 77, 295)
    full = conductivity_integral("304L", 20, 295)
    assert full == pytest.approx(a + b)


def test_no_extrapolation_outside_range():
    with pytest.raises(ValueError, match="extrapolate"):
        conductivity_integral("Al-Li 2195", 4, 90)  # curve starts at 20 K
    with pytest.raises(ValueError):
        conductivity_integral("PEEK", 20, 90)  # no conductivity curve at all


def test_heat_leak_scales_with_geometry():
    q1 = heat_leak("G-10", area_m2=1e-4, length_m=0.1, T_cold=20 * K, T_hot=295 * K)
    q2 = heat_leak("G-10", area_m2=2e-4, length_m=0.2, T_cold=20 * K, T_hot=295 * K)
    assert q1 == pytest.approx(q2)
    assert q1 > 0


def test_compare_ranks_insulators_below_metals():
    ranked = compare_heat_leak(["304L", "G-10", "Inconel 718"],
                               area_m2=1e-4, length_m=0.1, T_cold=20, T_hot=295)
    assert ranked[0][0] == "G-10/FR-4 glass epoxy"
    assert {n for n, _ in ranked} == {"G-10/FR-4 glass epoxy", "Stainless Steel 304L", "Inconel 718"}


def test_accepts_material_objects():
    m = get("Inconel 718")
    assert conductivity_integral(m, 20, 295) > 0
