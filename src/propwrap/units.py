"""SI unit system and converters for propwrap.

Public results use **strict SI** (except Isp, which is reported in seconds as
the rocketry standard, plus effective exhaust velocity in m/s).

Base SI used in results
-----------------------
- pressure: pascal (Pa)
- temperature: kelvin (K)
- velocity / c*: metre per second (m/s)
- density: kilogram per cubic metre (kg/m³)
- specific heat: J/(kg·K)
- viscosity: Pa·s
- thermal conductivity: W/(m·K)
- specific impulse: seconds (s)  — also ve = Isp · g0 [m/s]
- density impulse: s · kg/m³

All RocketCEA English units are converted in ``cea_backend`` only.
"""

from __future__ import annotations

from typing import SupportsFloat

# ---------------------------------------------------------------------------
# Constants (CODATA / standard)
# ---------------------------------------------------------------------------

G0: float = 9.80665
"""Standard gravity [m/s²] — Isp [s] · g0 = effective exhaust velocity [m/s]."""

R_UNIVERSAL: float = 8314.462618
"""Universal gas constant [J/(kmol·K)]."""

# Pressure
PA_PER_BAR: float = 1.0e5
PA_PER_MPA: float = 1.0e6
PA_PER_ATM: float = 101325.0
PA_PER_PSI: float = 6894.757293168
PA_PER_PSIA: float = PA_PER_PSI  # alias
BAR_PER_PSIA: float = PA_PER_PSI / PA_PER_BAR  # ≈ 0.0689476
PSIA_PER_BAR: float = PA_PER_BAR / PA_PER_PSI  # ≈ 14.5037738

# Length / velocity
M_PER_FT: float = 0.3048
M_PER_IN: float = 0.0254
FT_PER_M: float = 1.0 / M_PER_FT

# Temperature
# T_K = T_R * 5/9 ; T_R = T_K * 9/5
# T_K = (T_F + 459.67) * 5/9 ; T_C = T_K - 273.15

# Density
KG_M3_PER_G_CM3: float = 1000.0
KG_M3_PER_LBM_FT3: float = 16.01846337396
G_CM3_PER_KG_M3: float = 0.001

# Mass
KG_PER_LBM: float = 0.45359237

# Energy / heat capacity (CEA cal/g-K → J/kg-K)
J_PER_CAL: float = 4.184
J_KG_K_PER_CAL_G_K: float = 4184.0  # 1 cal/(g·K) = 4184 J/(kg·K)

# Viscosity: 1 millipoise = 1e-4 Pa·s
PA_S_PER_MILLIPOISE: float = 1.0e-4

# Thermal conductivity: 1 mcal/(cm·s·K) = 0.4184 W/(m·K)
W_M_K_PER_MCAL_CM_S_K: float = 0.4184

# Atmosphere
SL_PAMB_PA: float = 101325.0
SL_PAMB_PSIA: float = 14.6959487755

# RocketCEA g0 in English units for Cf = Isp * g0_ft / c*_ft
G0_FT_S2: float = 32.1740485564


def _f(x: SupportsFloat) -> float:
    return float(x)


# ---------------------------------------------------------------------------
# Pressure
# ---------------------------------------------------------------------------


def bar_to_pa(bar: SupportsFloat) -> float:
    return _f(bar) * PA_PER_BAR


def pa_to_bar(pa: SupportsFloat) -> float:
    return _f(pa) / PA_PER_BAR


def mpa_to_pa(mpa: SupportsFloat) -> float:
    return _f(mpa) * PA_PER_MPA


def pa_to_mpa(pa: SupportsFloat) -> float:
    return _f(pa) / PA_PER_MPA


def mpa_to_bar(mpa: SupportsFloat) -> float:
    return pa_to_bar(mpa_to_pa(mpa))


def bar_to_mpa(bar: SupportsFloat) -> float:
    return pa_to_mpa(bar_to_pa(bar))


def atm_to_pa(atm: SupportsFloat) -> float:
    return _f(atm) * PA_PER_ATM


def pa_to_atm(pa: SupportsFloat) -> float:
    return _f(pa) / PA_PER_ATM


def psi_to_pa(psi: SupportsFloat) -> float:
    return _f(psi) * PA_PER_PSI


def pa_to_psi(pa: SupportsFloat) -> float:
    return _f(pa) / PA_PER_PSI


psia_to_pa = psi_to_pa
pa_to_psia = pa_to_psi


def bar_to_psia(bar: SupportsFloat) -> float:
    return _f(bar) * PSIA_PER_BAR


def psia_to_bar(psia: SupportsFloat) -> float:
    return _f(psia) * BAR_PER_PSIA


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------


def celsius_to_kelvin(c: SupportsFloat) -> float:
    return _f(c) + 273.15


def kelvin_to_celsius(k: SupportsFloat) -> float:
    return _f(k) - 273.15


def fahrenheit_to_kelvin(f: SupportsFloat) -> float:
    return (_f(f) + 459.67) * (5.0 / 9.0)


