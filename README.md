# propwrap

**Typed propellant thermochemistry for liquid rockets** — a clean Python API over [NASA CEA](https://www1.grc.nasa.gov/research-and-engineering/ceaweb/) (via [RocketCEA](https://rocketcea.readthedocs.io/)) with optional [Cantera](https://cantera.org/) cross-checks.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/shanthoshkv/propwrap/blob/main/LICENSE)

> **Scope:** propellants and mixture performance — not full engine design (nozzles, injectors, cooling cycles).  
> **Numbers:** ideal theoretical CEA unless you apply efficiency factors. **Not flight-certified.**  
> **Units:** public results in **SI** (Pa, K, m/s, kg/m³); Isp stays in **seconds** (rocketry standard) plus `ve` in m/s.

---

## Project website

**[https://aboutkvs.vercel.app/propwrap.html](https://aboutkvs.vercel.app/propwrap.html)** — full project site (overview, SI units, validation, install).

Same page is also in the repo as [`website/index.html`](https://github.com/shanthoshkv/propwrap/blob/main/website/index.html) (and `website/propwrap.html`).

Local preview from a clone:

```bash
python -m http.server 8080 --directory website
# then http://localhost:8080
```

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

## What this project is

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
- **CLI** — `propwrap run`, `scan-of`, `characterize`, `compare-pairs`, …  
- **Validation** — goldens + regression + physics checks  

---

## Install

**Requirements:** Python **3.10+** (3.11/3.12 recommended), Windows / Linux / macOS.

### From PyPI (recommended)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate

pip install propwrap
```

Required dependencies (installed automatically): **rocketcea**, **cantera**, **pydantic≥2**, **matplotlib**, **numpy**.

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

Add `--json` for machine-readable output.

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

## Stable API (0.1.x)

Treat these as stable across 0.1.x patch releases:

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
5. **Cantera γ** — approximate major-species frozen compare (Cantera is a required dependency).  
6. **RocketCEA** is GPL-family; this repo’s own code is MIT — review licenses for proprietary products.  
7. **Not flight-certified.**

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
