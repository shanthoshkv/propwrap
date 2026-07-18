"""Cantera / NASA-9 polynomial thermo for frozen γ cross-checks.

CEA and Cantera do not share an identical species set. We map major combustion
products into a Cantera ideal-gas phase (gri30 or nasa_gas when available) and
evaluate frozen γ = cp/cv at the CEA temperature and pressure.
"""

from __future__ import annotations

from typing import Any

# CEA / common rocket species → Cantera gri30-style names
_SPECIES_MAP: dict[str, str] = {
    "CO2": "CO2",
    "CO": "CO",
    "H2O": "H2O",
    "H2": "H2",
    "O2": "O2",
    "OH": "OH",
    "H": "H",
    "O": "O",
    "N2": "N2",
    "NO": "NO",
    "NO2": "NO2",
    "N": "N",
    "NH3": "NH3",
    "CH4": "CH4",
    "C2H2": "C2H2",
    "C2H4": "C2H4",
    "AR": "AR",
    "Ar": "AR",
    "HO2": "HO2",
    "H2O2": "H2O2",
    # condensed / solid markers from CEA — skip
    "*C(gr)": "",
    "C(gr)": "",
    "*AL2O3(L)": "",
    "AL2O3(L)": "",
}


def _get_solution() -> Any:
    """Load a Cantera Solution suitable for high-T product thermo."""
    import cantera as ct

    for name in ("nasa_gas.yaml", "gri30.yaml", "h2o2.yaml"):
        try:
            return ct.Solution(name)
        except Exception:
            continue
    # Last resort: pure air-like — still allows γ at T if composition set fails
    return ct.Solution("gri30.yaml")


def map_species(species_mole_fractions: dict[str, float]) -> dict[str, float]:
    """Map CEA species names to Cantera names; drop unmapped; renormalize."""
    mapped: dict[str, float] = {}
    for name, x in species_mole_fractions.items():
        # strip asterisks / phase markers
        clean = name.strip().lstrip("*")
        # drop condensed phase markers like (L), (S), (gr)
        base = clean.split("(")[0]
        ct_name = _SPECIES_MAP.get(name) or _SPECIES_MAP.get(clean) or _SPECIES_MAP.get(base)
        if not ct_name:
            # try exact base if present in map keys via upper
            ct_name = _SPECIES_MAP.get(base.upper(), "")
            if not ct_name and base.upper() in {
                "CO2",
                "CO",
                "H2O",
                "H2",
                "O2",
                "OH",
                "N2",
                "NO",
                "H",
                "O",
                "N",
            }:
                ct_name = base.upper() if base.upper() != "AR" else "AR"
        if ct_name and x > 0:
            mapped[ct_name] = mapped.get(ct_name, 0.0) + float(x)

    total = sum(mapped.values())
    if total <= 0:
        return {}
    return {k: v / total for k, v in mapped.items()}


def gamma_frozen(
    T_k: float,
    P_bar: float,
    species_mole_fractions: dict[str, float],
    fallback_gamma: float | None = None,
) -> float:
    """Frozen γ = cp/cv at (T [K], P [bar]) for the given mole fractions.

    If composition cannot be set (empty map / missing species), returns
    ``fallback_gamma`` when provided, else raises.
    """
    import cantera as ct

    mapped = map_species(species_mole_fractions)
    gas = _get_solution()

    if not mapped:
        if fallback_gamma is not None:
            return float(fallback_gamma)
        raise ValueError("No mappable species for Cantera γ evaluation")

    # Keep only species present in the phase
    species_in_phase = {s: x for s, x in mapped.items() if s in gas.species_names}
    if not species_in_phase:
        if fallback_gamma is not None:
            return float(fallback_gamma)
        raise ValueError(
            f"None of {list(mapped)} exist in Cantera phase {gas.name}"
        )
    total = sum(species_in_phase.values())
    species_in_phase = {k: v / total for k, v in species_in_phase.items()}

    P_pa = P_bar * 1e5
    gas.TPX = T_k, P_pa, species_in_phase
    # Frozen γ
    cp = gas.cp_mass
    cv = gas.cv_mass
    if cv <= 0:
        raise RuntimeError("Cantera returned non-positive cv")
    return float(cp / cv)


def gamma_from_cea_chamber(
    T_k: float,
    P_bar: float,
    species_mole_fractions: dict[str, float],
    cea_gamma: float,
) -> float:
    """Convenience: frozen γ with CEA γ as fallback."""
    return gamma_frozen(
        T_k, P_bar, species_mole_fractions, fallback_gamma=cea_gamma
    )
