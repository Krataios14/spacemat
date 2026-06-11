"""Guard rails on the bundled data itself, so contributions stay honest."""

from spacemat import load_all, outgassing


def test_every_curve_has_a_source():
    for m in load_all():
        for key, c in m.curves.items():
            assert c.source, f"{m.name}/{key} is missing a source string"


def test_every_outgassing_value_has_a_source():
    for m in load_all():
        if m.outgassing:
            assert m.outgassing.source, f"{m.name} outgassing has no source"


def test_curves_cover_a_sane_temperature_range():
    for m in load_all():
        for key, c in m.curves.items():
            assert 0 < c.t_min < c.t_max <= 400, f"{m.name}/{key} range looks wrong"


def test_contraction_curves_anchor_at_reference():
    for m in load_all():
        c = m.curves.get("thermal_contraction_pct")
        if c:
            assert c.at(293) == 0.0, f"{m.name} contraction not zero at 293 K"
            assert all(v >= 0 for v in c.values), f"{m.name} negative contraction"


def test_strength_decreases_toward_room_temperature():
    # Every alloy here strengthens on cooling; a transposed row would break this.
    for m in load_all():
        c = m.curves.get("yield_strength_mpa")
        if c:
            assert list(c.values) == sorted(c.values, reverse=True), \
                f"{m.name} yield curve not monotonic"


def test_flammability_values_are_valid():
    for m in load_all():
        assert m.flammability in ("pass", "fail", "untested"), m.name


def test_nasa_snapshot_values_in_plausible_ranges():
    # The upstream database contains a couple of slightly negative CVCM
    # values (collector mass artifacts) which we preserve as published,
    # so the lower bound is loose rather than zero.
    bad_tml = [e for e in outgassing.load() if e.tml is not None and not -1 <= e.tml <= 100]
    bad_cvcm = [e for e in outgassing.load() if e.cvcm is not None and not -1 <= e.cvcm <= 100]
    assert not bad_tml and not bad_cvcm


def test_nasa_snapshot_mostly_parsed():
    entries = outgassing.load()
    with_tml = sum(1 for e in entries if e.tml is not None)
    assert with_tml / len(entries) > 0.95, "too many unparsed TML values"
