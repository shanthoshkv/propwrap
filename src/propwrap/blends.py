"""Multi-component propellant blend cards (fuels or oxidizers)."""

from __future__ import annotations

from typing import Sequence

from propwrap.registry import PropellantRecord, register, resolve_name


class BlendComponent:
    """One species in a blend: name + weight percent."""

    __slots__ = ("name", "wt_percent")

    def __init__(self, name: str, wt_percent: float) -> None:
        self.name = name.strip()
        self.wt_percent = float(wt_percent)


def add_blend(
    name: str,
    components: Sequence[tuple[str, float]] | Sequence[BlendComponent],
    *,
    kind: str = "fuel",
    density_kg_m3: float | None = None,
    density_g_cm3: float | None = None,
    default_temp_k: float | None = None,
    notes: str = "",
) -> str:
    """Register a multi-component blend and make it usable as fuel/ox name.

    Parameters
    ----------
    name :
        Canonical name for the blend (used later in ``Propellant(fuel=name, ...)``).
    components :
        Sequence of ``(species_name, weight_percent)`` or :class:`BlendComponent`.
        Weight percents must sum to 100 ± 0.5.
    kind :
        ``"fuel"`` or ``"oxidizer"``.
    density_kg_m3 :
        Optional bulk liquid density [kg/m³]. If omitted, mass-weighted from
        registry densities when all components have densities.
    density_g_cm3 :
        Optional density [g/cm³]; converted to kg/m³ if ``density_kg_m3`` omitted.
    default_temp_k :
        Optional default inlet temperature [K].
    notes :
        Free-text provenance.

    Returns
    -------
    str
        The RocketCEA-facing blend name (usually ``name``).

    Notes
    -----
    Uses RocketCEA ``newFuelBlend`` / ``newOxBlend`` for built-in species.
    """
    if kind not in ("fuel", "oxidizer"):
        raise ValueError("kind must be 'fuel' or 'oxidizer'")
    if not name or not name.strip():
        raise ValueError("name is required")
    name = name.strip()

    comps: list[tuple[str, float]] = []
    for c in components:
        if isinstance(c, BlendComponent):
            comps.append((c.name, c.wt_percent))
        else:
            comps.append((str(c[0]), float(c[1])))

    if len(comps) < 2:
        raise ValueError("blend requires at least 2 components")

    total = sum(w for _, w in comps)
    if abs(total - 100.0) > 0.5:
        raise ValueError(f"weight percents must sum to ~100, got {total:.2f}")

    scale = 100.0 / total
    names: list[str] = []
    pcts: list[float] = []
    for n, w in comps:
        from propwrap.registry import get_propellant

        rec = get_propellant(n)
        names.append(rec.name if rec else resolve_name(n, kind=kind))  # type: ignore[arg-type]
        pcts.append(w * scale)

    if kind == "fuel":
        from rocketcea.blends import newFuelBlend

        cea_name = newFuelBlend(fuelL=names, fuelPcentL=pcts)
    else:
        from rocketcea.blends import newOxBlend

        cea_name = newOxBlend(oxL=names, oxPcentL=pcts)

    # RocketCEA may return its own name string; prefer user name if it registered under that
    # newFuelBlend returns e.g. MMH_50_UDMH_50 — we also register user alias
    blend_name = str(cea_name)

    dens = density_kg_m3
    if dens is None and density_g_cm3 is not None:
        from propwrap.units import g_cm3_to_kg_m3

        dens = g_cm3_to_kg_m3(density_g_cm3)
    if dens is None:
        from propwrap.registry import get_propellant

        acc = 0.0
        ok = True
        for n, w in zip(names, pcts):
            rec = get_propellant(n)
            d = rec.density_kg_m3 if rec else None
            if d is None:
                ok = False
                break
            acc += (w / 100.0) / d
        if ok and acc > 0:
            dens = 1.0 / acc

    blend_map = {n: p for n, p in zip(names, pcts)}
    register(
        PropellantRecord(
            name=name,
            kind=kind,  # type: ignore[arg-type]
            aliases=[blend_name] if blend_name != name else [],
            density_kg_m3=dens,
            default_temp_k=default_temp_k,
            storage="storable",
            is_blend=True,
            blend_components=blend_map,
            cea_name=blend_name,
            notes=notes or f"blend {blend_map}",
            source="custom-blend",
        ),
        overwrite=True,
    )
    if blend_name != name:
        register(
            PropellantRecord(
                name=blend_name,
                kind=kind,  # type: ignore[arg-type]
                aliases=[name],
                density_kg_m3=dens,
                default_temp_k=default_temp_k,
                storage="storable",
                is_blend=True,
                blend_components=blend_map,
                cea_name=blend_name,
                notes=notes or f"blend {blend_map}",
                source="custom-blend",
            ),
            overwrite=True,
        )

    return name


def blend_card_summary(name: str) -> str:
    """Human-readable summary of a registered blend."""
    from propwrap.registry import get_propellant

    rec = get_propellant(name)
    if rec is None or not rec.is_blend or not rec.blend_components:
        raise ValueError(f"'{name}' is not a registered blend")
    parts = [f"{n} {p:.1f}%" for n, p in rec.blend_components.items()]
    dens = f", ρ={rec.density_kg_m3:.1f} kg/m³" if rec.density_kg_m3 else ""
    return f"{rec.name} ({rec.kind}): " + " + ".join(parts) + dens
