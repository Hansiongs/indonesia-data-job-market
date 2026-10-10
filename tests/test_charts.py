"""Tests for :mod:`app.charts`.

Right now this module focuses on :func:`pretty_skill_label` — the only
public function that produces pure strings (the rest return Plotly
Figures and would need snapshot fixtures). The label helper is the single
source of truth for human-readable skill names across every chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.charts import (  # noqa: E402
    CATEGORICAL_PALETTE,
    SEQUENTIAL_PALETTE,
    plot_top_skills_bar,
    pretty_skill_label,
)


@pytest.mark.parametrize(
    "column, expected",
    [
        ("skill_python", "Python"),
        ("skill_sql", "SQL"),
        ("skill_r", "R"),
        ("skill_power_bi", "Power BI"),
        ("skill_scikit_learn", "Scikit-learn"),
        ("skill_machine_learning", "Machine Learning"),
        ("skill_etl", "ETL"),
        ("skill_nlp", "NLP"),
        ("skill_aws", "AWS"),
        ("skill_postgres", "Postgres"),
        ("skill_postgresql", "PostgreSQL"),
        ("skill_mongodb", "MongoDB"),
        ("skill_tensorflow", "TensorFlow"),
        ("skill_pytorch", "PyTorch"),
        ("skill_numpy", "NumPy"),
        # Legacy ``is_*`` prefix is also accepted.
        ("is_python", "Python"),
        ("is_sql", "SQL"),
        ("is_power_bi", "Power BI"),
        # Idempotent on already-clean labels (e.g. when build_skill_columns
        # has already stripped the prefix).
        ("python", "Python"),
    ],
)
def test_pretty_skill_label(column: str, expected: str) -> None:
    """Skill labels render in title case with acronyms preserved."""
    assert pretty_skill_label(column) == expected


def test_pretty_skill_label_unknown_falls_back_to_title() -> None:
    """Skills not in the override map get a clean title-cased fallback."""
    assert pretty_skill_label("skill_docker") == "Docker"
    assert pretty_skill_label("skill_kubernetes") == "Kubernetes"
    assert pretty_skill_label("skill_computer_vision") == "Computer Vision"


def test_pretty_skill_label_strips_either_prefix() -> None:
    """Either ``skill_`` or ``is_`` prefix must be stripped."""
    assert pretty_skill_label("skill_sql") == pretty_skill_label("is_sql")


def test_palettes_are_nonempty() -> None:
    """The exported palettes must always carry at least one entry."""
    assert len(CATEGORICAL_PALETTE) > 0
    assert isinstance(SEQUENTIAL_PALETTE, str) and SEQUENTIAL_PALETTE


def test_top_skills_bar_uses_pretty_labels() -> None:
    """The bar chart's y-axis must render human-readable skill names, not raw column IDs.

    Regression guard for the bug where ``skill_python`` / ``is_sql`` leaked
    into the chart instead of ``Python`` / ``SQL``.
    """
    import pandas as pd

    df = pd.DataFrame(
        {
            "keyword": ["data analyst"] * 3,
            "job_title": ["A", "B", "C"],
            "skill_python": [True, True, False],
            "skill_sql": [True, False, True],
            "skill_power_bi": [True, False, False],
        }
    )
    fig: go.Figure = plot_top_skills_bar(df, top_n=3)
    # The y-axis tick labels are stored on the layout (Plotly uses tickvals
    # + ticktext for categorical axes).
    ticktext: list[str] = []
    for axis in (fig.layout.yaxis,):
        if axis is not None and getattr(axis, "ticktext", None):
            ticktext = list(axis.ticktext)
            break
    # Fallback: read from the bar trace's y array.
    if not ticktext:
        for trace in fig.data:
            y_vals = getattr(trace, "y", None)
            if y_vals is not None:
                ticktext = list(y_vals)
                break
    assert ticktext, "expected at least one tick on the y-axis"
    for label in ticktext:
        assert not label.startswith("skill_"), f"raw column leaked: {label!r}"
        assert not label.startswith("is_"), f"raw column leaked: {label!r}"
