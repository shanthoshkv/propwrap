# propwrap

**Typed propellant thermochemistry for liquid rockets** — a clean Python API over [NASA CEA](https://www1.grc.nasa.gov/research-and-engineering/ceaweb/) (via [RocketCEA](https://rocketcea.readthedocs.io/)) with optional [Cantera](https://cantera.org/) cross-checks.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/shanthoshkv/propwrap/blob/main/LICENSE)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/shanthoshkv/propwrap/blob/main/examples/quickstart.ipynb)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue.svg)](https://shanthoshkv.github.io/propwrap/)

> **Scope:** propellants and mixture performance, plus first-cut thrust sizing, altitude and throttle tables — not detailed engine design (nozzle contours, injectors, cooling cycles).  
> **Numbers:** ideal theoretical CEA unless you apply efficiency factors. **Not flight-certified.**  
> **Units:** public results in **SI** (Pa, K, m/s, kg/m³); Isp stays in **seconds** (rocketry standard) plus `ve` in m/s.

Project site: **[aboutkvs.vercel.app/propwrap.html](https://aboutkvs.vercel.app/propwrap.html)** (mirrored in this repo at [`website/`](https://github.com/shanthoshkv/propwrap/tree/main/website), preview with `python -m http.server 8080 --directory website`).

<p align="center">
  <img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/isp_map.png" alt="Vacuum Isp over O/F and chamber pressure for RP-1/LOX, made with propwrap" width="860">
  <br><sub>One call: <code>Mixture("RP-1","LOX").isp_map((1.8, 3.6, 0.1), (20, 200, 10), eps=20)</code>. Dashed line is the best O/F at each pressure.</sub>
</p>

---

## What this project is

I started propwrap because every propulsion course project I did began the same way: a half-working CEA script, a spreadsheet of unit conversions, and a nagging doubt about whether `ft/s` had snuck into a `m/s` column somewhere. This library is the thing I wished I'd had at the start. You name a fuel and an oxidizer, ask for a point or a sweep, and get numbers back in SI that you can paste straight into the next calculation.

`propwrap` is a **pip-installable library** for defining liquid propellant systems and computing their **ideal thermochemical performance**:

- Vacuum / sea-level specific impulse (shifting and frozen)
- Effective exhaust velocity \(v_e = I_{sp} \cdot g_0\) in m/s
- Characteristic velocity \(c^*\), chamber / throat / exit temperatures
- Product γ, molecular weight, transport properties (SI)
- Density impulse (ρ·Isp) and fair multi-propellant trades
- Custom fuels/oxidizers and multi-component **blends**
- Structured results (Pydantic), SQLite cache, CLI, dark-theme plots (**opt-in**)
- Built-in **unit converters** (`convert`, `propwrap.units`)

It is meant to be the **shared propellant backbone** for other tools — or a standalone desk tool for propellant selection studies.

---

## Why it exists

Working with CEA is powerful but awkward for modern workflows:

| Pain | What propwrap does |
|------|---------------------|
| Ad-hoc scripts and copy-paste CEA decks | One importable, typed library |
| English units leak (psia, Rankine, ft/s) | **SI public API** (Pa, K, m/s, kg/m³) + converters |
| Dicts / parsed strings as “results” | Pydantic models with readable `print(result)` |
| Comparing RP-1 vs CH₄ vs LH₂ at the **same** O/F | Trades at **each pair’s own optimum O/F** |
| “Did I already run this?” | Transparent SQLite cache |
| Hard to trust numbers | Documented [validation suite](https://github.com/shanthoshkv/propwrap/blob/main/docs/validation.md) |

**Why that matters:** a wrong γ, Isp, or mixture ratio propagates into every downstream calculation. Propellant choices are early and high-leverage. A single tested API reduces silent mistakes across a team or project.

---

## Overview

```text
You (script, CLI, or sibling tool)
        │
        ▼
   Mixture("RP-1", "LOX")          ← propellant pair
        │
        ├── evaluate / scan_of / density_impulse
        ├── compare_propellants([...])   ← fair trades
        ├── registry + blends
        ├── units.convert(...)           ← bar↔Pa, Isp↔ve, …
        │
        ├── cea_backend  → RocketCEA (NASA CEA)
        ├── cantera_backend → frozen γ cross-check
        └── cache → ~/.propwrap/cache.db
```

**In one sentence:** define a fuel/oxidizer pair, evaluate it at (O/F, Pc, ε), scan mixture ratio, and compare propellant systems with theoretical metrics in SI.

---

## What it produces

Everything below came out of the library itself (RP-1/LOX, Pc = 70 bar, LOX at 90 K). Plots use a dark theme by default; `set_theme("light")` or `--theme light` gives print-friendly output. Output is 300 dpi PNG.

### O/F sweep

The first thing most people want: where is the best mixture ratio, and how much does it cost to miss it? The shaded band is the gain from shifting equilibrium over frozen composition, the dotted line is stoichiometric.

<p align="center"><img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/of_sweep.png" alt="O/F sweep: shifting and frozen Isp, sea-level Isp and chamber temperature" width="860"></p>

```python
m = Mixture("RP-1", "LOX", fuel_temp_k=298.15, ox_temp_k=90.17)
m.scan_of((1.8, 3.6, 0.1), pc_bar=70, eps=20).plot(save="of_sweep.png")
```

### Nozzle and altitude behaviour

Left: how Isp and thrust coefficient grow with expansion ratio, with the point where exit pressure equals ambient and the Summerfield separation limit marked. Right: the same fixed nozzle flown through the US Standard 1976 atmosphere.

<p align="center">
  <img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/eps_sweep.png" alt="Area-ratio sweep" width="425">
  <img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/altitude.png" alt="Isp vs altitude" width="425">
</p>

### Pressure and composition

Chamber pressure pays off quickly then flattens out. The species plot shows what the flame is actually made of as you go richer: CO2 gives way to CO and H2.

<p align="center">
  <img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/pc_sweep.png" alt="Chamber pressure sweep" width="425">
  <img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/species.png" alt="Chamber species mole fractions vs O/F" width="425">
</p>

### Fair propellant trades

Comparing propellants at one shared O/F is a classic mistake. `compare_propellants` runs each pair at its own optimum and reports Isp, density impulse, flame temperature and c* side by side. Note how LH2/LOX wins on Isp and loses badly on density impulse.

<p align="center"><img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/compare.png" alt="Propellant comparison bars" width="860"></p>

### Station properties

One evaluation also gives you the gas state at chamber, throat and exit, which is what you need to start thinking about nozzle contours or heat loads.

<p align="center"><img src="https://raw.githubusercontent.com/shanthoshkv/propwrap/main/docs/img/stations.png" alt="Temperature, pressure, gamma and molar mass at each station" width="860"></p>

---

## Features

- **Beginner-friendly API** — `Mixture.evaluate()`, `print(result)`, optional plots  
- **SI results** — Pa, K, m/s, kg/m³; Isp in s + `ve_*` in m/s  
- **Unit converters** — `convert(70, "bar", "Pa")`, etc.  
- **Convenience inputs** — `pc_bar=70`, `pc_mpa=7`, or `pc=7e6` (Pa)  
- **Legacy aliases** — `Propellant`, `performance()` (bar) still work  
- **Workflows** — `characterize()`, `compare_propellants()`, `define_blend()`  
- **Registry** — densities, cryo defaults, storability, name aliases  
- **Blends** — multi-component wt% fuels/oxs  
- **Density-Isp** — ρ·Isp curves and rankings  
- **CLI** — `run`, `scan-of`, `map`, `altitude`, `throttle`, `info`, `doctor`, `characterize`, `compare-pairs`, …  
- **First-cut sizing** — thrust to mass flow, throat and exit diameter; altitude and throttle tables  
- **Parallel sweeps** — `workers=4` on any sweep or Isp map  
- **Jupyter and Excel** — results render as tables; `to_dataframe()` and `to_excel()`  
- **Validation** — goldens + regression + physics checks  

---

## Install

**Requirements:** Python **3.10+** (3.11/3.12 recommended), Windows / Linux / macOS.

### From PyPI (recommended)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate

pip install "propwrap[all]"   # core only: pip install propwrap
```

The core install is deliberately light: **rocketcea**, **pydantic≥2** and **numpy**. Everything else is an extra, and you get a friendly install hint if you use a feature whose extra is missing:

| Extra | Adds |
|-------|------|
| `propwrap[plot]` | matplotlib figures |
| `propwrap[cantera]` | frozen-γ cross-check |
| `propwrap[excel]` | pandas + openpyxl for `to_excel()` |
| `propwrap[all]` | all of the above |

Not sure your setup is right? Run `propwrap doctor`. It checks each package, whether the RocketCEA data folder is writable, and runs one sample point.

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

### From source (development)

```bash
git clone https://github.com/shanthoshkv/propwrap.git
cd propwrap
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

Full walkthrough: **[docs/how_to_use.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/how_to_use.md)** · Lab install notes: **[docs/INSTALL.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/INSTALL.md)**.

---

## Quick start

```python
from propwrap import Mixture, compare_propellants, set_defaults, convert

# --- one mixture point (pressure: use pc_bar for ease, stored as Pa) ---
m = Mixture("RP-1", "LOX")
r = m.evaluate(of=2.56, pc_bar=70, eps=20)
print(r)                              # human summary
print(r.isp_vac_shifting, "s")        # Isp
print(r.ve_vac_shifting, "m/s")       # exhaust velocity (SI)
print(r.pc_pa, "Pa", r.pc_bar, "bar")

# --- O/F scan (no plot unless you ask) ---
sw = m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20)
print(sw.summary())
# sw.plot(save="of_scan.png")

# --- unit conversion ---
print(convert(70, "bar", "Pa"))
print(convert(343.7, "s", "m/s"))     # Isp → ve

# --- session defaults ---
set_defaults(pc_bar=70, eps=40)
m.evaluate(of=2.56)

# --- fair multi-pair trade (each at its own best O/F) ---
trade = compare_propellants(
    ["RP-1/LOX", "CH4/LOX", "LH2/LOX", "MMH/N2O4"],
    pc_bar=70,
    eps=40,
)
print(trade)
```

Legacy names still work: `Propellant`, `performance(of, pc_bar, eps)` with **bar**.

---

## From propellant to hardware numbers (new in 0.2)

Once you have a performance point, the next question is always "so how big is the engine?". `size_engine` turns thrust into flow rates and geometry using the CEA result, with no hidden fudge factors. For a 1 MN sea-level RP-1/LOX engine at 70 bar and ε = 20, you get about a **339 mm throat** and a 1.52 m exit, at 351 kg/s total flow.

```python
r = m.evaluate(of=2.56, pc_bar=70, eps=20)
r.size(1e6, sea_level=True)
# {'mdot_kg_s': 350.9, 'mdot_ox_kg_s': 252.4, 'mdot_fuel_kg_s': 98.6,
#  'throat_diameter_m': 0.339, 'exit_diameter_m': 1.515, 'isp_s': 290.6, ...}

from propwrap import altitude_performance, throttle
altitude_performance(m, 2.56, 7e6, 20, [0, 5e3, 10e3, 30e3, 80e3])
throttle(m, 2.56, 7e6, 20, 1e6)      # fixed geometry, Pc scaled down
```

`throttle` also flags when the nozzle is likely to separate (Pe/Pamb below 0.4, the Summerfield rule of thumb). The ε = 20 nozzle above sits at 0.41 at full power, so any throttling at sea level crosses the line. That is a first-cut screen, not a flow-separation model.

If you set efficiencies on the mixture (`eta_cstar`, `eta_cf`), sizing uses the delivered Isp and c* rather than the ideal ones.

---

## CLI

Plots are **off** unless you pass `--plot` or `--save`.

```bash
# Pressure: prefer --pc-bar or --pc-mpa; --pc is pascals (SI)
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
propwrap run RP-1 LOX --of 2.56 --pc-mpa 7 --eps 20
propwrap run RP-1 LOX --of 2.56 --pc 7000000 --eps 20

propwrap scan-of RP-1 LOX --pc-bar 70 --eps 20 --range 2.0 3.5 0.1
propwrap characterize CH4 LOX --of 3.0 --pc-bar 100 --eps 25
propwrap compare-pairs --combos "RP-1/LOX,LH2/LOX,CH4/LOX" --pc-bar 70 --eps 40
propwrap density-isp --fuel RP-1 --ox LOX --range 1.8 3.4 0.1 --pc-bar 70 --eps 40
propwrap list --cryogenic
propwrap clear-cache
```

New in 0.2:

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20 --thrust 1e6 --sea-level   # adds engine sizing
propwrap scan-of RP-1 LOX --pc-bar 70 -j 4 --species --xlsx scan.xlsx           # parallel, Excel out
propwrap map RP-1 LOX --of-range 1.8 3.6 0.1 --pc-range 20 200 10 --eps 20 -j 4   # O/F x Pc Isp contour
propwrap altitude RP-1 LOX --of 2.56 --pc-bar 70 --eps 20 --save alt.png        # Isp vs altitude
propwrap throttle RP-1 LOX --of 2.56 --pc-bar 70 --eps 20 --thrust 1e6        # throttle table + separation flag
propwrap info CH4                      # properties + stoichiometric O/F with LOX
propwrap doctor                        # check the install
```

Global options: `--theme light` for print-ready plots and `--config case.toml` to keep a case in a file (keys are the argparse names, e.g. `pc_bar = 70`). Add `--json` for machine-readable output; hints go to stderr so JSON stays clean.

---

## Students & coursework

| Start here | Link |
|------------|------|
| **Install (lab PCs)** | [docs/INSTALL.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/INSTALL.md) |
| **How to use (beginner)** | [docs/how_to_use.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/how_to_use.md) |
| **Learning path** | [docs/learning/](https://github.com/shanthoshkv/propwrap/tree/main/docs/learning) |
| **1-page cheat sheet** | [docs/cheat_sheet.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/cheat_sheet.md) |
| **Sample lab assignment** | [docs/lab_assignment.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/lab_assignment.md) |
| **Generate lab pack** | `propwrap homework kerolox --name YourName` |

```bash
propwrap homework kerolox --name YourName
# → summary.md, assumptions.txt, CSV tables, PNG figures
```

Presets: `Case.student_lab()`, `Case.booster()`, `Case.upper_stage()`.

---

## Metrics (what gets computed)

| Metric | Field | Unit | Meaning |
|--------|--------|------|---------|
| Vacuum Isp (shifting) | `isp_vac_shifting` | s | Ideal equilibrium expansion |
| Vacuum Isp (frozen) | `isp_vac_frozen` | s | Frozen composition |
| Exhaust velocity | `ve_vac_shifting` | m/s | \(I_{sp} \cdot g_0\) |
| Sea-level Isp | `isp_sl_*` | s | ~1 atm ambient |
| Characteristic velocity | `c_star` | m/s | Chamber performance |
| Chamber / throat / exit T | `tc_kelvin`, … | K | |
| Chamber / exit pressure | `pc_pa`, `pe_pa` | Pa | |
| γ | `gamma_chamber`, … | — | |
| Molecular weight | `mw_chamber` | kg/kmol | |
| Bulk density | `bulk_density_kg_m3` | kg/m³ | Liquid mixture ρ(O/F) |
| Density impulse | `density_impulse_vac_shifting` | s·kg/m³ | Isp × ρ |
| Transport | `chamber.cp_j_kg_k`, `mu_pa_s`, … | SI | |

**Inputs (boundary conditions for CEA):**

| Input | Typical kwargs | Unit |
|-------|----------------|------|
| Mixture ratio | `of` / `of_ratio` | mass ox / mass fuel |
| Chamber pressure | `pc` / `pc_pa` / `pc_bar` / `pc_mpa` | Pa (or bar/MPa helpers) |
| Expansion ratio | `eps` | Ae/At (dimensionless) |

Pc and ε are **thermo boundary conditions** for evaluating the mixture — not a full engine design interface.

---

## Units (SI public API)

| Quantity | SI in results | Notes |
|----------|---------------|--------|
| Pressure | **Pa** | `.pc_bar` convenience view; input via `pc_bar=` / `pc_mpa=` |
| Temperature | **K** | |
| Velocity / c* | **m/s** | |
| Density | **kg/m³** | |
| Isp | **s** | plus `ve_*` in m/s |
| Density-Isp | **s·kg/m³** | |
| cp | J/(kg·K) | |
| Viscosity | Pa·s | |

```python
from propwrap import convert, units

convert(70, "bar", "Pa")
convert(7, "MPa", "bar")
convert(300, "s", "m/s")           # Isp → ve
convert(0.81, "g/cm3", "kg/m3")
units.bar_to_pa(70)
units.isp_s_to_ve_m_s(300)
```

Module reference: [`src/propwrap/units.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/units.py).

---

## Validation

| Asset | Description |
|-------|-------------|
| **[docs/validation.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/validation.md)** | Full report: NASA RP-1311, RocketCEA goldens, SI identities |
| **[tests/data/validation_catalog.json](https://github.com/shanthoshkv/propwrap/blob/main/tests/data/validation_catalog.json)** | Machine-readable anchors + primary sources |
| **[tests/test_physics_identities.py](https://github.com/shanthoshkv/propwrap/blob/main/tests/test_physics_identities.py)** | Hard physics: \(v_e=I_{sp}g_0\), \(C_f=v_e/c^*\), CEA bit-level match |
| **[tests/test_validation_suite.py](https://github.com/shanthoshkv/propwrap/blob/main/tests/test_validation_suite.py)** | Catalog-driven multi-propellant suite |

**Secured against:**

- NASA CEA methodology (RP-1311) via RocketCEA  
- RocketCEA published LOX/LH₂ Isp table (readthedocs QuickStart) — machine-precision match  
- BIPM standard \(g_0 = 9.80665\,\mathrm{m/s^2}\)  
- SI bar = \(10^5\) Pa exactly  
- Multi-pair regression + ideal-gas chamber density check  

```bash
pytest tests/test_physics_identities.py tests/test_validation_suite.py -v
pytest -q
```

**Remember:** catalog Isp values are **theoretical CEA**, not flight Merlin/RS-25 delivered performance.

---

## Documentation map

| Document | Audience |
|----------|----------|
| **[docs/how_to_use.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/how_to_use.md)** | **Beginners — start here** |
| [Docs site](https://shanthoshkv.github.io/propwrap/) | Generated API reference |
| [examples/quickstart.ipynb](https://colab.research.google.com/github/shanthoshkv/propwrap/blob/main/examples/quickstart.ipynb) | Run it in Colab, nothing to install |
| [README.md](https://github.com/shanthoshkv/propwrap/blob/main/README.md) | Overview (this file) |
| [docs/api_reference.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/api_reference.md) | API field/method list |
| [docs/validation.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/validation.md) | Validation report |
| [examples/](https://github.com/shanthoshkv/propwrap/tree/main/examples) | Runnable scripts |
| [LICENSE](https://github.com/shanthoshkv/propwrap/blob/main/LICENSE) | MIT |
| [pyproject.toml](https://github.com/shanthoshkv/propwrap/blob/main/pyproject.toml) | Package metadata |

---

## Project layout

```text
propwrap/
├── README.md
├── LICENSE
├── pyproject.toml
├── docs/
│   ├── how_to_use.md          ← beginner tutorial
│   ├── api_reference.md
│   └── validation.md
├── examples/
├── src/propwrap/              ← library
└── tests/
```

### Key modules

| Module | Role |
|--------|------|
| [`propellant.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/propellant.py) | `Mixture` main API |
| [`units.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/units.py) | SI converters |
| [`workflows.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/workflows.py) | characterize / compare / blend |
| [`trades.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/trades.py) | optimum-O/F trades, density-Isp |
| [`registry.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/registry.py) | propellant identity |
| [`cea_backend.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/cea_backend.py) | RocketCEA + English→SI |
| [`cli.py`](https://github.com/shanthoshkv/propwrap/blob/main/src/propwrap/cli.py) | command line |

---

## Examples

```bash
python examples/basic_performance.py
python examples/propellant_trade.py
python examples/lox_ch4_case.py
```

| Script | Topic |
|--------|--------|
| [examples/basic_performance.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/basic_performance.py) | Single point |
| [examples/of_sweep_lox_rp1.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/of_sweep_lox_rp1.py) | O/F sweep |
| [examples/propellant_trade.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/propellant_trade.py) | Multi-pair trade |
| [examples/lox_ch4_case.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/lox_ch4_case.py) | Methalox |
| [examples/custom_propellants.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/custom_propellants.py) | Custom cards |
| [examples/gamma_profile_for_nozzle.py](https://github.com/shanthoshkv/propwrap/blob/main/examples/gamma_profile_for_nozzle.py) | γ(ε) data shape |

---

## Stable API (0.2.x)

Treat these as stable across 0.2.x patch releases:

| Surface | Examples |
|---------|----------|
| Core | `Mixture`, `Propellant`, `evaluate`, `scan_of`, `pc_bar` / `pc_mpa` / `pc` |
| Workflows | `compare_propellants`, `characterize`, `define_blend`, `density_isp_curve` |
| Units | `convert`, `propwrap.units` |
| Results | `PerformanceResult` fields in [docs/api_reference.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/api_reference.md) |
| CLI | `propwrap run`, `homework`, `scan-of`, `characterize`, `compare-pairs` |

May still change: Cantera cross-check details, plot styling, η efficiency knobs, cache internals. See [CHANGELOG.md](https://github.com/shanthoshkv/propwrap/blob/main/CHANGELOG.md).

---

## Limitations

1. **Ideal 1-D CEA** — not kinetics, multiphase losses, or flight performance.  
2. **Shifting vs frozen** — reality is between the two.  
3. **Theoretical ≠ delivered** — optional `efficiency=(ηc*, ηCf)` is rough only.  
4. **Custom cards** — validated for structure, not thermodynamic realism.  
5. **Cantera γ** — approximate major-species frozen compare (optional `cantera` extra). CEA's chamber γ is the equilibrium value while Cantera's is frozen, so expect them to differ.  
6. **Sizing and throttling are first-cut** — ideal-gas CEA numbers plus a standard atmosphere, no losses beyond the efficiencies you supply.  
7. **RocketCEA** is GPL-family; this repo’s own code is MIT — review licenses for proprietary products.  
8. **Not flight-certified.**

---

## Development

```bash
pip install -e ".[dev]"
pytest -q
python -m build          # sdist + wheel → dist/
twine check dist/*
```

CI runs on Ubuntu and Windows for Python 3.10–3.12 (see `.github/workflows/ci.yml`).

Release steps: [docs/RELEASING.md](https://github.com/shanthoshkv/propwrap/blob/main/docs/RELEASING.md).

---

## Acknowledgments

- **NASA CEA** — Gordon & McBride; NASA RP-1311  
- **[RocketCEA](https://rocketcea.readthedocs.io/)** — Charlie Taylor / Applied Python  
- **[Cantera](https://cantera.org/)**  

---

## License

MIT for propwrap source — see [LICENSE](https://github.com/shanthoshkv/propwrap/blob/main/LICENSE).  
**RocketCEA** (GPL-family) and other third-party packages keep their own licenses. Installing this stack is not “all MIT.”
