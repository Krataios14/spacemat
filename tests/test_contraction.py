import pytest

from spacemat import CONTRACTION, K, screen
from spacemat.thermal import contraction_mismatch


def test_contraction_curves_zero_at_reference():
    from spacemat import get
    for name in ("304L", "Inconel 718", "Al-Li 2195", "PTFE"):
        c = get(name).curves["thermal_contraction_pct"]
        assert c.at(293) == 0.0
        assert c.at(20) > 0


def test_ptfe_contracts_an_order_more_than_steel():
    mismatch = contraction_mismatch("PTFE", "304L", 77 * K)
    assert mismatch > 1.5  # percent differential strain


def test_mismatch_is_antisymmetric():
    a = contraction_mismatch("PTFE", "304L", 77)
    b = contraction_mismatch("304L", "PTFE", 77)
    assert a == pytest.approx(-b)


def test_mismatch_requires_data():
    with pytest.raises(ValueError, match="no thermal contraction"):
        contraction_mismatch("PEEK", "304L", 77)
    with pytest.raises(ValueError, match="outside"):
        contraction_mismatch("PTFE", "304L", 4)


def test_contraction_token_in_screen():
    stable = screen(CONTRACTION < 0.3, T_service=77 * K)
    names = {r.material.name for r in stable}
    assert "Inconel 718" in names
    assert "Stainless Steel 304L" in names
    assert "PTFE (Teflon)" not in names
