"""Demonstrate feeding gamma_vs_area_ratio into a mock nozzle consumer.

The real MOC nozzle contour tool is a sibling project; here we only prove that
the GammaProfile data shape is consumable downstream.
"""

from __future__ import annotations

from dataclasses import dataclass

from propwrap import GammaProfile, Propellant


@dataclass
class MockNozzleSegment:
    """Toy nozzle station that a MOC tool might construct."""

    area_ratio: float
    gamma: float
    temperature_k: float


def build_nozzle_stations(profile: GammaProfile) -> list[MockNozzleSegment]:
    """Convert a GammaProfile into mock nozzle stations (downstream contract)."""
    stations: list[MockNozzleSegment] = []
    for i, eps in enumerate(profile.area_ratios):
        stations.append(
            MockNozzleSegment(
                area_ratio=eps,
                gamma=profile.gamma_cea[i],
                temperature_k=profile.temperatures_k[i],
            )
        )
    return stations


def main() -> None:
    p = Propellant("RP-1", "LOX")
    profile = p.gamma_vs_area_ratio(
        of_ratio=2.56,
        pc_bar=70.0,
        eps_range=(1.5, 25.0, 1.5),
        use_cantera=True,
    )
    stations = build_nozzle_stations(profile)
    print(f"Built {len(stations)} nozzle stations")
    print(f"{'eps':>8} {'gamma':>8} {'T_K':>10}")
    for s in stations[::2]:
        print(f"{s.area_ratio:8.2f} {s.gamma:8.4f} {s.temperature_k:10.1f}")


if __name__ == "__main__":
    main()
