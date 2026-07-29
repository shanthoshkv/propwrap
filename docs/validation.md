# propwrap validation report

**Status:** Theoretical NASA CEA validation (ideal 1-D).  
**Not** flight-engine delivered performance.  
**Not** flight certification evidence.  
**Physics audit:** 2026-07-29 — bit-level CEA match + SI identities verified.

Companion files:

- [`tests/data/validation_catalog.json`](../tests/data/validation_catalog.json) — machine-readable anchors  
- [`tests/test_validation_suite.py`](../tests/test_validation_suite.py) — catalog-driven tests  
- [`tests/test_physics_identities.py`](../tests/test_physics_identities.py) — hard physics identities  

Run:

```bash
pytest tests/test_physics_identities.py tests/test_validation_suite.py tests/test_known_values.py -v
pytest -q
```

---

## 1. What we claim (and do not)

| Claim | Supported? | How secured |
|-------|------------|-------------|
| propwrap matches RocketCEA/NASA CEA for same inputs | **Yes** | Bit-level `get_Isp` identity tests |
| SI public units (Pa, K, m/s, kg/m³) | **Yes** | Unit guards + ideal-gas ρ check |
| \(v_e = I_{sp}\,g_0\) with \(g_0=9.80665\,\mathrm{m/s^2}\) | **Yes** | Identity test |
| \(C_{f,\mathrm{vac}} = v_e / c^*\) | **Yes** | Identity test |
| \(P_c/P_e\) consistent with stored pressures | **Yes** | Identity test |
| Numbers equal flight Merlin / RS-25 Isp | **No** | Explicitly excluded (delivered vs theoretical) |
| Cantera γ identical to CEA | **No** | Major-species frozen compare only |

---

## 2. Primary secured sources

### 2.1 NASA CEA methodology

