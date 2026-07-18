"""Propellant-system trade: each pair at its own optimum O/F + density-Isp."""

from propwrap import density_isp_curve, trade_at_optimum_of
from propwrap.plotting import plot_density_isp

trade = trade_at_optimum_of(
    [
        ("RP-1", "LOX"),
        ("CH4", "LOX"),
        ("LH2", "LOX"),
        ("MMH", "N2O4"),
    ],
    pc_bar=70.0,
    eps=40.0,
)
print(trade.summary_table())

curve = density_isp_curve("RP-1", "LOX", (1.8, 3.4, 0.1), pc_bar=70.0, eps=40.0)
print(
    f"\nRP-1/LOX: Isp opt O/F={curve.optimum_isp_of:.2f}, "
    f"ρ·Isp opt O/F={curve.optimum_density_isp_of}"
)
plot_density_isp(curve, save_path="density_isp_rp1_lox.png")
print("Wrote density_isp_rp1_lox.png")
