import pytest

from spacemat import get


# spot checks against values you can read off the NIST plots; if a refetch
# or parser change moves any of these, something is wrong upstream or in us
KNOWN = [
    ("304L", "thermal_conductivity_w_mk", 77, 7.9, 0.05),
    ("304L", "specific_heat_j_kgk", 295, 477, 0.05),
    ("Aluminum 6061-T6", "thermal_conductivity_w_mk", 77, 84, 0.05),
    ("Inconel 718", "thermal_conductivity_w_mk", 77, 6.4, 0.05),
    ("PTFE", "thermal_contraction_pct", 77, 1.94, 0.05),
    ("G-10", "thermal_conductivity_w_mk", 77, 0.28, 0.10),
    ("Ti-6Al-4V", "thermal_conductivity_w_mk", 77, 3.5, 0.05),
    ("Invar 36", "thermal_contraction_pct", 77, 0.04, 0.25),
]


@pytest.mark.parametrize("name,curve,t,expected,rtol", KNOWN)
def test_fit_matches_published_value(name, curve, t, expected, rtol):
    v = get(name).curves[curve].at(t)
    assert v == pytest.approx(expected, rel=rtol)


def test_fits_refuse_out_of_range():
    c = get("Ti-6Al-4V").curves["thermal_conductivity_w_mk"]
    assert c.at(10) is None  # fit starts at 20 K
    assert c.at(350) is None


def test_quartic_holds_constant_below_t_low():
    # 304L expansion fit switches to a constant below 23 K
    c = get("304L").curves["thermal_contraction_pct"]
    assert c.at(4) == c.at(20)


def test_modulus_fit_present():
    c = get("304L").curves["youngs_modulus_gpa"]
    assert c.at(77) == pytest.approx(214, rel=0.03)
    assert c.at(20) is None  # we only carry the 57-293 K segment
