import pytest

from spacemat import (CVCM, DENSITY, K, THERMAL_CONDUCTIVITY, TML, YIELD_STRENGTH,
                      compliance_report, get, load_all, screen)


def test_database_loads_and_is_nontrivial():
    mats = load_all()
    assert len(mats) >= 20
    names = {m.name for m in mats}
    assert "Stainless Steel 304L" in names
    assert "Inconel 718" in names


def test_get_exact_and_substring():
    assert get("Inconel 718").category == "metal"
    assert get("304L").name == "Stainless Steel 304L"
    with pytest.raises(KeyError):
        get("unobtainium")
    with pytest.raises(KeyError):
        get("Stainless")  # ambiguous: 304L and 301


def test_curve_interpolation_and_bounds():
    m = get("304L")
    c = m.curves["yield_strength_mpa"]
    # exact node
    assert c.at(77) == 430
    # interpolated between 77 and 90 K
    mid = c.at(83.5)
    assert 410 < mid < 430
    # out of range: no silent extrapolation
    assert c.at(4) is None
    assert c.at(400) is None


def test_units():
    assert (90 * K).to_kelvin() == 90
    from spacemat import degC
    assert abs((20 * degC).to_kelvin() - 293.15) < 1e-9


def test_screen_outgassing():
    results = screen(TML < 1.0, CVCM < 0.1)
    names = {r.material.name for r in results}
    assert "PTFE (Teflon)" in names
    assert "Stainless Steel 304L" in names
    assert "Apiezon N" not in names       # fails both
    assert "Nylon 6/6" not in names       # fails TML
    assert "Vespel SP-1" not in names     # TML 1.09 > 1.0


def test_screen_at_service_temperature():
    results = screen(TML < 1.0, CVCM < 0.1, YIELD_STRENGTH > 1000, T_service=90 * K)
    names = {r.material.name for r in results}
    assert names == {"Stainless Steel 301", "Inconel 718"}


def test_screen_data_gaps_visible_when_requested():
    strict = screen(THERMAL_CONDUCTIVITY < 10, T_service=20 * K)
    loose = screen(THERMAL_CONDUCTIVITY < 10, T_service=20 * K, include_data_gaps=True)
    assert len(loose) > len(strict)
    gap_results = [r for r in loose if r.data_gaps]
    assert gap_results and not gap_results[0].passed


def test_screen_flammability_and_category_filters():
    metals = screen(DENSITY < 5000, category="metal")
    assert {r.material.name for r in metals} == {"Al-Li 2195"}
    flam = screen(require_flammability_pass=True)
    assert all(r.material.flammability == "pass" for r in flam)
    assert "Buna-N (nitrile)" not in {r.material.name for r in flam}


def test_compliance_report():
    rpt = compliance_report(
        ["Stainless Steel 304L", "Vespel SP-1", "Apiezon N", "Buna-N (nitrile)"],
        T_service=90 * K, project="Cryo tank demo")
    assert "# Materials Compliance Report" in rpt
    assert "Cryo tank demo" in rpt
    assert "**PASS**" in rpt
    assert "**FAIL**" in rpt
    # Vespel: TML 1.09 but WVR 0.9 -> TML-WVR passes -> conditional
    assert "CONDITIONAL" in rpt
    # 304L yield at 90 K appears
    assert "yield strength: 410" in rpt


def test_ashby_plot_smoke():
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    from spacemat import ashby_plot
    ax = ashby_plot(DENSITY, YIELD_STRENGTH, T_service=90 * K, logy=True)
    assert ax.get_xlabel().startswith("density")
