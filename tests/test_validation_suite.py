"""Comprehensive validation suite for propwrap trustworthiness.

Sources are documented in tests/data/validation_catalog.json and
docs/validation.md. Do not invent literature numbers — only catalogued
references and physical inequalities live here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from propwrap import Propellant

CATALOG_PATH = Path(__file__).parent / "data" / "validation_catalog.json"
PSIA_PER_BAR = 14.5037738


@pytest.fixture(scope="module")
def catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _rel_err(value: float, ref: float) -> float:
    return abs(value - ref) / abs(ref)


def _run(
    fuel: str,
    ox: str,
    of_ratio: float,
    pc_bar: float,
    eps: float,
) -> object:
    return Propellant(
        fuel, ox, apply_cryo_defaults=False, cache_enabled=True
    ).performance(of_ratio, pc_bar, eps)


# ---------------------------------------------------------------------------
# A. RocketCEA documentation golden values (highest trust)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "case_id",
    [
        "RC-DOC-DEFAULT-LH2",
        "RC-DOC-LH2-MR2",
        "RC-DOC-LH2-MR3",
        "RC-DOC-LH2-MR4",
        "RC-DOC-LH2-MR5",
        "RC-DOC-LH2-MR6",
        "RC-DOC-LH2-MR7",
        "RC-DOC-LH2-MR8",
    ],
)
def test_rocketcea_docs_golden_isp(catalog: dict, case_id: str) -> None:
    """Exact published RocketCEA QuickStart numbers (≤0.1% rel)."""
    case = next(c for c in catalog["rocketcea_docs_golden"] if c["id"] == case_id)
    pc_bar = case["pc_psia"] / PSIA_PER_BAR
    r = _run(case["fuel"], case["oxidizer"], case["of_ratio"], pc_bar, case["eps"])
    val = float(getattr(r, case["metric"]))
    err = _rel_err(val, case["reference"])
    assert err <= case["tolerance_rel"], (
        f"{case_id}: got {val:.6f}, ref {case['reference']:.6f}, "
        f"rel_err={err:.4e}; source={case['citation']}"
    )


def test_rocketcea_lh2_of_curve_shape(catalog: dict) -> None:
    """Published LH2 series: peak near O/F 4–5, falls at lean/rich extremes."""
    cases = {
        c["of_ratio"]: c["reference"]
        for c in catalog["rocketcea_docs_golden"]
        if c["id"].startswith("RC-DOC-LH2-MR")
    }
    assert cases[5.0] >= cases[4.0]
    assert cases[5.0] > cases[6.0]
    assert cases[5.0] > cases[2.0]
    assert cases[5.0] > cases[8.0]
    # propwrap reproduces the same shape
    pc = 100.0 / PSIA_PER_BAR
    isps = {
        mr: _run("LH2", "LOX", mr, pc, 40.0).isp_vac_shifting  # type: ignore[attr-defined]
        for mr in (2.0, 4.0, 5.0, 6.0, 8.0)
    }
    assert isps[5.0] == max(isps.values())


# ---------------------------------------------------------------------------
# B. Multi-propellant regression + literature bands
# ---------------------------------------------------------------------------


def _regression_cases(catalog: dict) -> list[dict]:
    return catalog["standard_condition_regression"]


@pytest.mark.parametrize("case_id", [
    "REG-RP1-LOX-1000psia-eps40",
    "REG-RP1-LOX-70bar-eps20",
    "REG-LH2-LOX-1000psia-eps40-OF5",
    "REG-LH2-LOX-RS25-class",
    "REG-CH4-LOX-1000psia-eps40-OF3.2",
    "REG-CH4-LOX-100bar-eps35",
    "REG-MMH-N2O4-1000psia-eps40",
    "REG-MMH-N2O4-OF2.2",
    "REG-UDMH-N2O4",
    "REG-A50-N2O4",
    "REG-ETHANOL-LOX",
    "REG-MMH-N2O4-lowP",
])
def test_regression_isp_and_units(catalog: dict, case_id: str) -> None:
    case = next(c for c in _regression_cases(catalog) if c["id"] == case_id)
    r = _run(case["fuel"], case["oxidizer"], case["of_ratio"], case["pc_bar"], case["eps"])
    assert _rel_err(r.isp_vac_shifting, case["isp_vac_shifting"]) <= case["tolerance_rel"]  # type: ignore[attr-defined]
    if "isp_vac_frozen" in case:
        assert _rel_err(r.isp_vac_frozen, case["isp_vac_frozen"]) <= case["tolerance_rel"] + 0.01  # type: ignore[attr-defined]
    if "c_star_m_s" in case:
        assert _rel_err(r.c_star, case["c_star_m_s"]) <= 0.03  # type: ignore[attr-defined]
        assert 1000 < r.c_star < 3500  # type: ignore[attr-defined]
    if "tc_k" in case:
        assert _rel_err(r.tc_kelvin, case["tc_k"]) <= 0.03  # type: ignore[attr-defined]
        assert 1500 < r.tc_kelvin < 4500  # type: ignore[attr-defined]
    if "literature_band_s" in case:
        lo, hi = case["literature_band_s"]
        assert lo <= r.isp_vac_shifting <= hi, (  # type: ignore[attr-defined]
            f"{case_id} Isp={r.isp_vac_shifting:.1f} outside literature band [{lo},{hi}]"  # type: ignore[attr-defined]
        )


# ---------------------------------------------------------------------------
# C. Physical consistency across many combos
# ---------------------------------------------------------------------------

PHYS_CASES = [
    ("RP1", "LOX", 2.3, 70.0, 20.0),
    ("RP1", "LOX", 2.56, 70.0, 40.0),
    ("LH2", "LOX", 5.0, 70.0, 40.0),
    ("LH2", "LOX", 6.0, 100.0, 69.0),
    ("CH4", "LOX", 3.0, 70.0, 40.0),
    ("CH4", "LOX", 3.5, 100.0, 25.0),
    ("MMH", "N2O4", 2.0, 70.0, 40.0),
    ("MMH", "N2O4", 2.2, 20.0, 60.0),
    ("UDMH", "N2O4", 2.6, 70.0, 40.0),
    ("A50", "N2O4", 2.0, 50.0, 30.0),
    ("Ethanol", "LOX", 1.5, 50.0, 20.0),
]


@pytest.mark.parametrize("fuel,ox,of_ratio,pc,eps", PHYS_CASES)
def test_physics_invariants(
    fuel: str, ox: str, of_ratio: float, pc: float, eps: float
) -> None:
    r = _run(fuel, ox, of_ratio, pc, eps)
    assert r.isp_vac_shifting >= r.isp_vac_frozen - 1e-6  # type: ignore[attr-defined]
    assert r.isp_vac_shifting >= r.isp_sl_shifting - 1e-6  # type: ignore[attr-defined]
    assert r.gamma_exit + 1e-6 >= r.gamma_chamber  # type: ignore[attr-defined]
    assert r.te_kelvin < r.tt_kelvin < r.tc_kelvin  # type: ignore[attr-defined]
    assert 1.05 < r.gamma_chamber < 1.45  # type: ignore[attr-defined]
    assert 1.05 < r.gamma_exit < 1.55  # type: ignore[attr-defined]
    assert r.pe_bar > 0 and r.pc_over_pe > 1  # type: ignore[attr-defined]
    assert r.chamber is not None and r.chamber.cp_j_kg_k > 500  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# D. Trend tests (engineering trust)
# ---------------------------------------------------------------------------


def test_propellant_ranking_vac_isp(catalog: dict) -> None:
    """LH2 > CH4 > RP1 > MMH/NTO at comparable Pc/ε (theoretical)."""
    rank = catalog["trend_expectations"]["propellant_rank_vac_isp"]["ordered_high_to_low"]
    pc, eps = 68.95, 40.0
    isps = [_run(f, o, of, pc, eps).isp_vac_shifting for f, o, of in rank]  # type: ignore[attr-defined]
    for a, b in zip(isps, isps[1:]):
        assert a > b, f"ranking broken: {isps}"


def test_higher_eps_raises_vac_isp(catalog: dict) -> None:
    t = catalog["trend_expectations"]["eps_increases_isp_vac"]
    lo = _run(t["fuel"], t["oxidizer"], t["of_ratio"], t["pc_bar"], t["eps_low"])
    hi = _run(t["fuel"], t["oxidizer"], t["of_ratio"], t["pc_bar"], t["eps_high"])
    assert hi.isp_vac_shifting > lo.isp_vac_shifting  # type: ignore[attr-defined]


def test_higher_pc_mild_isp_gain_rp1() -> None:
    low = _run("RP1", "LOX", 2.5, 40.0, 20.0)
    high = _run("RP1", "LOX", 2.5, 100.0, 20.0)
    assert high.isp_vac_shifting >= low.isp_vac_shifting - 0.5  # type: ignore[attr-defined]
    assert high.tc_kelvin >= low.tc_kelvin - 5.0  # type: ignore[attr-defined]


def test_of_sweep_has_interior_peak_rp1() -> None:
    p = Propellant("RP1", "LOX", apply_cryo_defaults=False, cache_enabled=True)
    sw = p.sweep_of_ratio((1.8, 3.4, 0.2), pc_bar=70.0, eps=20.0)
    opt = sw.optimum()
    assert 2.0 < opt.of_ratio < 3.2
    assert opt.of_ratio not in (sw.values[0], sw.values[-1]) or len(sw.values) < 3


def test_of_sweep_has_interior_peak_ch4() -> None:
    p = Propellant("CH4", "LOX", apply_cryo_defaults=False, cache_enabled=True)
    sw = p.sweep_of_ratio((2.2, 4.0, 0.2), pc_bar=70.0, eps=40.0)
    opt = sw.optimum()
    assert 2.4 < opt.of_ratio < 3.8


def test_ambient_isp_monotone_with_pamb() -> None:
    p = Propellant("RP1", "LOX", apply_cryo_defaults=False, cache_enabled=True)
    isps = [
        float(p.ambient_performance(2.5, 70.0, 20.0, pamb_bar=pb)["isp_s"])
        for pb in (0.01, 0.2, 1.01325)
    ]
    assert isps[0] > isps[1] > isps[2]


# ---------------------------------------------------------------------------
# E. Unit / SI leakage guards (many propellants)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fuel,ox,of_ratio,pc,eps", PHYS_CASES)
def test_no_english_unit_leak(
    fuel: str, ox: str, of_ratio: float, pc: float, eps: float
) -> None:
    r = _run(fuel, ox, of_ratio, pc, eps)
    # English leaks: c*~5900 ft/s, Tc~6600 R
    assert r.c_star < 4000  # type: ignore[attr-defined]
    assert r.tc_kelvin < 5000  # type: ignore[attr-defined]
    assert r.isp_vac_shifting < 600  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# F. Cantera cross-validation bands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fuel,ox,of_ratio,pc",
    [
        ("RP1", "LOX", 2.56, 70.0),
        ("LH2", "LOX", 5.0, 70.0),
        ("CH4", "LOX", 3.2, 70.0),
        ("MMH", "N2O4", 2.0, 50.0),
    ],
)
def test_cea_cantera_gamma_documented_band(
    fuel: str, ox: str, of_ratio: float, pc: float
) -> None:
    """Chamber γ CEA vs Cantera; allow species-set mismatch up to 25%."""
    rows = Propellant(fuel, ox, apply_cryo_defaults=False, cache_enabled=True).cross_validate(
        of_ratio, pc, 20.0, tolerance_pct=15.0
    )
    g = next(x for x in rows if x.parameter == "gamma_chamber")
    assert g.cea_value > 1.0 and g.cantera_value > 1.0
    assert g.percent_diff < 25.0, (
        f"{fuel}/{ox}: γ divergence {g.percent_diff:.1f}% "
        f"(cea={g.cea_value:.4f}, cantera={g.cantera_value:.4f})"
    )


# ---------------------------------------------------------------------------
# G. Density impulse sanity (handbook liquid densities)
# ---------------------------------------------------------------------------


def test_density_impulse_ordering() -> None:
    """RP-1 density-Isp should beat LH2 density-Isp despite lower Isp."""
    rp = _run("RP1", "LOX", 2.3, 70.0, 40.0)
    lh = _run("LH2", "LOX", 5.0, 70.0, 40.0)
    assert rp.density_impulse_vac_shifting is not None  # type: ignore[attr-defined]
    assert lh.density_impulse_vac_shifting is not None  # type: ignore[attr-defined]
    assert rp.isp_vac_shifting < lh.isp_vac_shifting  # type: ignore[attr-defined]
    assert rp.density_impulse_vac_shifting > lh.density_impulse_vac_shifting  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# H. Catalog integrity
# ---------------------------------------------------------------------------


def test_catalog_has_minimum_coverage(catalog: dict) -> None:
    assert len(catalog["rocketcea_docs_golden"]) >= 8
    assert len(catalog["standard_condition_regression"]) >= 10
    fuels = {c["fuel"] for c in catalog["standard_condition_regression"]}
    assert {"RP1", "LH2", "CH4", "MMH"}.issubset(fuels)
