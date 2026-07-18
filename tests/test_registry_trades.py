"""Registry, blends, density-Isp, optimum-O/F trades."""

from __future__ import annotations

from propwrap import (
    Propellant,
    add_blend,
    density_isp_curve,
    get_propellant,
    list_registry,
    trade_at_optimum_of,
)


def test_registry_lookup_and_filter() -> None:
    rp = get_propellant("RP-1")
    assert rp is not None and rp.name == "RP1"
    assert rp.density_g_cm3 is not None
    lox = get_propellant("LOX", kind="oxidizer")
    assert lox is not None and lox.storage == "cryogenic"
    storables = list_registry(storage="storable", kind="fuel")
    names = {r.name for r in storables}
    assert "RP1" in names and "MMH" in names
    assert "LH2" not in names


def test_blend_mmh_udmh() -> None:
    name = add_blend(
        "TestM20",
        [("MMH", 20.0), ("UDMH", 80.0)],
        kind="fuel",
        notes="test blend",
    )
    assert name == "TestM20"
    rec = get_propellant("TestM20")
    assert rec is not None and rec.is_blend
    p = Propellant("TestM20", "N2O4", apply_cryo_defaults=False, cache_enabled=False)
    r = p.performance(2.0, 50.0, 20.0)
    assert r.isp_vac_shifting > 250


def test_density_isp_curve_rp1() -> None:
    curve = density_isp_curve(
        "RP-1",
        "LOX",
        (2.0, 3.0, 0.25),
        pc_bar=70.0,
        eps=20.0,
        apply_cryo_defaults=False,
    )
    assert len(curve.points) >= 4
    assert all(p.bulk_density_g_cm3 and p.bulk_density_g_cm3 > 0.5 for p in curve.points)
    assert all(p.density_isp and p.density_isp > 100 for p in curve.points)
    assert 2.0 <= curve.optimum_isp_of <= 3.0
    # density-Isp optimum may differ slightly from Isp optimum
    assert curve.optimum_density_isp_of is not None


def test_trade_at_own_optimum_of() -> None:
    trade = trade_at_optimum_of(
        [
            ("RP-1", "LOX"),
            ("CH4", "LOX"),
            ("LH2", "LOX"),
            ("MMH", "N2O4"),
        ],
        pc_bar=70.0,
        eps=40.0,
        apply_cryo_defaults=False,
    )
    assert len(trade.rows) == 4
    labels = {r.label for r in trade.rows}
    assert "LH2/LOX" in labels
    # LH2 should rank first on Isp
    assert trade.ranking_by_isp[0] == "LH2/LOX"
    # RP-1 should beat LH2 on density-Isp
    assert "RP1/LOX" in trade.ranking_by_density_isp
    rp_rank = trade.ranking_by_density_isp.index("RP1/LOX")
    lh_rank = trade.ranking_by_density_isp.index("LH2/LOX")
    assert rp_rank < lh_rank
    # each pair has its own optimum O/F (not all identical)
    ofs = {r.optimum_of for r in trade.rows}
    assert len(ofs) >= 3
    text = trade.summary_table()
    assert "Isp_vac" in text and "LH2/LOX" in text


def test_trade_custom_of_range() -> None:
    trade = trade_at_optimum_of(
        [("RP-1", "LOX", (2.2, 2.8, 0.2))],
        pc_bar=50.0,
        eps=20.0,
        apply_cryo_defaults=False,
    )
    assert trade.rows[0].of_range == (2.2, 2.8, 0.2)
    assert 2.2 <= trade.rows[0].optimum_of <= 2.8
