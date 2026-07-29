"""RocketCEA wrapper — public outputs are SI (see propwrap.units)."""

from __future__ import annotations

import math
from typing import Any

from propwrap.models import GammaProfile, PerformanceResult, StationState
from propwrap.propellant_library import (
    bulk_density_kg_m3,
    cryo_default_temps_k,
    resolve_cea_names,
    stoich_of_ratio,
)
from propwrap.sanity import sanity_check
from propwrap.units import (
    G0,
    G0_FT_S2,
    R_UNIVERSAL,
    SL_PAMB_PA,
    SL_PAMB_PSIA,
    bar_to_psia,
    cea_cp_to_si,
    cea_k_to_si,
    cea_mu_to_si,
    density_impulse_si,
    ft_s_to_m_s,
    isp_s_to_ve_m_s,
    kelvin_to_rankine,
    lbm_ft3_to_kg_m3,
    pa_to_bar,
    pa_to_psi,
    rankine_to_kelvin,
)


def _finite(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    return v if math.isfinite(v) else default


def _pc_psia(pc_pa: float) -> float:
    return pa_to_psi(pc_pa)


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
        kwargs["fuelT"] = kelvin_to_rankine(fuel_temp_k)
    if ox_temp_k is not None:
        kwargs["oxT"] = kelvin_to_rankine(ox_temp_k)
    try:
        return CEA_Obj(**kwargs)
    except TypeError:
        kwargs.pop("fuelT", None)
        kwargs.pop("oxT", None)
        return CEA_Obj(oxName=ox_name, fuelName=fuel_name)


def _species_at_station(raw: Any, station_idx: int) -> dict[str, float]:
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
    cp, mu, k, pr = (float(tr[0]), float(tr[1]), float(tr[2]), float(tr[3]))
    return cea_cp_to_si(cp), cea_mu_to_si(mu), cea_k_to_si(k), pr


def _station(
    name: str,
    T_k: float,
    P_pa: float,
    rho_kg_m3: float,
    mw: float,
    gamma: float,
    tr: Any,
    species: dict[str, float],
) -> StationState:
    cp, mu, k, pr = _transport_si(tr)
    r_sp = R_UNIVERSAL / mw if mw > 0 else 0.0
    return StationState(
        name=name,  # type: ignore[arg-type]
        temperature_k=T_k,
        pressure_pa=P_pa,
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
    pc_pa: float,
    eps: float,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    *,
    eta_cstar: float = 1.0,
    eta_cf: float = 1.0,
    apply_cryo_defaults: bool = True,
    include_stations: bool = True,
) -> PerformanceResult:
    """CEA frozen + shifting performance. ``pc_pa`` is chamber pressure [Pa]."""
    if of_ratio <= 0:
        raise ValueError(f"of_ratio must be > 0, got {of_ratio}")
    if pc_pa <= 0:
        raise ValueError(f"pc_pa must be > 0 Pa, got {pc_pa}")
    if eps <= 1.0:
        raise ValueError(f"eps (Ae/At) must be > 1, got {eps}")
    if not (0 < eta_cstar <= 1.2 and 0 < eta_cf <= 1.2):
        raise ValueError("eta_cstar and eta_cf should be in (0, 1.2]")

    ft, ot, temps_default = resolve_temps(
        fuel, oxidizer, fuel_temp_k, ox_temp_k, apply_cryo_defaults=apply_cryo_defaults
    )
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_pa)
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
    pe_pa = pc_pa / pc_over_pe if pc_over_pe > 0 else 0.0

    cstar_m = ft_s_to_m_s(cstar_ft)
    cf_vac = float(isp_vac_s) * G0_FT_S2 / float(cstar_ft)
    fuel_name, ox_name = resolve_cea_names(fuel, oxidizer)

    stoich = stoich_of_ratio(fuel_name, ox_name, cea)
    rho_bulk, dens_basis = bulk_density_kg_m3(fuel_name, ox_name, mr)
    dens_isp = (
        density_impulse_si(isp_vac_s, rho_bulk) if rho_bulk is not None else None
    )

    ch = th = ex = None
    if include_stations:
        try:
            sp_raw = cea.get_SpeciesMoleFractions(Pc=pc, MR=mr, eps=eps)
        except Exception:
            sp_raw = None
        sp_ch = _species_at_station(sp_raw, 1)
        sp_th = _species_at_station(sp_raw, 2)
        sp_ex = _species_at_station(sp_raw, 3)
        tr_ch = cea.get_Chamber_Transport(Pc=pc, MR=mr, eps=eps)
        tr_th = cea.get_Throat_Transport(Pc=pc, MR=mr, eps=eps)
        tr_ex = cea.get_Exit_Transport(Pc=pc, MR=mr, eps=eps)
        dens = cea.get_Densities(Pc=pc, MR=mr, eps=eps)
        rho_ch = lbm_ft3_to_kg_m3(dens[0])
        rho_th = lbm_ft3_to_kg_m3(dens[1])
        rho_ex = lbm_ft3_to_kg_m3(dens[2])
        try:
            p_th_pa = pc_pa / float(cea.get_Throat_PcOvPe(Pc=pc, MR=mr, eps=eps))
        except Exception:
            p_th_pa = 0.56 * pc_pa
        ch = _station(
            "chamber",
            rankine_to_kelvin(tc_r),
            pc_pa,
            rho_ch,
            float(mw_ch),
            float(gam_ch),
            tr_ch,
            sp_ch,
        )
        th = _station(
            "throat",
            rankine_to_kelvin(tt_r),
            p_th_pa,
            rho_th,
            float(mw_th),
            float(gam_th),
            tr_th,
            sp_th,
        )
        ex = _station(
            "exit",
            rankine_to_kelvin(te_r),
            pe_pa,
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
        pc_pa=float(pc_pa),
        eps=float(eps),
        isp_vac_shifting=_finite(isp_vac_s),
        isp_vac_frozen=_finite(isp_vac_f),
        isp_sl_shifting=_finite(isp_sl_s),
        isp_sl_frozen=_finite(isp_sl_f),
        ve_vac_shifting=_finite(isp_s_to_ve_m_s(isp_vac_s)),
        ve_vac_frozen=_finite(isp_s_to_ve_m_s(isp_vac_f)),
        c_star=_finite(cstar_m * eta_cstar),
        cf_vac=_finite(float(cf_vac) * eta_cf),
        cf_sl=_finite(float(cf_sl_s) * eta_cf),
        gamma_chamber=_finite(gam_ch),
        gamma_throat=_finite(gam_th),
        gamma_exit=_finite(gam_ex),
        mw_chamber=_finite(mw_ch),
        tc_kelvin=_finite(rankine_to_kelvin(tc_r)),
        tt_kelvin=_finite(rankine_to_kelvin(tt_r)),
        te_kelvin=_finite(rankine_to_kelvin(te_r)),
        fuel=fuel_name,
        oxidizer=ox_name,
        pe_pa=pe_pa,
        pc_over_pe=pc_over_pe,
        ambient_mode=str(mode_s),
        fuel_temp_k=ft,
        ox_temp_k=ot,
        temps_are_default=temps_default,
        pamb_sl_pa=SL_PAMB_PA,
        chamber=ch,
        throat=th,
        exit=ex,
        stoich_of_ratio=stoich,
        density_impulse_vac_shifting=dens_isp,
        bulk_density_kg_m3=rho_bulk,
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
    pc_pa: float,
    eps: float,
    pamb_pa: float,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    *,
    frozen: bool = False,
) -> dict[str, float | str]:
    """Isp and Cf at ambient pressure [Pa]."""
    if pamb_pa < 0:
        raise ValueError("pamb_pa must be >= 0")
    ft, ot, _ = resolve_temps(fuel, oxidizer, fuel_temp_k, ox_temp_k)
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_pa)
    pamb = pa_to_psi(pamb_pa) if pamb_pa > 0 else 1e-6
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
        "ve_m_s": isp_s_to_ve_m_s(isp),
        "cf": float(cf),
        "pamb_pa": float(pamb_pa),
        "mode": str(mode),
    }


