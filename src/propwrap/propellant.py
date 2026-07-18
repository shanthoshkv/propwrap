"""Primary public API: Mixture (propellant pair) with friendly methods."""

from __future__ import annotations

from typing import Any, Literal

from propwrap import cea_backend
from propwrap.cache import ResultCache, clear_default_cache, get_default_cache
from propwrap.defaults import get_defaults, resolve_pc_eps
from propwrap.display import maybe_close, maybe_show
from propwrap.errors import (
    PropwrapError,
    did_you_mean,
    validate_eps,
    validate_of,
    validate_pc,
)
from propwrap.models import (
    CrossValidationResult,
    DensityIspCurve,
    GammaProfile,
    MixtureStudy,
    PerformanceResult,
    SweepResult,
)
from propwrap.propellant_library import normalize_name, stoich_of_ratio
from propwrap.registry import get_propellant
from propwrap.sanity import sanity_check
from propwrap.sweeps import expand_range

# re-export old name used internally
EngineCase = MixtureStudy


def _parse_inlet_temps(
    inlet_temps: Literal["auto", "none"] | dict[str, float] | None,
    fuel_temp_k: float | None,
    ox_temp_k: float | None,
    apply_cryo_defaults: bool,
) -> tuple[float | None, float | None, bool]:
    """Return (fuel_T, ox_T, apply_cryo_defaults)."""
    if inlet_temps == "none":
        return fuel_temp_k, ox_temp_k, False
    if inlet_temps == "auto" or inlet_temps is None:
        return fuel_temp_k, ox_temp_k, apply_cryo_defaults if inlet_temps != "none" else False
    if isinstance(inlet_temps, dict):
        ft = inlet_temps.get("fuel", inlet_temps.get("fuel_temp_k", fuel_temp_k))
        ot = inlet_temps.get("ox", inlet_temps.get("ox_temp_k", ox_temp_k))
        return ft, ot, False
    return fuel_temp_k, ox_temp_k, apply_cryo_defaults


