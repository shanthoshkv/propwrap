"""Core Propellant.performance tests."""

from __future__ import annotations

import pytest

from propwrap import PerformanceResult, Propellant


@pytest.fixture
def lox_rp1() -> Propellant:
    return Propellant("RP-1", "LOX", cache_enabled=False)


def test_performance_returns_model(lox_rp1: Propellant) -> None:
    r = lox_rp1.performance(of_ratio=2.56, pc_bar=70.0, eps=20.0)
    assert isinstance(r, PerformanceResult)
    assert r.fuel == "RP1"
    assert r.oxidizer == "LOX"
    assert r.of_ratio == pytest.approx(2.56)
    assert r.pc_bar == pytest.approx(70.0)
    assert r.eps == pytest.approx(20.0)


def test_units_si_adjacent_not_english(lox_rp1: Propellant) -> None:
    """c* must be m/s (~1800), not ft/s (~5900); Tc K (~3600), not Rankine (~6600)."""
    r = lox_rp1.performance(of_ratio=2.56, pc_bar=70.0, eps=20.0)
    assert 1400.0 < r.c_star < 2500.0, f"c* looks like English units: {r.c_star}"
    assert 2800.0 < r.tc_kelvin < 4200.0, f"Tc looks wrong: {r.tc_kelvin}"
    assert 2500.0 < r.tt_kelvin < r.tc_kelvin
    assert 1000.0 < r.te_kelvin < r.tt_kelvin
    assert r.isp_vac_shifting > r.isp_vac_frozen > 200.0
    assert r.isp_vac_shifting > r.isp_sl_shifting


def test_gamma_and_mw_sane(lox_rp1: Propellant) -> None:
    r = lox_rp1.performance(of_ratio=2.56, pc_bar=70.0, eps=20.0)
    assert 1.05 < r.gamma_chamber < 1.4
    assert 1.05 < r.gamma_exit < 1.5
    assert 15.0 < r.mw_chamber < 35.0
    # Physical: γ rises as T drops through expansion (master prompt inequality was inverted)
    assert r.gamma_exit >= r.gamma_chamber


def test_invalid_inputs(lox_rp1: Propellant) -> None:
    with pytest.raises(ValueError):
        lox_rp1.performance(of_ratio=-1, pc_bar=70, eps=20)
    with pytest.raises(ValueError):
        lox_rp1.performance(of_ratio=2.5, pc_bar=0, eps=20)
    with pytest.raises(ValueError):
        lox_rp1.performance(of_ratio=2.5, pc_bar=70, eps=0.5)


def test_alias_rp1() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=False)
    assert p.fuel == "RP1"
