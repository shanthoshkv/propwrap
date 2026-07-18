"""O/F sweep for LOX/RP-1 with dark-theme plot."""

from pathlib import Path

from propwrap import Propellant

p = Propellant("RP-1", "LOX")
sweep = p.sweep_of_ratio((2.0, 3.2, 0.1), pc_bar=70.0, eps=20.0)
opt = sweep.optimum("isp_vac_shifting")
print(f"Optimum O/F = {opt.of_ratio:.2f}, Isp_vac = {opt.isp_vac_shifting:.2f} s")

out = Path(__file__).with_name("of_sweep_lox_rp1.png")
sweep.plot(save_path=str(out))
print(f"Wrote {out}")
