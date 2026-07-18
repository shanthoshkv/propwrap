# MASTER PROMPT: `propwrap` — Unified RocketCEA/Cantera Propellant Performance Library

You are building a production-quality, pip-installable Python library called **`propwrap`**. This is not a script or a notebook — it is a library other tools (nozzle design, injector design, cooling channel design) will import and depend on. Treat it with the rigor of infrastructure code: typed, tested, documented, cached, and correct.

Read this entire document before writing any code. Build in the phase order given. Do not skip validation or testing steps to "get to features faster" — a wrong γ or Isp propagates silently into every downstream tool.

---

## 1. PROJECT PURPOSE

`propwrap` wraps RocketCEA (NASA CEA FORTRAN code, Python-wrapped) and Cantera into a single clean, typed, cached interface for liquid rocket propellant performance analysis. It replaces ad-hoc, repeated CEA scripting with a proper API that:

- Returns structured, typed results (not parsed strings/dicts)
- Caches expensive CEA/Cantera calls
- Supports sweeps (O/F, Pc, area ratio) as first-class operations, not manual loops
- Cross-validates CEA frozen-equilibrium output against Cantera's NASA-9 polynomial thermo data
- Produces publication-quality dark-themed plots
- Exports structured data (JSON/CSV) consumable by sibling tools (a MOC nozzle contour generator, an injector design tool, a regen cooling channel designer)

This library is the shared thermochemistry backbone for a larger liquid rocket engine design suite. Downstream tools will call `propwrap.Propellant(...).performance(...)` and `.gamma_vs_area_ratio(...)` — so the API surface designed here is a contract other code will depend on. Design it accordingly: stable, explicit, well-documented.

---

## 2. TECH STACK & CONSTRAINTS