def nozzle_profile(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_pa: float,
    area_ratios: list[float],
    *,
    frozen: bool = True,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> GammaProfile:
    ft, ot, _ = resolve_temps(fuel, oxidizer, fuel_temp_k, ox_temp_k)
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_pa)
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
        temps.append(rankine_to_kelvin(temps_r[2]))
        mws.append(float(mw))
        press.append(pc_pa / pcope if pcope > 0 else 0.0)
    const_g = sum(gams) / len(gams) if gams else None
    return GammaProfile(
        area_ratios=list(area_ratios),
        gamma_cea=gams,
        gamma_cantera=None,
        temperatures_k=temps,
        mw=mws,
        pressure_pa=press,
        source="cea_frozen" if frozen else "cea_shifting",
        constant_gamma_equiv=const_g,
    )


def gamma_and_temp_at_eps(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_pa: float,
    eps: float,
    *,
    frozen: bool = True,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> tuple[float, float, float]:
    """Return ``(gamma_exit, T_exit_K, T_chamber_K)`` at one area ratio."""
    ft, ot, _ = resolve_temps(fuel, oxidizer, fuel_temp_k, ox_temp_k)
    cea = _make_cea_obj(fuel, oxidizer, ft, ot)
    pc = _pc_psia(pc_pa)
    frz = 1 if frozen else 0
    e = max(float(eps), 1.0001)
    temps_r = cea.get_Temperatures(
        Pc=pc, MR=of_ratio, eps=e, frozen=frz, frozenAtThroat=0
    )
    _mw, gam = cea.get_exit_MolWt_gamma(Pc=pc, MR=of_ratio, eps=e)
    tc_k = rankine_to_kelvin(temps_r[0])
    te_k = rankine_to_kelvin(temps_r[2])
    return float(gam), float(te_k), float(tc_k)


def chamber_state(
    fuel: str,
    oxidizer: str,
    of_ratio: float,
    pc_pa: float,
    eps: float = 20.0,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
) -> dict[str, Any]:
    r = compute_performance(
        fuel,
        oxidizer,
        of_ratio,
        pc_pa,
        eps,
        fuel_temp_k,
        ox_temp_k,
        include_stations=True,
    )
    sp = r.chamber.species_mole_fractions if r.chamber else {}
    return {
        "T_k": r.tc_kelvin,
        "P_pa": pc_pa,
        "P_bar": pa_to_bar(pc_pa),
        "gamma": r.gamma_chamber,
        "mw": r.mw_chamber,
        "species_mole_fractions": sp,
    }
