# propwrap

**Typed propellant thermochemistry for liquid rockets** — a clean Python API over [NASA CEA](https://www1.grc.nasa.gov/research-and-engineering/ceaweb/) (via [RocketCEA](https://rocketcea.readthedocs.io/)) with optional [Cantera](https://cantera.org/) cross-checks.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Scope:** propellants and mixture performance — not full engine design (nozzles, injectors, cooling cycles).  
> **Numbers:** ideal theoretical CEA unless you apply efficiency factors. Not flight-certified.

---

## What this project is

`propwrap` is a **pip-installable library** for defining liquid propellant systems and computing their **ideal thermochemical performance**:

- Vacuum / sea-level specific impulse (shifting and frozen)
- Characteristic velocity \(c^*\), chamber/throat/exit temperatures
- Product γ, molecular weight, transport properties
- Density impulse (ρ·Isp) and fair multi-propellant trades
- Custom fuels/oxidizers and multi-component **blends**
- Structured results (Pydantic), SQLite cache, CLI, dark-theme plots (opt-in)

It is meant to be the **shared propellant backbone** for other tools (nozzle MOC, injectors, cooling) — or a standalone desk tool for propellant selection studies.

---

## Why it exists

Working with CEA is powerful but awkward for modern engineering workflows:

| Pain | What propwrap does |
|------|---------------------|
| Ad-hoc scripts, notebooks, copy-paste CEA decks | One importable, typed library |
| English units leak into analysis (psia, Rankine, ft/s) | SI-adjacent public API (bar, K, s, m/s) |
| Dicts / parsed strings as “results” | Pydantic models with units in summaries |
| Comparing RP-1 vs CH₄ vs LH₂ at the **same** O/F | Trades at **each pair’s own optimum O/F** |
| “Did I already run this?” | Transparent SQLite cache |
| Hard to trust numbers | Documented [validation suite](docs/validation.md) |

**Why that matters:** a wrong γ, Isp, or mixture ratio choice propagates into every downstream calculation. Propellant decisions are early, high-leverage, and easy to get inconsistently wrong across a team. A single, tested API reduces that risk.

---

## Overview

```text
You (or a sibling tool)
        │
        ▼
   Mixture("RP-1", "LOX")     ← propellant pair
        │
        ├── evaluate / scan_of / density_impulse
        ├── compare_propellants([...])   ← fair trades
        ├── registry + blends            ← identity & custom cards
        │
        ├── cea_backend  → RocketCEA (NASA CEA)
        ├── cantera_backend → frozen γ cross-check
        └── cache → ~/.propwrap/cache.db
```

**In one sentence:** define a fuel/oxidizer pair, evaluate it at (O/F, Pc, ε), scan mixture ratio, and compare propellant systems with citable theoretical metrics.

---

## Features

- **Friendly API** — `Mixture.evaluate()`, `scan_of()`, human-readable `print(result)`
- **Legacy aliases** — `Propellant`, `performance()`, etc. still work
- **Session defaults** — `set_defaults(pc=70, eps=40)` or `Case(pc=70, eps=40)`
- **Workflows** — `characterize()`, `compare_propellants()`, `define_blend()`
- **Registry** — densities, cryo temps, storability tags, aliases (`RP-1` → `RP1`)
- **Blends** — multi-component wt% fuels/oxs via RocketCEA blend cards
- **Density-Isp** — ρ·Isp curves and ranking vs pure Isp
- **Product state** — chamber/throat/exit thermo + transport + major species
- **Plots opt-in** — no surprise windows; `plot=True` / `save=` / `.plot()`
- **CLI** — `propwrap run`, `scan-of`, `characterize`, `compare-pairs`, …
- **Validation** — RocketCEA doc goldens + multi-propellant regression + physics checks

---

## Install

**Requirements:** Python **3.10+**, Windows / Linux / macOS.

```bash
git clone https://github.com/shanthoshkv/propwrap.git
cd propwrap

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

Core dependencies (installed automatically): `rocketcea`, `cantera`, `pydantic>=2`, `matplotlib`, `numpy`.

Verify:

```bash
propwrap run RP-1 LOX --of 2.56 --pc 70 --eps 20
pytest -q
```

---

## Quick start

```python
from propwrap import Mixture, compare_propellants, set_defaults, characterize

# --- one mixture point ---
m = Mixture("RP-1", "LOX")
r = m.evaluate(of=2.56, pc=70, eps=20)
print(r)
# RP1/LOX  O/F=2.56  Pc=70 bar  ε=20
# Isp_vac  343.7 s (shifting)  ...

# --- O/F scan (no plot unless you ask) ---
sw = m.scan_of((2.0, 3.2, 0.1), pc=70, eps=20)
print(sw.summary())
# sw.plot(save="of_scan.png")   # opt-in

# --- session defaults ---
set_defaults(pc=70, eps=40)
m.evaluate(of=2.56)

# --- fair propellant trade (each pair at its own best O/F) ---
trade = compare_propellants(
    ["RP-1/LOX", "CH4/LOX", "LH2/LOX", "MMH/N2O4"],
    pc_bar=70,
    eps=40,
)
print(trade)

# --- full characterization workflow ---
characterize("CH4", "LOX", of=3.0, plot=False)
```

### Registry, blends, density-Isp

```python
from propwrap import get_propellant, list_registry, add_blend, density_isp_curve

print(get_propellant("RP-1").density_g_cm3)
print([p.name for p in list_registry(storage="cryogenic")])

add_blend("MyM20", [("MMH", 20), ("UDMH", 80)], kind="fuel")

curve = density_isp_curve("RP-1", "LOX", (1.8, 3.4, 0.1), pc_bar=70, eps=40)
print(curve.summary())
```

---

## CLI

Plots are **off** unless you pass `--plot` or `--save`.

```bash
# Single point
propwrap run RP-1 LOX --of 2.56 --pc 70 --eps 20

# O/F scan
propwrap scan-of RP-1 LOX --pc 70 --eps 20 --range 2.0 3.5 0.1

# Characterize pair
propwrap characterize CH4 LOX --of 3.0 --pc 70 --eps 40

# Compare pairs at each optimum O/F
propwrap compare-pairs --combos "RP-1/LOX,LH2/LOX,CH4/LOX,MMH/N2O4" --pc 70 --eps 40

# Density impulse curve
propwrap density-isp --fuel RP-1 --ox LOX --range 1.8 3.4 0.1 --pc 70 --eps 40

propwrap list --cryogenic
propwrap clear-cache
```

Use `--json` for machine-readable output.

---

## What it computes (metrics)

| Metric | Symbol / field | Unit | Meaning |
|--------|----------------|------|---------|
| Vacuum Isp (shifting) | `isp_vac_shifting` | s | Ideal equilibrium expansion |
| Vacuum Isp (frozen) | `isp_vac_frozen` | s | Composition frozen in nozzle |
| Sea-level Isp | `isp_sl_*` | s | Ambient ≈ 1 atm |
| Characteristic velocity | `c_star` | m/s | Chamber energy metric |
| Thrust coefficient | `cf_vac`, `cf_sl` | — | |
| Chamber / throat / exit T | `tc_kelvin`, … | K | |
| Exit pressure | `pe_bar` | bar | |
| γ at stations | `gamma_chamber`, … | — | |
| Molecular weight | `mw_chamber` | kg/kmol | |
| Bulk density | `bulk_density_g_cm3` | g/cm³ | Liquid mixture ρ(O/F) |
| Density impulse | `density_impulse_vac_shifting` | s·g/cm³ | Isp × ρ_bulk |
| Product transport | `chamber.cp_j_kg_k`, `mu_pa_s`, … | SI | cp, μ, k, Pr |
| Delivered Isp (optional) | `isp_vac_delivered` | s | If `eta_cstar` / `eta_cf` set |

**Boundary conditions** for a CEA rocket problem:

| Input | Field | Unit |
|-------|--------|------|
| Mixture ratio | `of` / `of_ratio` | mass ox / mass fuel |
| Chamber pressure | `pc` / `pc_bar` | bar |
| Expansion ratio | `eps` / `expansion_ratio` | Ae/At |

ε and Pc are **thermo boundary conditions** for evaluating the mixture — not an invitation to design the whole engine inside this package.

---

## Units (public API)

English units from CEA (psia, Rankine, ft/s) are converted **inside** `cea_backend` and never returned from public methods.

| Quantity | Public unit |
|----------|-------------|
| Pressure | bar |
| Temperature | K |
| Specific impulse | s |
| \(c^*\) | m/s |
| Density (liquids) | g/cm³ |
| Gas density | kg/m³ |
| cp | J/(kg·K) |
| Viscosity | Pa·s |

---

## Validation

Credibility is enforced by automated tests and a written report.

| Document / asset | Description |
|------------------|-------------|
| **[docs/validation.md](docs/validation.md)** | Full validation report: methods, sources, gaps |
| **[tests/data/validation_catalog.json](tests/data/validation_catalog.json)** | Machine-readable golden values |
| **[tests/test_validation_suite.py](tests/test_validation_suite.py)** | Executable suite |

### Layers

1. **RocketCEA documentation goldens** — LOX/LH₂ Isp series from the [RocketCEA QuickStart](https://rocketcea.readthedocs.io/en/latest/quickstart.html) (≤ 0.1% relative).
2. **Multi-propellant regression** — RP-1, LH₂, CH₄, MMH, UDMH, A-50, ethanol at standard Pc/ε.
3. **Literature bands** — order-of-magnitude consistency with public CEA-class summaries (not flight Isp).
4. **Physics invariants** — e.g. shifting ≥ frozen Isp, \(T_e < T_t < T_c\), \(\gamma_\mathrm{exit} \ge \gamma_\mathrm{chamber}\).
5. **Trends** — propellant ranking (LH₂ > CH₄ > RP-1 on vac Isp), ε↑ → Isp↑, density-Isp ordering.
6. **Unit-leak guards** — fail if results look like Rankine or ft/s.
7. **Cantera γ band** — chamber γ cross-check with documented tolerance for species-set mismatch.

```bash
pytest tests/test_validation_suite.py -v
pytest -q   # full suite (~110 tests)
```

### Example theoretical anchors (ideal CEA, not flight)

| System | Typical conditions | Approx. Isp_vac (shifting) |
|--------|--------------------|----------------------------|
| LOX / LH₂ | Pc ≈ 100 psia, ε = 40, O/F = 5 | ~453 s ([RocketCEA docs](https://rocketcea.readthedocs.io/en/latest/quickstart.html)) |
| LOX / RP-1 | Pc = 70 bar, ε = 20, O/F = 2.56 | ~344 s (CEA theoretical) |
| LOX / CH₄ | Pc ≈ 69 bar, ε = 40, O/F ≈ 3.2 | ~368 s |
| N₂O₄ / MMH | Pc ≈ 69 bar, ε = 40, O/F = 2.0 | ~339 s |

**Flight engines deliver less** (efficiency, mixture bias, losses). Optional `efficiency=(ηc*, ηCf)` scales ideal Isp for rough studies only.

---

## Project layout

```text
propwrap/
├── README.md                 ← you are here
├── LICENSE                   ← MIT
├── pyproject.toml
├── docs/
│   ├── api_reference.md      ← API reference
│   └── validation.md         ← validation report
├── examples/
│   ├── basic_performance.py
│   ├── of_sweep_lox_rp1.py
│   ├── propellant_trade.py
│   ├── lox_ch4_case.py
│   ├── propellant_comparison.py
│   ├── gamma_profile_for_nozzle.py
│   └── custom_propellants.py
├── src/propwrap/             ← library source
└── tests/                    ← pytest + validation catalog
```

### Documentation & related files

| File | Purpose |
|------|---------|
| [docs/api_reference.md](docs/api_reference.md) | Public API reference |
| [docs/validation.md](docs/validation.md) | Validation methodology and citations |
| [tests/data/validation_catalog.json](tests/data/validation_catalog.json) | Golden / regression catalog |
| [LICENSE](LICENSE) | MIT license |
| [pyproject.toml](pyproject.toml) | Package metadata and dependencies |
| [examples/](examples/) | Runnable scripts |
| [propwrap_master_prompt.md](propwrap_master_prompt.md) | Original design brief (historical) |

---

## Architecture (modules)

| Module | Role |
|--------|------|
| [`propellant.py`](src/propwrap/propellant.py) | `Mixture` — main API |
| [`workflows.py`](src/propwrap/workflows.py) | `characterize`, `compare_propellants`, `define_blend` |
| [`trades.py`](src/propwrap/trades.py) | Optimum-O/F trades, density-Isp curves |
| [`registry.py`](src/propwrap/registry.py) | Propellant identity registry |
| [`blends.py`](src/propwrap/blends.py) | Multi-component blend cards |
| [`cea_backend.py`](src/propwrap/cea_backend.py) | RocketCEA + unit conversion |
| [`cantera_backend.py`](src/propwrap/cantera_backend.py) | Frozen γ cross-check |
| [`models.py`](src/propwrap/models.py) | Pydantic result types |
| [`cache.py`](src/propwrap/cache.py) | SQLite memoization |
| [`plotting.py`](src/propwrap/plotting.py) | Dark-theme plots (opt-in) |
| [`cli.py`](src/propwrap/cli.py) | Command-line entry point |
| [`defaults.py`](src/propwrap/defaults.py) | `set_defaults`, `Case` |

---

## Limitations (read before citing numbers)

1. **Ideal 1-D CEA** — not kinetics, not multiphase losses, not flight performance.
2. **Shifting vs frozen** — reality sits between; both are reported.
3. **Theoretical ≠ delivered** — apply your own η if needed; do not claim Merlin/RS-25 flight Isp from raw CEA.
4. **Custom cards / blends** — field validation only; bad Hf or formulas fail at CEA runtime.
5. **Cantera γ** — major-species frozen compare; divergence can be large for exotic products.
6. **RocketCEA license** — RocketCEA is GPL-family; if you ship proprietary products, review dependency licenses carefully. This repo is MIT for *propwrap’s own code*.
7. **Not flight-certified** — engineering aid for preliminary propellant analysis only.

---

## Examples

| Script | What it shows |
|--------|----------------|
| [examples/basic_performance.py](examples/basic_performance.py) | Single-point LOX/RP-1 |
| [examples/of_sweep_lox_rp1.py](examples/of_sweep_lox_rp1.py) | O/F banana curve + plot |
| [examples/propellant_trade.py](examples/propellant_trade.py) | Multi-pair trade + density-Isp |
| [examples/lox_ch4_case.py](examples/lox_ch4_case.py) | Methalox characterization |
| [examples/propellant_comparison.py](examples/propellant_comparison.py) | Side-by-side comparison plot |
| [examples/gamma_profile_for_nozzle.py](examples/gamma_profile_for_nozzle.py) | γ(ε) handoff shape for other tools |
| [examples/custom_propellants.py](examples/custom_propellants.py) | Custom card examples |

```bash
python examples/basic_performance.py
python examples/propellant_trade.py
```

---

## Development

```bash
pip install -e ".[dev]"
pytest -q
# optional
mypy src/propwrap
```

---

## Roadmap / non-goals

**In scope:** better propellant data, blends, trades, validation, composition exports.  
**Out of scope:** full engine design (cycle analysis, turbomachinery, regen sizing, trajectory).

---

## Acknowledgments

- **NASA CEA** — Gordon & McBride; NASA RP-1311  
- **[RocketCEA](https://rocketcea.readthedocs.io/)** — Charlie Taylor / Applied Python  
- **[Cantera](https://cantera.org/)** — thermochemistry cross-checks  

---

## License

MIT for propwrap source code — see [LICENSE](LICENSE).

Third-party packages (RocketCEA, Cantera, etc.) retain their own licenses. Review them before commercial redistribution.
