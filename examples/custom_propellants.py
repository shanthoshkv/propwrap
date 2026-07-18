"""Two custom propellant definitions via the validated card-deck path."""

from propwrap import Propellant, add_custom_propellant

# 1) Kerosene blend surrogate (C12H24) — illustrative Hf only
card1 = add_custom_propellant(
    name="KeroBlend",
    formula="C12H24",
    heat_of_formation=-82_000.0,  # cal/mol (CEA convention)
    kind="fuel",
    temperature_k=298.15,
    density_g_ml=0.81,
    comment="Illustrative kerosene blend — not a certified propellant card",
)
print("Card 1:\n", card1)

# 2) Hybrid fuel grain surrogate (HTPB-like simplified CH formula)
card2 = add_custom_propellant(
    name="HybridGrain",
    formula="C4 H 6 O 0.1",  # already spaced CEA form
    heat_of_formation=-5_000.0,
    kind="fuel",
    temperature_k=298.15,
    comment="Toy hybrid grain binder surrogate",
)
print("Card 2:\n", card2)

try:
    p = Propellant("KeroBlend", "LOX", cache_enabled=False)
    r = p.performance(of_ratio=2.4, pc_bar=50.0, eps=12.0)
    print(f"KeroBlend/LOX Isp_vac = {r.isp_vac_shifting:.2f} s, Tc = {r.tc_kelvin:.1f} K")
except Exception as exc:
    print(f"Custom propellant CEA run failed (card may need tuning): {exc}")
