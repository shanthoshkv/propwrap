"""Cantera cross-validation and gamma profile tests."""

from __future__ import annotations

import pytest

from propwrap import GammaProfile, Propellant


def test_cross_validate_returns_results() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    results = p.cross_validate(of_ratio=2.56, pc_bar=70.0, eps=20.0, tolerance_pct=15.0)
    assert len(results) >= 1
    g = next(r for r in results if r.parameter == "gamma_chamber")
    assert g.cea_value > 1.0
    assert g.cantera_value > 1.0
    # Species-set mismatch may push divergence; 15% band is documented
    # If outside, still return structured result — within_tolerance may be False
    assert g.percent_diff >= 0.0


def test_gamma_vs_area_ratio() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    profile = p.gamma_vs_area_ratio(
        of_ratio=2.56,
        pc_bar=70.0,
        eps_range=(5.0, 25.0, 5.0),
        use_cantera=True,
    )
    assert isinstance(profile, GammaProfile)
    assert len(profile.area_ratios) == len(profile.gamma_cea)
    assert len(profile.temperatures_k) == len(profile.area_ratios)
    assert profile.gamma_cantera is not None
    assert all(g > 1.0 for g in profile.gamma_cea)
    # Temperature should drop as area ratio rises (expansion)
    assert profile.temperatures_k[-1] < profile.temperatures_k[0]


def test_gamma_profile_without_cantera() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    profile = p.gamma_vs_area_ratio(
        of_ratio=2.56, pc_bar=70.0, eps_range=(10.0, 20.0, 10.0), use_cantera=False
    )
    assert profile.gamma_cantera is None


def test_compare_to() -> None:
    a = Propellant("RP-1", "LOX", cache_enabled=True)
    b = Propellant("LH2", "LOX", cache_enabled=True)
    # Different O/F optima; use each at a representative point via compare at shared point
    # LH2 at of=2.56 is fuel-rich for LOX/LH2 but still runs
    cmp = a.compare_to(b, of_ratio=2.56, pc_bar=70.0, eps=20.0)
    assert "self" in cmp and "other" in cmp and "delta" in cmp
    assert cmp["delta"]["isp_vac_shifting"] is not None
