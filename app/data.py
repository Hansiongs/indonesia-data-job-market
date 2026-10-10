"""Data loading and filtering layer for the Glints Job Intel dashboard.

This module is the *only* place the dashboard talks to raw disk. It exposes
four pure-function building blocks:

* :func:`load_master_dataset` — load the committed demo snapshot or local output.
* :func:`build_skill_columns` — pivot any boolean / ``is_*`` columns into a
  clean ``skill_<name>`` matrix for the skills tab.
* :func:`filter_dataframe` — apply sidebar filters (role / city / work method
  / experience / search query).
* :func:`compute_summary_stats` — produce the KPI tile values shown at the
  top of the dashboard.

The module deliberately depends on :mod:`streamlit` only for caching; the
filter / summary functions are pure and side-effect free so they are easy
to unit-test.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Final

import pandas as pd
import streamlit as st

# Default location of the upstream pipeline's master dataset, relative to the
# repository root. Kept as a module-level constant so tests can monkey-patch
# it without re-importing the module.
DEFAULT_MASTER_PATH: Final[Path] = Path("data/processed/master_dataset_eda.csv")

# Anonymised sample committed for fresh clones without scraped data.
SAMPLE_MASTER_PATH: Final[Path] = Path("data/sample/sample_master_dataset.csv")

# Columns that identify boolean skill flags in the production schema.
_IS_SKILL_PREFIX: Final[str] = "is_"
_SKILL_PREFIX: Final[str] = "skill_"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def load_master_dataset(path: Path | str | None = None) -> pd.DataFrame:
    """Load the cleaned master dataset, raising FileNotFoundError if missing.

    When no ``path`` is supplied the loader first looks for the production
    master at :data:`DEFAULT_MASTER_PATH`; if absent it falls back to the
    anonymised sample committed at :data:`SAMPLE_MASTER_PATH`. This makes
    the dashboard runnable on a fresh clone without scraping.
    """
    target = Path(path) if path is not None else DEFAULT_MASTER_PATH
    if not target.exists():
        if path is None and SAMPLE_MASTER_PATH.exists():
            return pd.read_csv(SAMPLE_MASTER_PATH)
        raise FileNotFoundError(
            f"Master dataset not found at {target}. "
            "Restore the demo snapshot or run `make pipeline` after preparing a raw scrape."
        )
    return pd.read_csv(target)


# ---------------------------------------------------------------------------
# Skill column extraction
# ---------------------------------------------------------------------------


def _is_skill_column(series: pd.Series, name: str) -> bool:
    if name.startswith(_IS_SKILL_PREFIX):
        return True
    if name.startswith(_SKILL_PREFIX):
        return True
    return bool(pd.api.types.is_bool_dtype(series))


def build_skill_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Expand ``is_*`` / boolean skill flags into a ``skill_<name>`` matrix."""
    out = df.copy()
    skill_cols: list[str] = []

    for col in df.columns:
        if not _is_skill_column(df[col], col):
            continue
        if col.startswith(_SKILL_PREFIX):
            new_name = col
        elif col.startswith(_IS_SKILL_PREFIX):
            # is_python -> skill_python
            new_name = f"{_SKILL_PREFIX}{col[len(_IS_SKILL_PREFIX):]}"
        else:
            # boolean dtype but no prefix: synthesise a name.
            new_name = f"{_SKILL_PREFIX}{col}"

        if new_name not in out.columns:
            out[new_name] = df[col].astype(bool)
        skill_cols.append(new_name)

    return out, skill_cols


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def filter_dataframe(
    df: pd.DataFrame,
    *,
    role: list[str] | None,
    city: list[str] | None,
    work_method: list[str] | None,
    experience_band: tuple[int, int] | None,
    search_query: str | None,
) -> pd.DataFrame:
    """Apply sidebar filters; multi-selects are OR, empty selection = no filter."""
    if df.empty:
        return df.copy()

    out = df

    if role:
        out = out[out["keyword"].isin(role)]
    if city:
        out = out[out["city_clean"].isin(city)]
    if work_method:
        out = out[out["workplace_type"].isin(work_method)]

    if experience_band is not None:
        lo, hi = experience_band
        out = out[(out["exp_min_years"] >= lo) & (out["exp_min_years"] <= hi)]

    if search_query:
        needle = str(search_query).strip().lower()
        if needle:
            title_hit = out["job_title"].astype(str).str.lower().str.contains(needle, na=False)
            company_hit = out["company_name"].astype(str).str.lower().str.contains(needle, na=False)
            out = out[title_hit | company_hit]

    return out


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


