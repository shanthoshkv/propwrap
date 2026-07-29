"""Dark-themed publication-quality plots for propwrap sweeps and profiles."""

from __future__ import annotations

import os
from typing import Sequence

# Headless-friendly default (lab servers, CI, broken Tk installs)
import matplotlib

if os.environ.get("MPLBACKEND") is None:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from propwrap.models import GammaProfile, PerformanceResult, SweepResult

# Design system
BG = "#0a0a0a"
FG = "#e0e0e0"
GRID = "#2a2a2a"
ACCENT = "#5b8dee"
SECONDARY = "#d4924a"  # amber-copper
SPINE = "#333333"


def _resolve_font(preferred: Sequence[str], fallback: str) -> str:
    from matplotlib import font_manager

    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in preferred:
        if name in available:
            return name
    return fallback


def apply_dark_theme(fig: Figure | None = None, ax: Axes | None = None) -> None:
    """Apply the suite dark theme to a figure/axes (or rcParams globally)."""
    mono = _resolve_font(["DM Mono", "DejaVu Sans Mono", "Consolas"], "DejaVu Sans Mono")
    sans = _resolve_font(["DM Sans", "DejaVu Sans", "Arial"], "DejaVu Sans")

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
        fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
    return fig


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
        xytext=(8, 10),
        textcoords="offset points",
        color=SECONDARY,
        fontsize=8,
        fontfamily=_resolve_font(["DM Mono", "DejaVu Sans Mono"], "DejaVu Sans Mono"),
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
    isp = [r.isp_vac_shifting for r in sweep_result.results]
    tc = [r.tc_kelvin for r in sweep_result.results]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax1)
    ax1.plot(xs, isp, color=ACCENT, lw=2.0, label="Isp vac (shifting)")
    ax1.set_xlabel("O/F mass ratio [-]")
    ax1.set_ylabel("Isp vacuum [s]", color=ACCENT)
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
            color="#888888",
            ls=":",
            lw=1.0,
            label=f"stoich O/F={sweep_result.stoich_of_ratio:.2f}",
        )
        ax1.legend(loc="best", framealpha=0.9)
    ax1.set_title("O/F sweep — vacuum Isp & chamber temperature")
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
    isp = [r.isp_vac_shifting for r in sweep_result.results]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax)
    ax.plot(xs, isp, color=ACCENT, lw=2.0)
    ax.set_xlabel("Area ratio Ae/At [-]")
    ax.set_ylabel("Isp vacuum [s]")
    opt = sweep_result.optimum("isp_vac_shifting")
    _annotate_optimum(
        ax,
        opt.eps,
        opt.isp_vac_shifting,
        f"opt ε={opt.eps:.1f}\nIsp={opt.isp_vac_shifting:.1f}s",
    )
    ax.set_title("Area ratio sweep — vacuum Isp")
    fig.tight_layout()
    return _save(fig, save_path)


def plot_gamma_profile(
    gamma_profile: GammaProfile,
    *,
    save_path: str | None = None,
) -> Figure:
    """γ vs area ratio, with optional CEA/Cantera overlay."""
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
    from propwrap.models import DensityIspCurve as _DIC  # noqa: F401

    xs = [p.of_ratio for p in curve.points]
    isp = [p.isp_vac_shifting for p in curve.points]
    di = [p.density_isp for p in curve.points]

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    apply_dark_theme(fig, ax1)
    ax1.plot(xs, isp, color=ACCENT, lw=2.0, label="Isp vac")
    ax1.set_xlabel("O/F mass ratio [-]")
    ax1.set_ylabel("Isp vacuum [s]", color=ACCENT)
    ax1.axvline(curve.optimum_isp_of, color=ACCENT, ls=":", lw=1.0, alpha=0.7)

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
            )

    if curve.stoich_of_ratio is not None:
        ax1.axvline(
            curve.stoich_of_ratio,
            color="#888888",
            ls=":",
            lw=1.0,
            label=f"stoich={curve.stoich_of_ratio:.2f}",
        )
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

    metrics = [
        ("isp_vac_shifting", "Isp vac [s]"),
        ("tc_kelvin", "Tc [K]"),
        ("c_star", "c* [m/s]"),
    ]
    n_metrics = len(metrics)
    n = len(results)
    x = list(range(n))
    width = 0.25

    fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 4.2))
    if n_metrics == 1:
        axes = [axes]
    apply_dark_theme(fig)

    colors = [ACCENT, SECONDARY, "#7dcea0"]
    for ax, (attr, ylabel), color in zip(axes, metrics, colors):
        apply_dark_theme(fig, ax)
        vals = [float(getattr(r, attr)) for r in results]
        ax.bar(x, vals, width=0.6, color=color, edgecolor=SPINE)
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=20, ha="right")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel)

    fig.suptitle("Propellant comparison", color=FG, fontsize=13)
    fig.tight_layout()
    return _save(fig, save_path)
