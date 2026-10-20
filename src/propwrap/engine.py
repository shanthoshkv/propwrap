"""Engine-level helpers: thrust sizing, altitude performance, fixed-geometry throttling."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Sequence

from propwrap import cea_backend
from propwrap.units import G0

if TYPE_CHECKING:
    from propwrap.models import PerformanceResult
    from propwrap.propellant import Mixture

# US Standard Atmosphere 1976 layers: (H_base [m geopotential], T_base [K], lapse [K/m], P_base [Pa])
_US1976 = [
    (0.0, 288.15, -0.0065, 101325.0),
    (11000.0, 216.65, 0.0, 22632.06),
    (20000.0, 216.65, 0.001, 5474.889),
    (32000.0, 228.65, 0.0028, 868.0187),
    (47000.0, 270.65, 0.0, 110.9063),
    (51000.0, 270.65, -0.0028, 66.93887),
    (71000.0, 214.65, -0.002, 3.956420),
]
_GMR = 0.034163195  # g0·M_air/R* [K/m]
_R_EARTH = 6356766.0  # m


def us1976_pressure(h_m: float) -> float:
    """Ambient pressure [Pa] at geometric altitude ``h_m`` [m]; 0 above 86 km."""
    if h_m < 0:
        raise ValueError("altitude must be >= 0 m")
    H = _R_EARTH * h_m / (_R_EARTH + h_m)
    if H > 84852.0:
        return 0.0
    Hb, Tb, L, Pb = next(layer for layer in reversed(_US1976) if H >= layer[0])
    if L == 0.0:
        return Pb * math.exp(-_GMR * (H - Hb) / Tb)
    return float(Pb * (Tb / (Tb + L * (H - Hb))) ** (_GMR / L))


def size_engine(
    r: PerformanceResult, thrust_n: float, *, sea_level: bool = False
) -> dict[str, float]:
    """Throat/exit size and mass flows for thrust ``thrust_n`` [N] at vacuum (or sea level).

    Uses delivered Isp/c* when efficiencies were set on the mixture.
    """
    if thrust_n <= 0:
        raise ValueError("thrust_n must be > 0")
    if sea_level:
        isp = r.isp_sl_delivered or r.isp_sl_shifting
    else:
        isp = r.isp_vac_delivered or r.isp_vac_shifting
    mdot = thrust_n / (isp * G0)
    at = mdot * r.c_star / r.pc_pa
    ae = at * r.eps
    return {
        "thrust_n": thrust_n,
        "isp_s": isp,
        "mdot_kg_s": mdot,
        "mdot_ox_kg_s": mdot * r.of_ratio / (1.0 + r.of_ratio),
        "mdot_fuel_kg_s": mdot / (1.0 + r.of_ratio),
        "throat_area_m2": at,
        "throat_diameter_m": math.sqrt(4.0 * at / math.pi),
        "exit_area_m2": ae,
        "exit_diameter_m": math.sqrt(4.0 * ae / math.pi),
    }


def _ambient(m: Mixture, of: float, pc_pa: float, eps: float, pamb_pa: float) -> dict[str, Any]:
    return cea_backend.ambient_isp(
        m.fuel, m.oxidizer, of, pc_pa, eps, pamb_pa, m.fuel_temp_k, m.ox_temp_k,
        eta_cstar=m.eta_cstar, eta_cf=m.eta_cf,
    )


def altitude_performance(
    m: Mixture, of: float, pc_pa: float, eps: float, altitudes_m: Sequence[float]
) -> list[dict[str, Any]]:
    """Isp / Cf vs altitude along the US-1976 atmosphere (fixed geometry, fixed Pc)."""
    rows = []
    for h in altitudes_m:
        pamb = us1976_pressure(h)
        a = _ambient(m, of, pc_pa, eps, pamb)
        rows.append({"altitude_m": float(h), **a})
    return rows


def throttle(
    m: Mixture,
    of: float,
    pc_design_pa: float,
    eps: float,
    thrust_design_n: float,
    fractions: Sequence[float] = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4),
    *,
    pamb_pa: float = 101325.0,
) -> list[dict[str, Any]]:
    """Fixed-geometry throttling: throat sized at design, Pc scaled by ``fractions``.

    Flags Summerfield separation risk (Pe/Pamb < 0.4) at each point.
    """
    design = m.evaluate(of=of, pc_pa=pc_design_pa, eps=eps, full=False)
    at = size_engine(design, thrust_design_n, sea_level=pamb_pa > 0)["throat_area_m2"]
    rows = []
    for f in fractions:
        pc = pc_design_pa * f
        r = m.evaluate(of=of, pc_pa=pc, eps=eps, full=False)
        mdot = pc * at / r.c_star
        a = _ambient(m, of, pc, eps, pamb_pa)
        rows.append(
            {
                "fraction": float(f),
                "pc_pa": pc,
                "mdot_kg_s": mdot,
                "isp_s": float(a["isp_s"]),
                "thrust_n": mdot * float(a["isp_s"]) * G0,
                "pe_over_pamb": r.pe_pa / pamb_pa if pamb_pa > 0 else math.inf,
                "separation_risk": pamb_pa > 0 and r.pe_pa / pamb_pa < 0.4,
            }
        )
    return rows
