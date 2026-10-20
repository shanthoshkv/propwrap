"""Engine helpers, CLI additions and a golden-image check for the plot theme."""

from __future__ import annotations

from pathlib import Path

import pytest

from propwrap import Mixture, altitude_performance, throttle, us1976_pressure
from propwrap.cli import main

BASELINE = Path(__file__).parent / "baseline"


def test_us1976_pressure() -> None:
    assert us1976_pressure(0) == pytest.approx(101325.0)
    assert us1976_pressure(11000) == pytest.approx(22700, rel=0.01)
    assert us1976_pressure(30000) == pytest.approx(1197, rel=0.01)
    assert us1976_pressure(100000) == 0.0


def test_size_and_throttle() -> None:
    m = Mixture("RP-1", "LOX", cache_enabled=False)
    r = m.evaluate(of=2.56, pc_bar=70, eps=20, full=False)
    sz = r.size(1e6, sea_level=True)
    # At = mdot·c*/Pc and F = mdot·Isp·g0 must close
    assert sz["throat_area_m2"] == pytest.approx(sz["mdot_kg_s"] * r.c_star / r.pc_pa)
    assert sz["mdot_ox_kg_s"] + sz["mdot_fuel_kg_s"] == pytest.approx(sz["mdot_kg_s"])
    rows = throttle(m, 2.56, 70e5, 20, 1e6, fractions=(1.0, 0.5))
    assert rows[0]["thrust_n"] == pytest.approx(1e6, rel=0.01)
    assert rows[1]["thrust_n"] < rows[0]["thrust_n"]
    alt = altitude_performance(m, 2.56, 70e5, 20, [0, 20000])
    assert alt[1]["isp_s"] > alt[0]["isp_s"]


def test_cli_new_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["info", "CH4"]) == 0
    assert "stoich" in capsys.readouterr().out
    cfg = tmp_path / "case.toml"
    cfg.write_text("of = 2.56\npc_bar = 70\neps = 20\nthrust = 1e5\n", encoding="utf-8")
    assert main(["--config", str(cfg), "run", "RP-1", "LOX", "--of", "2.56"]) == 0
    assert "sizing" in capsys.readouterr().out


def test_plot_golden_image(tmp_path: Path) -> None:
    from matplotlib.testing.compare import compare_images

    from propwrap.plotting import plot_altitude

    rows = [{"altitude_m": h * 1e3, "isp_s": 290 + h, "pamb_pa": 101325 * 0.88**h} for h in range(0, 40, 5)]
    out = tmp_path / "alt.png"
    plot_altitude(rows, save_path=str(out))  # type: ignore[arg-type]
    ref = BASELINE / "altitude.png"
    if not ref.exists():
        BASELINE.mkdir(exist_ok=True)
        ref.write_bytes(out.read_bytes())
        pytest.skip("baseline image created; commit tests/baseline/altitude.png")
    # tolerance absorbs font rasterisation differences between OSes
    assert compare_images(str(ref), str(out), tol=20) is None
