"""Cantera / NASA-9 polynomial thermo for frozen γ cross-checks.

CEA and Cantera do not share an identical species set. We look CEA product
names up directly in a Cantera ideal-gas phase (nasa_gas or gri30) and
evaluate frozen γ = cp/cv at the CEA temperature and pressure.
"""

from __future__ import annotations

import warnings
from functools import lru_cache
from typing import Any

_ALIASES = {"Ar": "AR"}


@lru_cache(maxsize=1)
def _get_solution() -> Any:
    """Load a Cantera Solution suitable for high-T product thermo."""
    from propwrap.errors import require

    ct = require("cantera", "cantera")
    for name in ("nasa_gas.yaml", "gri30.yaml"):
        try:
            return ct.Solution(name)
        except ct.CanteraError:
            continue
    return ct.Solution("h2o2.yaml")


def map_species(species_mole_fractions: dict[str, float]) -> dict[str, float]:
    """Map CEA species names onto the Cantera phase; drop unknown; renormalize.

    Condensed species (``(L)``, ``(S)``, ``(gr)``) are dropped with a warning
    when they carry > 0.1 % of the mixture — γ is then gas-phase only.
    """
    names = set(_get_solution().species_names)
    mapped: dict[str, float] = {}
    condensed = 0.0
    for name, x in species_mole_fractions.items():
        clean = name.strip().lstrip("*")
        if "(" in clean:
            condensed += float(x)
            continue
        ct_name = _ALIASES.get(clean, clean)
        if ct_name not in names:
            ct_name = clean.upper()
        if ct_name in names and x > 0:
            mapped[ct_name] = mapped.get(ct_name, 0.0) + float(x)

    if condensed > 1e-3:
        warnings.warn(
            f"Cantera γ ignores condensed species (mole fraction {condensed:.3f})",
            stacklevel=2,
        )
    total = sum(mapped.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in mapped.items()}


def gamma_frozen(
    T_k: float,
    P_pa: float | None = None,
    species_mole_fractions: dict[str, float] | None = None,
    fallback_gamma: float | None = None,
    *,
    P_bar: float | None = None,
) -> float:
    """Frozen γ = cp/cv at (T [K], P [Pa]) for the given mole fractions.

    ``P_bar`` is accepted for back-compat and converted to Pa.
    """
    if species_mole_fractions is None:
        species_mole_fractions = {}
    if P_pa is None:
        if P_bar is not None:
            from propwrap.units import bar_to_pa

            P_pa = bar_to_pa(P_bar)
        else:
            raise ValueError("P_pa (or P_bar) required")

    mapped = map_species(species_mole_fractions)
    if not mapped:
        if fallback_gamma is not None:
            return float(fallback_gamma)
        raise ValueError("No mappable species for Cantera γ evaluation")

    gas = _get_solution()
    gas.TPX = T_k, float(P_pa), mapped
    cv = gas.cv_mass
    if cv <= 0:
        raise RuntimeError("Cantera returned non-positive cv")
    return float(gas.cp_mass / cv)


def gamma_from_cea_chamber(
    T_k: float,
    P_pa: float,
    species_mole_fractions: dict[str, float],
    cea_gamma: float,
) -> float:
    """Convenience: frozen γ with CEA γ as fallback."""
    return gamma_frozen(
        T_k, P_pa, species_mole_fractions, fallback_gamma=cea_gamma
    )


def equilibrium_hp(
    fuel_species: str,
    ox_species: str,
    of_ratio: float,
    P_pa: float,
    T0_k: float = 298.15,
) -> tuple[float, float]:
    """Independent adiabatic (HP) equilibrium: return ``(Tc [K], MW [kg/kmol])``.

    Reactants are Cantera gas species (e.g. ``"CH4"``, ``"H2"``, ``"O2"``).
    """
    # ponytail: gaseous reactants at T0 — no liquid enthalpy / latent heat, so Tc
    # reads high vs CEA for cryogenic liquids; add an inlet-enthalpy offset if needed.
    gas = _get_solution()
    gas.TPY = T0_k, float(P_pa), {
        fuel_species: 1.0 / (1.0 + of_ratio),
        ox_species: of_ratio / (1.0 + of_ratio),
    }
    gas.equilibrate("HP")
    return float(gas.T), float(gas.mean_molecular_weight)
