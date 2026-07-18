"""High-level propellant workflows: characterize, compare, blend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from propwrap.defaults import resolve_pc_eps
from propwrap.models import DensityIspCurve, PerformanceResult, TradeResult
from propwrap.propellant import Mixture
from propwrap.trades import density_isp_curve, trade_at_optimum_of


@dataclass
class CharacterizeResult:
    """Output of :func:`characterize` — one pair, fully described."""

    point: PerformanceResult | None
    of_scan: Any = None
    density_impulse: DensityIspCurve | None = None
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["=== Propellant characterization ==="]
        if self.point is not None:
            lines.append(self.point.summary())
        if self.of_scan is not None:
            opt = self.of_scan.optimum()
            lines.append(
                f"O/F scan peak: O/F={opt.of_ratio:.3f}  "
                f"Isp_vac={opt.isp_vac_shifting:.1f} s"
            )
        if self.density_impulse is not None:
            di = self.density_impulse
            lines.append(
                f"Density-Isp: Isp-opt O/F={di.optimum_isp_of:.3f}, "
                f"ρ·Isp-opt O/F={di.optimum_density_isp_of}"
            )
        for n in self.notes:
            lines.append(f"note: {n}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


def characterize(
    fuel: str,
    oxidizer: str,
    *,
    of: float | None = None,
    of_ratio: float | None = None,
    mixture_ratio: float | None = None,
    pc_bar: float | None = None,
    pc_pa: float | None = None,
    eps: float | None = None,
    expansion_ratio: float | None = None,
    of_range: tuple[float, float, float] | None = None,
    plot: bool = False,
    save: str | None = None,
    show: bool = False,
    verbose: bool = False,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> CharacterizeResult:
    """Workflow 1 — characterize one propellant pair.

    Runs optional design point, O/F scan, and density-Isp curve.
    Plots only if ``plot=True`` or ``save=`` is set. Pressure in Pa (or pc_bar=).
    """
    pc, ep = resolve_pc_eps(
        None, eps, expansion_ratio=expansion_ratio, pc_pa=pc_pa, pc_bar=pc_bar
    )
    m = Mixture(
        fuel,
        oxidizer,
        cache_enabled=cache_enabled,
        apply_cryo_defaults=apply_cryo_defaults,
    )
    of_v = of if of is not None else of_ratio if of_ratio is not None else mixture_ratio

    notes: list[str] = []
    point = None
    if of_v is not None:
        point = m.evaluate(of=of_v, pc_pa=pc, eps=ep, verbose=verbose)
        notes.extend(point.warnings)

    # default O/F range by family
    if of_range is None:
        from propwrap.trades import _default_range_for

        of_range = _default_range_for(m.fuel, m.oxidizer, (1.8, 3.5, 0.1))

    of_scan = m.scan_of(
        of_range, pc_pa=pc, eps=ep, plot=plot, save=_save_path(save, "of_scan")
    )
    dens = m.density_impulse(
        of_range, pc_pa=pc, eps=ep, plot=plot, save=_save_path(save, "density_isp")
    )

    if show and plot:
        import matplotlib.pyplot as plt

        plt.show()

    if verbose:
        notes.append(f"Pc={pc} bar, ε={ep}, O/F range={of_range}")

    result = CharacterizeResult(
        point=point, of_scan=of_scan, density_impulse=dens, notes=notes
    )
    if verbose:
        print(result.summary())
    return result


def compare_propellants(
    pairs: Sequence[str | tuple[str, str] | tuple[str, str, tuple[float, float, float]]],
    *,
    pc_bar: float | None = None,
    pc_pa: float | None = None,
    eps: float | None = None,
    expansion_ratio: float | None = None,
    plot: bool = False,
    save: str | None = None,
    show: bool = False,
    verbose: bool = False,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
) -> TradeResult:
    """Workflow 2 — fair trade: each pair at its own optimum O/F.

    ``pairs`` may be ``\"RP-1/LOX\"`` strings or ``(fuel, ox)`` tuples.
    """
    pc, ep = resolve_pc_eps(
        None, eps, expansion_ratio=expansion_ratio, pc_pa=pc_pa, pc_bar=pc_bar
    )
    parsed: list[tuple[str, str] | tuple[str, str, tuple[float, float, float]]] = []
    for p in pairs:
        if isinstance(p, str):
            if "/" not in p:
                raise ValueError(
                    f"Pair '{p}' must look like FUEL/OX (e.g. 'RP-1/LOX')"
                )
            f, o = p.split("/", 1)
            parsed.append((f.strip(), o.strip()))
        else:
            parsed.append(p)  # type: ignore[arg-type]

    trade = trade_at_optimum_of(
        parsed,
        pc_pa=pc,
        eps=ep,
        cache_enabled=cache_enabled,
        apply_cryo_defaults=apply_cryo_defaults,
    )

    if plot or save:
        from propwrap.plotting import plot_propellant_comparison

        results = [r.performance for r in trade.rows]
        labels = [r.label for r in trade.rows]
        path = save if isinstance(save, str) else None
        fig = plot_propellant_comparison(results, labels, save_path=path)
        if show:
            import matplotlib.pyplot as plt

            plt.show()
        else:
            import matplotlib.pyplot as plt

            plt.close(fig)

    if verbose:
        print(trade.summary_table())
    return trade


def define_blend(
    name: str,
    components: Sequence[tuple[str, float]],
    *,
    kind: str = "fuel",
    density_g_cm3: float | None = None,
    notes: str = "",
    evaluate_with: str | None = None,
    of: float = 2.0,
    pc_bar: float | None = None,
    eps: float | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Workflow 3 — register a blend and optionally evaluate it.

    Parameters
    ----------
    evaluate_with :
        Oxidizer (if fuel blend) or fuel (if ox blend) to run a quick point.
    """
    from propwrap.blends import add_blend, blend_card_summary

    blend_name = add_blend(
        name,
        components,
        kind=kind,
        density_g_cm3=density_g_cm3,
        notes=notes,
    )
    out: dict[str, Any] = {
        "name": blend_name,
        "summary": blend_card_summary(blend_name),
        "performance": None,
    }
    if evaluate_with:
        pc, ep = resolve_pc_eps(None, eps, pc_pa=None, pc_bar=pc_bar)
        if kind == "fuel":
            m = Mixture(blend_name, evaluate_with)
        else:
            m = Mixture(evaluate_with, blend_name)
        r = m.evaluate(of=of, pc_pa=pc, eps=ep, verbose=False)
        out["performance"] = r
        if verbose:
            print(out["summary"])
            print(r.summary())
    elif verbose:
        print(out["summary"])
    return out


def _save_path(save: str | None, stem: str) -> str | None:
    if not save:
        return None
    if save.endswith((".png", ".svg", ".pdf", ".jpg")):
        # single file requested — only first plot uses it; others get suffix
        if stem == "of_scan":
            return save
        base = save.rsplit(".", 1)[0]
        ext = save.rsplit(".", 1)[-1]
        return f"{base}_{stem}.{ext}"
    # directory or prefix
    return f"{save}_{stem}.png"
