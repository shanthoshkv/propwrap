# propwrap API reference

For a beginner walkthrough, see **[how_to_use.md](how_to_use.md)**.

---

## `Mixture` (preferred)

Aliases: `Propellant`, `PropellantPair`.

```python
Mixture(
    fuel: str,
    oxidizer: str,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    cache_enabled: bool = True,
    apply_cryo_defaults: bool = True,
    eta_cstar: float = 1.0,
    eta_cf: float = 1.0,
    efficiency: tuple[float, float] | None = None,  # (ηc*, ηCf)
    inlet_temps: "auto" | "none" | dict | None = None,
)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `evaluate(of=..., pc_bar=... \| pc=... \| pc_mpa=..., eps=...)` | `PerformanceResult` | One point (SI storage) |
| `performance(of_ratio, pc_bar, eps)` | `PerformanceResult` | Legacy; **pc_bar in bar** |
| `scan_of(of_range, pc_bar=..., eps=...)` | `SweepResult` | O/F scan |
| `density_impulse(of_range, pc_bar=..., eps=...)` | `DensityIspCurve` | ρ·Isp vs O/F |
| `product_gamma_profile(of=..., pc_bar=..., eps_range=...)` | `GammaProfile` | γ, T, Mw vs ε |
| `study(of=..., pc_bar=..., eps=...)` | `MixtureStudy` | Point + optional scans |
| `cross_validate(...)` | `list[CrossValidationResult]` | CEA vs Cantera |
| `clear_cache()` | `int` | Clear SQLite cache |

### Pressure inputs

| Kwarg | Unit |
|-------|------|
| `pc` / `pc_pa` | Pa (SI) |
| `pc_bar` | bar |
| `pc_mpa` | MPa |
| `pc_psi` | psi |

Stored always as `pc_pa` [Pa]. Convenience: `result.pc_bar`.

---

## Workflows

```python
from propwrap import characterize, compare_propellants, define_blend, Case, set_defaults

set_defaults(pc_bar=70, eps=40)
characterize("RP-1", "LOX", of=2.56, pc_bar=70, eps=20, plot=False)
compare_propellants(["RP-1/LOX", "CH4/LOX", "LH2/LOX"], pc_bar=70, eps=40)
define_blend("MyM20", [("MMH", 20), ("UDMH", 80)], kind="fuel")

case = Case(pc_bar=70, eps=40)
case.evaluate("RP-1", "LOX", of=2.56)
```

---

## Units module

```python
from propwrap import convert, units

convert(70, "bar", "Pa")
convert(300, "s", "m/s")      # Isp → ve
units.bar_to_pa(70)
units.isp_s_to_ve_m_s(300)
units.g_cm3_to_kg_m3(0.81)
```

See [`src/propwrap/units.py`](../src/propwrap/units.py).

---

## Models (SI fields)

### `PerformanceResult`

| Field | Unit |
|-------|------|
| `of_ratio` | — |
| `pc_pa` | Pa |
| `eps` | — |
| `isp_vac_shifting`, `isp_vac_frozen`, `isp_sl_*` | s |
| `ve_vac_shifting`, `ve_vac_frozen` | m/s |
| `c_star` | m/s |
| `cf_vac`, `cf_sl` | — |
| `gamma_*` | — |
| `mw_chamber` | kg/kmol |
| `tc_kelvin`, `tt_kelvin`, `te_kelvin` | K |
| `pe_pa` | Pa |
| `bulk_density_kg_m3` | kg/m³ |
| `density_impulse_vac_shifting` | s·kg/m³ |
| `chamber` / `throat` / `exit` | `StationState` |
| `warnings` | list[str] |

Properties (not serialized): `pc_bar`, `pe_bar`, `bulk_density_g_cm3`.

### `StationState`

T [K], `pressure_pa` [Pa], `density_kg_m3`, Mw, γ, cp [J/(kg·K)], R, μ [Pa·s], k [W/(m·K)], Pr, species.

### `SweepResult` / `DensityIspCurve` / `TradeResult` / `GammaProfile`

See models in source; all pressures in Pa, densities in kg/m³.

---

## Registry & blends

```python
from propwrap import get_propellant, list_registry, add_blend, add_custom_propellant

get_propellant("RP-1").density_kg_m3
list_registry(storage="cryogenic")
add_blend("MyM20", [("MMH", 20), ("UDMH", 80)], kind="fuel")
```

---

## CLI

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
propwrap scan-of RP-1 LOX --pc-bar 70 --eps 20 --range 2.0 3.2 0.1
propwrap compare-pairs --combos "RP-1/LOX,LH2/LOX" --pc-bar 70 --eps 40
propwrap list --cryogenic
propwrap clear-cache
```

`--pc` = Pa, `--pc-bar` = bar, `--pc-mpa` = MPa. Plots: `--plot` / `--save`.

---

## Plotting

All plot functions return a matplotlib `Figure`. They do **not** call `plt.show()` unless `show=True`.

```python
sweep.plot(save="out.png", show=False)
```
