"""SI unit converters."""

from propwrap.units import (
    G0,
    bar_to_pa,
    convert,
    g_cm3_to_kg_m3,
    isp_s_to_ve_m_s,
    pa_to_bar,
    resolve_pressure_pa,
)


def test_pressure_roundtrip() -> None:
    assert abs(pa_to_bar(bar_to_pa(70)) - 70) < 1e-9
    assert abs(convert(70, "bar", "Pa") - 7e6) < 1e-3
    assert abs(convert(7, "MPa", "bar") - 70) < 1e-9


def test_density() -> None:
    assert abs(g_cm3_to_kg_m3(0.81) - 810) < 1e-9
    assert abs(convert(810, "kg/m3", "g/cm3") - 0.81) < 1e-9


def test_isp_to_ve() -> None:
    assert abs(isp_s_to_ve_m_s(100) - 100 * G0) < 1e-9
    assert abs(convert(100, "s", "m/s") - 100 * G0) < 1e-6


def test_resolve_pressure() -> None:
    assert resolve_pressure_pa(pc_bar=70) == bar_to_pa(70)
    assert resolve_pressure_pa(pc_mpa=7) == 7e6
    assert resolve_pressure_pa(pc=5e6) == 5e6


def test_performance_si_fields() -> None:
    from propwrap import Mixture

    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    assert abs(r.pc_pa - 7e6) < 1
    assert r.bulk_density_kg_m3 is not None and r.bulk_density_kg_m3 > 500
    assert r.ve_vac_shifting > 1000
    assert r.chamber is not None and r.chamber.pressure_pa > 1e6
