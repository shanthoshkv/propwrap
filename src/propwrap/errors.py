"""Friendly errors with suggestions."""

from __future__ import annotations

from difflib import get_close_matches

from propwrap.registry import list_registry


class PropwrapError(ValueError):
    """User-facing propwrap error."""


def did_you_mean(name: str, *, kind: str | None = None) -> str:
    """Build a 'Did you mean …?' suffix for unknown propellant names."""
    recs = list_registry(kind=kind) if kind else list_registry()  # type: ignore[arg-type]
    candidates = []
    for r in recs:
        candidates.append(r.name)
        candidates.extend(r.aliases)
    matches = get_close_matches(name, candidates, n=3, cutoff=0.5)
    if not matches:
        # also try without separators
        compact = {c.replace("-", "").replace("_", "").upper(): c for c in candidates}
        key = name.replace("-", "").replace("_", "").replace(" ", "").upper()
        if key in compact:
            matches = [compact[key]]
    if matches:
        return f" Did you mean {', '.join(repr(m) for m in matches)}?"
    return ""


def validate_of(of_ratio: float) -> None:
    if of_ratio <= 0:
        raise PropwrapError(
            f"mixture ratio (O/F) must be > 0, got {of_ratio}. "
            "O/F is mass oxidizer / mass fuel."
        )


def validate_pc(pc_pa: float) -> None:
    if pc_pa <= 0:
        raise PropwrapError(
            f"chamber pressure must be > 0 Pa, got {pc_pa}. "
            "Example: pc=7e6 or pc_bar=70 or pc_mpa=7."
        )
    # Heuristic: user likely passed bar as Pa (e.g. pc=70 instead of pc_bar=70)
    if 1.0 < pc_pa < 500.0:
        raise PropwrapError(
            f"chamber pressure pc={pc_pa} Pa is unrealistically low for a liquid rocket "
            f"(that is only {pc_pa:.4g} Pa ≈ {pc_pa/1e5:.2e} bar). "
            "If you meant 70 bar, use pc_bar=70 or pc=7_000_000 (Pa) or pc_mpa=7. "
            "Remember: keyword pc / pc_pa is always pascals (SI)."
        )
    if 500.0 <= pc_pa < 1.0e5:
        # 0.005–1 bar: possible but warn via PropwrapError soft? keep as error for students
        raise PropwrapError(
            f"pc={pc_pa} Pa ({pc_pa/1e5:.4g} bar) is very low. "
            "Did you mean pc_bar={0} (bar) or pc_mpa=...? "
            "SI path: pc is in pascals (70 bar = 7e6 Pa).".format(pc_pa)
        )


def warn_if_ambiguous_pc(pc: float | None, pc_bar: float | None) -> str | None:
    """Return a warning string if pc looks like bar mistaken for Pa (non-fatal)."""
    if pc is not None and pc_bar is None and 1.0 < pc < 500.0:
        return (
            f"pc={pc} looks like bar, but pc means pascals. "
            "Use pc_bar={} or pc={}e6.".format(pc, pc)
        )
    return None


def validate_eps(eps: float) -> None:
    if eps <= 1.0:
        raise PropwrapError(
            f"expansion ratio ε (Ae/At) must be > 1, got {eps}. "
            "If you meant chamber contraction Ac/At, that is a different parameter "
            "and is not used here."
        )


def suggest_propellant(name: str, *, kind: str = "fuel") -> str:
    """Resolve name or raise with suggestions."""
    from propwrap.registry import get_propellant

    rec = get_propellant(name, kind=kind)  # type: ignore[arg-type]
    if rec is not None:
        return rec.name
    # allow unknown CEA names through but warn via suggestion if close
    hint = did_you_mean(name, kind=kind)
    if hint and name.strip().upper() not in {r.name.upper() for r in list_registry()}:
        # still pass through for custom/CEA-native names; only error if empty
        pass
    if not name or not str(name).strip():
        raise PropwrapError(f"Empty {kind} name.{hint}")
    return name.strip()
