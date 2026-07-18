"""Minimal performance query — README quickstart companion."""

from propwrap import Propellant

p = Propellant("RP-1", "LOX")
r = p.performance(of_ratio=2.56, pc_bar=70.0, eps=20.0)

print(f"Fuel/Ox:     {r.fuel}/{r.oxidizer}")
print(f"Isp vac:     {r.isp_vac_shifting:.2f} s  (shifting)")
print(f"Isp vac frz: {r.isp_vac_frozen:.2f} s")
print(f"c*:          {r.c_star:.1f} m/s")
print(f"Tc:          {r.tc_kelvin:.1f} K")
print(f"γ chamber:   {r.gamma_chamber:.4f}")
print(f"γ exit:      {r.gamma_exit:.4f}")
