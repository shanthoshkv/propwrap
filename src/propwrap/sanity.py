"""Engineering sanity checks on performance results."""

from __future__ import annotations

from propwrap.models import PerformanceResult
from propwrap.units import G0, R_UNIVERSAL


def sanity_check(r: PerformanceResult) -> list[str]:
    """Return human-readable warnings (empty if all checks pass)."""
    w: list[str] = []
    if r.gamma_exit < r.gamma_chamber - 1e-6:
        w.append(
            f"gamma_exit ({r.gamma_exit:.4f}) < gamma_chamber ({r.gamma_chamber:.4f}); "
            "unexpected for typical expansion"
        )
    if not (r.te_kelvin < r.tt_kelvin < r.tc_kelvin):
        w.append(
            f"temperature order odd: Te={r.te_kelvin:.1f}, Tt={r.tt_kelvin:.1f}, "
            f"Tc={r.tc_kelvin:.1f} K"
        )
    if r.isp_vac_shifting + 1e-6 < r.isp_sl_shifting:
        w.append("Isp_vac_shifting < Isp_sl_shifting (unexpected)")
    if r.isp_vac_shifting + 1e-6 < r.isp_vac_frozen:
        w.append("shifting Isp_vac < frozen Isp_vac (unexpected for ideal CEA)")
    if r.c_star < 1000 or r.c_star > 3500:
        w.append(f"c*={r.c_star:.1f} m/s outside typical 1000–3500 m/s band")
    if r.tc_kelvin < 1500 or r.tc_kelvin > 4500:
        w.append(f"Tc={r.tc_kelvin:.1f} K outside typical 1500–4500 K band")
    if r.pe_pa <= 0 and r.eps > 1.5:
        w.append(f"pe_pa={r.pe_pa} non-positive")
    if r.eps > 40 and r.isp_vac_shifting > 0 and r.isp_sl_shifting < 0.85 * r.isp_vac_shifting:
        w.append(
            f"ε={r.eps:.1f} large for sea-level: overexpansion likely "
            f"(Isp_sl/Isp_vac={r.isp_sl_shifting / r.isp_vac_shifting:.2f})"
        )
    # Internal SI consistency (hard physics identities)
    if r.isp_vac_shifting > 0 and r.ve_vac_shifting > 0:
        ve_expect = r.isp_vac_shifting * G0
        if abs(r.ve_vac_shifting - ve_expect) / ve_expect > 1e-6:
            w.append(
                f"ve_vac_shifting inconsistent with Isp*g0 "
                f"({r.ve_vac_shifting:.3f} vs {ve_expect:.3f} m/s)"
            )
    if r.c_star > 0 and r.isp_vac_shifting > 0:
        cf_expect = (r.isp_vac_shifting * G0) / r.c_star
        if abs(r.cf_vac - cf_expect) / cf_expect > 1e-4:
            w.append(
                f"cf_vac inconsistent with ve/c* ({r.cf_vac:.6f} vs {cf_expect:.6f})"
            )
    if r.pc_over_pe > 0 and r.pe_pa > 0:
        if abs(r.pc_pa / r.pe_pa - r.pc_over_pe) / r.pc_over_pe > 1e-4:
            w.append("pc_pa/pe_pa does not match pc_over_pe")
    if r.chamber is not None and r.tc_kelvin > 0 and r.mw_chamber > 0:
        rho_ig = r.pc_pa * r.mw_chamber / (R_UNIVERSAL * r.tc_kelvin)
        if r.chamber.density_kg_m3 > 0:
            rel = abs(r.chamber.density_kg_m3 - rho_ig) / rho_ig
            # CEA density should match ideal-gas P·Mw/(R·T) closely for gas phase
            if rel > 0.05:
                w.append(
                    f"chamber density differs from ideal-gas estimate by {rel*100:.1f}%"
                )
    if r.temps_are_default and r.oxidizer == "LOX":
        w.append(
            "using default inlet temperatures; set fuel_temp_k/ox_temp_k for cryogens"
        )
    if r.stoich_of_ratio is not None and r.of_ratio > 0:
        ratio = r.of_ratio / r.stoich_of_ratio
        if ratio < 0.5 or ratio > 1.5:
            w.append(
                f"O/F={r.of_ratio:.3f} is {ratio:.2f}× stoich "
                f"(stoich≈{r.stoich_of_ratio:.3f}); check mixture ratio"
            )
    return w
