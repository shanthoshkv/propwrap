"""Propellant-system trades: optimum O/F comparison and density-Isp curves."""

from __future__ import annotations

from typing import Sequence

from propwrap.models import DensityIspCurve, DensityIspPoint, PerformanceResult, TradeResult, TradeRow
from propwrap.propellant import Propellant
from propwrap.propellant_library import bulk_density_g_cm3, stoich_of_ratio
from propwrap.registry import get_propellant
from propwrap.sweeps import expand_range


def density_isp_curve(
    fuel: str,
    oxidizer: str,
    of_range: tuple[float, float, float],
    pc_bar: float,
    eps: float,
    *,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> DensityIspCurve:
    """Isp_vac, bulk density, and density-Isp vs O/F for one propellant pair.

    Density-Isp = Isp_vac_shifting × ρ_bulk [s · g/cm³], with
    ρ_bulk = (r+1) / (r/ρ_ox + 1/ρ_fuel), r = O/F.
    """
    p = Propellant(
        fuel,
        oxidizer,
        cache_enabled=cache_enabled,
        apply_cryo_defaults=apply_cryo_defaults,
    )
    values = expand_range(of_range)
    points: list[DensityIspPoint] = []
    for of in values:
        r = p.performance(of, pc_bar, eps)
        rho, basis = bulk_density_g_cm3(p.fuel, p.oxidizer, of)
        dens_isp = (
            r.isp_vac_shifting * rho if rho is not None else None
        )
        points.append(
            DensityIspPoint(
                of_ratio=of,
                isp_vac_shifting=r.isp_vac_shifting,
                bulk_density_g_cm3=rho,
                density_isp=dens_isp,
                tc_kelvin=r.tc_kelvin,
                c_star=r.c_star,
            )
        )

    best_isp = max(points, key=lambda q: q.isp_vac_shifting)
    dens_pts = [q for q in points if q.density_isp is not None]
    best_dens = max(dens_pts, key=lambda q: q.density_isp or 0.0) if dens_pts else None
    stoich = stoich_of_ratio(p.fuel, p.oxidizer)

    return DensityIspCurve(
        fuel=p.fuel,
        oxidizer=p.oxidizer,
        pc_bar=pc_bar,
        eps=eps,
        points=points,
        optimum_isp_of=best_isp.of_ratio,
        optimum_density_isp_of=best_dens.of_ratio if best_dens else None,
        stoich_of_ratio=stoich,
        density_basis=points[0] and _basis_note(p.fuel, p.oxidizer),
    )


def _basis_note(fuel: str, oxidizer: str) -> str:
    rf = get_propellant(fuel)
    ro = get_propellant(oxidizer)
    parts = []
    if rf and rf.density_g_cm3:
        parts.append(f"{fuel} ρ={rf.density_g_cm3:.4f}")
    if ro and ro.density_g_cm3:
        parts.append(f"{oxidizer} ρ={ro.density_g_cm3:.4f}")
    return " g/cm³; ".join(parts) + " g/cm³ (registry)" if parts else "registry densities"


def trade_at_optimum_of(
    pairs: Sequence[tuple[str, str] | tuple[str, str, tuple[float, float, float]]],
    pc_bar: float,
    eps: float,
    *,
    default_of_range: tuple[float, float, float] = (1.5, 4.0, 0.1),
    of_ranges: dict[str, tuple[float, float, float]] | None = None,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> TradeResult:
    """Compare propellant pairs each at **its own** optimum O/F (max Isp_vac).

    Parameters
    ----------
    pairs :
        ``(fuel, oxidizer)`` or ``(fuel, oxidizer, of_range)``.
    pc_bar, eps :
        Shared thermo boundary conditions for a fair propellant comparison.
    default_of_range :
        Used when a pair does not specify its own O/F grid.
    of_ranges :
        Optional map ``"FUEL/OX" → (start, stop, step)``.

    Notes
    -----
    Comparing all pairs at one fixed O/F is misleading (e.g. O/F=2.5 is poor
    for LOX/LH2). This trade always optimizes mixture ratio per pair.
    """
    of_ranges = of_ranges or {}
    rows: list[TradeRow] = []

    for item in pairs:
        if len(item) == 3:
            fuel, ox, of_range = item[0], item[1], item[2]  # type: ignore[misc]
        else:
            fuel, ox = item[0], item[1]  # type: ignore[misc]
            key = f"{fuel}/{ox}"
            of_range = of_ranges.get(key) or of_ranges.get(
                f"{Propellant(fuel, ox).fuel}/{Propellant(fuel, ox).oxidizer}"
            )
            if of_range is None:
                of_range = _default_range_for(fuel, ox, default_of_range)

        p = Propellant(
            fuel,
            ox,
            cache_enabled=cache_enabled,
            apply_cryo_defaults=apply_cryo_defaults,
        )
        sweep = p.sweep_of_ratio(of_range, pc_bar, eps)
        opt = sweep.optimum("isp_vac_shifting")
        # density-isp at Isp optimum and at density-isp optimum
        dens_curve = density_isp_curve(
            p.fuel,
            p.oxidizer,
            of_range,
            pc_bar,
            eps,
            cache_enabled=cache_enabled,
            apply_cryo_defaults=apply_cryo_defaults,
        )
        best_di = None
        if dens_curve.optimum_density_isp_of is not None:
            best_di = next(
                pt
                for pt in dens_curve.points
                if abs(pt.of_ratio - dens_curve.optimum_density_isp_of) < 1e-9
                or pt.of_ratio == dens_curve.optimum_density_isp_of
            )
        # match opt of on dens curve
        di_at_isp_opt = next(
            (
                pt.density_isp
                for pt in dens_curve.points
                if abs(pt.of_ratio - opt.of_ratio) < 1e-6
            ),
            opt.density_impulse_vac_shifting,
        )
        if di_at_isp_opt is None and dens_curve.points:
            # nearest O/F on curve
            nearest = min(
                dens_curve.points, key=lambda pt: abs(pt.of_ratio - opt.of_ratio)
            )
            di_at_isp_opt = nearest.density_isp

        rows.append(
            TradeRow(
                fuel=p.fuel,
                oxidizer=p.oxidizer,
                of_range=of_range,
                optimum_of=opt.of_ratio,
                performance=opt,
                density_isp_at_isp_opt=di_at_isp_opt,
                optimum_density_isp_of=dens_curve.optimum_density_isp_of,
                density_isp_max=best_di.density_isp if best_di else None,
                stoich_of_ratio=sweep.stoich_of_ratio,
                label=f"{p.fuel}/{p.oxidizer}",
            )
        )

    # ranking
    by_isp = sorted(rows, key=lambda r: r.performance.isp_vac_shifting, reverse=True)
    by_di = sorted(
        [r for r in rows if r.density_isp_at_isp_opt is not None],
        key=lambda r: r.density_isp_at_isp_opt or 0.0,
        reverse=True,
    )

    return TradeResult(
        pc_bar=pc_bar,
        eps=eps,
        rows=rows,
        ranking_by_isp=[r.label for r in by_isp],
        ranking_by_density_isp=[r.label for r in by_di],
    )


def _default_range_for(
    fuel: str, ox: str, default: tuple[float, float, float]
) -> tuple[float, float, float]:
    """Sensible O/F grids by propellant family."""
    f = resolve_family(fuel)
    if f == "LH2":
        return (3.5, 7.0, 0.25)
    if f == "CH4":
        return (2.2, 4.0, 0.1)
    if f in ("MMH", "UDMH", "A50"):
        return (1.4, 2.8, 0.1)
    if f == "Ethanol":
        return (1.0, 2.2, 0.1)
    if f in ("RP1", "JP4", "JP5", "JP10"):
        return (1.8, 3.4, 0.1)
    return default


def resolve_family(fuel: str) -> str:
    from propwrap.registry import resolve_name

    return resolve_name(fuel, kind="fuel")
