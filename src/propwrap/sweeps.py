"""Sweep helpers for O/F, Pc, and area-ratio ranges."""

from __future__ import annotations


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

    values: list[float] = []
    # Use integer steps to avoid float drift
    n = int(round((stop - start) / step))
    for i in range(n + 1):
        v = start + i * step
        if v > stop + step * 1e-9:
            break
        values.append(round(v, 12))

    # Ensure stop included if very close
    if values and abs(values[-1] - stop) > max(1e-9, abs(step) * 1e-6):
        if values[-1] < stop:
            values.append(round(stop, 12))

    if not values:
        raise ValueError(f"range {rng} produced no samples")
    return values
