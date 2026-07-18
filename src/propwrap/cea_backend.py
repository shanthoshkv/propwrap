"""RocketCEA wrapper — SI-adjacent public units only."""

from __future__ import annotations

import math
from typing import Any

from propwrap.models import GammaProfile, PerformanceResult, StationState
from propwrap.propellant_library import (
    bulk_density_g_cm3,
    cryo_default_temps_k,
    resolve_cea_names,
    stoich_of_ratio,
)
from propwrap.sanity import sanity_check

BAR_TO_PSIA = 14.5037738
FT_TO_M = 0.3048
R_TO_K = 5.0 / 9.0
K_TO_R = 9.0 / 5.0
G0_FT = 32.174049
SL_PAMB_PSIA = 14.6959
SL_PAMB_BAR = 1.01325
# CEA transport printout → SI
CP_CAL_G_K_TO_J_KG_K = 4184.0
MILLIPOISE_TO_PA_S = 1e-4
MCAL_CM_S_K_TO_W_M_K = 0.4184
LBM_FT3_TO_KG_M3 = 16.018463
R_UNIV = 8314.462618  # J/(kmol·K)


def _pc_psia(pc_bar: float) -> float:
    return pc_bar * BAR_TO_PSIA


def _finite(x: Any, default: float = 0.0) -> float:
    """Coerce CEA outputs to JSON-safe finite floats (no inf/nan)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _make_cea_obj(
    fuel: str,
    oxidizer: str,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> Any:
    from rocketcea.cea_obj import CEA_Obj

    fuel_name, ox_name = resolve_cea_names(fuel, oxidizer)
    kwargs: dict[str, Any] = {"oxName": ox_name, "fuelName": fuel_name}
    if fuel_temp_k is not None:
        kwargs["fuelT"] = fuel_temp_k * K_TO_R
    if ox_temp_k is not None:
        kwargs["oxT"] = ox_temp_k * K_TO_R
    try:
        return CEA_Obj(**kwargs)
    except TypeError:
        kwargs.pop("fuelT", None)
        kwargs.pop("oxT", None)
        return CEA_Obj(oxName=ox_name, fuelName=fuel_name)


def _species_at_station(raw: Any, station_idx: int) -> dict[str, float]:
    """RocketCEA: (mw_dict, {sp: [inj, chm, tht, exit]})."""
    if not isinstance(raw, tuple) or len(raw) < 2:
        return _normalize_species(raw)
    fracs = raw[1]
    if not isinstance(fracs, dict):
        return {}
    out: dict[str, float] = {}
    for sp, arr in fracs.items():
        try:
            if isinstance(arr, (list, tuple)) and len(arr) > station_idx:
                out[str(sp).lstrip("*")] = float(arr[station_idx])
            elif isinstance(arr, (int, float)):
                out[str(sp).lstrip("*")] = float(arr)
        except (TypeError, ValueError):
            continue
    return out


def _normalize_species(raw: Any) -> dict[str, float]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        out: dict[str, float] = {}
        for k, v in raw.items():
            if isinstance(v, (int, float)):
                out[str(k).lstrip("*")] = float(v)
            elif isinstance(v, (list, tuple)) and v:
                out[str(k).lstrip("*")] = float(v[0])
        return out
    return {}


def _transport_si(tr: Any) -> tuple[float, float, float, float]:
    """(cp, mu, k, Pr) from CEA printout units → SI."""
    cp, mu, k, pr = (float(tr[0]), float(tr[1]), float(tr[2]), float(tr[3]))
    return (
        cp * CP_CAL_G_K_TO_J_KG_K,
        mu * MILLIPOISE_TO_PA_S,
        k * MCAL_CM_S_K_TO_W_M_K,
        pr,
    )


def _station(
    name: str,
    T_k: float,
    P_bar: float,
    rho_kg_m3: float,
    mw: float,
    gamma: float,
    tr: Any,
    species: dict[str, float],
) -> StationState:
    cp, mu, k, pr = _transport_si(tr)
    r_sp = R_UNIV / mw if mw > 0 else 0.0
    return StationState(
        name=name,  # type: ignore[arg-type]
        temperature_k=T_k,
        pressure_bar=P_bar,
        density_kg_m3=rho_kg_m3,
        mw=mw,
        gamma=gamma,
        cp_j_kg_k=cp,
        r_specific_j_kg_k=r_sp,
        mu_pa_s=mu,
        k_w_m_k=k,
        prandtl=pr,
        species_mole_fractions=species,
    )


def resolve_temps(
    fuel: str,
    oxidizer: str,
    fuel_temp_k: float | None,
    ox_temp_k: float | None,
    *,
    apply_cryo_defaults: bool = True,
) -> tuple[float | None, float | None, bool]:
    """Return (fuel_T, ox_T, temps_are_default)."""
    if fuel_temp_k is not None or ox_temp_k is not None:
        return fuel_temp_k, ox_temp_k, False
    if apply_cryo_defaults:
        ft, ot = cryo_default_temps_k(fuel, oxidizer)
        if ft is not None or ot is not None:
            return ft, ot, False
    return None, None, True


def compute_performance(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_bar: float,
    eps: float,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    *,
    eta_cstar: float = 1.0,
    eta_cf: float = 1.0,
    apply_cryo_defaults: bool = True,
    include_stations: bool = True,
) -> PerformanceResult:
    if of_ratio <= 0:
        raise ValueError(f"of_ratio must be > 0, got {of_ratio}")
    if pc_bar <= 0:
        raise ValueError(f"pc_bar must be > 0, got {pc_bar}")
    if eps <= 1.0:
        raise ValueError(f"eps (Ae/At) must be > 1, got {eps}")
    if not (0 < eta_cstar <= 1.2 and 0 < eta_cf <= 1.2):
        raise ValueError("eta_cstar and eta_cf should be in (0, 1.2]")

    ft, ot, temps_default = resolve_temps(
        fuel, oxidizer, fuel_temp_k, ox_temp_k, apply_cryo_defaults=apply_cryo_defaults
    )
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_bar)
    mr = of_ratio

    isp_vac_s, cstar_ft, _ = cea.get_IvacCstrTc(Pc=pc, MR=mr, eps=eps)
    isp_vac_f, _, _ = cea.getFrozen_IvacCstrTc(
        Pc=pc, MR=mr, eps=eps, frozenAtThroat=0
    )
    _cf_cea_s, cf_sl_s, mode_s = cea.get_PambCf(
        Pamb=SL_PAMB_PSIA, Pc=pc, MR=mr, eps=eps
    )
    _, cf_sl_f, _ = cea.getFrozen_PambCf(
        Pamb=SL_PAMB_PSIA, Pc=pc, MR=mr, eps=eps, frozenAtThroat=0
    )
    isp_sl_s, _ = cea.estimate_Ambient_Isp(
        Pc=pc, MR=mr, eps=eps, Pamb=SL_PAMB_PSIA
    )
    isp_sl_f, _ = cea.estimate_Ambient_Isp(
        Pc=pc, MR=mr, eps=eps, Pamb=SL_PAMB_PSIA, frozen=1, frozenAtThroat=0
    )

    temps_r = cea.get_Temperatures(Pc=pc, MR=mr, eps=eps, frozen=0, frozenAtThroat=0)
    tc_r, tt_r, te_r = float(temps_r[0]), float(temps_r[1]), float(temps_r[2])
    mw_ch, gam_ch = cea.get_Chamber_MolWt_gamma(Pc=pc, MR=mr, eps=eps)
    mw_th, gam_th = cea.get_Throat_MolWt_gamma(Pc=pc, MR=mr, eps=eps)
    mw_ex, gam_ex = cea.get_exit_MolWt_gamma(Pc=pc, MR=mr, eps=eps)

    pc_over_pe = float(cea.get_PcOvPe(Pc=pc, MR=mr, eps=eps))
    pe_bar = pc_bar / pc_over_pe if pc_over_pe > 0 else 0.0

    cstar_m = float(cstar_ft) * FT_TO_M
    cf_vac = float(isp_vac_s) * G0_FT / float(cstar_ft)
    fuel_name, ox_name = resolve_cea_names(fuel, oxidizer)

    stoich = stoich_of_ratio(fuel_name, ox_name, cea)
    rho_bulk, dens_basis = bulk_density_g_cm3(fuel_name, ox_name, mr)
    dens_isp = (
        float(isp_vac_s) * rho_bulk if rho_bulk is not None else None
    )

    ch = th = ex = None
    if include_stations:
        try:
            sp_raw = cea.get_SpeciesMoleFractions(Pc=pc, MR=mr, eps=eps)
        except Exception:
            sp_raw = None
        # station indices in species arrays: often [inj, chm, tht, exit] → 1,2,3
        sp_ch = _species_at_station(sp_raw, 1)
        sp_th = _species_at_station(sp_raw, 2)
        sp_ex = _species_at_station(sp_raw, 3)
        tr_ch = cea.get_Chamber_Transport(Pc=pc, MR=mr, eps=eps)
        tr_th = cea.get_Throat_Transport(Pc=pc, MR=mr, eps=eps)
        tr_ex = cea.get_Exit_Transport(Pc=pc, MR=mr, eps=eps)
        dens = cea.get_Densities(Pc=pc, MR=mr, eps=eps)
        # dens: chamber, throat, exit in lbm/ft³
        rho_ch = float(dens[0]) * LBM_FT3_TO_KG_M3
        rho_th = float(dens[1]) * LBM_FT3_TO_KG_M3
        rho_ex = float(dens[2]) * LBM_FT3_TO_KG_M3
        p_th_bar = pc_bar  # approx; throat ~ 0.5–0.6 Pc — use isentropic if needed
        try:
            # throat pressure from sonic relation rough: use Pc / PcOvPe_throat
            p_th_bar = pc_bar / float(cea.get_Throat_PcOvPe(Pc=pc, MR=mr, eps=eps))
        except Exception:
            p_th_bar = 0.56 * pc_bar
        ch = _station(
            "chamber",
            tc_r * R_TO_K,
            pc_bar,
            rho_ch,
            float(mw_ch),
            float(gam_ch),
            tr_ch,
            sp_ch,
        )
        th = _station(
            "throat",
            tt_r * R_TO_K,
            p_th_bar,
            rho_th,
            float(mw_th),
            float(gam_th),
            tr_th,
            sp_th,
        )
        ex = _station(
            "exit",
            te_r * R_TO_K,
            pe_bar,
            rho_ex,
            float(mw_ex),
            float(gam_ex),
            tr_ex,
            sp_ex,
        )

    isp_vac_d = float(isp_vac_s) * eta_cstar * eta_cf
    isp_sl_d = float(isp_sl_s) * eta_cstar * eta_cf

    result = PerformanceResult(
        of_ratio=float(of_ratio),
        pc_bar=float(pc_bar),
        eps=float(eps),
        isp_vac_shifting=_finite(isp_vac_s),
        isp_vac_frozen=_finite(isp_vac_f),
        isp_sl_shifting=_finite(isp_sl_s),
        isp_sl_frozen=_finite(isp_sl_f),
        c_star=_finite(cstar_m * eta_cstar),
        cf_vac=_finite(float(cf_vac) * eta_cf),
        cf_sl=_finite(float(cf_sl_s) * eta_cf),
        gamma_chamber=_finite(gam_ch),
        gamma_throat=_finite(gam_th),
        gamma_exit=_finite(gam_ex),
        mw_chamber=_finite(mw_ch),
        tc_kelvin=_finite(tc_r * R_TO_K),
        tt_kelvin=_finite(tt_r * R_TO_K),
        te_kelvin=_finite(te_r * R_TO_K),
        fuel=fuel_name,
        oxidizer=ox_name,
        pe_bar=pe_bar,
        pc_over_pe=pc_over_pe,
        ambient_mode=str(mode_s),
        fuel_temp_k=ft,
        ox_temp_k=ot,
        temps_are_default=temps_default,
        chamber=ch,
        throat=th,
        exit=ex,
        stoich_of_ratio=stoich,
        density_impulse_vac_shifting=dens_isp,
        bulk_density_g_cm3=rho_bulk,
        density_basis=dens_basis,
        isp_vac_delivered=isp_vac_d if (eta_cstar < 1 or eta_cf < 1) else None,
        isp_sl_delivered=isp_sl_d if (eta_cstar < 1 or eta_cf < 1) else None,
        eta_cstar=eta_cstar if eta_cstar != 1.0 else None,
        eta_cf=eta_cf if eta_cf != 1.0 else None,
        propwrap_version="0.1.0",
    )
    result.warnings = sanity_check(result)
    return result


def ambient_isp(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_bar: float,
    eps: float,
    pamb_bar: float,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    *,
    frozen: bool = False,
) -> dict[str, float | str]:
    """Isp and Cf at arbitrary ambient pressure [bar]."""
    if pamb_bar < 0:
        raise ValueError("pamb_bar must be >= 0")
    ft, ot, _ = resolve_temps(fuel, oxidizer, fuel_temp_k, ox_temp_k)
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_bar)
    pamb = pamb_bar * BAR_TO_PSIA if pamb_bar > 0 else 1e-6
    if frozen:
        isp, mode = cea.estimate_Ambient_Isp(
            Pc=pc, MR=of_ratio, eps=eps, Pamb=pamb, frozen=1, frozenAtThroat=0
        )
        _a, cf, _ = cea.getFrozen_PambCf(
            Pamb=pamb, Pc=pc, MR=of_ratio, eps=eps, frozenAtThroat=0
        )
    else:
        isp, mode = cea.estimate_Ambient_Isp(
            Pc=pc, MR=of_ratio, eps=eps, Pamb=pamb
        )
        _a, cf, _ = cea.get_PambCf(Pamb=pamb, Pc=pc, MR=of_ratio, eps=eps)
    return {
        "isp_s": float(isp),
        "cf": float(cf),
        "pamb_bar": float(pamb_bar),
        "mode": str(mode),
    }


def nozzle_profile(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_bar: float,
    area_ratios: list[float],
    *,
    frozen: bool = True,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> GammaProfile:
    ft, ot, _ = resolve_temps(fuel, oxidizer, fuel_temp_k, ox_temp_k)
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_bar)
    frz = 1 if frozen else 0
    gams: list[float] = []
    temps: list[float] = []
    mws: list[float] = []
    press: list[float] = []
    for eps in area_ratios:
        e = max(float(eps), 1.0001)
        temps_r = cea.get_Temperatures(
            Pc=pc, MR=of_ratio, eps=e, frozen=frz, frozenAtThroat=0
        )
        mw, gam = cea.get_exit_MolWt_gamma(Pc=pc, MR=of_ratio, eps=e)
        pcope = float(cea.get_PcOvPe(Pc=pc, MR=of_ratio, eps=e))
        gams.append(float(gam))
        temps.append(float(temps_r[2]) * R_TO_K)
        mws.append(float(mw))
        press.append(pc_bar / pcope if pcope > 0 else 0.0)
    const_g = sum(gams) / len(gams) if gams else None
    return GammaProfile(
        area_ratios=list(area_ratios),
        gamma_cea=gams,
        gamma_cantera=None,
        temperatures_k=temps,
        mw=mws,
        pressure_bar=press,
        source="cea_frozen" if frozen else "cea_shifting",
        constant_gamma_equiv=const_g,
    )


def gamma_and_temp_at_eps(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_bar: float,
    eps: float,
    *,
    frozen: bool = True,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> tuple[float, float, float]:
    prof = nozzle_profile(
        fuel,
        oxidizer,
        of_ratio,
        pc_bar,
        [eps],
        frozen=frozen,
        fuel_temp_k=fuel_temp_k,
        ox_temp_k=ox_temp_k,
    )
    return prof.gamma_cea[0], prof.temperatures_k[0], prof.temperatures_k[0]


def chamber_state(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_bar: float,
    eps: float = 20.0,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> dict[str, Any]:
    r = compute_performance(
        fuel,
        oxidizer,
        of_ratio,
        pc_bar,
        eps,
        fuel_temp_k,
        ox_temp_k,
        include_stations=True,
    )
    sp = r.chamber.species_mole_fractions if r.chamber else {}
    return {
        "T_k": r.tc_kelvin,
        "P_bar": pc_bar,
        "gamma": r.gamma_chamber,
        "mw": r.mw_chamber,
        "species_mole_fractions": sp,
    }
