"""Session defaults and shared study context (Pc, ε, plot flags)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

_DEFAULTS: dict[str, Any] = {
    "pc_bar": 70.0,
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
    """Set process-wide defaults for evaluate/scan/compare.

    Recognized keys: pc_bar, eps (or expansion_ratio), plot, show, save,
    verbose, full, cache_enabled, apply_cryo_defaults.
    """
    for k, v in kwargs.items():
        if k == "expansion_ratio":
            k = "eps"
        if k == "pc":
            k = "pc_bar"
        if k not in _DEFAULTS and k not in ("pc_bar", "eps"):
            # allow setting known keys only
            if k not in _DEFAULTS:
                raise ValueError(
                    f"Unknown default '{k}'. "
                    f"Valid: {sorted(set(_DEFAULTS) | {'pc', 'expansion_ratio'})}"
                )
        _DEFAULTS[k] = v
    return dict(_DEFAULTS)


def get_defaults() -> dict[str, Any]:
    """Return a copy of current session defaults."""
    return dict(_DEFAULTS)


def reset_defaults() -> None:
    """Restore factory defaults."""
    _DEFAULTS.update(
        {
            "pc_bar": 70.0,
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
    pc_bar: float | None = None,
    eps: float | None = None,
    *,
    expansion_ratio: float | None = None,
    pc: float | None = None,
) -> tuple[float, float]:
    d = get_defaults()
    pc_v = pc_bar if pc_bar is not None else (pc if pc is not None else d["pc_bar"])
    eps_v = (
        eps
        if eps is not None
        else (expansion_ratio if expansion_ratio is not None else d["eps"])
    )
    return float(pc_v), float(eps_v)


@dataclass
class Case:
    """Shared thermo boundary conditions for a propellant study.

    Examples
    --------
    >>> case = Case(pc=70, eps=40)
    >>> case.evaluate("RP-1", "LOX", of=2.56)
    >>> case.compare(["RP-1/LOX", "CH4/LOX", "LH2/LOX"])
    """

    pc_bar: float = 70.0
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

    def __post_init__(self) -> None:
        # accept pc= via replace patterns from callers
        pass

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> Case:
        if "pc" in kwargs and "pc_bar" not in kwargs:
            kwargs["pc_bar"] = kwargs.pop("pc")
        if "expansion_ratio" in kwargs and "eps" not in kwargs:
            kwargs["eps"] = kwargs.pop("expansion_ratio")
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in kwargs.items() if k in known})

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
            pc=self.pc_bar,
            eps=self.eps,
            verbose=self.verbose if verbose is None else verbose,
            full=self.full,
            **kwargs,
        )

    def compare(
        self,
        pairs: list[str] | list[tuple[str, str]],
        **kwargs: Any,
    ) -> Any:
        from propwrap.workflows import compare_propellants

        return compare_propellants(
            pairs,
            pc_bar=self.pc_bar,
            eps=self.eps,
            plot=kwargs.get("plot", self.plot),
            save=kwargs.get("save", self.save),
            show=kwargs.get("show", self.show),
            verbose=kwargs.get("verbose", self.verbose),
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
        )

    def characterize(
        self,
        fuel: str,
        oxidizer: str,
        of: float | None = None,
        **kwargs: Any,
    ) -> Any:
        from propwrap.workflows import characterize

        return characterize(
            fuel,
            oxidizer,
            of=of,
            pc_bar=self.pc_bar,
            eps=self.eps,
            plot=kwargs.get("plot", self.plot),
            save=kwargs.get("save", self.save),
            show=kwargs.get("show", self.show),
            verbose=kwargs.get("verbose", self.verbose),
            cache_enabled=self.cache_enabled,
            apply_cryo_defaults=self.apply_cryo_defaults,
        )


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