class Mixture:
    """A fuel/oxidizer pair — main user-facing object.

    Also available as :class:`Propellant` and :class:`PropellantPair` (aliases).

    Examples
    --------
    >>> m = Mixture("RP-1", "LOX")
    >>> print(m.evaluate(of=2.56, pc=70, eps=20))
    >>> m.scan_of((2.0, 3.2, 0.1), pc=70, eps=20, plot=False)
    """

    def __init__(
        self,
        fuel: str,
        oxidizer: str,
        fuel_temp_k: float | None = None,
        ox_temp_k: float | None = None,
        cache_enabled: bool | None = None,
        cache: ResultCache | None = None,
        apply_cryo_defaults: bool | None = None,
        eta_cstar: float = 1.0,
        eta_cf: float = 1.0,
        *,
        efficiency: tuple[float, float] | None = None,
        inlet_temps: Literal["auto", "none"] | dict[str, float] | None = None,
    ) -> None:
        d = get_defaults()
        fuel_n = normalize_name(fuel, kind="fuel")
        ox_n = normalize_name(oxidizer, kind="oxidizer")
        # soft suggestion if unknown-looking
        if get_propellant(fuel) is None and get_propellant(fuel_n) is None:
            hint = did_you_mean(fuel, kind="fuel")
            if hint and " " in fuel or "-" in fuel:
                pass  # still allow CEA pass-through
            _ = hint
        self.fuel = fuel_n
        self.oxidizer = ox_n

        ft, ot, cryo = _parse_inlet_temps(
            inlet_temps,
            fuel_temp_k,
            ox_temp_k,
            d["apply_cryo_defaults"]
            if apply_cryo_defaults is None
            else apply_cryo_defaults,
        )
        self.fuel_temp_k = ft
        self.ox_temp_k = ot
        self.cache_enabled = (
            d["cache_enabled"] if cache_enabled is None else cache_enabled
        )
        self._cache = cache
        self.apply_cryo_defaults = cryo
        if efficiency is not None:
            eta_cstar, eta_cf = efficiency
        self.eta_cstar = eta_cstar
        self.eta_cf = eta_cf

    def _get_cache(self) -> ResultCache | None:
        if not self.cache_enabled:
            return None
        return self._cache if self._cache is not None else get_default_cache()

    def _resolve_point_args(
        self,
        of: float | None = None,
        pc: float | None = None,
        eps: float | None = None,
        *,
        of_ratio: float | None = None,
        mixture_ratio: float | None = None,
        pc_bar: float | None = None,
        expansion_ratio: float | None = None,
    ) -> tuple[float, float, float]:
        of_v = next((v for v in (of, of_ratio, mixture_ratio) if v is not None), None)
        if of_v is None:
            raise PropwrapError(
                "Mixture ratio required. Pass of=..., of_ratio=..., or mixture_ratio=..."
            )
        pc_v, eps_v = resolve_pc_eps(
            pc_bar if pc_bar is not None else pc,
            eps,
            expansion_ratio=expansion_ratio,
            pc=pc if pc_bar is None else None,
        )
        # if user passed nothing, resolve_pc_eps uses defaults — good
        if pc is None and pc_bar is None:
            pc_v = resolve_pc_eps(None, eps_v)[0]
        validate_of(float(of_v))
        validate_pc(float(pc_v))
        validate_eps(float(eps_v))
        return float(of_v), float(pc_v), float(eps_v)

    def evaluate(
        self,
        of: float | None = None,
        pc: float | None = None,
        eps: float | None = None,
        *,
        of_ratio: float | None = None,
        mixture_ratio: float | None = None,
        pc_bar: float | None = None,
        expansion_ratio: float | None = None,
        verbose: bool = False,
        full: bool = True,
        frozen: bool = False,
    ) -> PerformanceResult:
        """Evaluate mixture at one (O/F, Pc, ε). Alias of ``performance``."""
        of_v, pc_v, eps_v = self._resolve_point_args(
            of,
            pc,
            eps,
            of_ratio=of_ratio,
            mixture_ratio=mixture_ratio,
            pc_bar=pc_bar,
            expansion_ratio=expansion_ratio,
        )
        result = self._compute(of_v, pc_v, eps_v, include_stations=full)
        if verbose:
            print(result.summary(frozen=frozen))
            if result.temps_are_default is False and (
                result.fuel_temp_k or result.ox_temp_k
            ):
                print(
                    f"inlet T: fuel={result.fuel_temp_k} K  ox={result.ox_temp_k} K"
                )
        return result

    def performance(
        self, of_ratio: float, pc_bar: float, eps: float
    ) -> PerformanceResult:
        """Classic API: evaluate(of_ratio, pc_bar, eps)."""
        return self.evaluate(of=of_ratio, pc=pc_bar, eps=eps)

    def _compute(
        self,
        of_ratio: float,
        pc_bar: float,
        eps: float,
        *,
        include_stations: bool = True,
    ) -> PerformanceResult:
        cache = self._get_cache()
        key = None
        if cache is not None:
            key = ResultCache.make_key(
                self.fuel,
                self.oxidizer,
                of_ratio,
                pc_bar,
                eps,
                self.fuel_temp_k,
                self.ox_temp_k,
                method="cea_performance_v2",
                eta_cstar=self.eta_cstar,
                eta_cf=self.eta_cf,
                cryo=self.apply_cryo_defaults,
                full=include_stations,
            )
            hit = cache.get(key, PerformanceResult)
            if hit is not None:
                hit.from_cache = True
                return hit

        result = cea_backend.compute_performance(
            fuel=self.fuel,
            oxidizer=self.oxidizer,
            of_ratio=of_ratio,
            pc_bar=pc_bar,
            eps=eps,
            fuel_temp_k=self.fuel_temp_k,
            ox_temp_k=self.ox_temp_k,
            eta_cstar=self.eta_cstar,
            eta_cf=self.eta_cf,
            apply_cryo_defaults=self.apply_cryo_defaults,
            include_stations=include_stations,
        )
        if cache is not None and key is not None:
            cache.set(key, result)
        return result

    def scan_of(
        self,
        of_range: tuple[float, float, float] | None = None,
        pc: float | None = None,
        eps: float | None = None,
        *,
        pc_bar: float | None = None,
        expansion_ratio: float | None = None,
        plot: bool = False,
        save: str | None = None,
        show: bool = False,
        verbose: bool = False,
    ) -> SweepResult:
        """Scan mixture ratio (O/F). Alias: ``scan_mixture_ratio``, ``sweep_of_ratio``."""
        pc_v, eps_v = resolve_pc_eps(pc_bar if pc_bar is not None else pc, eps, expansion_ratio=expansion_ratio)
        validate_pc(pc_v)
        validate_eps(eps_v)
        if of_range is None:
            from propwrap.trades import _default_range_for

            of_range = _default_range_for(self.fuel, self.oxidizer, (1.8, 3.5, 0.1))
        values = expand_range(of_range)
        results = [self._compute(v, pc_v, eps_v) for v in values]
        sweep = SweepResult(
            sweep_variable="of_ratio",
            values=values,
            results=results,
            stoich_of_ratio=stoich_of_ratio(self.fuel, self.oxidizer),
        )
        if plot or save:
            sweep.plot(save=save, show=show)
        if verbose:
            print(sweep.summary())
        return sweep

    def scan_mixture_ratio(self, *args: Any, **kwargs: Any) -> SweepResult:
        return self.scan_of(*args, **kwargs)

    def sweep_of_ratio(
        self,
        of_range: tuple[float, float, float],
        pc_bar: float,
        eps: float,
    ) -> SweepResult:
        return self.scan_of(of_range, pc=pc_bar, eps=eps)

    def sweep_pc(
        self,
        of_ratio: float,
        pc_range: tuple[float, float, float],
        eps: float,
        *,
        plot: bool = False,
        save: str | None = None,
        show: bool = False,
    ) -> SweepResult:
        values = expand_range(pc_range)
        results = [self._compute(of_ratio, v, eps) for v in values]
        sweep = SweepResult(sweep_variable="pc_bar", values=values, results=results)
        if plot or save:
            sweep.plot(save=save, show=show)
        return sweep

    def sweep_eps(
        self,
        of_ratio: float,
        pc_bar: float,
        eps_range: tuple[float, float, float],
        *,
        plot: bool = False,
        save: str | None = None,
        show: bool = False,
    ) -> SweepResult:
        values = expand_range(eps_range)
        results = [self._compute(of_ratio, pc_bar, v) for v in values]
        sweep = SweepResult(sweep_variable="eps", values=values, results=results)
        if plot or save:
            sweep.plot(save=save, show=show)
        return sweep

    def density_impulse(
        self,
        of_range: tuple[float, float, float] | None = None,
        pc: float | None = None,
        eps: float | None = None,
        *,
        pc_bar: float | None = None,
        expansion_ratio: float | None = None,
        plot: bool = False,
        save: str | None = None,
        show: bool = False,
        verbose: bool = False,
    ) -> DensityIspCurve:
        """Density-Isp vs O/F for this pair."""
        from propwrap.trades import density_isp_curve

        pc_v, eps_v = resolve_pc_eps(
            pc_bar if pc_bar is not None else pc, eps, expansion_ratio=expansion_ratio
        )
        if of_range is None:
            from propwrap.trades import _default_range_for

            of_range = _default_range_for(self.fuel, self.oxidizer, (1.8, 3.5, 0.1))
        curve = density_isp_curve(
            self.fuel,
            self.oxidizer,
            of_range,
            pc_v,
            eps_v,
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
        )
        if plot or save:
            curve.plot(save=save, show=show)
        if verbose:
            print(curve.summary())
        return curve

    def product_gamma_profile(
        self,
        of: float | None = None,
        pc: float | None = None,
        eps_range: tuple[float, float, float] | None = None,
        *,
        of_ratio: float | None = None,
        use_cantera: bool = False,
        frozen: bool = True,
        plot: bool = False,
        save: str | None = None,
        show: bool = False,
    ) -> GammaProfile:
        """γ (and T, Mw) of combustion products vs expansion ratio."""
        of_v = of if of is not None else of_ratio
        if of_v is None:
            raise PropwrapError("of= mixture ratio required for product_gamma_profile")
        pc_v, _ = resolve_pc_eps(pc, None)
        if eps_range is None:
            eps_range = (2.0, 40.0, 2.0)
        profile = self.gamma_vs_area_ratio(
            of_v, pc_v, eps_range, use_cantera=use_cantera, frozen=frozen
        )
        if plot or save:
            profile.plot(save=save, show=show)
        return profile

    def gamma_vs_area_ratio(
        self,
        of_ratio: float,
        pc_bar: float,
        eps_range: tuple[float, float, float],
        use_cantera: bool = True,
        *,
        frozen: bool = True,
    ) -> GammaProfile:
        from propwrap import cantera_backend

        values = expand_range(eps_range)
        if values and values[0] > 1.01:
            values = [1.0] + values
        profile = cea_backend.nozzle_profile(
            self.fuel,
            self.oxidizer,
            of_ratio,
            pc_bar,
            values,
            frozen=frozen,
            fuel_temp_k=self.fuel_temp_k,
            ox_temp_k=self.ox_temp_k,
        )
        if use_cantera:
            chamber = cea_backend.chamber_state(
                self.fuel,
                self.oxidizer,
                of_ratio,
                pc_bar,
                eps=values[-1],
                fuel_temp_k=self.fuel_temp_k,
                ox_temp_k=self.ox_temp_k,
            )
            g_ct: list[float] = []
            for te, gcea in zip(profile.temperatures_k, profile.gamma_cea):
                try:
                    g_ct.append(
                        cantera_backend.gamma_frozen(
                            T_k=te,
                            P_bar=pc_bar,
                            species_mole_fractions=chamber["species_mole_fractions"],
                            fallback_gamma=gcea,
                        )
                    )
                except Exception:
                    g_ct.append(gcea)
            profile.gamma_cantera = g_ct
        return profile

    def study(
        self,
        of: float,
        pc: float | None = None,
        eps: float | None = None,
        *,
        of_range: tuple[float, float, float] | None = None,
        eps_range: tuple[float, float, float] | None = (5.0, 30.0, 5.0),
        verbose: bool = False,
    ) -> MixtureStudy:
        """Mixture study at a point + optional O/F scan (alias of engine_case)."""
        pc_v, eps_v = resolve_pc_eps(pc, eps)
        design = self.evaluate(of=of, pc=pc_v, eps=eps_v)
        notes = list(design.warnings)
        of_sw = self.scan_of(of_range, pc=pc_v, eps=eps_v) if of_range else None
        eps_sw = (
            self.sweep_eps(of, pc_v, eps_range) if eps_range is not None else None
        )
        gprof = self.product_gamma_profile(
            of=of, pc=pc_v, eps_range=eps_range or (2.0, eps_v, max(1.0, (eps_v - 2) / 5))
        )
        if of_sw is not None:
            od = of_sw.off_design(of)
            notes.append(
                f"O/F off-design: {od['loss_pct']:.2f}% Isp below peak "
                f"(peak O/F={od['optimum_of']:.3f})"
            )
        out = MixtureStudy(
            design=design,
            of_sweep=of_sw,
            eps_sweep=eps_sw,
            gamma_profile=gprof,
            notes=notes,
        )
        if verbose:
            print(out.summary())
        return out

    def engine_case(self, of_ratio: float, pc_bar: float, eps: float, **kwargs: Any) -> MixtureStudy:
        return self.study(of=of_ratio, pc=pc_bar, eps=eps, **kwargs)

    def ambient_performance(
        self,
        of_ratio: float,
        pc_bar: float,
        eps: float,
        pamb_bar: float,
        *,
        frozen: bool = False,
    ) -> dict[str, float | str]:
        return cea_backend.ambient_isp(
            self.fuel,
            self.oxidizer,
            of_ratio,
            pc_bar,
            eps,
            pamb_bar,
            self.fuel_temp_k,
            self.ox_temp_k,
            frozen=frozen,
        )

    def cross_validate(
        self,
        of_ratio: float,
        pc_bar: float,
        eps: float,
        tolerance_pct: float = 5.0,
    ) -> list[CrossValidationResult]:
        from propwrap.cross_validation import run_cross_validation

        return run_cross_validation(
            fuel=self.fuel,
            oxidizer=self.oxidizer,
            of_ratio=of_ratio,
            pc_bar=pc_bar,
            eps=eps,
            tolerance_pct=tolerance_pct,
            fuel_temp_k=self.fuel_temp_k,
            ox_temp_k=self.ox_temp_k,
        )

    def compare_to(
        self,
        other: Mixture,
        of_ratio: float,
        pc_bar: float,
        eps: float,
    ) -> dict[str, Any]:
        a = self.evaluate(of=of_ratio, pc=pc_bar, eps=eps)
        b = other.evaluate(of=of_ratio, pc=pc_bar, eps=eps)
        a_d, b_d = a.model_dump(), b.model_dump()
        delta: dict[str, Any] = {}
        for k, va in a_d.items():
            vb = b_d.get(k)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
                delta[k] = float(va) - float(vb)
            else:
                delta[k] = None
        return {
            "self": a_d,
            "other": b_d,
            "delta": delta,
            "labels": {
                "self": f"{self.fuel}/{self.oxidizer}",
                "other": f"{other.fuel}/{other.oxidizer}",
            },
        }

    def sanity(self, result: PerformanceResult) -> list[str]:
        return sanity_check(result)

    def clear_cache(self) -> int:
        if self._cache is not None:
            return self._cache.clear()
        return clear_default_cache()

    def __repr__(self) -> str:
        return f"Mixture({self.fuel!r}, {self.oxidizer!r})"

    def __str__(self) -> str:
        return f"{self.fuel}/{self.oxidizer}"


# Friendly / legacy aliases
Propellant = Mixture
PropellantPair = Mixture
