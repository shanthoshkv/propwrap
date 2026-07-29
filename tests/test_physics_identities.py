"""Hard physics identities and bit-level CEA consistency checks.

These tests secure the unit conversions and definitions that must never
silently drift (g0, ve, Cf, Pc/Pe, Rankine→K, ft/s→m/s).
"""

from __future__ import annotations

import pytest

from propwrap import Mixture
from propwrap.units import G0, bar_to_pa, psi_to_pa


def test_ve_equals_isp_times_g0() -> None:
    """ve [m/s] ≡ Isp [s] · g0 with CODATA/standard g0 = 9.80665 m/s².

    Source: BIPM / NIST standard acceleration of gravity (conventional).
    """
    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False, cache_enabled=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    assert r.ve_vac_shifting == pytest.approx(r.isp_vac_shifting * G0, rel=1e-12)
    assert r.ve_vac_frozen == pytest.approx(r.isp_vac_frozen * G0, rel=1e-12)


def test_cf_vac_equals_ve_over_cstar() -> None:
    """Vacuum Cf = ve / c* = Isp·g0 / c* (consistent SI definition)."""
    r = Mixture("CH4", "LOX", apply_cryo_defaults=False, cache_enabled=False).evaluate(
        of=3.2, pc_bar=70, eps=40
    )
    assert r.cf_vac == pytest.approx(r.ve_vac_shifting / r.c_star, rel=1e-9)


def test_pc_over_pe_matches_pressures() -> None:
    r = Mixture("LH2", "LOX", apply_cryo_defaults=False, cache_enabled=False).evaluate(
        of=5.0, pc_bar=70, eps=40
    )
    assert r.pe_pa > 0
    assert r.pc_pa / r.pe_pa == pytest.approx(r.pc_over_pe, rel=1e-9)


def test_temperature_and_gamma_ordering() -> None:
    for fuel, ox, of_r, pc, eps in [
        ("RP-1", "LOX", 2.56, 70, 20),
        ("LH2", "LOX", 5.5, 100, 69),
        ("CH4", "LOX", 3.0, 100, 35),
        ("MMH", "N2O4", 2.0, 70, 40),
    ]:
        r = Mixture(fuel, ox, apply_cryo_defaults=False, cache_enabled=True).evaluate(
            of=of_r, pc_bar=pc, eps=eps
        )
        assert r.te_kelvin < r.tt_kelvin < r.tc_kelvin
        assert r.gamma_exit + 1e-9 >= r.gamma_chamber
        assert r.isp_vac_shifting + 1e-9 >= r.isp_vac_frozen
        assert r.isp_vac_shifting + 1e-9 >= r.isp_sl_shifting


def test_chamber_density_matches_ideal_gas() -> None:
    """CEA gas density ≈ P·Mw/(R·T) in SI (dissociation corrections small here)."""
    from propwrap.units import R_UNIVERSAL

    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False, cache_enabled=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    assert r.chamber is not None
    rho_ig = r.pc_pa * r.mw_chamber / (R_UNIVERSAL * r.tc_kelvin)
    assert r.chamber.density_kg_m3 == pytest.approx(rho_ig, rel=1e-4)


def test_bit_level_match_rocketcea_lh2_docs() -> None:
    """propwrap Isp must match RocketCEA get_Isp at identical Pc/MR/ε.

    Source: RocketCEA QuickStart published table + direct CEA_Obj call.
    https://rocketcea.readthedocs.io/en/latest/quickstart.html
    """
    from rocketcea.cea_obj import CEA_Obj

    cea = CEA_Obj(oxName="LOX", fuelName="LH2")
    for mr in (2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0):
        isp_rc = float(cea.get_Isp(Pc=100.0, MR=mr, eps=40.0))
        r = Mixture("LH2", "LOX", apply_cryo_defaults=False, cache_enabled=False).evaluate(
            of=mr, pc_pa=psi_to_pa(100.0), eps=40.0
        )
        assert r.isp_vac_shifting == pytest.approx(isp_rc, rel=1e-12)


def test_bit_level_match_rp1_and_ch4() -> None:
    from rocketcea.cea_obj import CEA_Obj

    for fuel, ox, mr, pc_bar, eps in [
        ("RP1", "LOX", 2.56, 70.0, 20.0),
        ("CH4", "LOX", 3.2, 68.94757293168, 40.0),  # 1000 psia
        ("MMH", "N2O4", 2.0, 68.94757293168, 40.0),
    ]:
        cea = CEA_Obj(oxName=ox, fuelName=fuel)
        pc_psia = pc_bar * 14.503773773  # bar → psia (consistent with units.PSIA_PER_BAR)
        from propwrap.units import bar_to_psia

        pc_psia = bar_to_psia(pc_bar)
        isp_rc = float(cea.get_Isp(Pc=pc_psia, MR=mr, eps=eps))
        r = Mixture(fuel, ox, apply_cryo_defaults=False, cache_enabled=False).evaluate(
            of=mr, pc_bar=pc_bar, eps=eps
        )
        assert r.isp_vac_shifting == pytest.approx(isp_rc, abs=1e-6)


def test_cstar_si_not_english() -> None:
    """c* for LOX/RP-1 must be ~1800 m/s, never ~5900 ft/s."""
    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    assert 1500 < r.c_star < 2200
    assert r.tc_kelvin < 5000  # not Rankine ~6600


def test_gamma_and_temp_returns_chamber_and_exit() -> None:
    from propwrap import cea_backend

    g, te, tc = cea_backend.gamma_and_temp_at_eps(
        "RP1", "LOX", 2.56, bar_to_pa(70), 20.0, frozen=True
    )
    assert te < tc
    assert 1.05 < g < 1.5


def test_bulk_density_and_density_impulse_positive() -> None:
    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    assert r.bulk_density_kg_m3 is not None and r.bulk_density_kg_m3 > 800
    assert r.density_impulse_vac_shifting == pytest.approx(
        r.isp_vac_shifting * r.bulk_density_kg_m3, rel=1e-12
    )


def test_standard_g0_value() -> None:
    """g0 must remain standard gravity 9.80665 m/s² (CGPM / BIPM convention)."""
    assert G0 == 9.80665
