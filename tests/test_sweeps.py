"""Sweep and optimum tests."""

from __future__ import annotations

import pytest

from propwrap import Propellant
from propwrap.sweeps import expand_range


def test_expand_range() -> None:
    vals = expand_range((2.0, 3.0, 0.5))
    assert vals == pytest.approx([2.0, 2.5, 3.0])


def test_expand_range_invalid() -> None:
    with pytest.raises(ValueError):
        expand_range((3.0, 2.0, 0.1))
    with pytest.raises(ValueError):
        expand_range((1.0, 2.0, -0.1))


def test_of_sweep_optimum_in_band() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    sweep = p.sweep_of_ratio((2.0, 3.2, 0.2), pc_bar=70.0, eps=20.0)
    assert sweep.sweep_variable == "of_ratio"
    assert len(sweep.results) == len(sweep.values)
    opt = sweep.optimum("isp_vac_shifting")
    # LOX/RP-1 theoretical optimum O/F typically ~2.3–2.8 at these conditions
    assert 2.0 <= opt.of_ratio <= 3.2
    assert opt.isp_vac_shifting == max(r.isp_vac_shifting for r in sweep.results)


def test_pc_and_eps_sweeps() -> None:
    p = Propellant("RP-1", "LOX", cache_enabled=True)
    sw_pc = p.sweep_pc(of_ratio=2.56, pc_range=(50.0, 90.0, 20.0), eps=20.0)
    assert sw_pc.sweep_variable == "pc_bar"
    assert len(sw_pc.results) >= 2

    sw_eps = p.sweep_eps(of_ratio=2.56, pc_bar=70.0, eps_range=(10.0, 30.0, 10.0))
    assert sw_eps.sweep_variable == "eps"
    # Higher expansion generally raises vacuum Isp
    assert sw_eps.results[-1].isp_vac_shifting >= sw_eps.results[0].isp_vac_shifting
