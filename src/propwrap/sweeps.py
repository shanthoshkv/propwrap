"""Sweep helpers for O/F, Pc, and area-ratio ranges."""

from __future__ import annotations

import numpy as np


def expand_range(rng: tuple[float, float, float]) -> list[float]:
    """Expand ``(start, stop, step)`` into a list of sample values.

    Includes ``start``. Includes ``stop`` when it lands on a step boundary
    (within a small float tolerance).

    Parameters
    ----------
    rng :
        ``(start, stop, step)`` with ``stop > start`` and ``step > 0``.

    Raises
    ------
    ValueError
        If the range is invalid.
    """
    if len(rng) != 3:
        raise ValueError("range must be a tuple of (start, stop, step)")
    start, stop, step = (float(rng[0]), float(rng[1]), float(rng[2]))
    if stop <= start:
        raise ValueError(f"stop must be > start, got start={start}, stop={stop}")
    if step <= 0:
        raise ValueError(f"step must be > 0, got {step}")

    n = int(np.floor((stop - start) / step + 1e-9))
    values: list[float] = np.round(start + step * np.arange(n + 1), 12).tolist()
    if stop - values[-1] > max(1e-9, step * 1e-6):
        values.append(round(stop, 12))
    return values