def kelvin_to_fahrenheit(k: SupportsFloat) -> float:
    return _f(k) * (9.0 / 5.0) - 459.67


def rankine_to_kelvin(r: SupportsFloat) -> float:
    return _f(r) * (5.0 / 9.0)


def kelvin_to_rankine(k: SupportsFloat) -> float:
    return _f(k) * (9.0 / 5.0)


# ---------------------------------------------------------------------------
# Length / velocity
# ---------------------------------------------------------------------------


def ft_to_m(ft: SupportsFloat) -> float:
    return _f(ft) * M_PER_FT


def m_to_ft(m: SupportsFloat) -> float:
    return _f(m) * FT_PER_M


def ft_s_to_m_s(ft_s: SupportsFloat) -> float:
    return ft_to_m(ft_s)


def m_s_to_ft_s(m_s: SupportsFloat) -> float:
    return m_to_ft(m_s)


# ---------------------------------------------------------------------------
# Density
# ---------------------------------------------------------------------------


def g_cm3_to_kg_m3(g_cm3: SupportsFloat) -> float:
    return _f(g_cm3) * KG_M3_PER_G_CM3


def kg_m3_to_g_cm3(kg_m3: SupportsFloat) -> float:
    return _f(kg_m3) * G_CM3_PER_KG_M3


def lbm_ft3_to_kg_m3(lbm_ft3: SupportsFloat) -> float:
    return _f(lbm_ft3) * KG_M3_PER_LBM_FT3


# ---------------------------------------------------------------------------
# Specific impulse / exhaust velocity
# ---------------------------------------------------------------------------


def isp_s_to_ve_m_s(isp_s: SupportsFloat, g0: float = G0) -> float:
    """Convert Isp [s] → effective exhaust velocity [m/s]."""
    return _f(isp_s) * g0


def ve_m_s_to_isp_s(ve_m_s: SupportsFloat, g0: float = G0) -> float:
    """Convert effective exhaust velocity [m/s] → Isp [s]."""
    return _f(ve_m_s) / g0


def density_impulse_si(isp_s: SupportsFloat, density_kg_m3: SupportsFloat) -> float:
    """Density impulse [s · kg/m³] = Isp [s] × ρ [kg/m³]."""
    return _f(isp_s) * _f(density_kg_m3)


# ---------------------------------------------------------------------------
# CEA transport printout → SI
# ---------------------------------------------------------------------------


def cea_cp_to_si(cp_cal_g_k: SupportsFloat) -> float:
    """CEA Cp [cal/(g·K)] → [J/(kg·K)]."""
    return _f(cp_cal_g_k) * J_KG_K_PER_CAL_G_K


def cea_mu_to_si(mu_millipoise: SupportsFloat) -> float:
    """CEA viscosity [millipoise] → [Pa·s]."""
    return _f(mu_millipoise) * PA_S_PER_MILLIPOISE


def cea_k_to_si(k_mcal_cm_s_k: SupportsFloat) -> float:
    """CEA thermal conductivity [mcal/(cm·s·K)] → [W/(m·K)]."""
    return _f(k_mcal_cm_s_k) * W_M_K_PER_MCAL_CM_S_K


# ---------------------------------------------------------------------------
# Generic convert()
# ---------------------------------------------------------------------------

_PRESSURE = {
    ("bar", "pa"): bar_to_pa,
    ("pa", "bar"): pa_to_bar,
    ("mpa", "pa"): mpa_to_pa,
    ("pa", "mpa"): pa_to_mpa,
    ("mpa", "bar"): mpa_to_bar,
    ("bar", "mpa"): bar_to_mpa,
    ("atm", "pa"): atm_to_pa,
    ("pa", "atm"): pa_to_atm,
    ("psi", "pa"): psi_to_pa,
    ("pa", "psi"): pa_to_psi,
    ("psia", "pa"): psia_to_pa,
    ("pa", "psia"): pa_to_psia,
    ("bar", "psia"): bar_to_psia,
    ("psia", "bar"): psia_to_bar,
}

_TEMP = {
    ("c", "k"): celsius_to_kelvin,
    ("k", "c"): kelvin_to_celsius,
    ("f", "k"): fahrenheit_to_kelvin,
    ("k", "f"): kelvin_to_fahrenheit,
    ("r", "k"): rankine_to_kelvin,
    ("k", "r"): kelvin_to_rankine,
    ("celsius", "kelvin"): celsius_to_kelvin,
    ("kelvin", "celsius"): kelvin_to_celsius,
    ("rankine", "kelvin"): rankine_to_kelvin,
    ("kelvin", "rankine"): kelvin_to_rankine,
}

_DENSITY = {
    ("g/cm3", "kg/m3"): g_cm3_to_kg_m3,
    ("kg/m3", "g/cm3"): kg_m3_to_g_cm3,
    ("g_cm3", "kg_m3"): g_cm3_to_kg_m3,
    ("kg_m3", "g_cm3"): kg_m3_to_g_cm3,
    ("lbm/ft3", "kg/m3"): lbm_ft3_to_kg_m3,
}

