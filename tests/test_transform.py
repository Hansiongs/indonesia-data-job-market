"""Tests for :mod:`glints_scraper.transform`.

The transform module turns raw Glints job-detail rows into the canonical
master schema. Each public helper gets at least one happy-path and one
edge-case test; :func:`transform` itself is exercised end-to-end on a
small in-memory frame so we cover the column reordering and dropping.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from glints_scraper.transform import (
    SKILL_CATALOG,
    detect_skills,
    extract_city,
    parse_education,
    parse_employment,
    parse_experience,
    parse_salary,
    parse_workplace,
    transform,
)

# ---------------------------------------------------------------------------
# parse_salary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Rp 10.000.000 - 15.000.000 / bulan", (10_000_000.0, 15_000_000.0)),
        ("Rp 8.500.000", (8_500_000.0, 8_500_000.0)),
        ("Dirahasiakan", (np.nan, np.nan)),
        ("USD 2,000", (np.nan, np.nan)),  # non-IDR filtered upstream; parser must be safe
        ("", (np.nan, np.nan)),
        ("bogus", (np.nan, np.nan)),
    ],
)
def test_parse_salary(raw: str, expected: tuple[float, float]) -> None:
    """parse_salary handles ranges, flats, undisclosed, garbage."""
    lo, hi = parse_salary(raw)
    if np.isnan(expected[0]):
        assert np.isnan(lo)
        assert np.isnan(hi)
    else:
        assert lo == expected[0]
        assert hi == expected[1]


def test_parse_salary_handles_nan_input() -> None:
    """Non-string inputs (NaN/float) must not crash."""
    assert (np.isnan(parse_salary(np.nan)[0]))
    assert (np.isnan(parse_salary(12345.0)[0]))


# ---------------------------------------------------------------------------
# parse_experience
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2-3 tahun", 2),
        ("5+ tahun", 5),
        ("kurang dari 1 tahun", 0),
        ("less than a year experience", 0),
        ("fresh graduate", 0),
        ("1 year experience", 1),
        ("", None),
        (np.nan, None),
    ],
)
def test_parse_experience(raw: object, expected: int | None) -> None:
    """parse_experience extracts the floor year from free-text input."""
    assert parse_experience(raw) == expected


# ---------------------------------------------------------------------------
# parse_education
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("S1 Manajemen", "S1"),
        ("Bachelor Degree in Computer Science", "S1"),
        ("Gelar Sarjana", "S1"),
        ("S2 Magister", "S2"),
        ("Master's degree", "S2"),
        ("D3 Akuntansi", "D3/Diploma"),
        ("Diploma 4", "D3/Diploma"),
        ("SMA/SMK", "SMA/SMK"),
        ("High School graduate", "SMA/SMK"),
        ("PhD", "Other"),
        ("", "Other"),
        (np.nan, "Other"),
    ],
)
def test_parse_education(raw: object, expected: str) -> None:
    """parse_education maps recruiter spellings to canonical buckets."""
    assert parse_education(raw) == expected


def test_parse_education_s2_beats_s1() -> None:
    """S2 must take precedence over S1 in the pattern order."""
    # "Bachelor" matches S1, but "S2" should still win.
    assert parse_education("S2 with Bachelor background") == "S2"


# ---------------------------------------------------------------------------
# parse_employment
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Full-time", "Full-time"),
        ("Penuh Waktu", "Full-time"),
        ("Kontrak 6 bulan", "Contract"),
        ("Contract position", "Contract"),
        ("Magang", "Intern"),
        ("Internship", "Intern"),
        ("Freelance project", "Freelance"),
        ("Paruh Waktu", "Part-time"),
        ("Volunteer", "Other"),
        ("", "Other"),
        (np.nan, "Other"),
    ],
)
def test_parse_employment(raw: object, expected: str) -> None:
    """parse_employment classifies job_method strings."""
    assert parse_employment(raw) == expected


# ---------------------------------------------------------------------------
# parse_workplace
# ---------------------------------------------------------------------------


def test_parse_workplace_remote_english() -> None:
    assert parse_workplace("Data Analyst", "Fully remote position, work from home") == "Remote"


def test_parse_workplace_remote_indonesian() -> None:
    assert parse_workplace("Data Analyst", "Bisa kerja dari jarak jauh") == "Remote"


def test_parse_workplace_hybrid() -> None:
    assert parse_workplace("Engineer", "Hybrid working arrangement with flexible days") == "Hybrid"


def test_parse_workplace_onsite_default() -> None:
    assert parse_workplace("Data Engineer", "Office-based in Jakarta") == "On-site"


def test_parse_workplace_remote_wins_over_hybrid() -> None:
    """When both keyword groups appear, Remote takes precedence."""
    text = "Hybrid but mostly remote work from home with flexible days"
    assert parse_workplace("Engineer", text) == "Remote"


def test_parse_workplace_handles_nan() -> None:
    assert parse_workplace(np.nan, np.nan) == "On-site"


# ---------------------------------------------------------------------------
# detect_skills
# ---------------------------------------------------------------------------


def test_detect_skills_python_and_sql() -> None:
    flags = detect_skills("Looking for python and SQL expert", "Python, SQL, Tableau")
    assert flags["skill_python"] is True
    assert flags["skill_sql"] is True
    assert flags["skill_tableau"] is True
    assert flags["skill_r"] is False


def test_detect_skills_power_bi_phrase() -> None:
    """Multi-word tools match as literal substrings."""
    flags = detect_skills("Experience with Power BI dashboards", "")
    assert flags["skill_power_bi"] is True


def test_detect_skills_handles_empty_corpus() -> None:
    flags = detect_skills("", "")
    assert all(flag is False for flag in flags.values())


def test_detect_skills_handles_nan_inputs() -> None:
    flags = detect_skills(np.nan, np.nan)  # type: ignore[arg-type]
    assert all(flag is False for flag in flags.values())


def test_skill_catalog_has_32_entries() -> None:
    """The skill catalogue is the documented surface area; pin the count."""
    assert len(SKILL_CATALOG) == 32


# ---------------------------------------------------------------------------
# extract_city
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Jakarta, Indonesia", "Jakarta"),
        ("Bandung", "Bandung"),
        ("Surabaya, East Java", "Surabaya"),
        ("Daerah Istimewa Yogyakarta", "Yogyakarta"),
        ("Jogja", "Yogyakarta"),
        ("Bali", "Denpasar"),
        ("Remote", "Remote"),
        ("Antarctica", None),
        ("", None),
        (np.nan, None),
    ],
)
def test_extract_city(raw: object, expected: str | None) -> None:
    """extract_city maps raw location strings to canonical cities."""
    assert extract_city(raw) == expected  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# transform (end-to-end)
# ---------------------------------------------------------------------------


def _build_raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "keyword": ["data analyst", "data engineer", "data scientist"],
            "job_title": ["Data Analyst", "Data Engineer", "Senior Data Scientist"],
            "company_name": ["Acme", "Beta", "Gamma"],
            "job_location": ["Jakarta", "Bandung", "Remote"],
            "job_description": [
                "Looking for python and sql expert with Power BI experience",
                "spark airflow AWS pipeline engineer",
                "machine learning deep learning pytorch role, fully remote work from home",
            ],
            "skill_tags": ["Python, SQL", "Spark, Airflow", "ML, PyTorch"],
            "job_salary": [
                "Rp 10.000.000 - 15.000.000 / bulan",
                "Dirahasiakan",
                "Rp 25.000.000",
            ],
            "job_education": ["S1 Statistika", "Bachelor Degree", "S2 Magister"],
            "job_method": ["Full-time", "Kontrak", "Penuh Waktu"],
            "job_experience": ["2-3 tahun", "kurang dari 1 tahun", "5+ tahun"],
        }
    )


def test_transform_emits_canonical_columns() -> None:
    out = transform(_build_raw_frame())
    expected_core = {
        "keyword", "job_title", "company_name", "city_clean",
        "salary_min", "salary_max", "salary_avg",
        "exp_min_years", "employment_type", "workplace_type",
        "job_education_clean",
    }
    assert expected_core.issubset(out.columns)
    # All 32 skill flags present.
    skill_cols = [c for c in out.columns if c.startswith("skill_")]
    assert len(skill_cols) == 32


def test_transform_drops_redundant_raw_columns() -> None:
    out = transform(_build_raw_frame())
    for col in ("job_salary", "job_education", "job_method", "job_experience"):
        assert col not in out.columns


def test_transform_salary_parsing() -> None:
    out = transform(_build_raw_frame())
    assert out.loc[0, "salary_min"] == 10_000_000.0
    assert out.loc[0, "salary_max"] == 15_000_000.0
    assert out.loc[0, "salary_avg"] == 12_500_000.0
    assert pd.isna(out.loc[1, "salary_avg"])  # undisclosed
    assert out.loc[2, "salary_avg"] == 25_000_000.0  # flat salary


def test_transform_experience_parsing() -> None:
    out = transform(_build_raw_frame())
    assert out.loc[0, "exp_min_years"] == 2
    assert out.loc[1, "exp_min_years"] == 0  # fresh grad
    assert out.loc[2, "exp_min_years"] == 5


def test_transform_skill_detection() -> None:
    out = transform(_build_raw_frame())
    assert bool(out.loc[0, "skill_python"]) is True
    assert bool(out.loc[0, "skill_sql"]) is True
    assert bool(out.loc[0, "skill_power_bi"]) is True
    assert bool(out.loc[1, "skill_spark"]) is True
    assert bool(out.loc[1, "skill_airflow"]) is True
    assert bool(out.loc[2, "skill_machine_learning"]) is True
    assert bool(out.loc[2, "skill_pytorch"]) is True


def test_transform_education_normalisation() -> None:
    out = transform(_build_raw_frame())
    assert out.loc[0, "job_education_clean"] == "S1"
    assert out.loc[1, "job_education_clean"] == "S1"
    assert out.loc[2, "job_education_clean"] == "S2"


def test_transform_employment_classification() -> None:
    out = transform(_build_raw_frame())
    assert out.loc[0, "employment_type"] == "Full-time"
    assert out.loc[1, "employment_type"] == "Contract"
    assert out.loc[2, "employment_type"] == "Full-time"


def test_transform_workplace_classification() -> None:
    out = transform(_build_raw_frame())
    # No workplace keywords in row 0/1 -> On-site. Row 2 says "Remote" in location.
    assert out.loc[0, "workplace_type"] == "On-site"
    assert out.loc[1, "workplace_type"] == "On-site"
    assert out.loc[2, "workplace_type"] == "Remote"


def test_transform_city_extraction() -> None:
    out = transform(_build_raw_frame())
    assert out.loc[0, "city_clean"] == "Jakarta"
    assert out.loc[1, "city_clean"] == "Bandung"
    assert out.loc[2, "city_clean"] == "Remote"


def test_transform_does_not_mutate_input() -> None:
    raw = _build_raw_frame()
    before = raw.copy(deep=True)
    _ = transform(raw)
    pd.testing.assert_frame_equal(raw, before)


def test_transform_drops_rows_missing_required_fields() -> None:
    raw = _build_raw_frame()
    raw.loc[0, "skill_tags"] = np.nan
    out = transform(raw)
    assert len(out) == 2
    # The surviving rows are the original rows 1 and 2.
    assert out["job_title"].tolist() == ["Data Engineer", "Senior Data Scientist"]


def test_transform_drops_closed_listings() -> None:
    raw = _build_raw_frame()
    raw.loc[0, "job_experience"] = "lowongan telah ditutup"
    out = transform(raw)
    # Closed row is dropped; surviving rows are the original rows 1 and 2.
    assert len(out) == 2
    assert out["job_title"].tolist() == ["Data Engineer", "Senior Data Scientist"]


def test_transform_works_on_empty_frame() -> None:
    out = transform(pd.DataFrame(columns=["job_salary", "skill_tags", "job_education",
                                          "job_method", "job_experience", "job_description",
                                          "job_title", "keyword", "company_name", "job_location"]))
    assert out.empty
    # Canonical columns should still be present even if empty.
    assert "skill_python" in out.columns
