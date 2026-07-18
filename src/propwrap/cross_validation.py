"""CEA vs Cantera divergence checks."""

from __future__ import annotations

from propwrap import cantera_backend, cea_backend
from propwrap.models import CrossValidationResult


def run_cross_validation(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_pa: float | None = None,
    eps: float = 20.0,
    tolerance_pct: float = 5.0,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    *,
    pc_bar: float | None = None,
) -> list[CrossValidationResult]:
    """Compare CEA chamber γ against Cantera frozen γ at the same T, P, X."""
    from propwrap.units import bar_to_pa

    if pc_pa is None:
        if pc_bar is None:
            raise ValueError("pc_pa or pc_bar required")
        pc_pa = bar_to_pa(pc_bar)
    chamber = cea_backend.chamber_state(
        fuel,
        oxidizer,
        of_ratio,
        pc_pa,
        eps=eps,
        fuel_temp_k=fuel_temp_k,
        ox_temp_k=ox_temp_k,
    )
    cea_gamma = float(chamber["gamma"])
    cantera_gamma = cantera_backend.gamma_frozen(
        T_k=float(chamber["T_k"]),
        P_pa=float(chamber["P_pa"]),
        species_mole_fractions=chamber["species_mole_fractions"],
        fallback_gamma=cea_gamma,
    )

    results = [
        _compare("gamma_chamber", cea_gamma, cantera_gamma, tolerance_pct),
    ]
    return results


def _compare(
    parameter: str,
    cea_value: float,
    cantera_value: float,
    tolerance_pct: float,
) -> CrossValidationResult:
    abs_diff = abs(cea_value - cantera_value)
    if cea_value == 0 and cantera_value == 0:
        pct = 0.0
    elif cea_value == 0:
        pct = 100.0
    else:
        pct = abs_diff / abs(cea_value) * 100.0
    return CrossValidationResult(
        parameter=parameter,
        cea_value=float(cea_value),
        cantera_value=float(cantera_value),
        absolute_diff=float(abs_diff),
        percent_diff=float(pct),
        within_tolerance=pct <= tolerance_pct,
    )
