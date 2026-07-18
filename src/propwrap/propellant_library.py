"""Name resolution, custom cards, densities — backed by the registry."""

from __future__ import annotations

from typing import Any

from propwrap.registry import (
    PropellantRecord,
    density_g_cm3 as registry_density,
    get_propellant,
    list_registry,
    register,
    resolve_name,
)

# Legacy alias tables kept for tests / explicit exports
_FUEL_ALIASES: dict[str, str] = {
    "RP-1": "RP1",
    "RP1": "RP1",
    "RP_1": "RP1",
    "KEROSENE": "RP1",
    "LH2": "LH2",
    "H2": "LH2",
    "HYDROGEN": "LH2",
    "MMH": "MMH",
    "UDMH": "UDMH",
    "A50": "A50",
    "AEROZINE-50": "A50",
    "AEROZINE50": "A50",
    "CH4": "CH4",
    "LCH4": "CH4",
    "METHANE": "CH4",
    "C2H5OH": "Ethanol",
    "ETHANOL": "Ethanol",
    "JP-4": "JP4",
    "JP4": "JP4",
    "JP-5": "JP5",
    "JP5": "JP5",
    "JP-10": "JP10",
    "JP10": "JP10",
}

_OX_ALIASES: dict[str, str] = {
    "LOX": "LOX",
    "O2": "LOX",
    "LO2": "LOX",
    "OXYGEN": "LOX",
    "N2O4": "N2O4",
    "NTO": "N2O4",
    "N2O": "N2O",
    "NITROUS": "N2O",
    "H2O2": "H2O2",
    "HTP": "H2O2",
    "FLOX70": "FLOX70",
    "CLF5": "CLF5",
    "IRFNA": "IRFNA",
    "AIR": "Air",
}

_CUSTOM_PROPELLANTS: dict[str, dict[str, Any]] = {}


def normalize_name(name: str, *, kind: str = "fuel") -> str:
    """Normalize to canonical registry / CEA name."""
    k = "fuel" if kind == "fuel" else "oxidizer"
    resolved = resolve_name(name, kind=k)  # type: ignore[arg-type]
    # custom cards
    if resolved in _CUSTOM_PROPELLANTS:
        return resolved
    key = name.strip()
    upper = key.upper()
    aliases = _FUEL_ALIASES if kind == "fuel" else _OX_ALIASES
    if upper in aliases:
        return aliases[upper]
    if key in _CUSTOM_PROPELLANTS:
        return key
    for reg in _CUSTOM_PROPELLANTS:
        if reg.upper() == upper:
            return reg
    return resolved


def resolve_cea_names(fuel: str, oxidizer: str) -> tuple[str, str]:
    fuel_n = normalize_name(fuel, kind="fuel")
    ox_n = normalize_name(oxidizer, kind="oxidizer")
    if fuel_n in _CUSTOM_PROPELLANTS:
        _ensure_registered(fuel_n)
    if ox_n in _CUSTOM_PROPELLANTS:
        _ensure_registered(ox_n)
    frec = get_propellant(fuel_n)
    orec = get_propellant(ox_n)
    # Blends: RocketCEA knows the auto-generated name (cea_name)
    if frec and frec.cea_name:
        fuel_n = frec.cea_name
    if orec and orec.cea_name:
        ox_n = orec.cea_name
    return fuel_n, ox_n


def _ensure_registered(name: str) -> None:
    entry = _CUSTOM_PROPELLANTS[name]
    if entry.get("_registered"):
        return
    card = entry["card_str"]
    kind = entry["kind"]
    try:
        if kind == "fuel":
            from rocketcea.cea_obj import add_new_fuel

            add_new_fuel(name, card)
        else:
            from rocketcea.cea_obj import add_new_oxidizer

            add_new_oxidizer(name, card)
        entry["_registered"] = True
    except ImportError:
        from rocketcea import cea_obj as cea_mod

        if kind == "fuel" and hasattr(cea_mod, "add_new_fuel"):
            cea_mod.add_new_fuel(name, card)
            entry["_registered"] = True
        elif kind == "oxidizer" and hasattr(cea_mod, "add_new_oxidizer"):
            cea_mod.add_new_oxidizer(name, card)
            entry["_registered"] = True
        else:
            raise RuntimeError(
                f"Cannot register custom propellant '{name}'"
            ) from None


def list_propellants() -> dict[str, list[str]]:
    fuels = [r.name for r in list_registry(kind="fuel")]
    oxs = [r.name for r in list_registry(kind="oxidizer")]
    custom = sorted(_CUSTOM_PROPELLANTS.keys())
    blends = [r.name for r in list_registry() if r.is_blend]
    return {"fuels": fuels, "oxidizers": oxs, "custom": custom, "blends": blends}


