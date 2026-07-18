"""Compare several propellant combinations at a shared operating point."""

from pathlib import Path

from propwrap import Propellant
from propwrap.plotting import plot_propellant_comparison

COMBOS = [
    ("RP-1", "LOX", 2.56),
    ("LH2", "LOX", 5.5),
    ("MMH", "N2O4", 2.0),
]

results = []
labels = []
for fuel, ox, of in COMBOS:
    r = Propellant(fuel, ox).performance(of_ratio=of, pc_bar=70.0, eps=20.0)
    results.append(r)
    labels.append(f"{fuel}/{ox}")
    print(
        f"{labels[-1]:<12} Isp_vac={r.isp_vac_shifting:7.2f} s  "
        f"Tc={r.tc_kelvin:7.1f} K  c*={r.c_star:7.1f} m/s"
    )

out = Path(__file__).with_name("propellant_comparison.png")
plot_propellant_comparison(results, labels, save_path=str(out))
print(f"Wrote {out}")
