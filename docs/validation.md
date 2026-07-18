# propwrap validation report

**Status:** theoretical CEA validation (ideal 1-D).  
**Not** flight-engine delivered performance.  
**Not** flight certification evidence.

This document is the human-readable companion to `tests/data/validation_catalog.json` and `tests/test_validation_suite.py`.

---

## 1. What we claim

| Claim | Supported? |
|-------|------------|
| propwrap matches RocketCEA/NASA CEA for the same inputs | **Yes** (golden docs + regression) |
| Numbers equal flight Merlin / RS-25 Isp | **No** — those include engine efficiency |
| Frozen ≤ shifting Isp (ideal) | **Yes** |
| SI-adjacent units on public API | **Yes** (leak guards) |
| Cantera γ identical to CEA | **No** — major-species frozen compare only |

---

## 2. Methodology

1. **Primary engine:** NASA CEA FORTRAN via [RocketCEA](https://rocketcea.readthedocs.io/) (Gordon & McBride CEA; NASA RP-1311 methodology).
2. **propwrap role:** unit conversion (bar/K/m/s), structured results, cache — not a second thermo model.
3. **Validation layers:**
   - **A.** Published RocketCEA documentation numbers (highest external trust)
   - **B.** Multi-propellant regression anchors at standard Pc/ε
   - **C.** Physical invariants across ≥10 combos
   - **D.** Engineering trends (ranking, ε, O/F peak, ambient)
   - **E.** Unit-system guards
   - **F.** Cantera chamber-γ band (documented mismatch allowed)
   - **G.** Density-impulse ordering (handbook liquid densities)

---

## 3. Layer A — RocketCEA documentation goldens

**Source:** [RocketCEA QuickStart](https://rocketcea.readthedocs.io/en/latest/quickstart.html)  
“Test The Install” / `basic_cea.py` published output for **LOX/LH2**, `Pc = 100 psia`, `ε = 40`.

| O/F | Published Isp [s] | Role |
|-----|-------------------|------|
| (default get_Isp) | 374.3036… | install smoke |
| 2 | 424.360 | fuel-rich |
| 3 | 445.444 | |
| 4 | 453.133 | |
| 5 | 453.240 | near peak |
| 6 | 448.190 | |
| 7 | 438.743 | |
| 8 | 424.700 | oxidizer-rich |

**Tolerance:** 0.1% relative.  
**Result:** propwrap `performance()` matches bit-for-bit with RocketCEA `get_Isp` at the same Pc/MR/ε (verified).

Also: default `CEA_Obj(oxName='LOX', fuelName='LH2').get_Isp()` = **374.30361765576265** s (same page).

---

## 4. Layer B — Standard-condition regression matrix

Conditions often used in literature comparisons: **Pc ≈ 1000 psia (68.95 bar), ε = 40**, plus design-like points.

| ID | Propellants | O/F | Pc [bar] | ε | Isp_vac (shifting) [s] | Band / note |
|----|-------------|-----|----------|---|------------------------|-------------|
| REG-RP1-LOX-1000psia-eps40 | RP1/LOX | 2.3 | 68.95 | 40 | ~352.3 | lit. theor. ~340–370 |
| REG-RP1-LOX-70bar-eps20 | RP1/LOX | 2.56 | 70 | 20 | ~343.7 | master-prompt case |
| REG-LH2-LOX-1000psia-eps40-OF5 | LH2/LOX | 5.0 | 68.95 | 40 | ~454.9 | lit. ~445–465 |
| REG-LH2-LOX-RS25-class | LH2/LOX | 5.5 | 100 | 69 | ~463.7 | **theoretical**; flight RS-25 ~452 s delivered |
| REG-CH4-LOX-… | CH4/LOX | 3.2 | 68.95 | 40 | ~367.6 | methane class ~350–380 |
| REG-MMH-N2O4-… | MMH/N2O4 | 2.0 | 68.95 | 40 | ~338.6 | hypergolic ~320–355 |
| REG-UDMH-N2O4 | UDMH/N2O4 | 2.6 | 68.95 | 40 | ~338.3 | |
| REG-A50-N2O4 | A50/N2O4 | 2.0 | 68.95 | 40 | ~340.9 | |
| REG-ETHANOL-LOX | Ethanol/LOX | 1.5 | 68.95 | 40 | ~336.8 | |

**Regression tolerance:** typically 1.5–2% vs frozen catalog numbers (guards against silent thermo/unit regressions).  
**Literature bands:** order-of-magnitude consistency with public CEA-class summaries (e.g. Encyclopedia Astronautica LOX/LH2, LOX/kerosene, N2O4/MMH pages) — **not** page-cited Sutton edition tables (those require manual transcription from a physical edition).

### Important distinction

| Quantity | Example |
|----------|---------|
| CEA theoretical LOX/RP-1 vac Isp @ ε=20–40 | ~340–355 s |
| Merlin-class **flight** vac Isp | ~311–348 s |
| CEA LOX/LH2 theoretical @ high ε | ~450–465 s |
| RS-25 **flight** vac Isp | ~452 s (high η; close to theory) |

propwrap reports the **CEA theoretical** column unless you apply `eta_cstar` / `eta_cf`.

---

## 5. Layer C — Physical invariants

Checked on 11+ propellant/condition combos:

1. `isp_vac_shifting ≥ isp_vac_frozen`
2. `isp_vac_shifting ≥ isp_sl_shifting`
3. `gamma_exit ≥ gamma_chamber` (γ rises as T falls in expansion for these products)
4. `Te < Tt < Tc`
5. `pe > 0`, `Pc/Pe > 1`
6. Chamber `cp` present and positive (SI)

---

## 6. Layer D — Trends

| Trend | Expectation | Test |
|-------|-------------|------|
| Propellant ranking @ ~69 bar, ε=40 | LH2 > CH4 > RP1 > MMH/NTO | `test_propellant_ranking_vac_isp` |
| Area ratio | higher ε → higher Isp_vac | `test_higher_eps_raises_vac_isp` |
| O/F banana | interior peak for RP-1, CH4 | sweep peak tests |
| Ambient | lower Pamb → higher Isp | monotone ambient test |
| Density impulse | RP-1 beats LH2 on ρ·Isp | density ordering test |

---

## 7. Layer E — Units

Public API must never look like English CEA printout:

- `c*` in **m/s** (~1500–2400), not ft/s (~5000–7800)
- `T` in **K** (~3000–3700), not Rankine (~5400–6700)
- `Pc` in **bar**

---

## 8. Layer F — CEA vs Cantera γ

Chamber γ compared via major-species mapping into Cantera (`gri30` / `nasa_gas`).

| Allowed | Meaning |
|---------|---------|
| &lt; ~15% | `within_tolerance` at default 15% |
| &lt; 25% | hard CI fail threshold |

Divergence is expected: condensed phases, minor radicals, equilibrium vs frozen, mechanism species set. This is a **sanity cross-check**, not a proof of CEA correctness.

---

## 9. Primary references

1. **Gordon, S.; McBride, B. J.** *Computer Program for Calculation of Complex Chemical Equilibrium Compositions and Applications.* NASA RP-1311 (CEA).  
2. **RocketCEA documentation** — https://rocketcea.readthedocs.io/ (QuickStart published LOX/LH2 Isp table).  
3. **RocketCEA** Python package wrapping NASA CEA FORTRAN (baseline tests: v1.2.3).  
4. **Public CEA-class propellant summaries** (Astronautix LOX/LH2, LOX/kerosene, N2O4/MMH) — used only for **wide literature bands**, not point references.  
5. **Sutton, G. P.; Biblarz, O.** *Rocket Propulsion Elements* — recommended for manual table cross-checks; specific edition/page numbers are **not** transcribed here without a physical copy (see §11).

---

## 10. How to re-run

```bash
pytest tests/test_validation_suite.py tests/test_known_values.py -v
```

Full suite:

```bash
pytest -q
```

---

## 11. Known gaps (honesty)

| Gap | Impact |
|-----|--------|
| No page-cited Sutton table transcription | Literature bands are wide, not tight textbook points |
| No independent NASA CEARUN file dump in-repo | Goldens are RocketCEA-doc + local CEA |
| Cantera is not full multi-phase CEA | γ compare is approximate |
| No kinetics / finite-rate nozzle | Ideal shifting/frozen only |
| Cryogenic defaults optional | Inlet T changes Isp — document your temps |

**To strengthen further:** run NASA CEAWeb/CEARUN on the same cards, archive `.out` files under `tests/data/cea_outputs/`, and add point-wise asserts against those files.

---

## 12. Change control

If a regression test fails after a dependency bump:

1. Confirm whether RocketCEA/CEA thermo data changed.
2. Update `validation_catalog.json` **only** with measured new values + note in this file.
3. Never “widen tolerance until green” without a written reason.