def add_custom_propellant(
    name: str,
    formula: str,
    heat_of_formation: float,
    *,
    kind: str = "fuel",
    temperature_k: float = 298.15,
    density_g_ml: float | None = None,
    hf_unit: str = "cal/mol",
    comment: str = "",
) -> str:
    """Register a single-species custom propellant card.

    Parameters
    ----------
    heat_of_formation :
        Enthalpy of formation. Default unit ``cal/mol`` (CEA convention).
        Pass ``hf_unit="kJ/mol"`` to convert automatically.
    """
    if not name or not name.strip():
        raise ValueError("name is required")
    if not formula or not formula.strip():
        raise ValueError("formula is required")
    if kind not in ("fuel", "oxidizer"):
        raise ValueError("kind must be 'fuel' or 'oxidizer'")
    if not isinstance(heat_of_formation, (int, float)):
        raise ValueError("heat_of_formation must be a number")

    hf = float(heat_of_formation)
    if hf_unit in ("kJ/mol", "kj/mol"):
        hf = hf * 1000.0 / 4.184  # kJ/mol → cal/mol
    elif hf_unit not in ("cal/mol", "cal_mol"):
        raise ValueError("hf_unit must be 'cal/mol' or 'kJ/mol'")

    name = name.strip()
    formula_cea = _to_cea_formula(formula.strip())
    density_line = ""
    if density_g_ml is not None:
        if density_g_ml <= 0:
            raise ValueError("density_g_ml must be > 0")
        density_line = f"  rho={density_g_ml:.5f}\n"

    prefix = "fuel" if kind == "fuel" else "oxid"
    card = (
        f"{prefix} {name} {formula_cea}  wt%=100.00\n"
        f"h,cal={hf:.4f}  t(k)={temperature_k:.2f}\n"
        f"{density_line}"
    )
    if comment:
        card = f"! {comment}\n" + card

    _CUSTOM_PROPELLANTS[name] = {
        "card_str": card,
        "kind": kind,
        "formula": formula_cea,
        "heat_of_formation": hf,
        "temperature_k": float(temperature_k),
        "density_g_ml": density_g_ml,
        "_registered": False,
    }
    _ensure_registered(name)

    register(
        PropellantRecord(
            name=name,
            kind=kind,  # type: ignore[arg-type]
            formula=formula_cea,
            density_g_cm3=density_g_ml,
            default_temp_k=temperature_k,
            heat_of_formation_cal_mol=hf,
            storage="unknown",
            notes=comment or "custom single-species card",
            source="custom-card",
        ),
        overwrite=True,
    )
    return card


def _to_cea_formula(formula: str) -> str:
    import re

    if " " in formula:
        return formula
    parts = re.findall(r"([A-Z][a-z]?)(\d*\.?\d*)", formula)
    if not parts:
        raise ValueError(
            f"Cannot parse formula '{formula}'. "
            "Use CEA form like 'C 12 H 26' or molecular 'C12H26'."
        )
    tokens: list[str] = []
    for elem, count in parts:
        tokens.append(elem)
        tokens.append(count if count else "1")
    return " ".join(tokens)


def get_custom_card(name: str) -> str | None:
    entry = _CUSTOM_PROPELLANTS.get(name)
    return entry["card_str"] if entry else None


def clear_custom_propellants() -> None:
    _CUSTOM_PROPELLANTS.clear()


def liquid_density_g_cm3(name: str) -> float | None:
    d = registry_density(name)
    if d is not None:
        return d
    rec = get_propellant(name)
    return rec.density_g_cm3 if rec else None


def bulk_density_g_cm3(
    fuel: str, oxidizer: str, of_ratio: float
) -> tuple[float | None, str | None]:
    """Mixture bulk density ρ = (of+1) / (of/ρox + 1/ρfuel) [g/cm³]."""
    rf = liquid_density_g_cm3(fuel)
    ro = liquid_density_g_cm3(oxidizer)
    if rf is None or ro is None or of_ratio <= 0:
        return None, None
    bulk = (of_ratio + 1.0) / (of_ratio / ro + 1.0 / rf)
    basis = f"ρ_fuel={rf:.4f}, ρ_ox={ro:.4f} g/cm³ (registry)"
    return bulk, basis


def cryo_default_temps_k(
    fuel: str, oxidizer: str
) -> tuple[float | None, float | None]:
    frec = get_propellant(fuel, kind="fuel")
    orec = get_propellant(oxidizer, kind="oxidizer")
    ft = frec.default_temp_k if frec and frec.storage in ("cryogenic", "semi_cryogenic") else None
    ot = orec.default_temp_k if orec and orec.storage in ("cryogenic", "semi_cryogenic") else None
    # LOX always cryo default if oxidizer is LOX
    if orec and orec.name == "LOX":
        ot = orec.default_temp_k
    if frec and frec.name in ("LH2", "CH4"):
        ft = frec.default_temp_k
    if ft is None and ot is None:
        return None, None
    return ft, ot


def stoich_of_ratio(fuel: str, oxidizer: str, cea: Any | None = None) -> float | None:
    try:
        if cea is None:
            from rocketcea.cea_obj import CEA_Obj

            fn, on = resolve_cea_names(fuel, oxidizer)
            cea = CEA_Obj(oxName=on, fuelName=fn)
        if hasattr(cea, "getMRforER"):
            return float(cea.getMRforER(1.0))
    except Exception:
        return None
    return None
