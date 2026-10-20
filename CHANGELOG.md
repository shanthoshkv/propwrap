# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-10-20

### Breaking

- `cantera`, `matplotlib`, `pandas` are now optional. Plain `pip install propwrap` is core only; use `pip install "propwrap[all]"` for the previous behaviour. Missing extras raise a message naming the extra to install.

### Added

- `propwrap.engine`: `size_engine` / `PerformanceResult.size()` (mass flows, throat/exit diameters), `altitude_performance` + US Standard 1976 atmosphere, fixed-geometry `throttle` with separation flag
- Plots: frozen-vs-shifting band, SL and delivered Isp on O/F sweep; Cf and Pe=Pamb / Summerfield markers on ε sweep; γ residual panel; `plot_isp_map`, `plot_species`, `plot_stations`, `plot_propellant_parallel`, `plot_altitude`; `set_theme("light")`; 300 dpi, vector output for .pdf/.svg
- CLI: `map`, `altitude`, `throttle`, `info`, `doctor`; `run --thrust/--sea-level/--pamb/--stations`; `scan-of -j/--species/--xlsx/--pc-bar`; global `--theme`, `--config case.toml`
- `workers=` for parallel sweeps; `Mixture.isp_map`; `SweepResult.to_dataframe/to_excel/plot_species`; Jupyter rich display; `cantera_backend.equilibrium_hp`
- Cantera frozen-γ cross-check shown in summaries; mkdocs site; Colab quickstart notebook

### Changed

- CEA objects cached per propellant pair (faster sweeps); cache keys include propwrap/RocketCEA versions
- `sweep_eps` / `sweep_of_ratio` accept `pc_pa=` / `pc_mpa=` as well as legacy `pc_bar`
- Sanity warnings now suggest a fix; RocketCEA import banner and internal divide-by-zero warnings silenced
- Legacy CLI aliases (`performance`, `trade`, `sweep`, `compare`, `list-propellants`) still work but are hidden from `--help`

## [0.1.3] — 2026-07-30

### Changed

- Author / maintainer email set to `shanthoshkv@gmail.com` (shown on PyPI)

## [0.1.2] — 2026-07-30

### Fixed

- PyPI long description: all doc/site links are absolute so Website and file links work on pypi.org
- Official Website URL: https://aboutkvs.vercel.app/propwrap.html

## [0.1.1] — 2026-07-30

### Fixed

- Add `python -m propwrap` entry (`__main__.py`) so module invocation works, not only the `propwrap` console script

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

[0.1.3]: https://github.com/shanthoshkv/propwrap/releases/tag/v0.1.3
[0.1.2]: https://github.com/shanthoshkv/propwrap/releases/tag/v0.1.2
[0.1.1]: https://github.com/shanthoshkv/propwrap/releases/tag/v0.1.1
[0.1.0]: https://github.com/shanthoshkv/propwrap/releases/tag/v0.1.0
