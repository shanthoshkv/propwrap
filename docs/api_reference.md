# propwrap API reference

## `Propellant`

```python
Propellant(
    fuel: str,
    oxidizer: str,
    fuel_temp_k: float | None = None,
    ox_temp_k: float | None = None,
    cache_enabled: bool = True,
)
```

| Method | Returns | Description |
|--------|---------|-------------|
| `performance(of_ratio, pc_bar, eps)` | `PerformanceResult` | Frozen + shifting performance at one point |
| `sweep_of_ratio(of_range, pc_bar, eps)` | `SweepResult` | O/F sweep; range = `(start, stop, step)` |
| `sweep_pc(of_ratio, pc_range, eps)` | `SweepResult` | Chamber pressure [bar] sweep |
| `sweep_eps(of_ratio, pc_bar, eps_range)` | `SweepResult` | Area-ratio sweep |
| `gamma_vs_area_ratio(of_ratio, pc_bar, eps_range, use_cantera=True)` | `GammaProfile` | γ(T) along nozzle for MOC tools |
| `cross_validate(of_ratio, pc_bar, eps, tolerance_pct=5.0)` | `list[CrossValidationResult]` | CEA vs Cantera |
| `compare_to(other, of_ratio, pc_bar, eps)` | `dict` | Side-by-side comparison |
| `clear_cache()` | `int` | Clear SQLite cache; returns rows deleted |

### Units

- `of_ratio`: mass oxidizer / mass fuel
- `pc_bar`: bar
- `eps`: Ae/At
- Isp fields: seconds
- `c_star`: m/s
- temperatures: K

---

## Models

### `PerformanceResult`

Fields: `of_ratio`, `pc_bar`, `eps`, `isp_vac_shifting`, `isp_vac_frozen`, `isp_sl_shifting`, `isp_sl_frozen`, `c_star`, `cf_vac`, `cf_sl`, `gamma_chamber`, `gamma_throat`, `gamma_exit`, `mw_chamber`, `tc_kelvin`, `tt_kelvin`, `te_kelvin`, `fuel`, `oxidizer`.

### `GammaProfile`

Fields: `area_ratios`, `gamma_cea`, `gamma_cantera` (optional), `temperatures_k`, `source`.

### `CrossValidationResult`

Fields: `parameter`, `cea_value`, `cantera_value`, `absolute_diff`, `percent_diff`, `within_tolerance`.

### `SweepResult`

Fields: `sweep_variable`, `values`, `results`.

Methods: `optimum(metric="isp_vac_shifting")`, `plot(...)`, `to_csv(path)`, `to_json(path)`.

---

## Library helpers

```python
list_propellants() -> dict[str, list[str]]
add_custom_propellant(name, formula, heat_of_formation, *, kind="fuel", temperature_k=298.15, density_g_ml=None, comment="") -> str
```

`heat_of_formation` is in **cal/mol** (CEA card convention).

---

## Plotting

```python
from propwrap.plotting import (
    plot_of_sweep,
    plot_pc_sweep,
    plot_eps_sweep,
    plot_gamma_profile,
    plot_propellant_comparison,
)
```

All return `matplotlib.figure.Figure`. Optional `save_path` writes PNG/SVG. None call `plt.show()`.

---

## Export

```python
from propwrap.export import (
    performance_to_json,
    performance_to_csv,
    sweep_to_json,
    sweep_to_csv,
    gamma_profile_to_json,
    gamma_profile_to_csv,
)
```

---

## CLI

Entry point: `propwrap` → `propwrap.cli:main`.

Commands: `performance`, `sweep`, `compare`, `list-propellants`, `clear-cache`.
