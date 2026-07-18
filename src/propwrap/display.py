"""Human-readable summaries for result models."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from propwrap.models import (
        DensityIspCurve,
        GammaProfile,
        PerformanceResult,
        SweepResult,
        TradeResult,
    )


def performance_summary(r: PerformanceResult, *, frozen: bool = False) -> str:
    isp = r.isp_vac_frozen if frozen else r.isp_vac_shifting
    mode = "frozen" if frozen else "shifting"
    lines = [
        f"{r.fuel}/{r.oxidizer}  O/F={r.of_ratio:g}  Pc={r.pc_bar:g} bar  ε={r.eps:g}",
        f"Isp_vac  {isp:.1f} s ({mode})   Isp_sl  {r.isp_sl_shifting:.1f} s",
        f"c*       {r.c_star:.0f} m/s      Tc  {r.tc_kelvin:.0f} K",
        f"γ_ch     {r.gamma_chamber:.4f}     γ_ex {r.gamma_exit:.4f}     Pe {r.pe_bar:.4g} bar",
    ]
    if r.density_impulse_vac_shifting is not None:
        lines.append(
            f"ρ·Isp    {r.density_impulse_vac_shifting:.1f} s·g/cm³"
            + (f"  (ρ={r.bulk_density_g_cm3:.3f} g/cm³)" if r.bulk_density_g_cm3 else "")
        )
    if r.isp_vac_delivered is not None:
        lines.append(
            f"delivered Isp_vac {r.isp_vac_delivered:.1f} s  "
            f"(ηc*={r.eta_cstar}, ηCf={r.eta_cf})"
        )
    if r.warnings:
        lines.append(f"warnings ({len(r.warnings)}):")
        for w in r.warnings[:5]:
            lines.append(f"  - {w}")
        if len(r.warnings) > 5:
            lines.append(f"  … +{len(r.warnings) - 5} more")
    if r.from_cache:
        lines.append("(from cache)")
    return "\n".join(lines)


def sweep_summary(s: SweepResult) -> str:
    opt = s.optimum()
    var = s.sweep_variable
    val = getattr(opt, var)
    lines = [
        f"Sweep {var}: n={len(s.values)}",
        f"Optimum: {var}={val:g}  Isp_vac={opt.isp_vac_shifting:.1f} s  "
        f"Tc={opt.tc_kelvin:.0f} K",
    ]
    if s.stoich_of_ratio is not None:
        lines.append(f"Stoich O/F ≈ {s.stoich_of_ratio:.3f}")
    return "\n".join(lines)


def density_isp_summary(c: DensityIspCurve) -> str:
    lines = [
        f"Density-Isp: {c.fuel}/{c.oxidizer}  Pc={c.pc_bar:g} bar  ε={c.eps:g}",
        f"Isp-optimum O/F = {c.optimum_isp_of:.3f}",
        f"ρ·Isp-optimum O/F = {c.optimum_density_isp_of}",
    ]
    if c.density_basis:
        lines.append(f"Density basis: {c.density_basis}")
    return "\n".join(lines)


def gamma_summary(g: GammaProfile) -> str:
    return (
        f"Product γ profile ({g.source}): n={len(g.area_ratios)}  "
        f"ε={g.area_ratios[0]:g}→{g.area_ratios[-1]:g}  "
        f"γ={g.gamma_cea[0]:.4f}→{g.gamma_cea[-1]:.4f}"
        + (
            f"  γ_const≈{g.constant_gamma_equiv:.4f}"
            if g.constant_gamma_equiv
            else ""
        )
    )


def maybe_show(fig: Any, show: bool) -> Any:
    if show:
        import matplotlib.pyplot as plt

        plt.show()
    return fig


def maybe_close(fig: Any, show: bool) -> None:
    if not show:
        import matplotlib.pyplot as plt

        plt.close(fig)