def compute_summary_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute KPI tile values shown at the top of the dashboard."""
    if df.empty:
        return {
            "total_jobs": 0,
            "unique_companies": 0,
            "median_salary_idr": 0.0,
            "remote_share_pct": 0.0,
            "top_role": "n/a",
            "top_city": "n/a",
        }

    total_jobs = len(df)
    unique_companies = int(df["company_name"].nunique())

    salary = pd.to_numeric(df.get("salary_avg", pd.Series(dtype=float)), errors="coerce")
    median_salary = float(salary.median()) if salary.notna().any() else 0.0

    # Remote share is derived from ``workplace_type`` (canonical column)
    # so this works even when the upstream pipeline did not emit a separate
    # ``is_remote`` boolean. ``is_remote`` is still respected if it happens
    # to be present, so legacy callers keep working.
    if "workplace_type" in df.columns and df["workplace_type"].notna().any():
        is_remote_series = df["workplace_type"].astype(str).str.lower() == "remote"
        remote_share = float(is_remote_series.mean() * 100.0)
    elif "is_remote" in df.columns and df["is_remote"].notna().any():
        remote_share = float(df["is_remote"].astype(bool).mean() * 100.0)
    else:
        remote_share = 0.0

    top_role = _top_value(df.get("keyword"))
    top_city = _top_value(df.get("city_clean"))

    return {
        "total_jobs": total_jobs,
        "unique_companies": unique_companies,
        "median_salary_idr": median_salary,
        "remote_share_pct": remote_share,
        "top_role": top_role,
        "top_city": top_city,
    }


def compute_market_insights(df: pd.DataFrame) -> dict[str, Any]:
    """Return plain-language metrics used by the dashboard insight cards."""
    if df.empty:
        return {
            "top_skill": "n/a",
            "top_skill_share_pct": 0.0,
            "top_city_share_pct": 0.0,
            "fresh_graduate_share_pct": 0.0,
            "salary_disclosure_pct": 0.0,
        }

    skill_cols = [
        col
        for col in df.columns
        if col.startswith(_SKILL_PREFIX) or col.startswith(_IS_SKILL_PREFIX)
    ]
    if skill_cols:
        skill_values = df[skill_cols].apply(pd.to_numeric, errors="coerce").fillna(False)
        skill_counts = skill_values.astype(bool).sum().sort_values(ascending=False)
        top_skill_column = str(skill_counts.index[0])
        top_skill = top_skill_column.removeprefix(_SKILL_PREFIX).removeprefix(_IS_SKILL_PREFIX)
        top_skill_share = float(skill_counts.iloc[0] / len(df) * 100.0)
    else:
        top_skill = "n/a"
        top_skill_share = 0.0

    city_share = 0.0
    if "city_clean" in df.columns:
        city_counts = df["city_clean"].dropna().astype(str).value_counts()
        if not city_counts.empty:
            city_share = float(city_counts.iloc[0] / len(df) * 100.0)

    fresher_share = 0.0
    if "exp_min_years" in df.columns:
        experience = pd.to_numeric(df["exp_min_years"], errors="coerce")
        fresher_share = float(experience.eq(0).mean() * 100.0)

    salary_disclosure = 0.0
    if "salary_avg" in df.columns:
        salary = pd.to_numeric(df["salary_avg"], errors="coerce")
        salary_disclosure = float(salary.notna().mean() * 100.0)

    return {
        "top_skill": top_skill,
        "top_skill_share_pct": top_skill_share,
        "top_city_share_pct": city_share,
        "fresh_graduate_share_pct": fresher_share,
        "salary_disclosure_pct": salary_disclosure,
    }


def _top_value(series: pd.Series | None) -> str:
    if series is None or series.empty:
        return "n/a"
    counts = series.dropna().astype(str).value_counts()
    if counts.empty:
        return "n/a"
    return str(counts.index[0])


__all__ = [
    "DEFAULT_MASTER_PATH",
    "build_skill_columns",
    "compute_market_insights",
    "compute_summary_stats",
    "filter_dataframe",
    "load_master_dataset",
]
