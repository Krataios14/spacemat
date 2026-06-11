from spacemat import outgassing


def test_snapshot_is_the_full_database():
    entries = outgassing.load()
    info = outgassing.snapshot_info()
    assert len(entries) == info["total_rows"]
    assert len(entries) > 13000
    assert "outgassing.nasa.gov" in info["source"]


def test_search_finds_known_materials():
    rtv = outgassing.search("RTV 566")
    assert rtv, "RTV 566 should have test entries"
    assert all("rtv 566" in e.material.lower() for e in rtv)
    refs = outgassing.search("GSFC", field="data_ref")
    assert len(refs) > 1000


def test_search_rejects_bad_field():
    import pytest
    with pytest.raises(ValueError):
        outgassing.search("x", field="density")


def test_screen_limits_and_missing_data():
    passing = outgassing.screen(tml_max=1.0, cvcm_max=0.10)
    assert len(passing) > 1000
    assert all(e.tml is not None and e.tml <= 1.0 for e in passing)
    assert all(e.cvcm is not None and e.cvcm <= 0.10 for e in passing)
    # entries with missing numbers must not appear in a numeric screen
    n_missing = sum(1 for e in outgassing.load() if e.tml is None)
    assert len(passing) + n_missing <= len(outgassing.load())


def test_screen_text_filters_compose():
    epoxies = outgassing.screen(tml_max=1.0, cvcm_max=0.1, contains="epoxy")
    assert epoxies
    assert all("epoxy" in e.material.lower() for e in epoxies)


def test_passes_e595_is_none_when_data_missing():
    incomplete = [e for e in outgassing.load() if e.tml is None or e.cvcm is None]
    if incomplete:
        assert incomplete[0].passes_e595() is None


def test_summarize_spread():
    s = outgassing.summarize("SCOTCHWELD 2216")
    assert s and s["n_tests"] >= 1
    assert s["tml_min"] <= s["tml_median"] <= s["tml_max"]
    assert outgassing.summarize("zzz-not-a-material") is None
