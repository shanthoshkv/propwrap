"""Propellant identity registry — fuels/oxidizers as data, not bare strings."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PropellantKind = Literal["fuel", "oxidizer"]
StorageClass = Literal["cryogenic", "storable", "semi_cryogenic", "gaseous", "unknown"]


class PropellantRecord(BaseModel):
    """Canonical identity for a single propellant species or named blend."""

    model_config = ConfigDict(extra="forbid")

    name: str
    kind: PropellantKind
    aliases: list[str] = Field(default_factory=list)
    formula: str | None = None
    molecular_weight: float | None = None  # g/mol
    density_kg_m3: float | None = None  # liquid handbook density
    default_temp_k: float | None = None  # suggested inlet T
    heat_of_formation_cal_mol: float | None = None
    storage: StorageClass = "unknown"
    hypergolic_with: list[str] = Field(default_factory=list)
    notes: str = ""
    is_blend: bool = False
    blend_components: dict[str, float] | None = None  # name → wt%
    cea_name: str | None = None  # RocketCEA identifier if different from name
    # Typical O/F when this species is the FUEL with a common oxidizer (student hint)
    typical_of_range: tuple[float, float] | None = None
    source: str = "built-in"


# --- built-in registry ---

_RECORDS: dict[str, PropellantRecord] = {}


def _add(rec: PropellantRecord) -> None:
    _RECORDS[rec.name] = rec
    for a in rec.aliases:
        # alias map handled in normalize via registry lookup
        pass


def _seed() -> None:
    if _RECORDS:
        return
    fuels = [
        PropellantRecord(
            name="RP1",
            kind="fuel",
            aliases=["RP-1", "RP_1", "KEROSENE"],
            formula="~C12H24",
            density_kg_m3=810.0,
            default_temp_k=298.15,
            storage="storable",
            notes="Refined kerosene rocket propellant",
            typical_of_range=(2.0, 2.8),
            source="RocketCEA built-in / handbook density",
        ),
        PropellantRecord(
            name="LH2",
            kind="fuel",
            aliases=["H2", "HYDROGEN"],
            formula="H2",
            molecular_weight=2.016,
            density_kg_m3=70.8,
            default_temp_k=20.4,
            storage="cryogenic",
            typical_of_range=(4.5, 6.5),
            notes="With LOX; peak Isp often near O/F≈5",
            source="RocketCEA built-in / NBP density",
        ),
        PropellantRecord(
            name="CH4",
            kind="fuel",
            aliases=["LCH4", "METHANE"],
            formula="CH4",
            molecular_weight=16.04,
            density_kg_m3=422.0,
            default_temp_k=111.6,
            storage="cryogenic",
            typical_of_range=(2.5, 3.6),
            source="RocketCEA built-in / NBP density",
        ),
        PropellantRecord(
            name="MMH",
            kind="fuel",
            aliases=[],
            formula="CH6N2",
            molecular_weight=46.07,
            density_kg_m3=874.0,
            default_temp_k=298.15,
            storage="storable",
            hypergolic_with=["N2O4", "IRFNA"],
            typical_of_range=(1.5, 2.5),
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="UDMH",
            kind="fuel",
            aliases=[],
            formula="C2H8N2",
            molecular_weight=60.10,
            density_kg_m3=793.0,
            default_temp_k=298.15,
            storage="storable",
            hypergolic_with=["N2O4", "IRFNA"],
            typical_of_range=(1.8, 2.8),
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="A50",
            kind="fuel",
            aliases=["AEROZINE-50", "AEROZINE50"],
            formula="50% UDMH / 50% N2H4",
            density_kg_m3=900.0,
            default_temp_k=298.15,
            storage="storable",
            is_blend=True,
            blend_components={"UDMH": 50.0, "N2H4": 50.0},
            hypergolic_with=["N2O4"],
            notes="Aerozine-50",
            typical_of_range=(1.5, 2.5),
            source="RocketCEA built-in blend",
        ),
        PropellantRecord(
            name="Ethanol",
            kind="fuel",
            aliases=["C2H5OH", "ETHANOL"],
            formula="C2H5OH",
            molecular_weight=46.07,
            density_kg_m3=789.0,
            default_temp_k=298.15,
            storage="storable",
            typical_of_range=(1.2, 2.0),
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP4",
            kind="fuel",
            aliases=["JP-4"],
            density_kg_m3=760.0,
            default_temp_k=298.15,
            storage="storable",
            typical_of_range=(2.0, 2.8),
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP5",
            kind="fuel",
            aliases=["JP-5"],
            density_kg_m3=810.0,
            default_temp_k=298.15,
            storage="storable",
            typical_of_range=(2.0, 2.8),
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP10",
            kind="fuel",
            aliases=["JP-10"],
            density_kg_m3=940.0,
            default_temp_k=298.15,
            storage="storable",
            typical_of_range=(2.0, 2.8),
            source="RocketCEA built-in",
        ),
    ]
    oxs = [
        PropellantRecord(
            name="LOX",
            kind="oxidizer",
            aliases=["O2", "LO2", "OXYGEN"],
            formula="O2",
            molecular_weight=32.0,
            density_kg_m3=1141.0,
            default_temp_k=90.2,
            storage="cryogenic",
            source="RocketCEA built-in / NBP density",
        ),
        PropellantRecord(
            name="N2O4",
            kind="oxidizer",
            aliases=["NTO"],
            formula="N2O4",
            molecular_weight=92.01,
            density_kg_m3=1443.0,
            default_temp_k=298.15,
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="N2O",
            kind="oxidizer",
            aliases=["NITROUS"],
            formula="N2O",
            molecular_weight=44.01,
            density_kg_m3=785.0,
            default_temp_k=185.0,
            storage="semi_cryogenic",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="H2O2",
            kind="oxidizer",
            aliases=["HTP"],
            formula="H2O2",
            molecular_weight=34.01,
            density_kg_m3=1390.0,
            default_temp_k=298.15,
            storage="storable",
            notes="High-test peroxide class; concentration varies in practice",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="IRFNA",
            kind="oxidizer",
            aliases=[],
            density_kg_m3=1570.0,
            default_temp_k=298.15,
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="FLOX70",
            kind="oxidizer",
            aliases=[],
            storage="cryogenic",
            notes="70% F2 / 30% LOX class blend in CEA",
            is_blend=True,
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="CLF5",
            kind="oxidizer",
            aliases=[],
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="Air",
            kind="oxidizer",
            aliases=["AIR"],
            formula="N2/O2",
            storage="gaseous",
            source="RocketCEA built-in",
        ),
    ]
    for r in fuels + oxs:
        _RECORDS[r.name] = r


def _ensure_seeded() -> None:
    _seed()


def register(record: PropellantRecord, *, overwrite: bool = False) -> None:
    """Add or replace a propellant record in the process registry."""
    _ensure_seeded()
    if record.name in _RECORDS and not overwrite and not _RECORDS[record.name].source.startswith(
        "custom"
    ):
        # allow custom overwrite of custom; block clobbering built-ins unless overwrite
        if _RECORDS[record.name].source.startswith("built-in") and not overwrite:
            raise ValueError(
                f"'{record.name}' is a built-in propellant; pass overwrite=True to replace"
            )
    _RECORDS[record.name] = record


def get_propellant(name: str, *, kind: PropellantKind | None = None) -> PropellantRecord | None:
    """Lookup by canonical name or alias."""
    _ensure_seeded()
    key = name.strip()
    if key in _RECORDS:
        rec = _RECORDS[key]
        if kind is None or rec.kind == kind:
            return rec
    upper = key.upper()
    for rec in _RECORDS.values():
        if kind is not None and rec.kind != kind:
            continue
        if rec.name.upper() == upper:
            return rec
        if any(a.upper() == upper for a in rec.aliases):
            return rec
    return None


def resolve_name(name: str, *, kind: PropellantKind = "fuel") -> str:
    """Resolve alias → canonical registry name (or pass-through)."""
    rec = get_propellant(name, kind=kind)
    if rec is not None:
        return rec.name
    # try other kind for pass-through naming
    rec2 = get_propellant(name, kind=None)
    if rec2 is not None:
        return rec2.name
    return name.strip()


def list_registry(
    *,
    kind: PropellantKind | None = None,
    storage: StorageClass | None = None,
    hypergolic_only: bool = False,
) -> list[PropellantRecord]:
    """List registry entries with optional filters."""
    _ensure_seeded()
    out: list[PropellantRecord] = []
    for rec in sorted(_RECORDS.values(), key=lambda r: (r.kind, r.name)):
        if kind is not None and rec.kind != kind:
            continue
        if storage is not None and rec.storage != storage:
            continue
        if hypergolic_only and not rec.hypergolic_with:
            continue
        out.append(rec)
    return out


def get_density_kg_m3(name: str) -> float | None:
    """Lookup liquid density [kg/m³]."""
    rec = get_propellant(name)
    return rec.density_kg_m3 if rec else None


# Alias used by propellant_library
density_kg_m3 = get_density_kg_m3  # type: ignore[misc]


def density_g_cm3(name: str) -> float | None:
    from propwrap.units import kg_m3_to_g_cm3

    d = get_density_kg_m3(name)
    return kg_m3_to_g_cm3(d) if d is not None else None
