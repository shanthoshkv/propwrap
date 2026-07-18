"""SQLite cache hit/miss behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from propwrap.cache import ResultCache
from propwrap.models import PerformanceResult
from propwrap.propellant import Propellant


def _fake_result(**overrides: object) -> PerformanceResult:
    base: dict = dict(
        of_ratio=2.56,
        pc_bar=70.0,
        eps=20.0,
        isp_vac_shifting=340.0,
        isp_vac_frozen=320.0,
        isp_sl_shifting=300.0,
        isp_sl_frozen=280.0,
        c_star=1800.0,
        cf_vac=1.85,
        cf_sl=1.55,
        gamma_chamber=1.14,
        gamma_throat=1.13,
        gamma_exit=1.20,
        mw_chamber=23.0,
        tc_kelvin=3600.0,
        tt_kelvin=3400.0,
        te_kelvin=2000.0,
        fuel="RP1",
        oxidizer="LOX",
    )
    base.update(overrides)
    return PerformanceResult(**base)


def test_second_call_does_not_hit_cea_backend(tmp_path: Path) -> None:
    cache = ResultCache(tmp_path / "cache.db")
    prop = Propellant("RP1", "LOX", cache_enabled=True, cache=cache)

    with patch(
        "propwrap.propellant.cea_backend.compute_performance",
        side_effect=lambda **kw: _fake_result(),
    ) as mock_cea:
        r1 = prop.performance(2.56, 70.0, 20.0)
        r2 = prop.performance(2.56, 70.0, 20.0)
        assert mock_cea.call_count == 1
        assert r1.isp_vac_shifting == r2.isp_vac_shifting


def test_cache_disabled_always_calls_backend(tmp_path: Path) -> None:
    prop = Propellant("RP1", "LOX", cache_enabled=False)
    with patch(
        "propwrap.propellant.cea_backend.compute_performance",
        side_effect=lambda **kw: _fake_result(),
    ) as mock_cea:
        prop.performance(2.56, 70.0, 20.0)
        prop.performance(2.56, 70.0, 20.0)
        assert mock_cea.call_count == 2


def test_different_inputs_miss_cache(tmp_path: Path) -> None:
    cache = ResultCache(tmp_path / "cache.db")
    prop = Propellant("RP1", "LOX", cache_enabled=True, cache=cache)
    with patch(
        "propwrap.propellant.cea_backend.compute_performance",
        side_effect=lambda **kw: _fake_result(of_ratio=kw["of_ratio"]),
    ) as mock_cea:
        prop.performance(2.5, 70.0, 20.0)
        prop.performance(2.6, 70.0, 20.0)
        assert mock_cea.call_count == 2


def test_clear_cache(tmp_path: Path) -> None:
    cache = ResultCache(tmp_path / "cache.db")
    prop = Propellant("RP1", "LOX", cache_enabled=True, cache=cache)
    with patch(
        "propwrap.propellant.cea_backend.compute_performance",
        side_effect=lambda **kw: _fake_result(),
    ) as mock_cea:
        prop.performance(2.56, 70.0, 20.0)
        assert prop.clear_cache() >= 1
        prop.performance(2.56, 70.0, 20.0)
        assert mock_cea.call_count == 2