_VELOCITY = {
    ("ft/s", "m/s"): ft_s_to_m_s,
    ("m/s", "ft/s"): m_s_to_ft_s,
    ("ft_s", "m_s"): ft_s_to_m_s,
    ("m_s", "ft_s"): m_s_to_ft_s,
}

_ISP = {
    ("s", "m/s"): isp_s_to_ve_m_s,
    ("m/s", "s"): ve_m_s_to_isp_s,
    ("isp_s", "ve_m_s"): isp_s_to_ve_m_s,
    ("ve_m_s", "isp_s"): ve_m_s_to_isp_s,
}


def convert(value: SupportsFloat, from_unit: str, to_unit: str) -> float:
    """Convert ``value`` between units.

    Examples
    --------
    >>> convert(70, "bar", "Pa")
    7000000.0
    >>> convert(343.7, "s", "m/s")  # Isp → ve
    3370.9...
    >>> convert(0.81, "g/cm3", "kg/m3")
    810.0
    """
    fr = from_unit.strip().lower().replace(" ", "")
    to = to_unit.strip().lower().replace(" ", "")
    # normalize aliases
    aliases = {
        "pascal": "pa",
        "pascals": "pa",
        "kelvin": "k",
        "celsius": "c",
        "centigrade": "c",
        "fahrenheit": "f",
        "rankine": "r",
        "sec": "s",
        "second": "s",
        "seconds": "s",
        "g/cc": "g/cm3",
        "g/ml": "g/cm3",
        "gcm3": "g/cm3",
        "kgm3": "kg/m3",
        "kg/m^3": "kg/m3",
        "m/sec": "m/s",
        "ft/sec": "ft/s",
    }
    fr = aliases.get(fr, fr)
    to = aliases.get(to, to)
    if fr == to:
        return _f(value)

    for table in (_PRESSURE, _TEMP, _DENSITY, _VELOCITY, _ISP):
        fn = table.get((fr, to))
        if fn is not None:
            return fn(value)

    raise ValueError(
        f"Unsupported conversion {from_unit!r} → {to_unit!r}. "
        "See propwrap.units module docstring for supported pairs."
    )


def pressure_to_pa(value: SupportsFloat, unit: str = "Pa") -> float:
    """Convert a pressure to pascals."""
    u = unit.strip().lower()
    if u in ("pa", "pascal", "pascals"):
        return _f(value)
    return convert(value, u, "pa")


def pressure_from_pa(pa: SupportsFloat, unit: str = "Pa") -> float:
    """Convert pascals to the requested unit."""
    u = unit.strip().lower()
    if u in ("pa", "pascal", "pascals"):
        return _f(pa)
    return convert(pa, "pa", u)


def density_to_kg_m3(value: SupportsFloat, unit: str = "kg/m3") -> float:
    u = unit.strip().lower().replace(" ", "")
    if u in ("kg/m3", "kgm3", "kg/m^3"):
        return _f(value)
    return convert(value, u, "kg/m3")


# ---------------------------------------------------------------------------
# Input helper: resolve chamber pressure from mixed kwargs
# ---------------------------------------------------------------------------


def resolve_pressure_pa(
    *,
    pc: float | None = None,
    pc_pa: float | None = None,
    pc_bar: float | None = None,
    pc_mpa: float | None = None,
    pc_psi: float | None = None,
    pc_psia: float | None = None,
    default_pa: float | None = None,
) -> float:
    """Pick exactly one pressure input and return pascals.

    Preference order if several given: pc_pa, pc, pc_bar, pc_mpa, pc_psi/psia.
    ``pc`` is interpreted as **Pa** (SI).
    """
    candidates: list[tuple[str, float]] = []
    if pc_pa is not None:
        candidates.append(("pc_pa", float(pc_pa)))
    if pc is not None:
        candidates.append(("pc", float(pc)))
    if pc_bar is not None:
        candidates.append(("pc_bar", bar_to_pa(pc_bar)))
    if pc_mpa is not None:
        candidates.append(("pc_mpa", mpa_to_pa(pc_mpa)))
    if pc_psi is not None:
        candidates.append(("pc_psi", psi_to_pa(pc_psi)))
    if pc_psia is not None:
        candidates.append(("pc_psia", psi_to_pa(pc_psia)))

    if not candidates:
        if default_pa is not None:
            return float(default_pa)
        raise ValueError(
            "Chamber pressure required in SI pascals: pass pc=... (Pa), "
            "or pc_bar=..., pc_mpa=..., pc_psi=..."
        )
    if len(candidates) > 1:
        # allow only one source
        names = [n for n, _ in candidates]
        # if pc and pc_pa both same role, prefer explicit
        if set(names) <= {"pc", "pc_pa"} and len(candidates) == 2:
            return candidates[0][1]
        raise ValueError(
            f"Multiple pressure inputs given: {names}. Use only one."
        )
    return candidates[0][1]
