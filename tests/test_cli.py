from spacemat.cli import main


def test_search(capsys):
    assert main(["search", "rtv 566", "--limit", "5"]) == 0
    out = capsys.readouterr().out
    assert "RTV 566" in out.upper()
    assert "TML%" in out


def test_search_no_match(capsys):
    assert main(["search", "zz-not-a-material"]) == 1


def test_summary(capsys):
    assert main(["summary", "scotchweld 2216"]) == 0
    out = capsys.readouterr().out
    assert "pass" in out and "median" in out


def test_screen_with_csv(tmp_path, capsys):
    out_csv = tmp_path / "pass.csv"
    assert main(["screen", "--tml", "0.1", "--cvcm", "0.01",
                 "--contains", "braycote", "--csv", str(out_csv)]) == 0
    assert out_csv.exists()
    assert "braycote" in out_csv.read_text(encoding="utf-8").lower()


def test_materials_and_show(capsys):
    assert main(["materials", "--category", "metal", "--temp", "90"]) == 0
    out = capsys.readouterr().out
    assert "Inconel 718" in out
    assert main(["show", "304L", "--temp", "90"]) == 0
    out = capsys.readouterr().out
    assert "yield" in out and "thermal_conductivity_w_mk" in out


def test_show_unknown_material(capsys):
    assert main(["show", "unobtainium"]) == 1


def test_report_to_file(tmp_path, capsys):
    out_md = tmp_path / "report.md"
    assert main(["report", "304L", "RTV 566", "--temp", "90",
                 "--project", "demo", "-o", str(out_md)]) == 0
    text = out_md.read_text(encoding="utf-8")
    assert "# Materials Compliance Report" in text
    assert "NASA database" in text


def test_info(capsys):
    assert main(["info"]) == 0
    out = capsys.readouterr().out
    assert "total_rows" in out
