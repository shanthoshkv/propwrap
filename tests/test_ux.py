"""User-experience API: names, defaults, summaries, workflows, opt-in plots."""

from __future__ import annotations

from pathlib import Path

import pytest

from propwrap import (
    Case,
    Mixture,
    Propellant,
    PropellantPair,
    characterize,
    compare_propellants,
    define_blend,
    get_defaults,
    reset_defaults,
    set_defaults,
)
from propwrap.errors import PropwrapError


def setup_function() -> None:
    reset_defaults()


def test_aliases_same_class() -> None:
    assert Mixture is Propellant is PropellantPair


def test_evaluate_summary_str() -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    r = m.evaluate(of=2.56, pc_bar=70, eps=20)
    text = str(r)
    assert "RP1/LOX" in text
    assert "Isp_vac" in text
    assert "m/s" in text


def test_set_defaults_evaluate_partial() -> None:
    set_defaults(pc_bar=70, eps=20)
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    r = m.evaluate(of=2.56)  # pc/eps from defaults
    assert abs(r.pc_pa - 7e6) < 1
    assert r.eps == 20


def test_case_evaluate_and_compare() -> None:
    case = Case(pc_bar=70, eps=40, apply_cryo_defaults=False)
    r = case.evaluate("RP-1", "LOX", of=2.5)
    assert r.isp_vac_shifting > 300
    trade = case.compare(["RP-1/LOX", "CH4/LOX"])
    assert len(trade.rows) == 2
    assert "Isp_vac" in trade.summary()


def test_scan_of_no_plot_by_default(tmp_path: Path) -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    sw = m.scan_of((2.2, 2.8, 0.3), pc_bar=70, eps=20, plot=False)
    assert len(sw.results) >= 2
    out = tmp_path / "of.png"
    sw.plot(save=str(out), show=False)
    assert out.exists()


def test_bad_eps_message() -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    with pytest.raises(PropwrapError, match="expansion ratio"):
        m.evaluate(of=2.5, pc_bar=70, eps=0.5)


def test_characterize_workflow() -> None:
    result = characterize(
        "RP-1",
        "LOX",
        of=2.56,
        pc_bar=70,
        eps=20,
        of_range=(2.2, 2.8, 0.3),
        plot=False,
        apply_cryo_defaults=False,
    )
    assert result.point is not None
    assert result.of_scan is not None
    assert result.density_impulse is not None
    assert "characterization" in result.summary().lower() or "RP1" in result.summary()


def test_compare_propellants_workflow() -> None:
    trade = compare_propellants(
        ["RP-1/LOX", "LH2/LOX"],
        pc_bar=70,
        eps=40,
        plot=False,
        apply_cryo_defaults=False,
    )
    assert trade.ranking_by_isp[0] == "LH2/LOX"


def test_define_blend_workflow() -> None:
    out = define_blend(
        "UXBlend",
        [("MMH", 50), ("UDMH", 50)],
        kind="fuel",
        evaluate_with="N2O4",
        of=2.0,
        pc_bar=50,
        eps=20,
        verbose=False,
    )
    assert out["performance"] is not None
    assert out["performance"].isp_vac_shifting > 250


def test_density_impulse_method() -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    c = m.density_impulse((2.0, 3.0, 0.5), pc_bar=70, eps=20, plot=False)
    assert c.optimum_isp_of > 0
    assert "Density-Isp" in c.summary()


def test_product_gamma_profile() -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    g = m.product_gamma_profile(of=2.56, pc_bar=70, eps_range=(5, 15, 5), use_cantera=False)
    assert len(g.gamma_cea) >= 2
