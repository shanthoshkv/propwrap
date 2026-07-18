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
    density_g_cm3: float | None = None  # liquid handbook density
    default_temp_k: float | None = None  # suggested inlet T
    heat_of_formation_cal_mol: float | None = None
    storage: StorageClass = "unknown"
    hypergolic_with: list[str] = Field(default_factory=list)
    notes: str = ""
    is_blend: bool = False
    blend_components: dict[str, float] | None = None  # name → wt%
    cea_name: str | None = None  # RocketCEA identifier if different from name
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
            density_g_cm3=0.81,
            default_temp_k=298.15,
            storage="storable",
            notes="Refined kerosene rocket propellant",
            source="RocketCEA built-in / handbook density",
        ),
        PropellantRecord(
            name="LH2",
            kind="fuel",
            aliases=["H2", "HYDROGEN"],
            formula="H2",
            molecular_weight=2.016,
            density_g_cm3=0.0708,
            default_temp_k=20.4,
            storage="cryogenic",
            source="RocketCEA built-in / NBP density",
        ),
        PropellantRecord(
            name="CH4",
            kind="fuel",
            aliases=["LCH4", "METHANE"],
            formula="CH4",
            molecular_weight=16.04,
            density_g_cm3=0.422,
            default_temp_k=111.6,
            storage="cryogenic",
            source="RocketCEA built-in / NBP density",
        ),
        PropellantRecord(
            name="MMH",
            kind="fuel",
            aliases=[],
            formula="CH6N2",
            molecular_weight=46.07,
            density_g_cm3=0.874,
            default_temp_k=298.15,
            storage="storable",
            hypergolic_with=["N2O4", "IRFNA"],
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="UDMH",
            kind="fuel",
            aliases=[],
            formula="C2H8N2",
            molecular_weight=60.10,
            density_g_cm3=0.793,
            default_temp_k=298.15,
            storage="storable",
            hypergolic_with=["N2O4", "IRFNA"],
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="A50",
            kind="fuel",
            aliases=["AEROZINE-50", "AEROZINE50"],
            formula="50% UDMH / 50% N2H4",
            density_g_cm3=0.90,
            default_temp_k=298.15,
            storage="storable",
            is_blend=True,
            blend_components={"UDMH": 50.0, "N2H4": 50.0},
            hypergolic_with=["N2O4"],
            notes="Aerozine-50",
            source="RocketCEA built-in blend",
        ),
        PropellantRecord(
            name="Ethanol",
            kind="fuel",
            aliases=["C2H5OH", "ETHANOL"],
            formula="C2H5OH",
            molecular_weight=46.07,
            density_g_cm3=0.789,
            default_temp_k=298.15,
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP4",
            kind="fuel",
            aliases=["JP-4"],
            density_g_cm3=0.76,
            default_temp_k=298.15,
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP5",
            kind="fuel",
            aliases=["JP-5"],
            density_g_cm3=0.81,
            default_temp_k=298.15,
            storage="storable",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="JP10",
            kind="fuel",
            aliases=["JP-10"],
            density_g_cm3=0.94,
            default_temp_k=298.15,
            storage="storable",
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
            density_g_cm3=1.141,
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
            density_g_cm3=1.443,
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
            density_g_cm3=0.785,
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
            density_g_cm3=1.39,
            default_temp_k=298.15,
            storage="storable",
            notes="High-test peroxide class; concentration varies in practice",
            source="RocketCEA built-in",
        ),
        PropellantRecord(
            name="IRFNA",
            kind="oxidizer",
            aliases=[],
            density_g_cm3=1.57,
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


def density_g_cm3(name: str) -> float | None:
    rec = get_propellant(name)
    return rec.density_g_cm3 if rec else None
