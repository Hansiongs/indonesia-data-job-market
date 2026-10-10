"""Smoke tests for the Streamlit dashboard layer.

These tests focus on the pure-Python building blocks (``app.data``,
``app.charts``, ``app.geo``) — the Streamlit ``dashboard.py`` entry
point is exercised manually via ``streamlit run`` because spinning up
the Streamlit test runner is out of scope here.

The tests deliberately avoid any network calls and rely on a small
inline fixture that matches the production schema, so they can run
anywhere without scraping or running the upstream pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

# Ensure repo root is on sys.path so ``import app.*`` works regardless of
# where pytest is invoked from.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.charts import (  # noqa: E402
    plot_education_distribution,
    plot_real_tech_stack_landscape,
    plot_remote_luxury_comparison,
    plot_role_distribution,
    plot_salary_distribution,
    plot_salary_reality_curve,
    plot_skill_burden_by_career_stage,
    plot_skill_cooccurrence_heatmap,
    plot_top_skills_bar,
)
from app.data import (  # noqa: E402
    build_skill_columns,
    compute_market_insights,
    compute_summary_stats,
    filter_dataframe,
    load_master_dataset,
)
from app.geo import city_summary, plot_geo_map  # noqa: E402

# ---------------------------------------------------------------------------
# Inline fixture — matches the production schema (post-pipeline)
# ---------------------------------------------------------------------------


def _build_fixture_df(n: int = 60, seed: int = 7) -> pd.DataFrame:
    """Return a tiny in-memory dataset that mirrors the production columns.

    Keeps tests self-contained (no disk CSV, no synthetic generator).
    """
    rng = np.random.default_rng(seed)
    roles = ["data analyst", "data scientist", "data engineer", "machine learning"]
    cities = ["Jakarta", "Bandung", "Surabaya", "Yogyakarta"]
    workplaces = ["On-site", "Remote", "Hybrid"]
    companies = ["PT TestCo", "Glints", "Tokopedia", "Gojek"]
    df = pd.DataFrame(
        {
            "keyword": rng.choice(roles, size=n).tolist(),
            "job_title": [f"Job {i}" for i in range(n)],
            "company_name": rng.choice(companies, size=n).tolist(),
            "city_clean": rng.choice(cities, size=n).tolist(),
            "salary_avg": rng.integers(5_000_000, 30_000_000, size=n).tolist(),
            "is_remote": rng.choice([True, False], size=n).tolist(),
            "exp_min_years": rng.integers(0, 6, size=n).tolist(),
            "exp_max_years": [int(x) + 2 for x in rng.integers(0, 6, size=n).tolist()],
            "workplace_type": rng.choice(workplaces, size=n).tolist(),
            "job_education_clean": rng.choice(["S1", "S2", "D3"], size=n).tolist(),
            "job_method": ["Full-time"] * n,
            "posted_date": pd.to_datetime("2026-01-01") + pd.to_timedelta(
                rng.integers(0, 90, size=n), unit="D"
            ),
        }
    )
    # 8 skill flags — enough to exercise the skill-column code path.
    for i in range(8):
        df[f"skill_skill_{i}"] = rng.choice([True, False], size=n).tolist()
    return df


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """Return a small in-memory dataset that matches the production schema."""
    return _build_fixture_df()


@pytest.fixture()
def sample_with_skills(sample_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return ``(df, skill_cols)`` after passing through ``build_skill_columns``."""
    return build_skill_columns(sample_df)


@pytest.fixture()
def master_csv(tmp_path: Path) -> Path:
    """Write a tiny CSV fixture to ``tmp_path`` and return its path."""
    df = _build_fixture_df(n=40)
    csv_path = tmp_path / "master.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


# ---------------------------------------------------------------------------
# 1. load_master_dataset
# ---------------------------------------------------------------------------


def test_load_master_dataset_returns_dataframe(master_csv: Path) -> None:
    """``load_master_dataset`` reads a real CSV and returns a DataFrame."""
    df: pd.DataFrame = load_master_dataset(path=master_csv)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "keyword" in df.columns


def test_load_master_dataset_missing_raises(tmp_path: Path) -> None:
    """Missing CSV must raise ``FileNotFoundError`` with a helpful message."""
    missing = tmp_path / "absent.csv"
    with pytest.raises(FileNotFoundError, match="Restore the demo snapshot"):
        load_master_dataset(path=missing)


# ---------------------------------------------------------------------------
# 2. build_skill_columns
# ---------------------------------------------------------------------------