| Field | Detail |
|-------|--------|
| **Document** | Gordon, S.; McBride, B. J. *Computer Program for Calculation of Complex Chemical Equilibrium Compositions and Applications* |
| **IDs** | NASA RP-1311 Part I (analysis, 1994); Part II (user manual, 1996) |
| **NTRS** | [19950013764](https://ntrs.nasa.gov/citations/19950013764) (Part I entry point) |
| **Role** | Defines the rocket equilibrium / frozen performance problem that RocketCEA wraps |

propwrap does **not** re-implement CEA chemistry. It wraps NASA CEA FORTRAN through RocketCEA and is responsible for **API, SI conversion, and result integrity**.

### 2.2 RocketCEA published numerical goldens

| Field | Detail |
|-------|--------|
| **Document** | RocketCEA QuickStart — “Test The Install” / `basic_cea.py` |
| **URL** | https://rocketcea.readthedocs.io/en/latest/quickstart.html |
| **Cases** | LOX/LH₂, Pc = 100 psia, ε = 40, O/F = 2…8 + default install Isp |
| **Tolerance** | ≤ 0.1% relative (effectively bit-level) |

Verified 2026-07-29: `propwrap` Isp equals `CEA_Obj.get_Isp` to machine precision for O/F = 2–8.

| O/F | Published Isp [s] | Role |
|-----|-------------------|------|
| default `get_Isp()` | 374.30361765576265 | install smoke |
| 2 | 424.3597085736007 | fuel-rich |
| 3 | 445.44434236555196 | |
| 4 | 453.13271951921837 | |
| 5 | 453.240429182719 | near peak |
| 6 | 448.190232998362 | |
| 7 | 438.74340042907266 | |
| 8 | 424.6998266323161 | ox-rich |

### 2.3 Metrology / SI constants

| Constant | Value | Source / role |
|----------|-------|----------------|
| \(g_0\) | **9.80665 m/s²** | CGPM/BIPM conventional standard gravity — \(v_e = I_{sp} g_0\) |
| 1 bar | **10⁵ Pa exactly** | SI-derived relationship — `pc_bar` ↔ `pc_pa` |
| \(R_\mathrm{univ}\) | **8314.462618 J/(kmol·K)** | Chamber density check \( \rho \approx P M_w / (R T) \) |

### 2.4 Secondary literature bands (sanity only)

Wide **CEA-class theoretical** envelopes (not flight, not page-cited Sutton tables):

| Family | Rough theoretical vac Isp band | Use |
|--------|--------------------------------|-----|
| LOX / kerosene | ~340–370 s (high ε) | envelope only |
| LOX / LH₂ | ~445–465 s (ε~40, Pc~1000 psia class) | envelope only |
| N₂O₄ / MMH | ~320–355 s | envelope only |

**Explicitly not used as point references:** Merlin ~311–348 s flight, RS-25 ~452 s flight (delivered).

---

## 3. Physics identities (must never drift)

Implemented in `tests/test_physics_identities.py` and runtime `sanity_check()`:

1. **\(v_{e,\mathrm{vac}} = I_{sp,\mathrm{vac}} \times g_0\)**  
2. **\(C_{f,\mathrm{vac}} = v_e / c^*\)**  
3. **\(P_c / P_e = \) CEA `Pc/Pe`**  
4. **Chamber \(\rho \approx P M_w / (R T)\)** (relative error ≪ 1% for tested LOX/RP-1 point)  
5. **Temperature order** \(T_e < T_t < T_c\)  
6. **γ order** \(\gamma_e \ge \gamma_c\) for typical products (γ rises as T falls)  
7. **Shifting ≥ frozen** vacuum Isp; **vac ≥ SL** Isp  
8. **c\* SI band** (~1500–2200 m/s kerolox; not ~5900 ft/s)  
9. **Density impulse** \(\rho I_{sp} = I_{sp} \times \rho_\mathrm{bulk}\) with liquid bulk density  

### Note on γ vs \(c_p/c_v\)

CEA chamber **transport** \(c_p\) can include equilibrium dissociation contributions, while CEA **performance γ** is the isentropic exponent used for nozzle relations. Therefore \(\gamma \neq c_p/(c_p-R)\) exactly is **expected**, not a conversion bug.

---

## 4. Multi-propellant regression matrix

Locked to NASA CEA via RocketCEA 1.2.x on the propwrap stack. Citations are **CEA reproducibility + RP-1311 methodology**, not flight tables.

| ID | Pair | O/F | Pc | ε | Isp_vac (shifting) |
|----|------|-----|----|---|---------------------|
| REG-RP1-LOX-1000psia-eps40 | RP1/LOX | 2.3 | ~1000 psia | 40 | ~352.3 s |
| REG-RP1-LOX-70bar-eps20 | RP1/LOX | 2.56 | 70 bar | 20 | ~343.7 s |
| REG-LH2-LOX-1000psia-eps40-OF5 | LH2/LOX | 5.0 | ~1000 psia | 40 | ~454.9 s |
| REG-LH2-LOX-RS25-class | LH2/LOX | 5.5 | 100 bar | 69 | ~463.7 s *theoretical* |
| REG-CH4-LOX-1000psia-eps40-OF3.2 | CH4/LOX | 3.2 | ~1000 psia | 40 | ~367.6 s |
| REG-MMH-N2O4-1000psia-eps40 | MMH/N2O4 | 2.0 | ~1000 psia | 40 | ~338.6 s |
| REG-UDMH-N2O4 | UDMH/N2O4 | 2.6 | ~1000 psia | 40 | ~338.3 s |
| REG-A50-N2O4 | A50/N2O4 | 2.0 | ~1000 psia | 40 | ~340.9 s |
| REG-ETHANOL-LOX | Ethanol/LOX | 1.5 | ~1000 psia | 40 | ~336.8 s |

Also bit-level checked against raw `CEA_Obj.get_Isp` for RP-1/LOX, CH4/LOX, MMH/N2O4 sample points.

---

## 5. Validation layers (automated)

| Layer | Content | Tests |
|-------|---------|-------|
| **A** | RocketCEA docs goldens | `test_validation_suite` + physics bit-level |
| **B** | Multi-propellant regression | `test_validation_suite` |
| **C** | Physics invariants (T, γ, frozen/shifting) | physics + validation suite |
| **D** | Trends (ranking, ε↑, O/F peak, ambient) | `test_validation_suite` |
| **E** | Unit-leak guards | validation + physics |
| **F** | Cantera γ band | `test_cross_validation` / known_values |
| **G** | Density-Isp ordering | `test_validation_suite` |
| **H** | SI identities (ve, Cf, ρ) | `test_physics_identities` |

---

## 6. Bugs fixed in physics audit (2026-07-29)

| Issue | Fix |
|-------|-----|
| `gamma_and_temp_at_eps` returned exit T twice as “chamber T” | Now returns true chamber and exit temperatures from CEA |
| Silent risk of ve/Cf drift | Hard identity tests + runtime `sanity_check` |
| Validation catalog under-cited | Expanded primary sources (NASA RP-1311, RocketCEA docs, BIPM g0, SI bar) |

---

## 7. Known gaps (honesty)

| Gap | Status |
|-----|--------|
| Page-cited Sutton edition tables | Not transcribed without physical edition |
| Independent NASA CEARUN `.out` archives in-repo | Recommended future work; current goldens are RocketCEA/CEA bit-level |
| Cantera species set ≠ full CEA | Documented; 15–25% γ band investigation threshold |
| Flight engine efficiency models | Optional η only; not validated as engine performance |

---

## 8. How to re-audit after dependency upgrades

1. Run full suite: `pytest -q`  
2. Re-run bit-level block: `pytest tests/test_physics_identities.py -v`  
3. If RocketCEA changes thermo data, update `validation_catalog.json` **with measured new values + changelog note** — never widen tolerances silently.  
4. Confirm `G0 == 9.80665` and bar = 1e5 Pa still hold in `propwrap.units`.
