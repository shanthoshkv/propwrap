"""Engineering upgrade tests."""

from __future__ import annotations

from propwrap import Propellant, sanity_check


def test_stations_and_pe() -> None:
    r = Propellant("RP-1", "LOX", apply_cryo_defaults=False).performance(
        2.56, 70.0, 20.0
    )
    assert r.chamber is not None and r.exit is not None
    assert r.chamber.cp_j_kg_k > 1000
    assert r.chamber.mu_pa_s > 0
    assert r.pe_pa > 0
    assert r.pc_over_pe > 1
    assert r.density_impulse_vac_shifting is not None
    assert r.bulk_density_kg_m3 is not None and r.bulk_density_kg_m3 > 500
    assert r.ve_vac_shifting > 1000
    assert r.warnings is not None


def test_ambient_altitude() -> None:
    p = Propellant("RP-1", "LOX", apply_cryo_defaults=False)
    vacish = p.ambient_performance(2.56, 70.0, 20.0, pamb_bar=0.01)
    sl = p.ambient_performance(2.56, 70.0, 20.0, pamb_bar=1.01325)
    assert float(vacish["isp_s"]) > float(sl["isp_s"])
    assert "ve_m_s" in vacish


def test_gamma_profile_mw() -> None:
    prof = Propellant("RP-1", "LOX", apply_cryo_defaults=False).gamma_vs_area_ratio(
        2.56, 70.0, (5.0, 20.0, 5.0), use_cantera=False
    )
    assert len(prof.mw) == len(prof.area_ratios)
    assert prof.constant_gamma_equiv is not None
    assert prof.pressure_bar[-1] < prof.pressure_bar[0] or prof.area_ratios[0] <= 1.01


def test_off_design_and_engine_case() -> None:
    p = Propellant("RP-1", "LOX", apply_cryo_defaults=False)
    sw = p.sweep_of_ratio((2.0, 3.0, 0.25), 70.0, 20.0)
    od = sw.off_design(2.0)
    assert "loss_pct" in od
    case = p.engine_case(2.56, 70.0, 20.0, of_range=(2.0, 3.0, 0.5), eps_range=(10.0, 20.0, 10.0))
    assert case.design.isp_vac_shifting > 300
    assert case.of_sweep is not None


def test_eta_delivered() -> None:
    p = Propellant("RP-1", "LOX", apply_cryo_defaults=False, eta_cstar=0.98, eta_cf=0.97)
    r = p.performance(2.56, 70.0, 20.0)
    assert r.isp_vac_delivered is not None
    assert r.isp_vac_delivered < r.isp_vac_shifting


def test_ch4_and_sanity() -> None:
    r = Propellant("CH4", "LOX").performance(3.0, 100.0, 25.0)
    assert r.isp_vac_shifting > 300
    assert r.oxidizer == "LOX"
    w = sanity_check(r)
    assert isinstance(w, list)
