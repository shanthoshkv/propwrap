# How to use propwrap (beginner guide)

This guide is written for people who may be **new to Python** and new to propellant analysis.  
You do **not** need to be a software engineer. Follow the steps in order the first time.

If something fails, jump to [Troubleshooting](#troubleshooting) at the bottom.

---

## What is propwrap in plain English?

Imagine you want to know:

> “If I burn **RP-1** (kerosene) with **LOX** (liquid oxygen) at this mixture ratio and chamber pressure, what vacuum Isp and chamber temperature do I get?”

Normally that means wrestling with NASA’s CEA code, weird units (psi, Rankine, feet/second), and messy scripts.

**propwrap** is a Python package that does that job with simple commands:

1. You name a **fuel** and an **oxidizer**.
2. You give a few numbers (mixture ratio, pressure, expansion ratio).
3. It returns **clear results** with **SI units** (mostly) and optional plots.

It is for **propellant performance**, not for designing a whole rocket engine (no pumps, no cooling channels, no flight trajectory).

> **Important honesty:** Numbers are **ideal / theoretical** (perfect 1-D chemistry). Real engines usually get **lower** Isp. Do not treat these as flight guarantees.

---

## What you need on your computer

1. **Python 3.10 or newer**  
   Check by opening a terminal (Command Prompt or PowerShell on Windows; Terminal on Mac) and typing:

   ```bash
   python --version
   ```

   or:

   ```bash
   py --version
   ```

   You want something like `Python 3.10`, `3.11`, `3.12`, etc.

2. **This project folder** (cloned or downloaded from GitHub).

3. About **10–20 minutes** the first time (installing packages can be slow).

---

## Part 1 — Install (do this once)

### Step 1: Open a terminal in the project folder

Go to the folder that contains `README.md` and `pyproject.toml` (the `propwrap` project root).

**Windows (PowerShell):**

```powershell
cd path\to\propwrap
```

**Mac / Linux:**

```bash
cd path/to/propwrap
```

### Step 2: Create a “virtual environment”

A virtual environment is a **private mini-Python** only for this project, so you don’t break other software.

**Windows:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\activate
```

(If 3.12 isn’t installed, try `py -3.11` or `python -m venv .venv`.)

**Mac / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When it works, you often see `(.venv)` at the start of your terminal line.

### Step 3: Install propwrap

```bash
pip install -e ".[dev]"
```

What this means:

- `pip` = Python’s package installer  
- `-e` = “editable” install (code changes apply immediately)  
- `.[dev]` = install this project **and** test tools  

Wait until it finishes without red errors.

### Step 4: Check that it works

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

You should see a short table of results (Isp, c*, temperatures, etc.).

If that command is “not found”, try:

```bash
python -m propwrap.cli run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

---

## Part 2 — Words you will see (mini glossary)

You only need these ideas to use the tool:

| Word | Simple meaning | Typical value |
|------|----------------|---------------|
| **Fuel** | What burns (e.g. RP-1, CH₄, LH₂, MMH) | name string |
| **Oxidizer** | What supplies oxygen (e.g. LOX, N₂O₄) | name string |
| **O/F** or **mixture ratio** | Mass of oxidizer ÷ mass of fuel | RP-1/LOX ~2.3–2.6; LH₂/LOX ~5–6 |
| **Pc** | Chamber pressure | often 50–100 **bar** in studies |
| **ε (eps)** | Nozzle area ratio Ae/At | e.g. 20, 40, 69 |
| **Isp** | Specific impulse — “how much push per propellant” | seconds (s) |
| **c\*** | Characteristic velocity — chamber energy metric | m/s |
| **Tc** | Chamber temperature | kelvin (K) |
| **γ (gamma)** | Ratio of specific heats of the gas | ~1.1–1.3 |
| **Density impulse** | Isp × propellant bulk density — good for tank size trades | s·kg/m³ |

### Units in propwrap (important)

Results are stored in **SI**:

- Pressure: **pascals (Pa)** — 1 bar = 100 000 Pa, so 70 bar = 7 000 000 Pa  
- Temperature: **kelvin (K)**  
- Speed / c\*: **metres per second (m/s)**  
- Density: **kg/m³**  
- Isp: still **seconds (s)** (everyone in rocketry uses this)  
- Also available: **ve** = exhaust velocity in m/s (= Isp × 9.80665)

You can **type** pressure in bar if that’s easier:

```python
pc_bar=70        # easy for humans
# or
pc=7_000_000     # pure SI pascals
# or
pc_mpa=7         # megapascals
```

---

## Part 3 — Your first Python script (copy-paste)

### Create a file

In the project folder, create a file named `my_first_run.py` (any name is fine).

Paste this:

```python
# my_first_run.py
# This is a comment. Python ignores lines starting with #

from propwrap import Mixture

# 1) Define the propellant pair: fuel first, oxidizer second
mixture = Mixture("RP-1", "LOX")

# 2) Run one calculation
#    of  = mixture ratio O/F (dimensionless)
#    pc_bar = chamber pressure in bar (converted to Pa inside)
#    eps = nozzle expansion ratio Ae/At
result = mixture.evaluate(of=2.56, pc_bar=70, eps=20)

# 3) Print a human-readable summary
print(result)
```

### Run it

With the virtual environment still activated:

```bash
python my_first_run.py
```

### What you should see

Something like:

```text
RP1/LOX  O/F=2.56  Pc=7.000e+06 Pa (70 bar)  ε=20
Isp_vac  343.7 s (shifting)   ve  3371 m/s   ...
c*       1798 m/s      Tc  3672 K
...
```

### Read individual numbers

```python
print("Vacuum Isp (s):", result.isp_vac_shifting)
print("Exhaust velocity (m/s):", result.ve_vac_shifting)
print("Chamber T (K):", result.tc_kelvin)
print("c* (m/s):", result.c_star)
print("Pressure (Pa):", result.pc_pa)
print("Pressure (bar):", result.pc_bar)   # convenience view
```

---

## Part 4 — The main object: `Mixture`

Think of `Mixture` as **one fuel + one oxidizer** you will study.

```python
from propwrap import Mixture

m = Mixture("CH4", "LOX")   # methane + liquid oxygen
# Same thing under old names:
# from propwrap import Propellant
# m = Propellant("CH4", "LOX")
```

### Common methods (what to call)

| What you want | What to type |
|---------------|--------------|
| One operating point | `m.evaluate(of=..., pc_bar=..., eps=...)` |
| Scan many O/F values | `m.scan_of((start, stop, step), pc_bar=..., eps=...)` |
| Density-impulse curve | `m.density_impulse((start, stop, step), pc_bar=..., eps=...)` |
| γ vs expansion ratio | `m.product_gamma_profile(of=..., pc_bar=..., eps_range=(...))` |
| Full mini-study | `m.study(of=..., pc_bar=..., eps=...)` |

### Plots are **off** by default

propwrap will **not** open random plot windows.

To save a plot:

```python
sweep = m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20)
sweep.plot(save="my_of_scan.png")   # creates a PNG file
```

Or:

```python
m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20, plot=True, save="my_of_scan.png")
```

---

## Part 5 — Everyday recipes

### Recipe A — “Just give me Isp for this mix”

```python
from propwrap import Mixture

m = Mixture("RP-1", "LOX")
r = m.evaluate(of=2.4, pc_bar=100, eps=35)
print(r.summary())
print("Isp vac =", r.isp_vac_shifting, "s")
```

### Recipe B — “What O/F is best for vacuum Isp?”

```python
from propwrap import Mixture

m = Mixture("RP-1", "LOX")

# Scan O/F from 2.0 to 3.2 in steps of 0.1
sweep = m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20)
print(sweep.summary())

best = sweep.optimum()   # highest isp_vac_shifting by default
print("Best O/F =", best.of_ratio)
print("Best Isp =", best.isp_vac_shifting, "s")
```

The triple `(2.0, 3.2, 0.1)` means:

- start at 2.0  
- stop at 3.2  
- step by 0.1  

### Recipe C — “Compare RP-1 vs methane vs hydrogen fairly”

**Wrong way:** use the same O/F for all three (e.g. 2.5).  
Hydrogen’s good O/F is ~5–6, not 2.5.

**Right way:** let each pair find **its own** best O/F:

```python
from propwrap import compare_propellants

trade = compare_propellants(
    ["RP-1/LOX", "CH4/LOX", "LH2/LOX", "MMH/N2O4"],
    pc_bar=70,
    eps=40,
)
print(trade)
```

You get:

- a table of each pair at its optimum O/F  
- ranking by **Isp**  
- ranking by **density-Isp** (tank-friendly metric; RP-1 often beats LH₂ here)

### Recipe D — “Density impulse (tank volume matters)”

```python
from propwrap import Mixture

m = Mixture("RP-1", "LOX")
curve = m.density_impulse((1.8, 3.4, 0.1), pc_bar=70, eps=40)
print(curve.summary())
print("O/F for max Isp:", curve.optimum_isp_of)
print("O/F for max ρ·Isp:", curve.optimum_density_isp_of)
```

### Recipe E — “I’m studying methane (methalox)”

```python
from propwrap import Mixture, characterize

# Quick point
m = Mixture("CH4", "LOX")  # cryogenic defaults applied for LOX/CH4 when enabled
print(m.evaluate(of=3.0, pc_bar=100, eps=25))

# Or one-shot workflow: point + O/F scan + density-Isp
report = characterize("CH4", "LOX", of=3.0, pc_bar=100, eps=25, plot=False)
print(report)
```

### Recipe F — “Blend two fuels (example M20-style)”

```python
from propwrap import define_blend, Mixture

# 20% MMH + 80% UDMH by weight
define_blend(
    "MyM20",
    [("MMH", 20), ("UDMH", 80)],
    kind="fuel",
    evaluate_with="N2O4",   # optional: run a quick point with this oxidizer
    of=2.0,
    pc_bar=50,
    eps=20,
)

m = Mixture("MyM20", "N2O4")
print(m.evaluate(of=2.0, pc_bar=50, eps=20))
```

Weight percents should add up to about **100**.

### Recipe G — “I think in bar, but I need pascals”

```python
from propwrap import convert, units

print(convert(70, "bar", "Pa"))      # 7000000.0
print(convert(7, "MPa", "bar"))      # 70.0
print(convert(300, "s", "m/s"))      # Isp → ve
print(units.g_cm3_to_kg_m3(0.81))    # 810.0
```

### Recipe H — “Don’t make me type pc and eps every time”

```python
from propwrap import Mixture, set_defaults

set_defaults(pc_bar=70, eps=40)

m = Mixture("RP-1", "LOX")
# uses the defaults for pressure and eps
r = m.evaluate(of=2.56)
print(r.pc_pa, r.eps)
```

Or use a `Case` object:

```python
from propwrap import Case

case = Case(pc_bar=70, eps=40)
print(case.evaluate("RP-1", "LOX", of=2.56))
print(case.compare(["RP-1/LOX", "CH4/LOX", "LH2/LOX"]))
```

---

## Part 6 — Using the command line (no Python file)

After install, these work in the terminal.

### One point

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

Same with SI pressure:

```bash
propwrap run RP-1 LOX --of 2.56 --pc 7000000 --eps 20
propwrap run RP-1 LOX --of 2.56 --pc-mpa 7 --eps 20
```

### JSON (for other programs)

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20 --json
```

### Scan O/F

```bash
propwrap scan-of RP-1 LOX --pc-bar 70 --eps 20 --range 2.0 3.2 0.1
```

### Compare propellants

```bash
propwrap compare-pairs --combos "RP-1/LOX,CH4/LOX,LH2/LOX" --pc-bar 70 --eps 40
```

### List propellants

```bash
propwrap list
propwrap list --cryogenic
propwrap list --storable
```

### Clear cache

Results are cached for speed. To wipe:

```bash
propwrap clear-cache
```

---

## Part 7 — Understanding the output (what to trust)

### Shifting vs frozen Isp

- **Shifting** (`isp_vac_shifting`): chemistry keeps adjusting in the nozzle (usually **higher**).  
- **Frozen** (`isp_vac_frozen`): chemistry freezes earlier (usually **lower**).  
Real engines sit **in between**.

### Vacuum vs sea-level

- **Vacuum Isp** assumes no atmosphere.  
- **Sea-level Isp** assumes ambient pressure ≈ 1 atm.  
A big nozzle (large ε) can look great in vacuum and worse at sea level.

### Warnings

If `result.warnings` is not empty, **read them**. Examples:

- extreme O/F far from stoich  
- odd temperature ordering  
- huge expansion at sea level  

```python
for w in result.warnings:
    print("Warning:", w)
```

### Chamber details (advanced but useful)

```python
r = Mixture("RP-1", "LOX").evaluate(of=2.56, pc_bar=70, eps=20)
if r.chamber:
    print("cp J/(kg·K):", r.chamber.cp_j_kg_k)
    print("mu Pa·s:", r.chamber.mu_pa_s)
    print("gamma:", r.chamber.gamma)
```

---

## Part 8 — Looking up propellant data

```python
from propwrap import get_propellant, list_registry

rp1 = get_propellant("RP-1")
print(rp1.name)                 # RP1
print(rp1.density_kg_m3)        # kg/m³
print(rp1.storage)              # e.g. storable / cryogenic

for p in list_registry(kind="fuel", storage="cryogenic"):
    print(p.name, p.density_kg_m3)
```

Aliases work: `"RP-1"`, `"RP1"`, `"LOX"`, `"O2"`, `"CH4"`, `"LCH4"`, etc.

---

## Part 9 — Examples that ship with the project

From the project root (venv activated):

```bash
python examples/basic_performance.py
python examples/propellant_trade.py
python examples/lox_ch4_case.py
python examples/of_sweep_lox_rp1.py
```

| File | What it teaches |
|------|-----------------|
| [examples/basic_performance.py](../examples/basic_performance.py) | Single point |
| [examples/of_sweep_lox_rp1.py](../examples/of_sweep_lox_rp1.py) | O/F sweep + plot file |
| [examples/propellant_trade.py](../examples/propellant_trade.py) | Multi-pair trade |
| [examples/lox_ch4_case.py](../examples/lox_ch4_case.py) | Methane case |
| [examples/custom_propellants.py](../examples/custom_propellants.py) | Custom cards |
| [examples/gamma_profile_for_nozzle.py](../examples/gamma_profile_for_nozzle.py) | γ vs area ratio data shape |

---

## Part 10 — Common mistakes (and fixes)

| Mistake | What happens | Fix |
|---------|--------------|-----|
| Same O/F for LH₂ and RP-1 in a “fair” compare | Nonsense ranking | Use `compare_propellants` |
| `eps=0.5` | Error | ε must be **> 1** (Ae/At), not a fraction of something else |
| `pc=70` thinking SI | 70 **Pa** is almost vacuum — wrong | Use `pc_bar=70` or `pc=7_000_000` |
| Forgetting to activate `.venv` | `propwrap` / import not found | Activate venv, reinstall if needed |
| Treating CEA Isp as Merlin flight Isp | Over-optimistic design | Apply your own efficiencies; read limitations |
| Expecting plots automatically | Nothing appears | Call `.plot(save="...")` or `plot=True` |

---

## Part 11 — Minimal mental model of “a good first study”

For a new propellant pair, do this every time:

1. **One point** at a reasonable O/F, Pc, ε → `evaluate`  
2. **O/F scan** → `scan_of` → find peak Isp  
3. **Density-Isp** → `density_impulse` if tanks matter  
4. **Compare** to alternatives → `compare_propellants`  
5. Write down: O/F*, Isp, Tc, ρ·Isp, and that values are **theoretical**

That’s a complete beginner workflow.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'propwrap'`

- Activate the virtual environment.  
- Run `pip install -e ".[dev]"` again from the project root.

### `propwrap` is not recognized

```bash
python -m propwrap.cli run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

### Install fails on RocketCEA / Cantera

- Use Python 3.10–3.12 if possible.  
- On Windows, prefer official Python from python.org, then:

  ```bash
  pip install --upgrade pip
  pip install -e ".[dev]"
  ```

### Results look insane (Isp thousands, Tc millions)

That usually means a **unit mix-up** (e.g. treating Rankine as kelvin).  
propwrap should prevent that; if you see it, open an issue with your exact code.

### I changed a custom propellant card but get old numbers

```bash
propwrap clear-cache
```

---

## Where to go next

| Document | When to open it |
|----------|-----------------|
| [../README.md](../README.md) | Project overview, features, install summary |
| [api_reference.md](api_reference.md) | Full list of functions and fields |
| [validation.md](validation.md) | How numbers are checked / what is trusted |
| [../tests/data/validation_catalog.json](../tests/data/validation_catalog.json) | Golden values used in tests |

---

## One-page cheat sheet

```python
from propwrap import Mixture, compare_propellants, convert, set_defaults

# Setup (optional)
set_defaults(pc_bar=70, eps=40)

# Single pair
m = Mixture("RP-1", "LOX")
r = m.evaluate(of=2.56, pc_bar=70, eps=20)
print(r)
print(r.isp_vac_shifting, r.ve_vac_shifting, r.tc_kelvin)

# O/F scan
sw = m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20)
print(sw.optimum().of_ratio)

# Fair multi-pair trade
print(compare_propellants(["RP-1/LOX", "CH4/LOX", "LH2/LOX"], pc_bar=70, eps=40))

# Unit conversion
print(convert(70, "bar", "Pa"))
```

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
propwrap compare-pairs --combos "RP-1/LOX,CH4/LOX,LH2/LOX" --pc-bar 70 --eps 40
```

You’ve got this. Start with **Part 3**, run one script, then try **Recipe C** when you want a real propellant trade.
