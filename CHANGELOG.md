# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-07-29

First public release.

### Added

- `Mixture` / `Propellant` API over NASA CEA via RocketCEA
- SI public results (Pa, K, m/s, kg/m³); Isp in seconds plus `ve_*` in m/s
- Unit converters (`convert`, `propwrap.units`)
- O/F, Pc, ε sweeps; `optimum()`; density impulse (ρ·Isp)
- Fair multi-pair trades (`compare_propellants`) at each pair’s own best O/F
- Propellant registry, aliases, multi-component blends
- Optional Cantera frozen-γ cross-check (Cantera is a **required** dependency)
- Dark-theme plotting (matplotlib is a **required** dependency)
- CLI: `propwrap run`, `scan-of`, `characterize`, `compare-pairs`, `homework`, …
- Student lab packs, Case presets, markdown/CSV export
- Validation suite: RocketCEA goldens, physics identities, regression catalog
- Typed package (`py.typed`) and console script entry point

### Notes

- Numbers are ideal 1-D CEA theory, not flight-delivered Isp
- This package’s source is MIT; RocketCEA is GPL-family — review both for proprietary work
- **Stable API (0.1.x):** `Mixture`, `compare_propellants`, `characterize`, `convert` / `units`, `PerformanceResult` fields listed in `docs/api_reference.md`, CLI `run` / `homework`
- **May change:** Cantera cross-check tolerances, plot styling, η efficiency knobs, internal cache layout

[0.1.0]: https://github.com/shanthoshkv/propwrap/releases/tag/v0.1.0
