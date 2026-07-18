"""LOX/CH4 engineering case — methane path."""

from propwrap import Propellant

p = Propellant("CH4", "LOX")  # cryo defaults applied
case = p.engine_case(of_ratio=3.0, pc_bar=100.0, eps=25.0)
r = case.design
print(f"CH4/LOX  O/F={r.of_ratio}  Pc={r.pc_bar} bar  ε={r.eps}")
print(f"Isp_vac={r.isp_vac_shifting:.1f}s  c*={r.c_star:.0f} m/s  Tc={r.tc_kelvin:.0f} K")
print(f"Pe={r.pe_bar:.4f} bar  density_Isp={r.density_impulse_vac_shifting}")
if r.chamber:
    print(f"Chamber cp={r.chamber.cp_j_kg_k:.0f} J/kg-K  μ={r.chamber.mu_pa_s:.3e} Pa·s")
print("Notes:", *case.notes, sep="\n  ")
