"""Command-line interface — friendly verbs aligned with workflows."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="propwrap",
        description="Propellant thermochemistry (RocketCEA/Cantera). "
        "Plots are opt-in via --plot / --save.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run (preferred) + performance (legacy)
    for name, help_ in (
        ("run", "Evaluate one mixture point (friendly)"),
        ("performance", "Alias of run"),
    ):
        p = sub.add_parser(name, help=help_)
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

    # scan-of
    p_sc = sub.add_parser("scan-of", help="Scan O/F for one pair")
    p_sc.add_argument("fuel", nargs="?", default=None)
    p_sc.add_argument("ox", nargs="?", default=None)
    p_sc.add_argument("--fuel", dest="fuel_opt", default=None)
    p_sc.add_argument("--ox", dest="ox_opt", default=None)
    p_sc.add_argument("--range", nargs=3, type=float, metavar=("A", "B", "D"), default=None)
    p_sc.add_argument("--pc", type=float, default=None)
    p_sc.add_argument("--eps", type=float, default=None)
    p_sc.add_argument("--plot", action="store_true")
    p_sc.add_argument("--save", default=None)
    p_sc.add_argument("--json", action="store_true")

    # sweep (legacy)
    p_sw = sub.add_parser("sweep", help="Parameter sweep (legacy)")
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
        p = sub.add_parser(name, help="Compare pairs at each optimum O/F")
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
    p_cmp = sub.add_parser("compare", help="Compare at fixed O/F (legacy)")
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
    p_ls = sub.add_parser("list", help="List propellants (alias: list-propellants)")
    p_ls.add_argument("--cryogenic", action="store_true")
    p_ls.add_argument("--storable", action="store_true")
    sub.add_parser("list-propellants", help="Alias of list")

    sub.add_parser("clear-cache", help="Clear SQLite cache")

    args = parser.parse_args(argv)
    cmd = args.command

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
    elif not args.verbose:
        print(r.summary())
    return 0


def _cmd_scan_of(args: argparse.Namespace) -> int:
    from propwrap import Mixture

    fuel, ox = _fuel_ox(args)
    m = Mixture(fuel, ox)
    rng = tuple(args.range) if args.range else None
    sw = m.scan_of(
        rng,  # type: ignore[arg-type]
        pc=args.pc,
        eps=args.eps,
        plot=args.plot,
        save=args.save,
        verbose=not args.json,
    )
    if args.json:
        print(sw.model_dump_json(indent=2))
    return 0


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

    rows = []
    for combo in args.combos.split(","):
        fuel, ox = combo.strip().split("/", 1)
        r = Mixture(fuel.strip(), ox.strip()).evaluate(
            of=args.of, pc=args.pc, eps=args.eps
        )
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

    if getattr(args, "cryogenic", False):
        for r in list_registry(storage="cryogenic"):
            print(f"{r.kind:9} {r.name}")
        return 0
    if getattr(args, "storable", False):
        for r in list_registry(storage="storable"):
            print(f"{r.kind:9} {r.name}")
        return 0
    data = list_propellants()
    print("Fuels:", ", ".join(data["fuels"]))
    print("Oxidizers:", ", ".join(data["oxidizers"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
