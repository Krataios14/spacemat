import pytest

from spacemat import K, compare, export, outgassing


def test_compare_table_at_temperature():
    table = compare(["304L", "Al-Li 2195", "Inconel 718"], T_service=90 * K)
    assert "At 90 K" in table
    assert "| yield [MPa] |" in table
    assert "410" in table       # 304L yield at 90 K
    assert "no data" not in table.split("contraction")[0].split("k [")[1]


def test_compare_without_temperature_marks_curves():
    table = compare(["304L", "PTFE"])
    assert "(need T)" in table


def test_to_records_with_temperature():
    recs = export.to_records(T_service=90 * K)
    rec_304 = next(r for r in recs if r["name"] == "Stainless Steel 304L")
    assert rec_304["yield_strength_mpa_at_90K"] == pytest.approx(410)
    assert rec_304["tml_pct"] == 0.0


def test_to_records_ranges_without_temperature():
    recs = export.to_records()
    rec_304 = next(r for r in recs if r["name"] == "Stainless Steel 304L")
    assert rec_304["thermal_conductivity_w_mk_range_K"] == "1-300"


def test_csv_roundtrip(tmp_path):
    recs = export.to_records(T_service=77 * K)
    text = export.to_csv(recs)
    assert text.splitlines()[0].startswith("name,category")
    p = tmp_path / "out.csv"
    export.to_csv(recs, str(p))
    assert p.read_text(encoding="utf-8") == text
    with pytest.raises(ValueError):
        export.to_csv([])


def test_outgassing_export():
    entries = outgassing.screen(tml_max=0.1, cvcm_max=0.01, contains="braycote")
    recs = export.outgassing_to_records(entries)
    assert recs and all("data_ref" in r for r in recs)
    text = export.to_csv(recs)
    assert "braycote" in text.lower()
