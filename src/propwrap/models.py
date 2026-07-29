"""Pydantic result models — all quantities in SI (see propwrap.units)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class StationState(BaseModel):
    """Thermo/transport at chamber, throat, or exit (SI).

    T [K], P [Pa], rho [kg/m³], Mw [kg/kmol], gamma [-],
    cp [J/(kg·K)], R [J/(kg·K)], mu [Pa·s], k [W/(m·K)], Pr [-].
    """

    model_config = ConfigDict(extra="forbid")

    name: Literal["chamber", "throat", "exit"]
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    mw: float
    gamma: float
    cp_j_kg_k: float
    r_specific_j_kg_k: float
    mu_pa_s: float
    k_w_m_k: float
    prandtl: float
    species_mole_fractions: dict[str, float] = Field(default_factory=dict)

    @property
    def pressure_bar(self) -> float:
        """Convenience: pressure [bar] = Pa / 1e5 (not serialized)."""
        from propwrap.units import pa_to_bar

        return pa_to_bar(self.pressure_pa)


class PerformanceResult(BaseModel):
    """Performance at one operating point — SI public units.

    Isp remains in seconds (rocketry standard); ve_* gives m/s (Isp · g0).
    """

    model_config = ConfigDict(extra="forbid")

    of_ratio: float
    pc_pa: float
    eps: float
    isp_vac_shifting: float  # s
    isp_vac_frozen: float
    isp_sl_shifting: float
    isp_sl_frozen: float
    ve_vac_shifting: float = 0.0  # m/s
    ve_vac_frozen: float = 0.0
    c_star: float  # m/s
    cf_vac: float
    cf_sl: float
    gamma_chamber: float
    gamma_throat: float
    gamma_exit: float
    mw_chamber: float
    tc_kelvin: float
    tt_kelvin: float
    te_kelvin: float
    fuel: str
    oxidizer: str
    pe_pa: float = 0.0
    pc_over_pe: float = 0.0
    ambient_mode: str = ""
    fuel_temp_k: float | None = None
    ox_temp_k: float | None = None
    temps_are_default: bool = True
    equilibrium_modes: str = "shifting+frozen"
    pamb_sl_pa: float = 101325.0
    chamber: StationState | None = None
    throat: StationState | None = None
    exit: StationState | None = None
    stoich_of_ratio: float | None = None
    density_impulse_vac_shifting: float | None = None  # s · kg/m³
    bulk_density_kg_m3: float | None = None
    density_basis: str | None = None
    isp_vac_delivered: float | None = None
    isp_sl_delivered: float | None = None
    eta_cstar: float | None = None
    eta_cf: float | None = None
    warnings: list[str] = Field(default_factory=list)
    propwrap_version: str = ""
    from_cache: bool = False

    # --- convenience views (not serialized) ---
    @property
    def pc_bar(self) -> float:
        from propwrap.units import pa_to_bar

        return pa_to_bar(self.pc_pa)

    @property
    def pe_bar(self) -> float:
        from propwrap.units import pa_to_bar

        return pa_to_bar(self.pe_pa)

    @property
    def bulk_density_g_cm3(self) -> float | None:
        from propwrap.units import kg_m3_to_g_cm3

        if self.bulk_density_kg_m3 is None:
            return None
        return kg_m3_to_g_cm3(self.bulk_density_kg_m3)

    def summary(self, *, frozen: bool = False) -> str:
        from propwrap.display import performance_summary

        return performance_summary(self, frozen=frozen)

    def to_markdown(self, *, heading: str = "Performance") -> str:
        from propwrap.reports import performance_to_markdown

        return performance_to_markdown(self, heading=heading)

    def __str__(self) -> str:
        return self.summary()


class GammaProfile(BaseModel):
    """γ, T, Mw along expansion (product properties). Pressures in Pa."""

    model_config = ConfigDict(extra="forbid")

    area_ratios: list[float]
    gamma_cea: list[float]
    gamma_cantera: list[float] | None = None
    temperatures_k: list[float]
    mw: list[float] = Field(default_factory=list)
    pressure_pa: list[float] = Field(default_factory=list)
    source: Literal["cea_frozen", "cea_shifting", "cantera_frozen"]
    constant_gamma_equiv: float | None = None

    @property
    def pressure_bar(self) -> list[float]:
        from propwrap.units import pa_to_bar

        return [pa_to_bar(p) for p in self.pressure_pa]

    def summary(self) -> str:
        from propwrap.display import gamma_summary

        return gamma_summary(self)

    def __str__(self) -> str:
        return self.summary()

    def plot(self, *, save: str | None = None, show: bool = False, **kwargs: Any) -> Figure:
        from propwrap.display import maybe_close, maybe_show
        from propwrap.plotting import plot_gamma_profile

        fig = plot_gamma_profile(self, save_path=save or kwargs.get("save_path"))
        maybe_show(fig, show)
        if not show:
            maybe_close(fig, show)
        return fig


class CrossValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameter: str
    cea_value: float
    cantera_value: float
    absolute_diff: float
    percent_diff: float
    within_tolerance: bool


class SweepResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sweep_variable: Literal["of_ratio", "pc_pa", "eps"]
    values: list[float]
    results: list[PerformanceResult]
    stoich_of_ratio: float | None = None

    def optimum(self, metric: str = "isp_vac_shifting") -> PerformanceResult:
        if not self.results:
            raise ValueError("Cannot compute optimum of an empty SweepResult")
        if not hasattr(self.results[0], metric):
            raise ValueError(f"Unknown metric '{metric}' on PerformanceResult")
        return max(self.results, key=lambda r: float(getattr(r, metric)))

    def summary(self) -> str:
        from propwrap.display import sweep_summary

        return sweep_summary(self)

    def __str__(self) -> str:
        return self.summary()

    def off_design(
        self, of_ratio: float, metric: str = "isp_vac_shifting"
    ) -> dict[str, float]:
        if self.sweep_variable != "of_ratio":
            raise ValueError("off_design requires of_ratio sweep")
        opt = self.optimum(metric)
        opt_v = float(getattr(opt, metric))
        idx = min(range(len(self.values)), key=lambda i: abs(self.values[i] - of_ratio))
        near = self.results[idx]
        val = float(getattr(near, metric))
        loss_pct = 0.0 if opt_v == 0 else (opt_v - val) / opt_v * 100.0
        return {
            "requested_of": of_ratio,
            "nearest_of": self.values[idx],
            "metric": metric,
            "value": val,
            "optimum_value": opt_v,
            "optimum_of": opt.of_ratio,
            "loss_pct": loss_pct,
        }

    def plot(
        self,
        *,
        save: str | None = None,
        show: bool = False,
        **kwargs: Any,
    ) -> Figure:
        from propwrap import plotting
        from propwrap.display import maybe_close, maybe_show

        path = save or kwargs.pop("save_path", None)
        if self.sweep_variable == "of_ratio":
            fig = plotting.plot_of_sweep(self, save_path=path, **kwargs)
        elif self.sweep_variable == "pc_pa":
            fig = plotting.plot_pc_sweep(self, save_path=path, **kwargs)
        elif self.sweep_variable == "eps":
            fig = plotting.plot_eps_sweep(self, save_path=path, **kwargs)
        else:
            raise ValueError(f"Unsupported sweep_variable: {self.sweep_variable}")
        maybe_show(fig, show)
        if not show:
            maybe_close(fig, show)
        return fig

    def to_csv(self, path: str) -> None:
        from propwrap.export import sweep_to_csv

        sweep_to_csv(self, path)

    def to_json(self, path: str) -> None:
        from propwrap.export import sweep_to_json

        sweep_to_json(self, path)


class MixtureStudy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    design: PerformanceResult
    of_sweep: SweepResult | None = None
    eps_sweep: SweepResult | None = None
    pc_sweep: SweepResult | None = None
    gamma_profile: GammaProfile | None = None
    notes: list[str] = Field(default_factory=list)

    def summary(self) -> str:
        lines = ["=== Mixture study ===", self.design.summary()]
        if self.of_sweep is not None:
            lines.append(self.of_sweep.summary())
        for n in self.notes:
            lines.append(f"note: {n}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


EngineCase = MixtureStudy


class DensityIspPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    of_ratio: float
    isp_vac_shifting: float
    bulk_density_kg_m3: float | None
    density_isp: float | None  # s · kg/m³
    tc_kelvin: float
    c_star: float


class DensityIspCurve(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuel: str
    oxidizer: str
    pc_pa: float
    eps: float
    points: list[DensityIspPoint]
    optimum_isp_of: float
    optimum_density_isp_of: float | None
    stoich_of_ratio: float | None = None
    density_basis: str | None = None

    @property
    def pc_bar(self) -> float:
        from propwrap.units import pa_to_bar

        return pa_to_bar(self.pc_pa)

    def summary(self) -> str:
        from propwrap.display import density_isp_summary

        return density_isp_summary(self)

    def __str__(self) -> str:
        return self.summary()

    def plot(
        self, *, save: str | None = None, show: bool = False, **kwargs: Any
    ) -> Figure:
        from propwrap.display import maybe_close, maybe_show
        from propwrap.plotting import plot_density_isp

        fig = plot_density_isp(self, save_path=save or kwargs.get("save_path"))
        maybe_show(fig, show)
        if not show:
            maybe_close(fig, show)
        return fig

    def to_csv(self, path: str) -> None:
        import csv
        from pathlib import Path

        fields = [
            "of_ratio",
            "isp_vac_shifting",
            "bulk_density_kg_m3",
            "density_isp",
            "tc_kelvin",
            "c_star",
        ]
        with Path(path).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for p in self.points:
                w.writerow(p.model_dump())


class TradeRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fuel: str
    oxidizer: str
    label: str
    of_range: tuple[float, float, float]
    optimum_of: float
    performance: PerformanceResult
    density_isp_at_isp_opt: float | None
    optimum_density_isp_of: float | None
    density_isp_max: float | None
    stoich_of_ratio: float | None = None


class TradeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pc_pa: float
    eps: float
    rows: list[TradeRow]
    ranking_by_isp: list[str]
    ranking_by_density_isp: list[str]

    @property
    def pc_bar(self) -> float:
        from propwrap.units import pa_to_bar

        return pa_to_bar(self.pc_pa)

    def summary_table(self) -> str:
        from propwrap.units import pa_to_bar

        lines = [
            f"Pc = {self.pc_pa:.3e} Pa ({pa_to_bar(self.pc_pa):.4g} bar)  ε = {self.eps:g}",
            f"{'pair':<16} {'O/F*':>6} {'Isp_vac':>8} {'ρ·Isp':>12} {'Tc':>8} {'c*':>8}",
            "-" * 68,
        ]
        for r in self.rows:
            di = r.density_isp_at_isp_opt
            di_s = f"{di:12.1f}" if di is not None else f"{'n/a':>12}"
            lines.append(
                f"{r.label:<16} {r.optimum_of:6.2f} "
                f"{r.performance.isp_vac_shifting:8.1f} {di_s} "
                f"{r.performance.tc_kelvin:8.0f} {r.performance.c_star:8.0f}"
            )
        lines.append("")
        lines.append("Rank by Isp: " + " > ".join(self.ranking_by_isp))
        lines.append("Rank by ρ·Isp: " + " > ".join(self.ranking_by_density_isp))
        lines.append("ρ·Isp unit: s · kg/m³  |  Isp: s  |  c*: m/s  |  Tc: K")
        return "\n".join(lines)

    def summary(self) -> str:
        return self.summary_table()

    def to_markdown(self, *, heading: str = "Propellant trade") -> str:
        from propwrap.reports import trade_to_markdown

        return trade_to_markdown(self, heading=heading)

    def __str__(self) -> str:
        return self.summary_table()
