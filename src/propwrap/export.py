"""JSON/CSV export utilities for propwrap result models."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from propwrap.models import GammaProfile, PerformanceResult, SweepResult


def performance_to_json(result: PerformanceResult, path: str | Path) -> None:
    """Write a single :class:`PerformanceResult` to JSON."""
    Path(path).write_text(result.model_dump_json(indent=2), encoding="utf-8")


def performance_to_csv(result: PerformanceResult, path: str | Path) -> None:
    """Write a single :class:`PerformanceResult` as a one-row CSV."""
    data = result.model_dump()
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(data.keys()))
        writer.writeheader()
        writer.writerow(data)


def sweep_to_json(sweep: SweepResult, path: str | Path) -> None:
    """Write a :class:`SweepResult` to JSON."""
    Path(path).write_text(sweep.model_dump_json(indent=2), encoding="utf-8")


def sweep_to_csv(sweep: SweepResult, path: str | Path) -> None:
    """Write a :class:`SweepResult` to CSV (one row per sample)."""
    if not sweep.results:
        Path(path).write_text("", encoding="utf-8")
        return
    rows = [r.model_dump() for r in sweep.results]
    fieldnames = list(rows[0].keys())
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def gamma_profile_to_json(profile: GammaProfile, path: str | Path) -> None:
    """Write a :class:`GammaProfile` to JSON."""
    Path(path).write_text(profile.model_dump_json(indent=2), encoding="utf-8")


def gamma_profile_to_csv(profile: GammaProfile, path: str | Path) -> None:
    """Write γ vs area ratio as CSV."""
    rows: list[dict[str, float | None]] = []
    for i, eps in enumerate(profile.area_ratios):
        row: dict[str, float | None] = {
            "area_ratio": eps,
            "gamma_cea": profile.gamma_cea[i],
            "temperature_k": profile.temperatures_k[i],
            "gamma_cantera": (
                profile.gamma_cantera[i] if profile.gamma_cantera is not None else None
            ),
        }
        rows.append(row)
    fieldnames = ["area_ratio", "gamma_cea", "gamma_cantera", "temperature_k"]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def results_list_to_json(
    results: Iterable[PerformanceResult], path: str | Path
) -> None:
    """Write a list of performance results to a JSON array."""
    payload = [r.model_dump() for r in results]
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