- Python 3.10+, fully type-hinted (mypy-clean)
- `RocketCEA` for CEA calls (frozen and shifting equilibrium)
- `Cantera` for NASA-9 polynomial thermo cross-validation and temperature-dependent cp/γ
- `pydantic` (v2) for all structured result models — no bare dicts returned from public methods
- `matplotlib` for plotting, with a shared dark theme module (see Section 6)
- `sqlite3` (stdlib) for the caching layer — no external cache dependencies
- `pytest` for testing
- Packaging: `pyproject.toml`, installable via `pip install -e .`, publishable to PyPI structure (even if you don't publish it yet)
- No Jupyter notebooks as deliverables. CLI + library only. Examples go in `examples/*.py`, runnable as scripts.

---

## 3. PACKAGE STRUCTURE

```
propwrap/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── src/
│   └── propwrap/
│       ├── __init__.py                 # public API exports
│       ├── propellant.py               # Propellant class — main entry point
│       ├── models.py                   # pydantic result models
│       ├── cea_backend.py              # RocketCEA wrapper internals
│       ├── cantera_backend.py          # Cantera wrapper internals, NASA-9 lookups
│       ├── cross_validation.py         # CEA vs Cantera divergence checks
│       ├── sweeps.py                   # SweepResult class, O/F, Pc, eps sweeps
│       ├── cache.py                    # SQLite memoization layer
│       ├── propellant_library.py       # built-in + custom propellant/card-deck handling
│       ├── plotting.py                 # dark-themed plot functions
│       ├── export.py                   # JSON/CSV export utilities
│       └── cli.py                      # command-line interface
├── tests/
│   ├── test_propellant.py
│   ├── test_cache.py
│   ├── test_sweeps.py
│   ├── test_cross_validation.py
│   └── test_known_values.py            # validation against published data (Section 8)
├── examples/
│   ├── basic_performance.py
│   ├── of_sweep_lox_rp1.py
│   ├── gamma_profile_for_nozzle.py
│   └── propellant_comparison.py
└── docs/
    └── api_reference.md
```

---

## 4. CORE DATA MODELS (`models.py`)

Define pydantic models for every public return type. Minimum required fields — add more if physically meaningful, but do not remove any of these:

```python
class PerformanceResult(BaseModel):
    of_ratio: float
    pc_bar: float
    eps: float
    isp_vac_shifting: float      # seconds
    isp_vac_frozen: float
    isp_sl_shifting: float
    isp_sl_frozen: float
    c_star: float                 # m/s
    cf_vac: float
    cf_sl: float
    gamma_chamber: float
    gamma_throat: float
    gamma_exit: float
    mw_chamber: float             # kg/kmol
    tc_kelvin: float               # chamber temperature
    tt_kelvin: float               # throat temperature
    te_kelvin: float               # exit temperature
    fuel: str
    oxidizer: str

class GammaProfile(BaseModel):
    area_ratios: list[float]
    gamma_cea: list[float]
    gamma_cantera: list[float] | None   # None if use_cantera=False
    temperatures_k: list[float]
    source: Literal["cea_frozen", "cea_shifting", "cantera_frozen"]

class CrossValidationResult(BaseModel):
    parameter: str                # e.g. "gamma_chamber"
    cea_value: float
    cantera_value: float
    absolute_diff: float
    percent_diff: float
    within_tolerance: bool         # flag if percent_diff exceeds configurable threshold

class SweepResult(BaseModel):
    sweep_variable: Literal["of_ratio", "pc_bar", "eps"]
    values: list[float]
    results: list[PerformanceResult]

    def optimum(self, metric: str = "isp_vac_shifting") -> PerformanceResult: ...
    def plot(self, ...) -> matplotlib.figure.Figure: ...
    def to_csv(self, path: str) -> None: ...
    def to_json(self, path: str) -> None: ...
```

All public methods on `Propellant` return one of these — never a raw tuple, dict, or CEA string.

---

## 5. THE `Propellant` CLASS (`propellant.py`) — PRIMARY API

This is what every downstream consumer imports. Design signature:

```python
class Propellant:
    def __init__(
        self,
        fuel: str,
        oxidizer: str,
        fuel_temp_k: float | None = None,
        ox_temp_k: float | None = None,
        cache_enabled: bool = True,
    ): ...

    def performance(
        self, of_ratio: float, pc_bar: float, eps: float
    ) -> PerformanceResult: ...

    def sweep_of_ratio(
        self, of_range: tuple[float, float, float], pc_bar: float, eps: float
    ) -> SweepResult: ...

    def sweep_pc(
        self, of_ratio: float, pc_range: tuple[float, float, float], eps: float
    ) -> SweepResult: ...

    def sweep_eps(
        self, of_ratio: float, pc_bar: float, eps_range: tuple[float, float, float]
    ) -> SweepResult: ...

    def gamma_vs_area_ratio(
        self,
        of_ratio: float,
        pc_bar: float,
        eps_range: tuple[float, float, float],
        use_cantera: bool = True,
    ) -> GammaProfile: ...

    def cross_validate(
        self, of_ratio: float, pc_bar: float, eps: float, tolerance_pct: float = 5.0
    ) -> list[CrossValidationResult]: ...

    def compare_to(
        self, other: "Propellant", of_ratio: float, pc_bar: float, eps: float
    ) -> dict: ...  # side-by-side performance comparison
```

Requirements:
- `of_range`/`pc_range`/`eps_range` tuples are `(start, stop, step)` — validate `stop > start`, `step > 0`.
- All CEA calls go through `cea_backend.py` — `Propellant` never calls `CEA_Obj` directly.
- Unit handling: accept and return **SI-adjacent units documented explicitly in docstrings** (bar for pressure, Kelvin for temperature, seconds for Isp, m/s for velocities). RocketCEA internally uses English units — all conversion happens inside `cea_backend.py`, never leaks to the public API.
- Every method must be cache-aware (Section 7) — identical inputs must not re-invoke CEA.

---

## 6. PLOTTING (`plotting.py`) — DARK AESTHETIC

Match the established design system used across the rest of this engine design suite:

- Pure black background (`#000000` or near-black `#0a0a0a`)
- Primary accent: steel-blue (`#5b8dee`)
- Secondary accent: amber-copper (for contrast series / highlighting optimum points)
- Font stack: monospace for axis labels/ticks (DM Mono or a bundled fallback), clean sans for titles (DM Sans fallback to a standard sans if unavailable in matplotlib's font list — do not fail if the exact font isn't installed, fall back gracefully)
- Gridlines: subtle, low-opacity, don't compete with data
- Every sweep plot must mark and annotate the optimum point (e.g., peak Isp on an O/F sweep — the classic "banana curve")

Required plot functions:
- `plot_of_sweep(sweep_result)` — Isp & Tc vs O/F, dual y-axis
- `plot_pc_sweep(sweep_result)`
- `plot_eps_sweep(sweep_result)`
- `plot_gamma_profile(gamma_profile)` — γ vs area ratio, CEA vs Cantera overlay if both present
- `plot_propellant_comparison(results: list[PerformanceResult], labels: list[str])` — bar or radar chart comparing Isp, density impulse, Tc across propellant combos
- All functions return a `matplotlib.figure.Figure` (do not call `plt.show()` internally — let the caller decide) and accept an optional `save_path` to also write PNG/SVG.

---

## 7. CACHING LAYER (`cache.py`)

- SQLite database at a configurable path (default `~/.propwrap/cache.db`)
- Cache key: hash of `(fuel, oxidizer, of_ratio, pc_bar, eps, fuel_temp_k, ox_temp_k, method)` — method distinguishes CEA calls from Cantera calls
- Store the full serialized `PerformanceResult`/`GammaProfile` JSON as the value
- Cache must be transparent: `Propellant(cache_enabled=True)` (default) always checks cache first, writes on miss
- Provide `Propellant.clear_cache()` and a `--clear-cache` CLI flag
- Write a test that asserts a second identical call does not invoke the CEA backend (mock/spy on `cea_backend` call count)

---

## 8. VALIDATION SUITE (`tests/test_known_values.py`) — NON-NEGOTIABLE

Before this library is considered done, validate against published reference data. This is the credibility layer — do not skip it or fake it.

Required validation cases:
1. **LOX/RP-1** at Pc = 70 bar, O/F = 2.56, eps = 20 → compare vacuum Isp against published values for this combo (Rocketdyne/SpaceX-class engines cite ~311-320s vacuum Isp for LOX/RP-1 at similar conditions — pull the actual reference number from RocketCEA's own documentation/test cases or a cited textbook (Sutton's *Rocket Propulsion Elements* has reference tables), not from memory. Assert within 2% tolerance.
2. **LOX/LH2** at Pc = 100 bar, O/F = 5.5 (approx. RS-25 conditions), eps = 69 → compare against known RS-25-class vacuum Isp (~452s range). Same tolerance approach.
3. **N2O4/MMH** (storable hypergolic, common for upper stages/attitude control) at representative Pc/O/F → sanity check against Sutton reference tables.
4. Cross-check that `gamma_chamber > gamma_exit` is always true (physically required — γ increases as temperature drops through expansion for real combustion products) for every test case above. If your Cantera/CEA integration ever produces the reverse, that's a bug — fail loudly, don't silently accept it.
5. Cross-validate CEA vs Cantera γ at chamber conditions for at least 2 propellant combos and assert the divergence is within a documented tolerance band (if it's not, document *why* in the test comment — species set mismatch, frozen vs equilibrium assumption, etc. — don't just widen the tolerance until it passes).

Cite your reference values in code comments (source + edition/page if from Sutton, or state clearly "from RocketCEA reference test suite" if pulled from there). Do not fabricate reference numbers — if you can't find a citable value for a given case, search for one or replace the test case with one you can source, and say so explicitly in the PR/handoff notes.

---

## 9. CUSTOM PROPELLANT SUPPORT (`propellant_library.py`)

- Expose the built-in RocketCEA propellant list via `propwrap.list_propellants()`
- Support adding custom fuel/oxidizer definitions via CEA's `card_str` format, but wrap it: `add_custom_propellant(name, formula, heat_of_formation, ...)` — validate required fields, raise clear errors on malformed card decks rather than letting CEA fail cryptically
- Include at least 2 example custom propellant definitions in `examples/` (e.g., a kerosene blend or a hybrid fuel grain formulation) to prove the path works end-to-end

---

## 10. CLI (`cli.py`)

Minimal but real — not a toy:

```
propwrap performance --fuel RP-1 --ox LOX --of 2.56 --pc 70 --eps 20
propwrap sweep --fuel RP-1 --ox LOX --sweep of --range 2.0 3.5 0.1 --pc 70 --eps 20 --plot
propwrap compare --combos "RP-1/LOX,LH2/LOX,MMH/N2O4" --of 2.5 --pc 70 --eps 20
propwrap list-propellants
propwrap clear-cache
```

Output human-readable tables to stdout by default; `--json` flag switches to structured JSON output for piping into other tools.

---

## 11. DOCUMENTATION

- `README.md`: install instructions, quickstart (the exact code example from Section 5 style), architecture overview, link to `docs/api_reference.md`
- Every public function/class needs a full docstring: purpose, units for every parameter, return type description, and a runnable example
- `docs/api_reference.md`: generated or hand-written full API reference
- Document explicitly, in one clear section, the **limitations**: frozen vs shifting equilibrium assumptions, what "custom propellant" support does and doesn't validate, known divergence cases between CEA and Cantera and why they occur. Do not oversell accuracy — state tolerances plainly.

---

## 12. BUILD PHASES — EXECUTE IN THIS ORDER

**Phase 1 — Core backend & models**
`models.py`, `cea_backend.py`, basic `Propellant.performance()` working end-to-end for one propellant combo. No caching, no plotting yet. Get this correct and unit-tested first.

**Phase 2 — Caching**
Implement `cache.py`, wire into `Propellant`. Test cache hit/miss behavior explicitly.

**Phase 3 — Sweeps**
`sweeps.py`, `SweepResult`, all three sweep methods on `Propellant`. Test `optimum()` against a hand-checkable case.

**Phase 4 — Cantera integration & cross-validation**
`cantera_backend.py`, `cross_validation.py`, `gamma_vs_area_ratio()`. This is the most technically involved phase — take care with species set consistency between CEA and Cantera (they need to agree on what's in the mixture for a fair comparison).

**Phase 5 — Custom propellants**
`propellant_library.py` custom propellant path, with working examples.

**Phase 6 — Plotting**
`plotting.py`, all required plot functions, dark theme applied consistently.

**Phase 7 — Export, CLI, docs**
`export.py`, `cli.py`, README, api_reference.md.

**Phase 8 — Validation suite**
`tests/test_known_values.py` fully populated per Section 8. This phase is the gate — do not consider the project complete until it passes with cited reference values.

At the end of each phase, run the full test suite and confirm nothing from a prior phase regressed before moving on.

---

## 13. DEFINITION OF DONE

- [ ] `pip install -e .` works cleanly from a fresh virtualenv
- [ ] `pytest` passes, including the full validation suite with cited reference values
- [ ] mypy runs clean (or documented exceptions with reasons)
- [ ] Every public method has a docstring with units specified
- [ ] CLI works for all commands listed in Section 10
- [ ] README quickstart example runs verbatim, copy-pasted, with no modification
- [ ] At least one example script demonstrates feeding `gamma_vs_area_ratio()` output into a downstream consumer (mock this if the nozzle tool isn't ready — just prove the data shape is consumable)
- [ ] Plots render in the dark theme and are saved successfully via `save_path`
- [ ] No raw CEA units (English/imperial) leak through any public API — confirm by grep or explicit test

Build it in this order, don't skip the validation phase, and flag clearly in your final summary any reference value you could not independently confirm rather than presenting an unverified number as fact.
