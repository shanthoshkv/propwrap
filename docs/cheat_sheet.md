# propwrap cheat sheet (1 page)

**Theoretical CEA · SI public units · Not flight Isp**

## Install (once)

```bash
cd propwrap
python -m venv .venv
# Win: .venv\Scripts\activate   |  Unix: source .venv/bin/activate
pip install -e ".[dev]"
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

## Python essentials

```python
from propwrap import Mixture, compare_propellants, Case, convert

m = Mixture("RP-1", "LOX")
r = m.evaluate(of=2.56, pc_bar=70, eps=20)
print(r)                          # human summary
print(r.isp_vac_shifting)         # s
print(r.ve_vac_shifting)          # m/s
print(r.pc_pa, r.tc_kelvin)       # Pa, K

sw = m.scan_of((2.0, 3.2, 0.1), pc_bar=70, eps=20)
print(sw.optimum().of_ratio)

print(compare_propellants(
    ["RP-1/LOX", "CH4/LOX", "LH2/LOX"], pc_bar=70, eps=40))

case = Case.student_lab()         # 70 bar, ε=20
case.evaluate("CH4", "LOX", of=3.0)

convert(70, "bar", "Pa")
```

## Pressure inputs

| You type | Meaning |
|----------|---------|
| `pc_bar=70` | 70 bar |
| `pc_mpa=7` | 7 MPa |
| `pc=7e6` | 7 000 000 Pa |

**Never** `pc=70` for “70 bar”.

## CLI

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
propwrap scan-of RP-1 LOX --pc-bar 70 --eps 20 --range 2.0 3.2 0.1
propwrap compare-pairs --combos "RP-1/LOX,CH4/LOX,LH2/LOX" --pc-bar 70 --eps 40
propwrap homework kerolox --name YourName
propwrap list --of-hints
propwrap clear-cache
```

## Units (results)

| | |
|--|--|
| P | Pa (`pc_pa`) |
| T | K |
| v, c* | m/s |
| ρ | kg/m³ |
| Isp | s |
| ρ·Isp | s·kg/m³ |

## Typical O/F (fuel with LOX or NTO)

| Fuel | O/F band |
|------|----------|
| RP-1 | 2.0–2.8 |
| CH₄ | 2.5–3.6 |
| LH₂ | 4.5–6.5 |
| MMH (w/ N₂O₄) | 1.5–2.5 |

## Fair trades

Use `compare_propellants` / `compare-pairs` (each pair’s own best O/F).  
Do **not** force one O/F on all chemistries.

## Frozen vs shifting

`isp_vac_shifting` ≥ `isp_vac_frozen` (usually). Reality is in between.

## Lab pack

```bash
propwrap homework kerolox --name Ada
# → summary.md, assumptions.txt, CSV, PNG figures
```

## Report sentence

> “Results are ideal NASA CEA theoretical performance (1-D equilibrium), not flight-delivered specific impulse.”
