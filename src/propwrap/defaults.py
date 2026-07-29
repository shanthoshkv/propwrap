"""Session defaults — SI (pressure in Pa)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from propwrap.units import bar_to_pa, pa_to_bar

# Default: 70 bar = 7 MPa
_DEFAULT_PC_PA = bar_to_pa(70.0)

_DEFAULTS: dict[str, Any] = {
    "pc_pa": _DEFAULT_PC_PA,
    "eps": 40.0,
    "plot": False,
    "show": False,
    "save": None,
    "verbose": False,
    "full": True,
    "cache_enabled": True,
    "apply_cryo_defaults": True,
}


def set_defaults(**kwargs: Any) -> dict[str, Any]:
    """Set process-wide defaults.

    Pressure: ``pc`` / ``pc_pa`` in **Pa**, or ``pc_bar`` / ``pc_mpa`` / ``pc_psi``.
    """
    from propwrap.units import resolve_pressure_pa

    # gather pressure kwargs
    pkeys = ("pc", "pc_pa", "pc_bar", "pc_mpa", "pc_psi", "pc_psia")
    if any(k in kwargs for k in pkeys):
        _DEFAULTS["pc_pa"] = resolve_pressure_pa(
            pc=kwargs.pop("pc", None),
            pc_pa=kwargs.pop("pc_pa", None),
            pc_bar=kwargs.pop("pc_bar", None),
            pc_mpa=kwargs.pop("pc_mpa", None),
            pc_psi=kwargs.pop("pc_psi", None),
            pc_psia=kwargs.pop("pc_psia", None),
            default_pa=_DEFAULTS["pc_pa"],
        )

    for k, v in kwargs.items():
        if k == "expansion_ratio":
            k = "eps"
        if k == "pc_bar":  # leftover
            _DEFAULTS["pc_pa"] = bar_to_pa(v)
            continue
        if k not in _DEFAULTS and k != "eps":
            raise ValueError(
                f"Unknown default '{k}'. "
                f"Valid: pc/pc_pa/pc_bar/pc_mpa, eps, plot, show, save, verbose, full, ..."
            )
        _DEFAULTS[k] = v
    return dict(_DEFAULTS)


def get_defaults() -> dict[str, Any]:
    d = dict(_DEFAULTS)
    d["pc_bar"] = pa_to_bar(d["pc_pa"])  # convenience mirror
    return d


def reset_defaults() -> None:
    _DEFAULTS.update(
        {
            "pc_pa": _DEFAULT_PC_PA,
            "eps": 40.0,
            "plot": False,
            "show": False,
            "save": None,
            "verbose": False,
            "full": True,
            "cache_enabled": True,
            "apply_cryo_defaults": True,
        }
    )


def resolve_pc_eps(
    pc: float | None = None,
    eps: float | None = None,
    *,
    expansion_ratio: float | None = None,
    pc_pa: float | None = None,
    pc_bar: float | None = None,
    pc_mpa: float | None = None,
    pc_psi: float | None = None,
    **_extra: Any,
) -> tuple[float, float]:
    """Return (pc_pa, eps) using session defaults for missing values."""
    from propwrap.units import resolve_pressure_pa

    d = _DEFAULTS
    # If only legacy positional `pc` given without unit, treat as Pa (SI).
    # Callers that still pass bar should use pc_bar=.
    try:
        pc_v = resolve_pressure_pa(
            pc=pc,
            pc_pa=pc_pa,
            pc_bar=pc_bar,
            pc_mpa=pc_mpa,
            pc_psi=pc_psi,
            default_pa=float(d["pc_pa"]),
        )
    except ValueError:
        pc_v = float(d["pc_pa"])

    eps_v = (
        float(eps)
        if eps is not None
        else (
            float(expansion_ratio)
            if expansion_ratio is not None
            else float(d["eps"])
        )
    )
    return pc_v, eps_v


@dataclass
class Case:
    """Shared thermo boundary conditions (Pc in Pa).

    >>> case = Case(pc_bar=70, eps=40)   # convenience
    >>> case = Case(pc_pa=7e6, eps=40)   # SI
    """

    pc_pa: float = _DEFAULT_PC_PA
    eps: float = 40.0
    plot: bool = False
    show: bool = False
    save: str | None = None
    verbose: bool = False
    full: bool = True
    cache_enabled: bool = True
    apply_cryo_defaults: bool = True
    eta_cstar: float = 1.0
    eta_cf: float = 1.0

    def __init__(self, **kwargs: Any) -> None:
        from propwrap.units import resolve_pressure_pa

        pc_pa = kwargs.pop("pc_pa", None)
        if pc_pa is None and any(
            k in kwargs for k in ("pc", "pc_bar", "pc_mpa", "pc_psi", "pc_psia")
        ):
            pc_pa = resolve_pressure_pa(
                pc=kwargs.pop("pc", None),
                pc_bar=kwargs.pop("pc_bar", None),
                pc_mpa=kwargs.pop("pc_mpa", None),
                pc_psi=kwargs.pop("pc_psi", None),
                pc_psia=kwargs.pop("pc_psia", None),
                default_pa=_DEFAULT_PC_PA,
            )
        elif "pc_bar" in kwargs:
            pc_pa = bar_to_pa(kwargs.pop("pc_bar"))
        if pc_pa is None:
            pc_pa = _DEFAULT_PC_PA
        if "expansion_ratio" in kwargs and "eps" not in kwargs:
            kwargs["eps"] = kwargs.pop("expansion_ratio")
        self.pc_pa = float(pc_pa)
        self.eps = float(kwargs.pop("eps", 40.0))
        self.plot = bool(kwargs.pop("plot", False))
        self.show = bool(kwargs.pop("show", False))
        self.save = kwargs.pop("save", None)
        self.verbose = bool(kwargs.pop("verbose", False))
        self.full = bool(kwargs.pop("full", True))
        self.cache_enabled = bool(kwargs.pop("cache_enabled", True))
        self.apply_cryo_defaults = bool(kwargs.pop("apply_cryo_defaults", True))
        self.eta_cstar = float(kwargs.pop("eta_cstar", 1.0))
        self.eta_cf = float(kwargs.pop("eta_cf", 1.0))
        if kwargs:
            raise TypeError(f"Unexpected Case kwargs: {sorted(kwargs)}")

    @property
    def pc_bar(self) -> float:
        return pa_to_bar(self.pc_pa)

    def mixture(self, fuel: str, oxidizer: str) -> Any:
        from propwrap.propellant import Mixture

        return Mixture(
            fuel,
            oxidizer,
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
            eta_cstar=self.eta_cstar,
            eta_cf=self.eta_cf,
        )

    def evaluate(
        self,
        fuel: str,
        oxidizer: str,
        of: float | None = None,
        *,
        of_ratio: float | None = None,
        mixture_ratio: float | None = None,
        verbose: bool | None = None,
        **kwargs: Any,
    ) -> Any:
        of_v = _coalesce_of(of, of_ratio, mixture_ratio)
        m = self.mixture(fuel, oxidizer)
        return m.evaluate(
            of=of_v,
            pc_pa=self.pc_pa,
            eps=self.eps,
            verbose=self.verbose if verbose is None else verbose,
            full=self.full,
            **kwargs,
        )

    def compare(self, pairs: list, **kwargs: Any) -> Any:
        from propwrap.workflows import compare_propellants

        return compare_propellants(
            pairs,
            pc_pa=self.pc_pa,
            eps=self.eps,
            plot=kwargs.get("plot", self.plot),
            save=kwargs.get("save", self.save),
            show=kwargs.get("show", self.show),
            verbose=kwargs.get("verbose", self.verbose),
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
        )

    def characterize(self, fuel: str, oxidizer: str, of: float | None = None, **kwargs: Any) -> Any:
        from propwrap.workflows import characterize

        return characterize(
            fuel,
            oxidizer,
            of=of,
            pc_pa=self.pc_pa,
            eps=self.eps,
            plot=kwargs.get("plot", self.plot),
            save=kwargs.get("save", self.save),
            show=kwargs.get("show", self.show),
            verbose=kwargs.get("verbose", self.verbose),
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
        )

    # --- student / course presets ---
    @classmethod
    def student_lab(cls) -> Case:
        """Typical university lab: moderate Pc, moderate ε, cryo defaults on."""
        return cls(pc_bar=70.0, eps=20.0, apply_cryo_defaults=True, verbose=False)

    @classmethod
    def booster(cls) -> Case:
        """Booster-ish study point: higher Pc, modest ε."""
        return cls(pc_bar=100.0, eps=20.0, apply_cryo_defaults=True)

    @classmethod
    def upper_stage(cls) -> Case:
        """Upper-stage-ish: moderate Pc, large ε (vacuum-oriented)."""
        return cls(pc_bar=50.0, eps=80.0, apply_cryo_defaults=True)

    @classmethod
    def rcs_storable(cls) -> Case:
        """Low-Pc storable / ACS-style study point."""
        return cls(pc_bar=10.0, eps=40.0, apply_cryo_defaults=False)


def _coalesce_of(
    of: float | None,
    of_ratio: float | None,
    mixture_ratio: float | None,
) -> float:
    for v in (of, of_ratio, mixture_ratio):
        if v is not None:
            return float(v)
    raise ValueError(
        "Mixture ratio required: pass of=..., of_ratio=..., or mixture_ratio=..."
    )
