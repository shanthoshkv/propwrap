"""Student/report helpers: markdown, captions, homework folder export."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from propwrap.models import (
    DensityIspCurve,
    PerformanceResult,
    SweepResult,
    TradeResult,
)
from propwrap.propellant import Mixture
from propwrap.units import pa_to_bar


ASSUMPTIONS_TEXT = """\
ASSUMPTIONS (read before interpreting results)
==============================================
1. Values come from NASA CEA (ideal 1-D chemical equilibrium) via RocketCEA.
2. Numbers are THEORETICAL, not flight-delivered engine Isp.
3. Real engines usually achieve lower Isp (efficiency losses, mixture bias, etc.).
4. Shifting equilibrium Isp is typically an upper bound; frozen is a lower bound.
5. Public units are SI: pressure Pa, temperature K, velocity m/s, density kg/m³.
   Isp is reported in seconds (rocketry convention); ve = Isp * g0 [m/s].
6. Do not claim these numbers as measured engine data without experimental work.
"""


def figure_caption(
    *,
    fig_num: int | str,
    title: str,
    fuel: str,
    oxidizer: str,
    pc_pa: float | None = None,
    pc_bar: float | None = None,
    eps: float | None = None,
    extra: str = "",
) -> str:
    """Standard report caption string for student lab figures."""
    if pc_bar is None and pc_pa is not None:
        pc_bar = pa_to_bar(pc_pa)
    bits = [f"Fig. {fig_num} — {title} ({fuel}/{oxidizer}"]
    cond: list[str] = []
    if pc_bar is not None:
        cond.append(f"Pc={pc_bar:g} bar")
    if eps is not None:
        cond.append(f"ε={eps:g}")
    cond.append("CEA theoretical, shifting unless noted")
    if extra:
        cond.append(extra)
    return bits[0] + ", " + ", ".join(cond) + ")."


def performance_to_markdown(r: PerformanceResult, *, heading: str = "Performance") -> str:
    """Markdown block suitable for pasting into a lab report."""
    lines = [
        f"## {heading}",
        "",
        f"**Propellants:** {r.fuel} / {r.oxidizer}  ",
        f"**O/F:** {r.of_ratio:g}  |  **Pc:** {r.pc_pa:.3e} Pa ({r.pc_bar:.4g} bar)  |  **ε:** {r.eps:g}",
        "",
        "| Quantity | Value | Unit |",
        "|----------|------:|------|",
        f"| Isp vac (shifting) | {r.isp_vac_shifting:.2f} | s |",
        f"| Isp vac (frozen) | {r.isp_vac_frozen:.2f} | s |",
        f"| ve vac (shifting) | {r.ve_vac_shifting:.1f} | m/s |",
        f"| Isp SL (shifting) | {r.isp_sl_shifting:.2f} | s |",
        f"| c* | {r.c_star:.1f} | m/s |",
        f"| Tc | {r.tc_kelvin:.1f} | K |",
        f"| Tt | {r.tt_kelvin:.1f} | K |",
        f"| Te | {r.te_kelvin:.1f} | K |",
        f"| γ chamber | {r.gamma_chamber:.4f} | — |",
        f"| γ exit | {r.gamma_exit:.4f} | — |",
        f"| Mw chamber | {r.mw_chamber:.2f} | kg/kmol |",
        f"| Pe | {r.pe_pa:.3e} | Pa |",
    ]
    if r.bulk_density_kg_m3 is not None:
        lines.append(f"| Bulk density | {r.bulk_density_kg_m3:.1f} | kg/m³ |")
    if r.density_impulse_vac_shifting is not None:
        lines.append(
            f"| Density impulse | {r.density_impulse_vac_shifting:.1f} | s·kg/m³ |"
        )
    lines.extend(
        [
            "",
            "> **Note:** Theoretical CEA values — not flight engine performance.",
            "",
        ]
    )
    if r.warnings:
        lines.append("**Warnings:**")
        for w in r.warnings:
            lines.append(f"- {w}")
        lines.append("")
    return "\n".join(lines)


def trade_to_markdown(trade: TradeResult, *, heading: str = "Propellant trade") -> str:
    lines = [
        f"## {heading}",
        "",
        f"**Pc** = {trade.pc_pa:.3e} Pa ({trade.pc_bar:.4g} bar), **ε** = {trade.eps:g}",
        "",
        "Each pair evaluated at **its own optimum O/F** (max vacuum Isp, shifting).",
        "",
        "| Pair | O/F* | Isp vac [s] | ρ·Isp [s·kg/m³] | Tc [K] | c* [m/s] |",
        "|------|-----:|------------:|----------------:|-------:|---------:|",
    ]
    for row in trade.rows:
        di = row.density_isp_at_isp_opt
        di_s = f"{di:.1f}" if di is not None else "—"
        lines.append(
            f"| {row.label} | {row.optimum_of:.3f} | "
            f"{row.performance.isp_vac_shifting:.2f} | {di_s} | "
            f"{row.performance.tc_kelvin:.0f} | {row.performance.c_star:.0f} |"
        )
    lines.extend(
        [
            "",
            f"**Rank by Isp:** {' > '.join(trade.ranking_by_isp)}  ",
            f"**Rank by ρ·Isp:** {' > '.join(trade.ranking_by_density_isp)}",
            "",
            "> Fair comparison: do not use one O/F for all propellants.",
            "",
        ]
    )
    return "\n".join(lines)


def discussion_prompts(topic: str = "general") -> str:
    """Suggested lab discussion questions."""
    base = [
        "Are these values theoretical or measured? What does that mean for your design?",
        "Why is shifting Isp usually higher than frozen Isp?",
        "If your Wikipedia engine Isp is lower than CEA, is that expected? Why?",
    ]
    extra = {
        "of_scan": [
            "Is the O/F for peak Isp the same as stoichiometric? Why or why not?",
            "How much Isp do you lose 10% off the peak O/F? Is the peak sharp or flat?",
        ],
        "trade": [
            "Which pair wins on Isp? Which wins on density-Isp? When does each matter?",
            "Why is comparing all pairs at O/F=2.5 unfair?",
        ],
        "general": [],
    }
    lines = ["## Discussion prompts", ""]
    for q in base + extra.get(topic, []):
        lines.append(f"- {q}")
    lines.append("")
    return "\n".join(lines)


def write_lab_report(
    out_dir: str | Path,
    *,
    fuel: str = "RP-1",
    oxidizer: str = "LOX",
    of_ratio: float = 2.56,
    pc_bar: float = 70.0,
    eps: float = 20.0,
    of_range: tuple[float, float, float] = (2.0, 3.2, 0.1),
    student_name: str = "Student",
    compare_pairs: Sequence[str] | None = None,
    make_plots: bool = True,
) -> Path:
    """Generate a complete student lab folder (markdown, CSV, optional PNGs).

    Returns the output directory path.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    m = Mixture(fuel, oxidizer, apply_cryo_defaults=True)
    point = m.evaluate(of=of_ratio, pc_bar=pc_bar, eps=eps)
    sweep = m.scan_of(of_range, pc_bar=pc_bar, eps=eps, plot=False)
    dens = m.density_impulse(of_range, pc_bar=pc_bar, eps=eps, plot=False)
    opt = sweep.optimum()

    # CSV point + sweep
    _write_point_csv(out / "point_performance.csv", point)
    _write_sweep_csv(out / "of_scan.csv", sweep)
    dens.to_csv(str(out / "density_isp.csv"))

    captions: list[str] = []
    if make_plots:
        of_png = out / "fig01_of_scan.png"
        di_png = out / "fig02_density_isp.png"
        sweep.plot(save=str(of_png), show=False)
        dens.plot(save=str(di_png), show=False)
        captions.append(
            figure_caption(
                fig_num=1,
                title="Vacuum Isp vs mixture ratio (O/F)",
                fuel=m.fuel,
                oxidizer=m.oxidizer,
                pc_bar=pc_bar,
                eps=eps,
                extra="shifting equilibrium",
            )
        )
        captions.append(
            figure_caption(
                fig_num=2,
                title="Density impulse vs mixture ratio",
                fuel=m.fuel,
                oxidizer=m.oxidizer,
                pc_bar=pc_bar,
                eps=eps,
            )
        )

    trade_md = ""
    if compare_pairs:
        from propwrap.workflows import compare_propellants

        trade = compare_propellants(
            list(compare_pairs),
            pc_bar=pc_bar,
            eps=eps,
            plot=False,
            apply_cryo_defaults=True,
        )
        trade_md = trade_to_markdown(trade)
        if make_plots:
            from propwrap.plotting import plot_propellant_comparison

            fig_path = out / "fig03_trade.png"
            plot_propellant_comparison(
                [row.performance for row in trade.rows],
                [row.label for row in trade.rows],
                save_path=str(fig_path),
            )
            captions.append(
                figure_caption(
                    fig_num=3,
                    title="Propellant comparison at each pair's optimum O/F",
                    fuel="multi",
                    oxidizer="multi",
                    pc_bar=pc_bar,
                    eps=eps,
                )
            )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    md = [
        f"# Propellant lab report — {student_name}",
        "",
        f"**Generated:** {now}  ",
        f"**Tool:** propwrap (theoretical CEA)  ",
        f"**Primary pair:** {m.fuel}/{m.oxidizer}",
        "",
        "## 1. Objectives",
        "",
        "1. Compute theoretical vacuum performance for a liquid bipropellant pair.",
        "2. Find the mixture ratio that maximises vacuum Isp.",
        "3. Compare density impulse behaviour (tank-relevant metric).",
        "",
        "## 2. Method",
        "",
        "- Thermochemistry: NASA CEA via RocketCEA (shifting + frozen).",
        f"- Design point: O/F={of_ratio:g}, Pc={pc_bar:g} bar, ε={eps:g}.",
        f"- O/F scan range: {of_range}.",
        "- **Important:** Results are ideal 1-D theory, not measured engine data.",
        "",
        performance_to_markdown(point, heading="3. Design-point results"),
        "## 4. O/F scan results",
        "",
        f"- Optimum O/F (max Isp vac shifting): **{opt.of_ratio:.3f}**",
        f"- Peak Isp vac: **{opt.isp_vac_shifting:.2f} s**",
        f"- At that point Tc = {opt.tc_kelvin:.0f} K, c* = {opt.c_star:.0f} m/s",
        f"- Density-Isp optimum O/F: **{dens.optimum_density_isp_of}**",
        "",
        "See `of_scan.csv` and `density_isp.csv` for full tables.",
        "",
    ]
    if trade_md:
        md.append(trade_md)
    if captions:
        md.append("## Figures")
        md.append("")
        for c in captions:
            md.append(c)
            md.append("")
    md.append(discussion_prompts("of_scan" if not compare_pairs else "trade"))
    md.append("## Files in this folder")
    md.append("")
    md.append("| File | Contents |")
    md.append("|------|----------|")
    md.append("| `summary.md` | This report |")
    md.append("| `assumptions.txt` | Required reading |")
    md.append("| `point_performance.csv` | Design point |")
    md.append("| `of_scan.csv` | O/F sweep |")
    md.append("| `density_isp.csv` | Density impulse sweep |")
    if make_plots:
        md.append("| `fig01_of_scan.png` | Isp vs O/F |")
        md.append("| `fig02_density_isp.png` | ρ·Isp vs O/F |")
        if compare_pairs:
            md.append("| `fig03_trade.png` | Pair comparison |")
    md.append("")

    (out / "summary.md").write_text("\n".join(md), encoding="utf-8")
    (out / "assumptions.txt").write_text(ASSUMPTIONS_TEXT, encoding="utf-8")
    (out / "captions.txt").write_text("\n\n".join(captions) + "\n", encoding="utf-8")
    return out


