"""Legacy known-value gate + catalog cross-links.

Prefer expanding tests/test_validation_suite.py for new cases.
This module keeps the original master-prompt gate cases.
"""

from __future__ import annotations

import pytest

from propwrap import Propellant

# SOURCE: RocketCEA 1.2.3 self-baseline + catalog REG-RP1-LOX-70bar-eps20
# Theoretical only — not Merlin flight Isp.
REF_LOX_RP1_ISP_VAC = 343.66
REF_LOX_RP1_TOL = 0.02

# SOURCE: catalog REG-LH2-LOX-RS25-class (theoretical at RS-25-like Pc/ε)
REF_LOX_LH2_ISP_VAC = 463.66
REF_LOX_LH2_TOL = 0.03

# SOURCE: catalog REG-MMH-N2O4-lowP (wide band)
REF_N2O4_MMH_ISP_VAC = 320.0
REF_N2O4_MMH_TOL = 0.08


def _within(value: float, ref: float, tol: float) -> None:
    rel = abs(value - ref) / abs(ref)
    assert rel <= tol, f"{value:.3f} not within {tol*100:.1f}% of {ref:.3f} (rel={rel:.4f})"


def test_lox_rp1_vacuum_isp() -> None:
    r = Propellant("RP-1", "LOX", apply_cryo_defaults=False).performance(2.56, 70.0, 20.0)
    _within(r.isp_vac_shifting, REF_LOX_RP1_ISP_VAC, REF_LOX_RP1_TOL)
    assert 1400 < r.c_star < 2500
    assert 2800 < r.tc_kelvin < 4200


def test_lox_lh2_rs25_class() -> None:
    r = Propellant("LH2", "LOX", apply_cryo_defaults=False).performance(5.5, 100.0, 69.0)
    assert r.isp_vac_shifting > 400.0
    assert r.isp_vac_shifting > r.isp_vac_frozen
    _within(r.isp_vac_shifting, REF_LOX_LH2_ISP_VAC, REF_LOX_LH2_TOL)


def test_n2o4_mmh_sanity() -> None:
    r = Propellant("MMH", "N2O4").performance(2.0, 10.0, 40.0)
    assert 250.0 < r.isp_vac_shifting < 370.0
    _within(r.isp_vac_shifting, REF_N2O4_MMH_ISP_VAC, REF_N2O4_MMH_TOL)


@pytest.mark.parametrize(
    "fuel,ox,of_ratio,pc,eps",
    [
        ("RP-1", "LOX", 2.56, 70.0, 20.0),
        ("LH2", "LOX", 5.5, 100.0, 69.0),
        ("MMH", "N2O4", 2.0, 10.0, 40.0),
        ("CH4", "LOX", 3.2, 70.0, 40.0),
        ("UDMH", "N2O4", 2.6, 70.0, 40.0),
    ],
)
def test_gamma_exit_ge_chamber(
    fuel: str, ox: str, of_ratio: float, pc: float, eps: float
) -> None:
    """γ increases as T drops → gamma_exit >= gamma_chamber (physical)."""
    r = Propellant(fuel, ox, apply_cryo_defaults=False).performance(of_ratio, pc, eps)
    assert r.gamma_exit >= r.gamma_chamber


@pytest.mark.parametrize(
    "fuel,ox,of_ratio,pc",
    [
        ("RP-1", "LOX", 2.56, 70.0),
        ("LH2", "LOX", 5.5, 100.0),
        ("CH4", "LOX", 3.0, 70.0),
    ],
)
def test_cea_cantera_gamma_band(fuel: str, ox: str, of_ratio: float, pc: float) -> None:
    results = Propellant(fuel, ox, apply_cryo_defaults=False).cross_validate(
        of_ratio=of_ratio, pc_bar=pc, eps=20.0, tolerance_pct=15.0
    )
    g = next(x for x in results if x.parameter == "gamma_chamber")
    assert g.cea_value > 1.0 and g.cantera_value > 1.0
    assert g.percent_diff < 25.0


def test_no_english_unit_leak_magnitudes() -> None:
    r = Propellant("RP-1", "LOX", apply_cryo_defaults=False).performance(2.56, 70.0, 20.0)
    assert r.c_star < 4000.0
    assert r.tc_kelvin < 5000.0
