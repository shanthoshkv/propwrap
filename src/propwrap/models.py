"""Pydantic result models for the public propwrap API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from matplotlib.figure import Figure


class StationState(BaseModel):
    """Thermo/transport at chamber, throat, or exit.

    Units: T [K], P [bar], rho [kg/m³], Mw [kg/kmol], gamma [-],
    cp [J/(kg·K)], R_specific [J/(kg·K)], mu [Pa·s], k [W/(m·K)], Pr [-].
    """

    model_config = ConfigDict(extra="forbid")

    name: Literal["chamber", "throat", "exit"]
    temperature_k: float
    pressure_bar: float
    density_kg_m3: float
    mw: float
    gamma: float
    cp_j_kg_k: float
    r_specific_j_kg_k: float
    mu_pa_s: float
    k_w_m_k: float
    prandtl: float
    species_mole_fractions: dict[str, float] = Field(default_factory=dict)


class PerformanceResult(BaseModel):
    """Frozen + shifting performance at one operating point (SI-adjacent units)."""

    model_config = ConfigDict(extra="forbid")

    of_ratio: float
    pc_bar: float
    eps: float
    isp_vac_shifting: float
    isp_vac_frozen: float
    isp_sl_shifting: float
    isp_sl_frozen: float
    c_star: float
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
    # Engineering extensions
    pe_bar: float = 0.0
    pc_over_pe: float = 0.0
    ambient_mode: str = ""
    fuel_temp_k: float | None = None
    ox_temp_k: float | None = None
    temps_are_default: bool = True
    equilibrium_modes: str = "shifting+frozen"
    pamb_sl_bar: float = 1.01325
    chamber: StationState | None = None
    throat: StationState | None = None
    exit: StationState | None = None
    stoich_of_ratio: float | None = None
    density_impulse_vac_shifting: float | None = None  # s · g/cm³ bulk
    bulk_density_g_cm3: float | None = None
    density_basis: str | None = None
    isp_vac_delivered: float | None = None
    isp_sl_delivered: float | None = None
    eta_cstar: float | None = None
    eta_cf: float | None = None
    warnings: list[str] = Field(default_factory=list)
    propwrap_version: str = ""
    from_cache: bool = False

    def summary(self, *, frozen: bool = False) -> str:
        from propwrap.display import performance_summary

        return performance_summary(self, frozen=frozen)

    def __str__(self) -> str:
        return self.summary()


class GammaProfile(BaseModel):
    """γ, T, Mw along nozzle area ratio (for MOC / contour tools)."""

    model_config = ConfigDict(extra="forbid")

    area_ratios: list[float]
    gamma_cea: list[float]
    gamma_cantera: list[float] | None = None
    temperatures_k: list[float]
    mw: list[float] = Field(default_factory=list)
    pressure_bar: list[float] = Field(default_factory=list)
    source: Literal["cea_frozen", "cea_shifting", "cantera_frozen"]
    constant_gamma_equiv: float | None = None  # throat-weighted simple average

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

    sweep_variable: Literal["of_ratio", "pc_bar", "eps"]
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
        """Isp loss vs optimum when running at ``of_ratio`` (nearest sample)."""
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
        """Opt-in plot. Does not show unless ``show=True``."""
        from propwrap import plotting
        from propwrap.display import maybe_close, maybe_show

        path = save or kwargs.pop("save_path", None)
        if self.sweep_variable == "of_ratio":
            fig = plotting.plot_of_sweep(self, save_path=path, **kwargs)
        elif self.sweep_variable == "pc_bar":
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
    """Bundled mixture study: design point + optional scans + γ profile.

    Formerly ``EngineCase`` (alias retained).
    """

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


# Back-compat alias
EngineCase = MixtureStudy


class DensityIspPoint(BaseModel):
    """One O/F sample on a density-Isp curve."""

    model_config = ConfigDict(extra="forbid")

    of_ratio: float
    isp_vac_shifting: float
    bulk_density_g_cm3: float | None
    density_isp: float | None  # s · g/cm³
    tc_kelvin: float
    c_star: float


class DensityIspCurve(BaseModel):
    """Density-impulse characterization of a propellant pair vs O/F."""

    model_config = ConfigDict(extra="forbid")

    fuel: str
    oxidizer: str
    pc_bar: float
    eps: float
    points: list[DensityIspPoint]
    optimum_isp_of: float
    optimum_density_isp_of: float | None
    stoich_of_ratio: float | None = None
    density_basis: str | None = None

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
            "bulk_density_g_cm3",
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
    """One propellant pair evaluated at its own optimum O/F."""

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
    """Multi-pair propellant trade at shared Pc/ε, each at optimum O/F."""

    model_config = ConfigDict(extra="forbid")

    pc_bar: float
    eps: float
    rows: list[TradeRow]
    ranking_by_isp: list[str]
    ranking_by_density_isp: list[str]

    def summary_table(self) -> str:
        lines = [
            f"{'pair':<16} {'O/F*':>6} {'Isp_vac':>8} {'ρ·Isp':>8} {'Tc':>8} {'c*':>8}",
            "-" * 60,
        ]
        for r in self.rows:
            di = r.density_isp_at_isp_opt
            di_s = f"{di:8.1f}" if di is not None else f"{'n/a':>8}"
            lines.append(
                f"{r.label:<16} {r.optimum_of:6.2f} "
                f"{r.performance.isp_vac_shifting:8.1f} {di_s} "
                f"{r.performance.tc_kelvin:8.0f} {r.performance.c_star:8.0f}"
            )
        lines.append("")
        lines.append("Rank by Isp: " + " > ".join(self.ranking_by_isp))
        lines.append("Rank by ρ·Isp: " + " > ".join(self.ranking_by_density_isp))
        return "\n".join(lines)

    def summary(self) -> str:
        return self.summary_table()

    def __str__(self) -> str:
        return self.summary_table()