def _write_point_csv(path: Path, r: PerformanceResult) -> None:
    data = {
        "fuel": r.fuel,
        "oxidizer": r.oxidizer,
        "of_ratio": r.of_ratio,
        "pc_pa": r.pc_pa,
        "pc_bar": r.pc_bar,
        "eps": r.eps,
        "isp_vac_shifting_s": r.isp_vac_shifting,
        "isp_vac_frozen_s": r.isp_vac_frozen,
        "ve_vac_shifting_m_s": r.ve_vac_shifting,
        "c_star_m_s": r.c_star,
        "tc_kelvin": r.tc_kelvin,
        "gamma_chamber": r.gamma_chamber,
        "gamma_exit": r.gamma_exit,
        "bulk_density_kg_m3": r.bulk_density_kg_m3 or "",
        "density_impulse_s_kg_m3": r.density_impulse_vac_shifting or "",
    }
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(data.keys()))
        w.writeheader()
        w.writerow(data)


def _write_sweep_csv(path: Path, sweep: SweepResult) -> None:
    fields = [
        "of_ratio",
        "isp_vac_shifting_s",
        "isp_vac_frozen_s",
        "tc_kelvin",
        "c_star_m_s",
        "gamma_chamber",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sweep.results:
            w.writerow(
                {
                    "of_ratio": r.of_ratio,
                    "isp_vac_shifting_s": r.isp_vac_shifting,
                    "isp_vac_frozen_s": r.isp_vac_frozen,
                    "tc_kelvin": r.tc_kelvin,
                    "c_star_m_s": r.c_star,
                    "gamma_chamber": r.gamma_chamber,
                }
            )


def homework_folder_name(student_name: str, label: str = "lab") -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in student_name.strip())
    safe = safe or "Student"
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"propwrap_{label}_{safe}_{stamp}"
