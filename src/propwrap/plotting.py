"""Dark-themed publication-quality plots for propwrap sweeps and profiles."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Sequence

from propwrap.errors import require

# Headless-friendly default (lab servers, CI, broken Tk installs)
matplotlib = require("matplotlib", "plot")

if os.environ.get("MPLBACKEND") is None:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from propwrap.models import DensityIspCurve, GammaProfile, PerformanceResult, SweepResult

# Design system
BG = "#0a0a0a"
FG = "#e0e0e0"
GRID = "#2a2a2a"
ACCENT = "#5b8dee"
SECONDARY = "#d4924a"  # amber-copper
SPINE = "#333333"
MUTED = "#888888"
PALETTE = [ACCENT, SECONDARY, "#7dcea0", "#c678dd", "#e06c75", "#56b6c2", "#e5c07b"]

THEMES = {
    "dark": {"BG": "#0a0a0a", "FG": "#e0e0e0", "GRID": "#2a2a2a", "SPINE": "#333333"},
    "light": {"BG": "#ffffff", "FG": "#1a1a1a", "GRID": "#d9d9d9", "SPINE": "#888888"},
}


def set_theme(name: str = "dark") -> None:
    """Switch plot palette: ``"dark"`` (screen) or ``"light"`` (print/LaTeX)."""
    globals().update(THEMES[name])


@lru_cache(maxsize=None)
def _resolve_font(preferred: Sequence[str], fallback: str) -> str:
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in available:
            return name
    return fallback


def apply_dark_theme(fig: Figure | None = None, ax: Axes | None = None) -> None:
    """Apply the suite dark theme to a figure/axes (or rcParams globally)."""
    mono = _resolve_font(("DM Mono", "DejaVu Sans Mono", "Consolas"), "DejaVu Sans Mono")
    sans = _resolve_font(("DM Sans", "DejaVu Sans", "Arial"), "DejaVu Sans")

    if fig is None and ax is None:
        plt.rcParams.update(
            {
                "figure.facecolor": BG,
                "axes.facecolor": BG,
                "axes.edgecolor": SPINE,
                "axes.labelcolor": FG,
                "text.color": FG,
                "xtick.color": FG,
                "ytick.color": FG,
                "grid.color": GRID,
                "grid.alpha": 0.45,
                "font.family": sans,
            }
        )
        plt.rcParams["font.monospace"] = [mono]
        return

    targets = []
    if ax is not None:
        targets.append(ax)
    if fig is not None:
        fig.patch.set_facecolor(BG)
        targets.extend(fig.axes)

    for a in targets:
        a.set_facecolor(BG)
        a.tick_params(colors=FG, labelsize=9)
        a.xaxis.label.set_color(FG)
        a.yaxis.label.set_color(FG)
        a.title.set_color(FG)
        for spine in a.spines.values():
            spine.set_color(SPINE)
        a.grid(True, color=GRID, alpha=0.45, linewidth=0.6)
        # monospace tick labels when possible
        for label in list(a.get_xticklabels()) + list(a.get_yticklabels()):
            label.set_fontfamily(mono)


def _save(fig: Figure, save_path: str | None) -> Figure:
    if save_path:
        # format follows extension: .pdf/.svg stay vector for LaTeX
        fig.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight")
    return fig


def _legend(*axes: Axes) -> None:
    """One legend on the first axes, collecting handles from twin axes too."""
    handles, labels = [], []
    for a in axes:
        h, lab = a.get_legend_handles_labels()
        handles += h
        labels += lab
    if handles:
        axes[0].legend(handles, labels, loc="best", framealpha=0.9, fontsize=8)


def _annotate_optimum(
    ax: Axes,
    x: float,
    y: float,
    label: str,
) -> None:
    ax.scatter([x], [y], color=SECONDARY, s=60, zorder=5, edgecolors="white", linewidths=0.6)
    ax.annotate(
        label,
        xy=(x, y),
        xytext=(12, -30),
        textcoords="offset points",
        color=SECONDARY,
        fontsize=8,
        bbox={"boxstyle": "round,pad=0.3", "fc": BG, "ec": SECONDARY, "lw": 0.6},
        arrowprops={"arrowstyle": "-", "color": SECONDARY, "lw": 0.6},
        fontfamily=_resolve_font(("DM Mono", "DejaVu Sans Mono"), "DejaVu Sans Mono"),
    )


def plot_of_sweep(
    sweep_result: SweepResult,
    *,
    save_path: str | None = None,
) -> Figure:
    """Isp (vac, shifting) & Tc vs O/F — dual y-axis banana curve."""
    if sweep_result.sweep_variable != "of_ratio":
        raise ValueError("plot_of_sweep requires sweep_variable='of_ratio'")

    xs = sweep_result.values
    rs = sweep_result.results
    isp = [r.isp_vac_shifting for r in rs]
    isp_f = [r.isp_vac_frozen for r in rs]
    tc = [r.tc_kelvin for r in rs]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax1)
    ax1.plot(xs, isp, color=ACCENT, lw=2.0, label="Isp vac (shifting)")
    ax1.plot(xs, isp_f, color=ACCENT, lw=1.2, ls="--", label="Isp vac (frozen)")
    ax1.fill_between(xs, isp_f, isp, color=ACCENT, alpha=0.12)
    ax1.plot(xs, [r.isp_sl_shifting for r in rs], color="#7dcea0", lw=1.2, label="Isp SL (shifting)")
    if rs[0].isp_vac_delivered is not None:
        ax1.plot(
            xs, [r.isp_vac_delivered or float("nan") for r in rs], color=FG, lw=1.0, ls="-.", label="Isp vac delivered (η)"
        )
    ax1.set_xlabel("O/F mass ratio [-]")
    ax1.set_ylabel("Isp [s]", color=ACCENT)
    ax1.tick_params(axis="y", labelcolor=ACCENT)

    ax2 = ax1.twinx()
    apply_dark_theme(fig, ax2)
    ax2.plot(xs, tc, color=SECONDARY, lw=1.5, ls="--", label="Tc")
    ax2.set_ylabel("Chamber temperature [K]", color=SECONDARY)
    ax2.tick_params(axis="y", labelcolor=SECONDARY)

    opt = sweep_result.optimum("isp_vac_shifting")
    _annotate_optimum(
        ax1,
        opt.of_ratio,
        opt.isp_vac_shifting,
        f"opt O/F={opt.of_ratio:.2f}\nIsp={opt.isp_vac_shifting:.1f}s",
    )
    if sweep_result.stoich_of_ratio is not None:
        ax1.axvline(
            sweep_result.stoich_of_ratio,
            color=MUTED,
            ls=":",
            lw=1.0,
            label=f"stoich O/F={sweep_result.stoich_of_ratio:.2f}",
        )
    _legend(ax1, ax2)
    ax1.set_title("O/F sweep — Isp (shifting vs frozen) & chamber temperature")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_pc_sweep(
    sweep_result: SweepResult,
    *,
    save_path: str | None = None,
) -> Figure:
    """Isp vs chamber pressure."""
    if sweep_result.sweep_variable != "pc_pa":
        raise ValueError("plot_pc_sweep requires sweep_variable='pc_pa'")

    from propwrap.units import pa_to_mpa

    xs = [pa_to_mpa(v) for v in sweep_result.values]
    isp = [r.isp_vac_shifting for r in sweep_result.results]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.plot(xs, isp, color=ACCENT, lw=2.0)
    ax.set_xlabel("Chamber pressure [MPa]")
    ax.set_ylabel("Isp vacuum [s]")
    opt = sweep_result.optimum("isp_vac_shifting")
    _annotate_optimum(
        ax,
        pa_to_mpa(opt.pc_pa),
        opt.isp_vac_shifting,
        f"opt Pc={pa_to_mpa(opt.pc_pa):.2f} MPa\nIsp={opt.isp_vac_shifting:.1f}s",
    )
    ax.set_title("Chamber pressure sweep — vacuum Isp")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_eps_sweep(
    sweep_result: SweepResult,
    *,
    save_path: str | None = None,
) -> Figure:
    """Isp vs area ratio."""
    if sweep_result.sweep_variable != "eps":
        raise ValueError("plot_eps_sweep requires sweep_variable='eps'")

    xs = sweep_result.values
    rs = sweep_result.results
    isp = [r.isp_vac_shifting for r in rs]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.plot(xs, isp, color=ACCENT, lw=2.0, label="Isp vac")
    ax.set_xlabel("Area ratio Ae/At [-]")
    ax.set_ylabel("Isp vacuum [s]")
    opt = sweep_result.optimum("isp_vac_shifting")
    _annotate_optimum(
        ax,
        opt.eps,
        opt.isp_vac_shifting,
        f"opt ε={opt.eps:.1f}\nIsp={opt.isp_vac_shifting:.1f}s",
    )

    ax2 = ax.twinx()
    apply_dark_theme(fig, ax2)
    ax2.plot(xs, [r.cf_vac for r in rs], color=SECONDARY, lw=1.4, ls="--", label="Cf vac")
    ax2.plot(xs, [r.cf_sl for r in rs], color="#7dcea0", lw=1.4, ls="--", label="Cf SL")
    ax2.set_ylabel("Cf [-]")

    # Sea-level expansion markers: Pe = Pamb (optimum) and Pe/Pamb = 0.4 (Summerfield)
    pr = [(r.pe_pa or 0.0) / (r.pamb_sl_pa or 101325.0) for r in rs]
    for target, label, ls in ((1.0, "Pe = Pamb (SL)", ":"), (0.4, "Summerfield Pe/Pa=0.4", "-.")):
        for i in range(len(pr) - 1):
            if (pr[i] - target) * (pr[i + 1] - target) <= 0 and pr[i] != pr[i + 1]:
                e = xs[i] + (target - pr[i]) * (xs[i + 1] - xs[i]) / (pr[i + 1] - pr[i])
                ax.axvline(e, color=MUTED, ls=ls, lw=1.0, label=f"{label}: ε={e:.1f}")
                break
    _legend(ax, ax2)
    ax.set_title("Area ratio sweep — vacuum Isp & Cf")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_gamma_profile(
    gamma_profile: GammaProfile,
    *,
    save_path: str | None = None,
) -> Figure:
    """γ vs area ratio, with optional CEA/Cantera overlay and residual panel."""
    g_ct = gamma_profile.gamma_cantera
    has_ct = g_ct is not None
    if g_ct is not None:
        fig, (ax, axr) = plt.subplots(
            2, 1, figsize=(8, 5.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
        )
        apply_dark_theme(fig, axr)
        resid = [c - g for c, g in zip(g_ct, gamma_profile.gamma_cea)]
        axr.plot(gamma_profile.area_ratios, resid, color=SECONDARY, lw=1.2)
        axr.axhline(0.0, color=MUTED, lw=0.8)
        axr.set_ylabel("Δγ (Ct−CEA)")
        axr.set_xlabel("Area ratio Ae/At [-]")
    else:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.plot(
        gamma_profile.area_ratios,
        gamma_profile.gamma_cea,
        color=ACCENT,
        lw=2.0,
        label="CEA",
    )
    if gamma_profile.gamma_cantera is not None:
        ax.plot(
            gamma_profile.area_ratios,
            gamma_profile.gamma_cantera,
            color=SECONDARY,
            lw=1.5,
            ls="--",
            label="Cantera frozen",
        )
    if not has_ct:
        ax.set_xlabel("Area ratio Ae/At [-]")
    ax.set_ylabel("γ [-]")
    ax.set_title(f"γ vs area ratio ({gamma_profile.source})")
    ax.legend(loc="best", framealpha=0.9)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_density_isp(
    curve: "DensityIspCurve",
    *,
    save_path: str | None = None,
) -> Figure:
    """Isp and density-Isp vs O/F (propellant characterization)."""
    xs = [p.of_ratio for p in curve.points]
    isp = [p.isp_vac_shifting for p in curve.points]
    di = [p.density_isp for p in curve.points]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax1)
    ax1.plot(xs, isp, color=ACCENT, lw=2.0, label="Isp vac")
    ax1.set_xlabel("O/F mass ratio [-]")
    ax1.set_ylabel("Isp vacuum [s]", color=ACCENT)
    ax1.axvline(
        curve.optimum_isp_of, color=ACCENT, ls=":", lw=1.0, alpha=0.7,
        label=f"max Isp O/F={curve.optimum_isp_of:.2f}",
    )

    axes = [ax1]
    if any(v is not None for v in di):
        ax2 = ax1.twinx()
        apply_dark_theme(fig, ax2)
        y2 = [v if v is not None else float("nan") for v in di]
        ax2.plot(xs, y2, color=SECONDARY, lw=1.5, ls="--", label="ρ·Isp")
        ax2.set_ylabel("Density-Isp [s·kg/m³]", color=SECONDARY)
        if curve.optimum_density_isp_of is not None:
            ax2.axvline(
                curve.optimum_density_isp_of,
                color=SECONDARY,
                ls=":",
                lw=1.0,
                alpha=0.7,
                label=f"max ρ·Isp O/F={curve.optimum_density_isp_of:.2f}",
            )
        axes.append(ax2)

    if curve.stoich_of_ratio is not None:
        ax1.axvline(
            curve.stoich_of_ratio,
            color=MUTED,
            ls=":",
            lw=1.0,
            label=f"stoich={curve.stoich_of_ratio:.2f}",
        )
    _legend(*axes)
    ax1.set_title(f"Density-Isp: {curve.fuel}/{curve.oxidizer}")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_propellant_comparison(
    results: list[PerformanceResult],
    labels: list[str],
    *,
    save_path: str | None = None,
) -> Figure:
    """Bar chart comparing Isp, Tc across propellant combinations."""
    if len(results) != len(labels):
        raise ValueError("results and labels must have the same length")
    if not results:
        raise ValueError("results must be non-empty")

    x = list(range(len(results)))
    colors = [PALETTE[i % len(PALETTE)] for i in x]

    fig, axes = plt.subplots(1, len(_COMPARE_METRICS), figsize=(4 * len(_COMPARE_METRICS), 4.2))
    apply_dark_theme(fig)

    for ax, (attr, ylabel) in zip(axes, _COMPARE_METRICS):
        apply_dark_theme(fig, ax)
        vals = [float(getattr(r, attr) or 0.0) for r in results]
        ax.bar(x, vals, width=0.6, color=colors, edgecolor=SPINE)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel)

    fig.suptitle("Propellant comparison", color=FG, fontsize=13)
    fig.tight_layout()
    return _save(fig, save_path)


_COMPARE_METRICS = [
    ("isp_vac_shifting", "Isp vac [s]"),
    ("density_impulse_vac_shifting", "ρ·Isp [s·kg/m³]"),
    ("tc_kelvin", "Tc [K]"),
    ("c_star", "c* [m/s]"),
]


def plot_propellant_parallel(
    results: list[PerformanceResult],
    labels: list[str],
    *,
    save_path: str | None = None,
) -> Figure:
    """Parallel coordinates: each metric normalised to the best propellant (=1)."""
    if len(results) != len(labels) or not results:
        raise ValueError("results and labels must be non-empty and the same length")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    cols = [[float(getattr(r, a) or 0.0) for r in results] for a, _ in _COMPARE_METRICS]
    xs = list(range(len(_COMPARE_METRICS)))
    for i, lab in enumerate(labels):
        ys = [c[i] / max(c) if max(c) > 0 else 0.0 for c in cols]
        ax.plot(xs, ys, "o-", color=PALETTE[i % len(PALETTE)], lw=1.8, label=lab)
    ax.set_xticks(xs)
    ax.set_xticklabels([lab for _, lab in _COMPARE_METRICS])
    ax.set_ylabel("Fraction of best [-]")
    ax.set_title("Propellant comparison — normalised")
    _legend(ax)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_isp_map(
    of_values: list[float],
    pc_pa_values: list[float],
    isp_grid: list[list[float]],
    *,
    save_path: str | None = None,
) -> Figure:
    """Contour of vacuum Isp over O/F × Pc (``isp_grid[pc][of]``), max-Isp ridge marked."""
    from propwrap.units import pa_to_mpa

    pcs = [pa_to_mpa(p) for p in pc_pa_values]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    cs = ax.contourf(of_values, pcs, isp_grid, levels=20, cmap="viridis")
    ax.contour(of_values, pcs, isp_grid, levels=10, colors=BG, linewidths=0.4)
    ax.grid(False)
    cb = fig.colorbar(cs, ax=ax)
    cb.set_label("Isp vac [s]", color=FG)
    cb.ax.tick_params(colors=FG)
    ridge = [of_values[row.index(max(row))] for row in isp_grid]
    ax.plot(ridge, pcs, color=SECONDARY, lw=1.5, ls="--", label="opt O/F")
    ax.set_xlabel("O/F mass ratio [-]")
    ax.set_ylabel("Chamber pressure [MPa]")
    ax.set_title("Isp map — O/F × Pc")
    _legend(ax)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_species(
    sweep_result: SweepResult,
    *,
    station: str = "chamber",
    top: int = 6,
    save_path: str | None = None,
) -> Figure:
    """Stacked mole fractions vs O/F at a station; minor species lumped as 'other'."""
    if sweep_result.sweep_variable != "of_ratio":
        raise ValueError("plot_species requires sweep_variable='of_ratio'")
    comps = [
        (getattr(r, station).species_mole_fractions if getattr(r, station) else {})
        for r in sweep_result.results
    ]
    peak: dict[str, float] = {}
    for c in comps:
        for sp, x in c.items():
            peak[sp] = max(peak.get(sp, 0.0), x)
    keep = sorted(peak, key=peak.__getitem__, reverse=True)[:top]
    ys = [[c.get(sp, 0.0) for c in comps] for sp in keep]
    ys.append([max(0.0, 1.0 - sum(c.get(sp, 0.0) for sp in keep)) for c in comps])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.stackplot(
        sweep_result.values, ys, labels=keep + ["other"],
        colors=(PALETTE * 2)[: len(keep)] + [MUTED], alpha=0.85,
    )
    ax.set_xlabel("O/F mass ratio [-]")
    ax.set_ylabel("Mole fraction [-]")
    ax.set_ylim(0, 1)
    ax.set_title(f"{station.capitalize()} composition vs O/F")
    _legend(ax)
    fig.tight_layout()
    return _save(fig, save_path)


def plot_stations(
    result: PerformanceResult,
    *,
    save_path: str | None = None,
) -> Figure:
    """T, P, γ and MW at chamber → throat → exit."""
    sts = [s for s in (result.chamber, result.throat, result.exit) if s is not None]
    if not sts:
        raise ValueError("result has no station data (evaluate with full=True)")
    names = [s.name for s in sts]
    panels = [
        ([s.temperature_k for s in sts], "T [K]"),
        ([s.pressure_pa / 1e5 for s in sts], "P [bar]"),
        ([s.gamma for s in sts], "γ [-]"),
        ([s.mw for s in sts], "MW [kg/kmol]"),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.6))
    apply_dark_theme(fig)
    for ax, (vals, lab), color in zip(axes, panels, PALETTE):
        apply_dark_theme(fig, ax)
        ax.plot(names, vals, "o-", color=color, lw=1.8)
        ax.set_title(lab)
    axes[1].set_yscale("log")
    fig.suptitle(
        f"Station properties — {result.fuel}/{result.oxidizer}, O/F={result.of_ratio:.2f}",
        color=FG, fontsize=12,
    )
    fig.tight_layout()
    return _save(fig, save_path)


def plot_altitude(
    rows: list[dict[str, float | str]],
    *,
    save_path: str | None = None,
) -> Figure:
    """Isp vs altitude from :func:`propwrap.engine.altitude_performance`."""
    hs = [float(r["altitude_m"]) / 1000.0 for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.plot(hs, [float(r["isp_s"]) for r in rows], color=ACCENT, lw=2.0, label="Isp")
    ax2 = ax.twinx()
    apply_dark_theme(fig, ax2)
    ax2.plot(hs, [float(r["pamb_pa"]) / 1000.0 for r in rows], color=MUTED, ls="--", label="Pamb")
    ax2.set_ylabel("Ambient pressure [kPa]")
    ax.set_xlabel("Altitude [km] (US Std 1976)")
    ax.set_ylabel("Isp [s]")
    ax.set_title("Isp vs altitude — fixed geometry")
    _legend(ax, ax2)
    fig.tight_layout()
    return _save(fig, save_path)
