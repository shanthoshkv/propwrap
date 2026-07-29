"""Student lab report starter — writes a full homework folder.

Usage (from repo root, venv active):

    python examples/lab_report_starter.py
    python examples/lab_report_starter.py --name Ada --preset methalox

Same as:  propwrap homework kerolox --name Ada
"""

from __future__ import annotations

import argparse
from pathlib import Path

from propwrap.reports import homework_folder_name, write_lab_report


PRESETS = {
    "kerolox": dict(
        fuel="RP-1",
        oxidizer="LOX",
        of_ratio=2.56,
        pc_bar=70.0,
        eps=20.0,
        compare=["RP-1/LOX", "CH4/LOX", "LH2/LOX"],
    ),
    "methalox": dict(
        fuel="CH4",
        oxidizer="LOX",
        of_ratio=3.0,
        pc_bar=100.0,
        eps=25.0,
        compare=["CH4/LOX", "RP-1/LOX", "LH2/LOX"],
    ),
    "hydrolox": dict(
        fuel="LH2",
        oxidizer="LOX",
        of_ratio=5.5,
        pc_bar=100.0,
        eps=40.0,
        compare=["LH2/LOX", "CH4/LOX", "RP-1/LOX"],
    ),
}


def main() -> None:
    p = argparse.ArgumentParser(description="Generate a propwrap student lab pack")
    p.add_argument("--name", default="Student")
    p.add_argument("--preset", choices=list(PRESETS), default="kerolox")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    cfg = PRESETS[args.preset]
    out = args.out or homework_folder_name(args.name, args.preset)
    path = write_lab_report(
        out,
        fuel=cfg["fuel"],
        oxidizer=cfg["oxidizer"],
        of_ratio=cfg["of_ratio"],
        pc_bar=cfg["pc_bar"],
        eps=cfg["eps"],
        student_name=args.name,
        compare_pairs=cfg["compare"],
        make_plots=True,
    )
    print("Wrote lab pack to:", Path(path).resolve())
    print("Open summary.md and read assumptions.txt before interpreting numbers.")


if __name__ == "__main__":
    main()
