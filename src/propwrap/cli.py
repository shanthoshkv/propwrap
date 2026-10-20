"""Command-line interface — friendly verbs aligned with workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence


def main(argv: Sequence[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # ε, γ, ρ crash cp1252 when piped on Windows
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        prog="propwrap",
        description="Propellant thermochemistry (RocketCEA/Cantera). "
        "Plots are opt-in via --plot / --save.",
    )
    parser.add_argument("--theme", choices=["dark", "light"], default=None, help="Plot theme")
    parser.add_argument("--config", default=None, help="TOML file with default arguments")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # run (preferred) + performance (legacy)
    for name, help_ in (
        ("run", "Evaluate one mixture point (friendly)"),
        ("performance", None),
    ):
        p = sub.add_parser(name, help=help_) if help_ else sub.add_parser(name)
        p.add_argument("fuel", nargs="?", default=None)
        p.add_argument("ox", nargs="?", default=None)
        p.add_argument("--fuel", dest="fuel_opt", default=None)
        p.add_argument("--ox", dest="ox_opt", default=None)
        p.add_argument("--of", type=float, required=True)
        p.add_argument("--pc", type=float, default=None, help="Pc [Pa] (SI)")
        p.add_argument("--pc-bar", type=float, default=None, dest="pc_bar", help="Pc [bar]")
        p.add_argument("--pc-mpa", type=float, default=None, dest="pc_mpa", help="Pc [MPa]")
        p.add_argument("--eps", type=float, default=None)
        p.add_argument("--json", action="store_true")
        p.add_argument("--verbose", "-v", action="store_true")
        p.add_argument("--thrust", type=float, default=None, help="Size engine for thrust [N]")
        p.add_argument("--sea-level", action="store_true", help="--thrust is sea-level thrust")
        p.add_argument("--pamb", type=float, default=None, help="Also report Isp at ambient [Pa]")
        p.add_argument("--stations", default=None, metavar="PNG", help="Save station plot")

    # scan-of
    p_sc = sub.add_parser("scan-of", help="Scan O/F for one pair")
    p_sc.add_argument("fuel", nargs="?", default=None)
    p_sc.add_argument("ox", nargs="?", default=None)
    p_sc.add_argument("--fuel", dest="fuel_opt", default=None)
    p_sc.add_argument("--ox", dest="ox_opt", default=None)
    p_sc.add_argument("--range", nargs=3, type=float, metavar=("A", "B", "D"), default=None)
    p_sc.add_argument("--pc", type=float, default=None)
    p_sc.add_argument("--pc-bar", type=float, default=None, dest="pc_bar")
    p_sc.add_argument("--eps", type=float, default=None)
    p_sc.add_argument("--plot", action="store_true")
    p_sc.add_argument("--save", default=None)
    p_sc.add_argument("--json", action="store_true")
    p_sc.add_argument("--species", default=None, metavar="PNG", help="Save composition plot")
    p_sc.add_argument("--xlsx", default=None, help="Write samples to Excel")
    p_sc.add_argument("-j", "--workers", type=int, default=1, help="Parallel processes")

    # map
    p_map = sub.add_parser("map", help="Isp contour over O/F x Pc")
    p_map.add_argument("fuel")
    p_map.add_argument("ox")
    p_map.add_argument("--of-range", nargs=3, type=float, required=True, metavar=("A", "B", "D"))
    p_map.add_argument("--pc-range", nargs=3, type=float, required=True, metavar=("A", "B", "D"), help="[bar]")
    p_map.add_argument("--eps", type=float, required=True)
    p_map.add_argument("--save", default="isp_map.png")
    p_map.add_argument("-j", "--workers", type=int, default=1)

    # altitude
    p_alt = sub.add_parser("altitude", help="Isp vs altitude (US Std 1976)")
    p_alt.add_argument("fuel")
    p_alt.add_argument("ox")
    p_alt.add_argument("--of", type=float, required=True)
    p_alt.add_argument("--pc-bar", type=float, required=True, dest="pc_bar")
    p_alt.add_argument("--eps", type=float, required=True)
    p_alt.add_argument("--max-km", type=float, default=50.0)
    p_alt.add_argument("--save", default=None)

    # throttle
    p_thr = sub.add_parser("throttle", help="Fixed-geometry throttle table")
    p_thr.add_argument("fuel")
    p_thr.add_argument("ox")
    p_thr.add_argument("--of", type=float, required=True)
    p_thr.add_argument("--pc-bar", type=float, required=True, dest="pc_bar")
    p_thr.add_argument("--eps", type=float, required=True)
    p_thr.add_argument("--thrust", type=float, required=True, help="Design thrust [N]")
    p_thr.add_argument("--pamb", type=float, default=101325.0, help="Ambient [Pa]")

    # info / doctor
    p_info = sub.add_parser("info", help="Show one propellant's properties")
    p_info.add_argument("name")
    sub.add_parser("doctor", help="Check installation and run a sample point")

    # sweep (legacy)
    p_sw = sub.add_parser("sweep")
    _flags_fuel_ox(p_sw)
    p_sw.add_argument("--sweep", choices=["of", "pc", "eps"], required=True)
    p_sw.add_argument("--range", nargs=3, type=float, required=True)
    p_sw.add_argument("--of", type=float, default=None)
    p_sw.add_argument("--pc", type=float, default=None)
    p_sw.add_argument("--eps", type=float, default=None)
    p_sw.add_argument("--plot", action="store_true")
    p_sw.add_argument("--save", default=None)
    p_sw.add_argument("--plot-path", default=None)
    p_sw.add_argument("--json", action="store_true")

    # characterize
    p_ch = sub.add_parser("characterize", help="Full pair characterization")
    p_ch.add_argument("fuel", nargs="?", default=None)
    p_ch.add_argument("ox", nargs="?", default=None)
    p_ch.add_argument("--fuel", dest="fuel_opt", default=None)
    p_ch.add_argument("--ox", dest="ox_opt", default=None)
    p_ch.add_argument("--of", type=float, default=None)
    p_ch.add_argument("--pc", type=float, default=None)
    p_ch.add_argument("--eps", type=float, default=None)
    p_ch.add_argument("--plot", action="store_true")
    p_ch.add_argument("--save", default=None)
    p_ch.add_argument("--verbose", "-v", action="store_true")

    # compare-pairs / trade
    for name in ("compare-pairs", "trade"):
        p = (
            sub.add_parser(name, help="Compare pairs at each optimum O/F")
            if name == "compare-pairs"
            else sub.add_parser(name)
        )
        p.add_argument(
            "--combos",
            required=True,
            help='FUEL/OX list, e.g. "RP-1/LOX,LH2/LOX,CH4/LOX"',
        )
        p.add_argument("--pc", type=float, default=None)
        p.add_argument("--eps", type=float, default=None)
        p.add_argument("--plot", action="store_true")
        p.add_argument("--save", default=None)
        p.add_argument("--json", action="store_true")

    # compare fixed O/F (legacy)
    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--combos", required=True)
    p_cmp.add_argument("--of", type=float, required=True)
    p_cmp.add_argument("--pc", type=float, required=True)
    p_cmp.add_argument("--eps", type=float, required=True)
    p_cmp.add_argument("--json", action="store_true")

    # density-isp
    p_di = sub.add_parser("density-isp", help="Density-Isp vs O/F")
    _flags_fuel_ox(p_di)
    p_di.add_argument("--range", nargs=3, type=float, required=True)
    p_di.add_argument("--pc", type=float, default=None)
    p_di.add_argument("--eps", type=float, default=None)
    p_di.add_argument("--plot", action="store_true")
    p_di.add_argument("--save", default=None)
    p_di.add_argument("--json", action="store_true")

    # list
    p_ls = sub.add_parser("list", help="List propellants")
    p_ls.add_argument("--cryogenic", action="store_true")
    p_ls.add_argument("--storable", action="store_true")
    p_ls.add_argument(
        "--of-hints",
        action="store_true",
        help="Show typical O/F ranges for fuels",
    )
    sub.add_parser("list-propellants")

    # homework / lab report pack
    p_hw = sub.add_parser(
        "homework",
        help="Generate student lab folder (summary.md, CSV, plots)",
    )
    p_hw.add_argument(
        "preset",
        nargs="?",
        default="kerolox",
        choices=["kerolox", "methalox", "hydrolox", "storable", "custom"],
        help="Homework preset (default: kerolox)",
    )
    p_hw.add_argument("--name", default="Student", help="Student name for folder/report")
    p_hw.add_argument("--out", default=None, help="Output directory (default: auto)")
    p_hw.add_argument("--fuel", default=None)
    p_hw.add_argument("--ox", default=None)
    p_hw.add_argument("--of", type=float, default=None)
    p_hw.add_argument("--pc-bar", type=float, default=None, dest="pc_bar")
    p_hw.add_argument("--eps", type=float, default=None)
    p_hw.add_argument("--no-plots", action="store_true")
    p_hw.add_argument(
        "--compare",
        default=None,
        help='Optional combos for trade plot, e.g. "RP-1/LOX,CH4/LOX,LH2/LOX"',
    )

    sub.add_parser("clear-cache", help="Clear SQLite cache")

    args = parser.parse_args(argv)
    if args.config:
        _apply_config(args, args.config)
    if args.theme:
        from propwrap.plotting import set_theme

        set_theme(args.theme)
    cmd = args.command
    handlers = {
        "map": _cmd_map,
        "altitude": _cmd_altitude,
        "throttle": _cmd_throttle,
        "info": _cmd_info,
        "doctor": _cmd_doctor,
    }
    if cmd in handlers:
        return handlers[cmd](args)

    if cmd in ("run", "performance"):
        return _cmd_run(args)
    if cmd == "scan-of":
        return _cmd_scan_of(args)
    if cmd == "sweep":
        return _cmd_sweep(args)
    if cmd == "characterize":
        return _cmd_characterize(args)
    if cmd in ("compare-pairs", "trade"):
        return _cmd_trade(args)
    if cmd == "compare":
        return _cmd_compare_fixed(args)
    if cmd == "density-isp":
        return _cmd_density_isp(args)
    if cmd in ("list", "list-propellants"):
        return _cmd_list(args)
    if cmd == "homework":
        return _cmd_homework(args)
    if cmd == "clear-cache":
        from propwrap.cache import clear_default_cache

        print(f"Cleared {clear_default_cache()} cache entries")
        return 0
    parser.error(f"Unknown command {cmd}")
    return 2


def _flags_fuel_ox(p: argparse.ArgumentParser) -> None:
    p.add_argument("--fuel", required=True)
    p.add_argument("--ox", required=True)


def _fuel_ox(args: argparse.Namespace) -> tuple[str, str]:
    fuel = getattr(args, "fuel_opt", None) or getattr(args, "fuel", None)
    ox = getattr(args, "ox_opt", None) or getattr(args, "ox", None)
    if not fuel or not ox:
        print("Need fuel and oxidizer (positional or --fuel/--ox)", file=sys.stderr)
        raise SystemExit(2)
    return fuel, ox


def _cmd_run(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    fuel, ox = _fuel_ox(args)
    m = Mixture(fuel, ox)
    r = m.evaluate(
        of=args.of,
        pc=args.pc,
        pc_bar=getattr(args, "pc_bar", None),
        pc_mpa=getattr(args, "pc_mpa", None),
        eps=args.eps,
        verbose=args.verbose,
    )
    if args.json:
        print(r.model_dump_json(indent=2))
        return 0
    if not args.verbose:
        print(r.summary())
    if args.thrust:
        sz = r.size(args.thrust, sea_level=args.sea_level)
        print(
            f"sizing  F={sz['thrust_n']:.4g} N  mdot={sz['mdot_kg_s']:.4g} kg/s "
            f"(ox {sz['mdot_ox_kg_s']:.4g}, fuel {sz['mdot_fuel_kg_s']:.4g})  "
            f"Dt={sz['throat_diameter_m'] * 1e3:.1f} mm  De={sz['exit_diameter_m'] * 1e3:.1f} mm"
        )
    if args.pamb is not None:
        from propwrap.cea_backend import ambient_isp

        a = ambient_isp(fuel, ox, r.of_ratio, r.pc_pa, r.eps, args.pamb,
                        eta_cstar=m.eta_cstar, eta_cf=m.eta_cf)
        print(f"Isp at Pamb={args.pamb:.4g} Pa: {float(a['isp_s']):.1f} s  ({a['mode']})")
    if args.stations:
        r.plot_stations(save=args.stations)
        print(f"saved {args.stations}")
    print(f"\nnext: propwrap scan-of {fuel} {ox} --plot   (find the optimum O/F)", file=sys.stderr)
    return 0


def _cmd_scan_of(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    fuel, ox = _fuel_ox(args)
    m = Mixture(fuel, ox)
    rng = tuple(args.range) if args.range else None
    sw = m.scan_of(
        rng,
        pc=args.pc,
        pc_bar=args.pc_bar,
        eps=args.eps,
        plot=args.plot,
        save=args.save,
        verbose=not args.json,
        workers=args.workers,
    )
    if args.json:
        print(sw.model_dump_json(indent=2))
    if args.species:
        sw.plot_species(save=args.species)
    if args.xlsx:
        sw.to_excel(args.xlsx)
    return 0


def _apply_config(args: argparse.Namespace, path: str) -> None:
    """Fill unset CLI options from a TOML file (keys = option names, e.g. pc_bar = 70)."""
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10
        from propwrap.errors import require

        tomllib = require("tomli", "toml")
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    for k, v in cfg.items():
        k = k.replace("-", "_")
        if getattr(args, k, None) in (None, False):
            setattr(args, k, tuple(v) if isinstance(v, list) else v)


def _cmd_map(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    Mixture(args.fuel, args.ox).isp_map(
        tuple(args.of_range), tuple(args.pc_range), args.eps,
        workers=args.workers, save=args.save,
    )
    print(f"saved {args.save}")
    return 0


def _cmd_altitude(args: argparse.Namespace) -> int:
    from propwrap import Mixture
    from propwrap.engine import altitude_performance
    from propwrap.units import bar_to_pa

    hs = [i * args.max_km * 100.0 for i in range(11)]  # 11 points, km → m
    rows = altitude_performance(
        Mixture(args.fuel, args.ox), args.of, bar_to_pa(args.pc_bar), args.eps, hs
    )
    print(f"{'h [km]':>8} {'Pamb [kPa]':>11} {'Isp [s]':>8}  mode")
    for r in rows:
        print(f"{r['altitude_m'] / 1e3:8.1f} {r['pamb_pa'] / 1e3:11.3f} {r['isp_s']:8.1f}  {r['mode']}")
    if args.save:
        from propwrap.plotting import plot_altitude

        plot_altitude(rows, save_path=args.save)
        print(f"saved {args.save}")
    return 0


def _cmd_throttle(args: argparse.Namespace) -> int:
    from propwrap import Mixture
    from propwrap.engine import throttle
    from propwrap.units import bar_to_pa

    rows = throttle(
        Mixture(args.fuel, args.ox), args.of, bar_to_pa(args.pc_bar), args.eps,
        args.thrust, pamb_pa=args.pamb,
    )
    print(f"{'%':>5} {'Pc [bar]':>9} {'mdot':>9} {'Isp [s]':>8} {'F [N]':>11}  Pe/Pa")
    for r in rows:
        flag = "  SEPARATION RISK" if r["separation_risk"] else ""
        print(
            f"{r['fraction'] * 100:5.0f} {r['pc_pa'] / 1e5:9.2f} {r['mdot_kg_s']:9.3f} "
            f"{r['isp_s']:8.1f} {r['thrust_n']:11.4g}  {r['pe_over_pamb']:.2f}{flag}"
        )
    return 0


def _cmd_info(args: argparse.Namespace) -> int:
    from propwrap.errors import did_you_mean
    from propwrap.propellant_library import stoich_of_ratio
    from propwrap.registry import get_propellant

    rec = get_propellant(args.name)
    if rec is None:
        print(f"Unknown propellant '{args.name}'. {did_you_mean(args.name)}", file=sys.stderr)
        return 1
    for k, v in rec.model_dump().items():
        if v not in (None, "", [], {}):
            print(f"{k:>24}: {v}")
    if rec.kind == "fuel":
        st = stoich_of_ratio(rec.cea_name or rec.name, "LOX")
        if st:
            print(f"{'stoich O/F with LOX':>24}: {st:.3f}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    import importlib
    import os
    import platform

    import propwrap

    print(f"propwrap {propwrap.__version__}  Python {platform.python_version()}  {platform.system()}")
    ok = True
    for mod, extra in (("rocketcea", None), ("cantera", "cantera"), ("matplotlib", "plot"),
                       ("pandas", "pandas"), ("openpyxl", "excel")):
        try:
            v = getattr(importlib.import_module(mod), "__version__", "?")
            print(f"  [ok]   {mod} {v}")
        except ImportError:
            ok = ok and extra is not None
            hint = f'pip install "propwrap[{extra}]"' if extra else "pip install rocketcea  (required)"
            print(f"  [miss] {mod} -> {hint}")
    data_dir = os.path.join(os.path.expanduser("~"), "RocketCEA")
    writable = os.access(data_dir if os.path.isdir(data_dir) else os.path.expanduser("~"), os.W_OK)
    print(f"  [{'ok' if writable else 'FAIL'}]   RocketCEA data dir writable: {data_dir}")
    ok = ok and writable
    try:
        from propwrap import Mixture

        r = Mixture("RP-1", "LOX", cache_enabled=False).evaluate(of=2.56, pc_bar=70, eps=20, full=False)
        print(f"  [ok]   sample RP-1/LOX Isp_vac = {r.isp_vac_shifting:.1f} s")
    except Exception as e:  # doctor must report, never crash
        ok = False
        print(f"  [FAIL] sample point: {type(e).__name__}: {e}")
    print("All good." if ok else "Problems found — see above.")
    return 0 if ok else 1


def _cmd_sweep(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    m = Mixture(args.fuel, args.ox)
    rng = (args.range[0], args.range[1], args.range[2])
    save = args.save or args.plot_path
    if args.sweep == "of":
        if args.pc is None or args.eps is None:
            print("sweep of needs --pc and --eps", file=sys.stderr)
            return 2
        sw = m.scan_of(rng, pc=args.pc, eps=args.eps, plot=args.plot, save=save)
    elif args.sweep == "pc":
        sw = m.sweep_pc(args.of, rng, args.eps, plot=args.plot, save=save)
    else:
        sw = m.sweep_eps(args.of, args.pc, rng, plot=args.plot, save=save)
    if args.json:
        print(sw.model_dump_json(indent=2))
    else:
        print(sw.summary())
    return 0


def _cmd_characterize(args: argparse.Namespace) -> int:
    from propwrap import characterize

    fuel, ox = _fuel_ox(args)
    result = characterize(
        fuel,
        ox,
        of=args.of,
        pc_bar=args.pc,
        eps=args.eps,
        plot=args.plot,
        save=args.save,
        verbose=True,
    )
    if not args.verbose:
        print(result.summary())
    return 0


def _cmd_trade(args: argparse.Namespace) -> int:
    from propwrap import compare_propellants

    pairs = [c.strip() for c in args.combos.split(",") if c.strip()]
    trade = compare_propellants(
        pairs,
        pc_bar=args.pc,
        eps=args.eps,
        plot=args.plot,
        save=args.save,
        verbose=not args.json,
    )
    if args.json:
        print(trade.model_dump_json(indent=2))
    return 0


def _cmd_compare_fixed(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    print(
        "NOTE: Fixed-O/F compare can be unfair across propellants "
        "(e.g. O/F=2.5 is poor for LH2). Prefer: propwrap compare-pairs ...",
        file=sys.stderr,
    )
    rows = []
    for combo in args.combos.split(","):
        fuel, ox = combo.strip().split("/", 1)
        r = Mixture(fuel.strip(), ox.strip()).evaluate(
            of=args.of, pc=args.pc, pc_bar=None, eps=args.eps
        )
        # if pc looks wrong, evaluate may raise; allow --pc as Pa only
        rows.append(
            {
                "combo": f"{r.fuel}/{r.oxidizer}",
                "isp_vac_shifting": r.isp_vac_shifting,
                "tc_kelvin": r.tc_kelvin,
                "c_star": r.c_star,
            }
        )
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(
                f"{row['combo']:<16} Isp={row['isp_vac_shifting']:.1f} s  "
                f"Tc={row['tc_kelvin']:.0f} K"
            )
    return 0


def _cmd_density_isp(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    m = Mixture(args.fuel, args.ox)
    rng = (args.range[0], args.range[1], args.range[2])
    curve = m.density_impulse(
        rng, pc=args.pc, eps=args.eps, plot=args.plot, save=args.save, verbose=not args.json
    )
    if args.json:
        print(curve.model_dump_json(indent=2))
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    from propwrap import list_propellants, list_registry

    storage = None
    if getattr(args, "cryogenic", False):
        storage = "cryogenic"
    if getattr(args, "storable", False):
        storage = "storable"

    if getattr(args, "of_hints", False) or storage:
        print(f"{'kind':9} {'name':12} {'storage':14} {'typical O/F':14} density")
        print("-" * 70)
        for r in list_registry(storage=storage):  # type: ignore[arg-type]
            of = (
                f"{r.typical_of_range[0]:g}–{r.typical_of_range[1]:g}"
                if r.typical_of_range
                else "—"
            )
            dens = f"{r.density_kg_m3:.0f} kg/m³" if r.density_kg_m3 else "—"
            print(f"{r.kind:9} {r.name:12} {r.storage:14} {of:14} {dens}")
        return 0

    data = list_propellants()
    print("Fuels:", ", ".join(data["fuels"]))
    print("Oxidizers:", ", ".join(data["oxidizers"]))
    print("(tip: propwrap list --of-hints  → typical O/F ranges for students)")
    return 0


def _cmd_homework(args: argparse.Namespace) -> int:
    from propwrap.reports import homework_folder_name, write_lab_report

    presets = {
        "kerolox": {
            "fuel": "RP-1",
            "oxidizer": "LOX",
            "of_ratio": 2.56,
            "pc_bar": 70.0,
            "eps": 20.0,
            "compare": ["RP-1/LOX", "CH4/LOX", "LH2/LOX"],
        },
        "methalox": {
            "fuel": "CH4",
            "oxidizer": "LOX",
            "of_ratio": 3.0,
            "pc_bar": 100.0,
            "eps": 25.0,
            "compare": ["CH4/LOX", "RP-1/LOX", "LH2/LOX"],
        },
        "hydrolox": {
            "fuel": "LH2",
            "oxidizer": "LOX",
            "of_ratio": 5.5,
            "pc_bar": 100.0,
            "eps": 40.0,
            "compare": ["LH2/LOX", "CH4/LOX", "RP-1/LOX"],
        },
        "storable": {
            "fuel": "MMH",
            "oxidizer": "N2O4",
            "of_ratio": 2.0,
            "pc_bar": 10.0,
            "eps": 40.0,
            "compare": ["MMH/N2O4", "UDMH/N2O4", "RP-1/LOX"],
        },
        "custom": {
            "fuel": args.fuel or "RP-1",
            "oxidizer": args.ox or "LOX",
            "of_ratio": args.of or 2.5,
            "pc_bar": args.pc_bar or 70.0,
            "eps": args.eps or 20.0,
            "compare": None,
        },
    }
    cfg = dict(presets[args.preset])
    if args.fuel:
        cfg["fuel"] = args.fuel
    if args.ox:
        cfg["oxidizer"] = args.ox
    if args.of is not None:
        cfg["of_ratio"] = args.of
    if args.pc_bar is not None:
        cfg["pc_bar"] = args.pc_bar
    if args.eps is not None:
        cfg["eps"] = args.eps

    compare = None
    if args.compare:
        compare = [c.strip() for c in args.compare.split(",") if c.strip()]
    elif cfg.get("compare"):
        compare = cfg["compare"]

    out = args.out or homework_folder_name(args.name, args.preset)
    path = write_lab_report(
        out,
        fuel=cfg["fuel"],
        oxidizer=cfg["oxidizer"],
        of_ratio=float(cfg["of_ratio"]),
        pc_bar=float(cfg["pc_bar"]),
        eps=float(cfg["eps"]),
        student_name=args.name,
        compare_pairs=compare,
        make_plots=not args.no_plots,
    )
    print(f"Lab pack written to: {path.resolve()}")
    print(f"  Open {path / 'summary.md'} and read assumptions.txt first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
