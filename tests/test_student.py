"""Student-facing helpers: reports, presets, pc guardrails."""

from __future__ import annotations

from pathlib import Path

import pytest

from propwrap import Case, Mixture, figure_caption, write_lab_report
from propwrap.errors import PropwrapError


def test_case_presets() -> None:
    lab = Case.student_lab()
    assert abs(lab.pc_bar - 70) < 1e-6
    assert lab.eps == 20.0
    boost = Case.booster()
    assert boost.pc_bar == 100.0
    up = Case.upper_stage()
    assert up.eps == 80.0


def test_pc_bar_mistaken_as_pa_raises() -> None:
    m = Mixture("RP-1", "LOX", apply_cryo_defaults=False)
    with pytest.raises(PropwrapError, match="pc_bar"):
        m.evaluate(of=2.56, pc=70, eps=20)


def test_figure_caption() -> None:
    s = figure_caption(
        fig_num=1,
        title="Isp vs O/F",
        fuel="RP1",
        oxidizer="LOX",
        pc_bar=70,
        eps=20,
    )
    assert "Fig. 1" in s and "70" in s and "theoretical" in s.lower()


def test_to_markdown() -> None:
    r = Mixture("RP-1", "LOX", apply_cryo_defaults=False).evaluate(
        of=2.56, pc_bar=70, eps=20
    )
    md = r.to_markdown()
    assert "Isp vac" in md and "theoretical" in md.lower()


def test_write_lab_report(tmp_path: Path) -> None:
    out = write_lab_report(
        tmp_path / "lab",
        fuel="RP-1",
        oxidizer="LOX",
        of_ratio=2.56,
        pc_bar=70,
        eps=20,
        of_range=(2.2, 2.8, 0.3),
        student_name="TestStudent",
        compare_pairs=["RP-1/LOX", "CH4/LOX"],
        make_plots=True,
    )
    assert (out / "summary.md").is_file()
    assert (out / "assumptions.txt").is_file()
    assert (out / "point_performance.csv").is_file()
    assert (out / "of_scan.csv").is_file()
    assert (out / "fig01_of_scan.png").is_file()
    text = (out / "summary.md").read_text(encoding="utf-8")
    assert "TestStudent" in text
    assert "theoretical" in text.lower()


def test_typical_of_in_registry() -> None:
    from propwrap import get_propellant

    assert get_propellant("LH2").typical_of_range == (4.5, 6.5)
    assert get_propellant("RP-1").typical_of_range is not None
