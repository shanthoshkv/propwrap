"""Smoke tests for plotting and export."""

from __future__ import annotations

from pathlib import Path

from propwrap import Propellant
from propwrap.export import performance_to_csv, performance_to_json, sweep_to_csv
from propwrap.plotting import plot_of_sweep, plot_propellant_comparison
from propwrap.propellant_library import add_custom_propellant, clear_custom_propellants


def test_export_json_csv(tmp_path: Path) -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    r = p.performance(2.56, 70.0, 20.0)
    jp = tmp_path / "r.json"
    cp = tmp_path / "r.csv"
    performance_to_json(r, jp)
    performance_to_csv(r, cp)
    assert jp.read_text(encoding="utf-8")
    assert "isp_vac_shifting" in cp.read_text(encoding="utf-8")


def test_plot_of_sweep_saves(tmp_path: Path) -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    sweep = p.sweep_of_ratio((2.2, 2.8, 0.3), pc_bar=70.0, eps=20.0)
    out = tmp_path / "of.png"
    fig = plot_of_sweep(sweep, save_path=str(out))
    assert out.exists() and out.stat().st_size > 0
    assert fig is not None


def test_plot_comparison(tmp_path: Path) -> None:
    combos = [("RP-1", "LOX"), ("LH2", "LOX")]
    results = []
    labels = []
    for fuel, ox in combos:
        r = Propellant(fuel, ox, cache_enabled=True).performance(2.5, 70.0, 20.0)
        results.append(r)
        labels.append(f"{fuel}/{ox}")
    out = tmp_path / "cmp.png"
    plot_propellant_comparison(results, labels, save_path=str(out))
    assert out.exists()


def test_custom_propellant_registration() -> None:
    clear_custom_propellants()
    # Simplified kerosene-like C12H24 with approximate Hf (cal/mol)
    card = add_custom_propellant(
        name="TestKero",
        formula="C12H24",
        heat_of_formation=-82_000.0,
        kind="fuel",
        temperature_k=298.15,
        comment="test kerosene blend",
    )
    assert "TestKero" in card
    assert "C 12 H 24" in card
    # Running CEA with custom fuel may work if RocketCEA accepts the card
    try:
        p = Propellant("TestKero", "LOX", cache_enabled=False)
        r = p.performance(of_ratio=2.5, pc_bar=50.0, eps=10.0)
        assert r.isp_vac_shifting > 100.0
    finally:
        clear_custom_propellants()