def test_build_skill_columns_extracts_correct_count(sample_df: pd.DataFrame) -> None:
    """build_skill_columns should pick up every ``skill_`` / ``is_`` column."""
    _, skill_cols = build_skill_columns(sample_df)
    assert len(skill_cols) >= 8, f"expected 8+ skill columns, got {len(skill_cols)}"
    # All returned names should use the canonical 'skill_' prefix.
    for name in skill_cols:
        assert name.startswith("skill_"), f"unexpected skill column: {name}"


# ---------------------------------------------------------------------------
# 3. filter_dataframe — role
# ---------------------------------------------------------------------------


def test_filter_dataframe_role(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """Filtering by role should only return rows matching that role."""
    df, _ = sample_with_skills
    target = "data scientist"
    filtered = filter_dataframe(
        df,
        role=[target],
        city=None,
        work_method=None,
        experience_band=None,
        search_query=None,
    )
    assert not filtered.empty
    assert (filtered["keyword"] == target).all()


# ---------------------------------------------------------------------------
# 4. filter_dataframe — search
# ---------------------------------------------------------------------------


def test_filter_dataframe_search(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """Free-text search must match case-insensitively across title or company."""
    df, _ = sample_with_skills
    target = "tokopedia"
    filtered = filter_dataframe(
        df,
        role=None,
        city=None,
        work_method=None,
        experience_band=None,
        search_query=target,
    )
    if not filtered.empty:
        title_hit = filtered["job_title"].astype(str).str.lower().str.contains(target, na=False)
        company_hit = filtered["company_name"].astype(str).str.lower().str.contains(target, na=False)
        assert (title_hit | company_hit).all()


# ---------------------------------------------------------------------------
# 5. compute_summary_stats
# ---------------------------------------------------------------------------


def test_compute_summary_stats_keys(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """compute_summary_stats returns the documented key set."""
    df, _ = sample_with_skills
    stats: dict[str, Any] = compute_summary_stats(df)

    expected = {
        "total_jobs",
        "unique_companies",
        "median_salary_idr",
        "remote_share_pct",
        "top_role",
        "top_city",
    }
    assert expected.issubset(stats.keys()), f"missing keys: {expected - set(stats.keys())}"
    assert stats["total_jobs"] == len(df)


def test_compute_summary_stats_empty() -> None:
    """compute_summary_stats must not blow up on an empty DataFrame."""
    empty = pd.DataFrame()
    stats = compute_summary_stats(empty)
    assert stats["total_jobs"] == 0
    assert stats["unique_companies"] == 0
    assert stats["top_role"] == "n/a"


def test_compute_market_insights_returns_reader_friendly_metrics(
    sample_df: pd.DataFrame,
) -> None:
    """Market insight metrics should work with the cleaned dashboard schema."""
    df = sample_df.iloc[:3].copy()
    for column in [column for column in df if column.startswith("skill_")]:
        df[column] = False
    df["skill_sql"] = [True, True, False]
    df["skill_python"] = [False, True, False]

    insights = compute_market_insights(df)

    assert insights["top_skill"] == "sql"
    assert insights["top_skill_share_pct"] == pytest.approx(2 / 3 * 100)
    city_share = df["city_clean"].value_counts().iloc[0] / len(df) * 100
    fresher_share = (df["exp_min_years"] == 0).mean() * 100
    assert insights["top_city_share_pct"] == pytest.approx(city_share)
    assert insights["fresh_graduate_share_pct"] == pytest.approx(fresher_share)


def test_compute_market_insights_empty() -> None:
    """Empty datasets should produce stable insight defaults."""
    insights = compute_market_insights(pd.DataFrame())

    assert insights["top_skill"] == "n/a"
    assert insights["salary_disclosure_pct"] == 0


# ---------------------------------------------------------------------------
# 6. plot_salary_distribution
# ---------------------------------------------------------------------------


def test_chart_salary_distribution_returns_figure(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """Salary distribution should return a Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_salary_distribution(df, by="keyword")
    assert isinstance(fig, go.Figure)
    # Should have at least one trace.
    assert len(fig.data) >= 1


# ---------------------------------------------------------------------------
# 7. plot_top_skills_bar
# ---------------------------------------------------------------------------


def test_chart_top_skills_bar_returns_figure(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """Top skills bar should return a Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_top_skills_bar(df, top_n=5)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


# ---------------------------------------------------------------------------
# 8. plot_skill_cooccurrence_heatmap
# ---------------------------------------------------------------------------


def test_chart_skill_cooccurrence_heatmap_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Skill co-occurrence heatmap should return a Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_skill_cooccurrence_heatmap(df, top_n=4)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


# ---------------------------------------------------------------------------
# 9. city_summary grouping
# ---------------------------------------------------------------------------


def test_city_summary_returns_grouped_dataframe(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """city_summary returns one row per city with the documented columns."""
    df, _ = sample_with_skills
    summary = city_summary(df)

    expected_cols = {"count", "median_salary", "remote_pct", "top_role"}
    assert expected_cols.issubset(summary.columns)
    # At least one row.
    assert len(summary) >= 1
    # Sorted by count descending.
    counts = summary["count"].tolist()
    assert counts == sorted(counts, reverse=True)
    # Sum of per-city counts equals total rows.
    assert int(summary["count"].sum()) == len(df)


# ---------------------------------------------------------------------------
# 10. plot_geo_map
# ---------------------------------------------------------------------------


def test_geo_plot_returns_folium_map(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """plot_geo_map must return a folium.Map instance."""
    df, _ = sample_with_skills
    m = plot_geo_map(df)
    assert isinstance(m, folium.Map)


def test_plot_role_distribution_returns_figure(sample_with_skills: tuple[pd.DataFrame, list[str]]) -> None:
    """Role distribution chart should also return a Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_role_distribution(df)
    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Regression: remote_share derivation when the production schema is in play
# ---------------------------------------------------------------------------
#
# The production master dataset does NOT carry an ``is_remote`` column —
# the canonical source of truth is ``workplace_type``. The dashboard must
# derive the remote share from there (or gracefully fall back to 0) so it
# does not crash with "Label(s) ['is_remote'] do not exist".


@pytest.fixture()
def production_schema_df() -> pd.DataFrame:
    """Mimic the real master dataset: no ``is_remote`` column."""
    return pd.DataFrame(
        {
            "keyword": ["data analyst", "data engineer", "data analyst"],
            "job_title": ["A", "B", "C"],
            "company_name": ["Acme", "Beta", "Acme"],
            "city_clean": ["Jakarta", "Jakarta", "Bandung"],
            "salary_avg": [10_000_000, 15_000_000, 8_000_000],
            "workplace_type": ["Remote", "On-site", "Hybrid"],
            "exp_min_years": [2, 3, 1],
            "job_education_clean": ["S1", "S1", "S1"],
        }
    )


def test_city_summary_works_without_is_remote_column(production_schema_df: pd.DataFrame) -> None:
    """Regression: city_summary must not crash when ``is_remote`` is absent.

    Previously the dashboard raised ``KeyError: 'is_remote'`` because
    :func:`app.geo._city_aggregates` grouped by a column the production
    schema does not carry. Now it derives the remote share from
    ``workplace_type``.
    """
    summary = city_summary(production_schema_df)
    assert not summary.empty
    # 1 of 3 postings is Remote -> ~33.3% overall.
    overall_remote = float(
        (production_schema_df["workplace_type"].str.lower() == "remote").mean() * 100.0
    )
    # Weighted average of per-city remote_pct should equal overall_remote.
    weighted = (summary["remote_pct"] * summary["count"]).sum() / summary["count"].sum()
    assert abs(weighted - overall_remote) < 1e-6


def test_compute_summary_stats_works_without_is_remote_column(production_schema_df: pd.DataFrame) -> None:
    """Regression: remote_share_pct must reflect workplace_type when is_remote is absent."""
    stats = compute_summary_stats(production_schema_df)
    expected_remote_share = 1 / 3 * 100.0  # 1 of 3 rows is Remote
    assert abs(stats["remote_share_pct"] - expected_remote_share) < 1e-6


def test_city_summary_still_works_with_legacy_is_remote_column(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Legacy callers passing an explicit ``is_remote`` column keep working."""
    df, _ = sample_with_skills  # the existing fixture carries is_remote
    summary = city_summary(df)
    assert not summary.empty
    assert "remote_pct" in summary.columns


def test_chart_skill_burden_by_career_stage_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Skill burden by career stage should return a valid Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_skill_burden_by_career_stage(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_chart_salary_reality_curve_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Salary reality curve should return a valid Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_salary_reality_curve(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_chart_remote_luxury_comparison_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Remote luxury comparison should return a valid Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_remote_luxury_comparison(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_chart_real_tech_stack_landscape_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Real tech stack landscape should return a valid Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_real_tech_stack_landscape(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_chart_education_distribution_returns_figure(
    sample_with_skills: tuple[pd.DataFrame, list[str]],
) -> None:
    """Education distribution chart should return a valid Plotly figure."""
    df, _ = sample_with_skills
    fig = plot_education_distribution(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_dashboard_processed_dataset_loads_and_has_valid_schema() -> None:
    """Verify that the production processed dataset loads and passes pipeline checks."""
    df = load_master_dataset()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 430
    df, skill_cols = build_skill_columns(df)
    assert len(skill_cols) >= 30
    stats = compute_summary_stats(df)
    assert stats["total_jobs"] == 430

