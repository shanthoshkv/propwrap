"""Propellant-system trades: optimum O/F comparison and density-Isp curves (SI)."""

from __future__ import annotations

from typing import Sequence

from propwrap.models import DensityIspCurve, DensityIspPoint, TradeResult, TradeRow
from propwrap.propellant import Propellant
from propwrap.propellant_library import bulk_density_kg_m3, stoich_of_ratio
from propwrap.registry import get_propellant
from propwrap.sweeps import expand_range
from propwrap.units import bar_to_pa, density_impulse_si, pa_to_bar


def density_isp_curve(
    fuel: str,
    oxidizer: str,
    of_range: tuple[float, float, float],
    pc_bar: float | None = None,
    eps: float = 40.0,
    *,
    pc_pa: float | None = None,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> DensityIspCurve:
    """Isp_vac, bulk density [kg/m³], density-Isp [s·kg/m³] vs O/F."""
    if pc_pa is None:
        if pc_bar is None:
            raise ValueError("pc_pa or pc_bar required")
        pc_pa = bar_to_pa(pc_bar)
    p = Propellant(
        fuel,
        oxidizer,
        cache_enabled=cache_enabled,
        apply_cryo_defaults=apply_cryo_defaults,
    )
    values = expand_range(of_range)
    points: list[DensityIspPoint] = []
    for of in values:
        r = p.performance(of, pa_to_bar(pc_pa), eps)
        rho, basis = bulk_density_kg_m3(p.fuel, p.oxidizer, of)
        dens_isp = density_impulse_si(r.isp_vac_shifting, rho) if rho is not None else None
        points.append(
            DensityIspPoint(
                of_ratio=of,
                isp_vac_shifting=r.isp_vac_shifting,
                bulk_density_kg_m3=rho,
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
        pc_pa=pc_pa,
        eps=eps,
        points=points,
        optimum_isp_of=best_isp.of_ratio,
        optimum_density_isp_of=best_dens.of_ratio if best_dens else None,
        stoich_of_ratio=stoich,
        density_basis=_basis_note(p.fuel, p.oxidizer),
    )


def _basis_note(fuel: str, oxidizer: str) -> str:
    rf = get_propellant(fuel)
    ro = get_propellant(oxidizer)
    parts = []
    if rf and rf.density_kg_m3:
        parts.append(f"{fuel} ρ={rf.density_kg_m3:.1f}")
    if ro and ro.density_kg_m3:
        parts.append(f"{oxidizer} ρ={ro.density_kg_m3:.1f}")
    return " kg/m³; ".join(parts) + " kg/m³ (registry)" if parts else "registry densities"


def trade_at_optimum_of(
    pairs: Sequence[tuple[str, str] | tuple[str, str, tuple[float, float, float]]],
    pc_bar: float | None = None,
    eps: float = 40.0,
    *,
    pc_pa: float | None = None,
    default_of_range: tuple[float, float, float] = (1.5, 4.0, 0.1),
    of_ranges: dict[str, tuple[float, float, float]] | None = None,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> TradeResult:
    if pc_pa is None:
        if pc_bar is None:
            raise ValueError("pc_pa or pc_bar required")
        pc_pa = bar_to_pa(pc_bar)
    pc_bar_v = pa_to_bar(pc_pa)

    of_ranges = of_ranges or {}
    rows: list[TradeRow] = []

    for item in pairs:
        if len(item) == 3:
            fuel, ox, of_range = item[0], item[1], item[2]  # type: ignore[misc]
        else:
            fuel, ox = item[0], item[1]  # type: ignore[misc]
            key = f"{fuel}/{ox}"
            of_range = of_ranges.get(key)
            if of_range is None:
                of_range = _default_range_for(fuel, ox, default_of_range)

        p = Propellant(
            fuel,
            ox,
            cache_enabled=cache_enabled,
            apply_cryo_defaults=apply_cryo_defaults,
        )
        sweep = p.sweep_of_ratio(of_range, pc_bar_v, eps)
        opt = sweep.optimum("isp_vac_shifting")
        dens_curve = density_isp_curve(
            p.fuel,
            p.oxidizer,
            of_range,
            pc_pa=pc_pa,
            eps=eps,
            cache_enabled=cache_enabled,
            apply_cryo_defaults=apply_cryo_defaults,
        )
        best_di = None
        if dens_curve.optimum_density_isp_of is not None:
            best_di = min(
                dens_curve.points,
                key=lambda pt: abs(pt.of_ratio - dens_curve.optimum_density_isp_of),  # type: ignore[arg-type]
            )
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

    by_isp = sorted(rows, key=lambda r: r.performance.isp_vac_shifting, reverse=True)
    by_di = sorted(
        [r for r in rows if r.density_isp_at_isp_opt is not None],
        key=lambda r: r.density_isp_at_isp_opt or 0.0,
        reverse=True,
    )

    return TradeResult(
        pc_pa=pc_pa,
        eps=eps,
        rows=rows,
        ranking_by_isp=[r.label for r in by_isp],
        ranking_by_density_isp=[r.label for r in by_di],
    )


def _default_range_for(
    fuel: str, ox: str, default: tuple[float, float, float]
) -> tuple[float, float, float]:
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
