"""Transform raw Glints job-detail scrapes into an analysis-ready master frame.

The cleaning logic used to live inline in ``clean.ipynb``; this module is a
Python extraction so it is unit-testable and reusable. The pipeline turns
the raw CSV produced by :mod:`glints_scraper.details` into the canonical
master schema documented in ``docs/schema.md``.

Pipeline stages:

1. Drop rows missing required fields (skill tags, education, method, experience).
2. Parse ``job_salary`` (IDR) into ``salary_min``, ``salary_max``, ``salary_avg``.
3. Drop closed listings ("telah ditutup") and parse ``exp_min_years``.
4. Detect skills across ``job_description + skill_tags`` -> 32 boolean flags.
5. Normalise ``job_education`` -> ``job_education_clean``.
6. Classify ``employment_type`` from ``job_method``.
7. Classify ``workplace_type`` from ``job_title + job_description``.

The single public entry point is :func:`transform`.

Notes on Indonesian text handling
---------------------------------

* "Dirahasiakan" means "undisclosed" — we keep the row but leave
  ``salary_min`` / ``salary_max`` as ``NaN`` so downstream code can drop or
  impute as needed.
* Salary parsing uses ``.split(" - ")`` (en-dash aware enough; recruiters
  consistently use ASCII hyphen-space-hyphen-space).
* Workplace detection looks for both Indonesian and English keywords because
  Glints postings mix languages freely.
"""
from __future__ import annotations

import re
from typing import Final

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Sentinel for undisclosed salaries in the raw ``job_salary`` field.
UNDISCLOSED_SALARY: Final[str] = "Dirahasiakan"

#: Marker for closed listings (Indonesian) in the ``job_experience`` field.
CLOSED_LISTING_MARKER: Final[str] = "telah ditutup"

#: Map of canonical education buckets -> regex fragments that match them.
#: Order matters: the first match wins, so more specific patterns (e.g. S2)
#: must come before more general ones (e.g. S1).
EDUCATION_PATTERNS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("S2", ("S2", "Magister", "Master")),
    ("S1", ("S1", "Sarjana", "Bachelor", "College Degree")),
    ("D3/Diploma", ("D1", "D2", "D3", "D4", "Diploma")),
    ("SMA/SMK", ("SMA", "SMK", "SLTA", "High School")),
)

#: Keywords for each employment type, scanned against ``job_method``.
EMPLOYMENT_PATTERNS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("Full-time", ("Penuh Waktu", "Full-time", "Full Time")),
    ("Part-time", ("Paruh Waktu", "Part-time", "Part Time")),
    ("Contract", ("Kontrak", "Contract")),
    ("Intern", ("Magang", "Intern", "Internship")),
    ("Freelance", ("Freelance",)),
)

#: Workplace detection: the order below sets the precedence when both
#: "remote" and "hybrid" keywords appear in the same posting (remote wins).
WORKPLACE_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "Remote": ("jarak jauh", "remote", "wfh", "wfa", "home-based", "work from home"),
    "Hybrid": ("hibrida", "hybrid", "fleksibel", "flexible"),
}

#: Skill catalogue — 32 tools, derived from the production master dataset
#: and documented in ``docs/schema.md``. Each entry maps the canonical
#: ``skill_<name>`` column to the list of substrings we scan for in the
#: combined description + skill_tags text. Multi-word phrases use a single
#: space (e.g. ``"power bi"``); single-word tools match as bare substrings.
SKILL_CATALOG: Final[dict[str, tuple[str, ...]]] = {
    "skill_python": ("python",),
    "skill_sql": ("sql",),
    "skill_r": (" r ", "(r)", " r,", " r.", "r language", "r programming"),
    "skill_tableau": ("tableau",),
    "skill_power_bi": ("power bi", "powerbi"),
    "skill_excel": ("excel",),
    "skill_aws": ("aws", "amazon web services"),
    "skill_gcp": ("gcp", "google cloud"),
    "skill_azure": ("azure",),
    "skill_spark": ("spark", "pyspark"),
    "skill_hadoop": ("hadoop",),
    "skill_kafka": ("kafka",),
    "skill_tensorflow": ("tensorflow",),
    "skill_pytorch": ("pytorch",),
    "skill_scikit_learn": ("scikit", "sklearn", "scikit-learn"),
    "skill_pandas": ("pandas",),
    "skill_numpy": ("numpy",),
    "skill_etl": ("etl",),
    "skill_airflow": ("airflow",),
    "skill_dbt": ("dbt",),
    "skill_postgres": ("postgres", "postgresql"),
    "skill_mongodb": ("mongodb", "mongo "),
    "skill_redis": ("redis",),
    "skill_docker": ("docker",),
    "skill_kubernetes": ("kubernetes", "k8s"),
    "skill_git": ("git",),
    "skill_statistics": ("statistics", "statistical"),
    "skill_machine_learning": ("machine learning", "ml"),
    "skill_deep_learning": ("deep learning",),
    "skill_nlp": ("nlp", "natural language processing"),
    "skill_computer_vision": ("computer vision",),
    "skill_data_visualization": ("data visualization", "data visualisation", "dataviz"),
}

#: Columns required by the downstream pipeline. Missing ones are dropped.
REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "skill_tags",
    "job_education",
    "job_method",
    "job_experience",
)


# ---------------------------------------------------------------------------
# Salary parsing
# ---------------------------------------------------------------------------


def parse_salary(raw: str | float) -> tuple[float, float]:
    """Parse an IDR salary string into ``(min, max)`` in IDR per month.

    Handles three shapes:

    * ``UNDISCLOSED_SALARY`` -> ``(nan, nan)``
    * ``"Rp 10.000.000 - 15.000.000 / bulan"`` -> ``(10_000_000.0, 15_000_000.0)``
    * ``"Rp 10.000.000"`` -> ``(10_000_000.0, 10_000_000.0)``

    Returns ``(nan, nan)`` for anything unparseable so the row survives but
    can be filtered downstream.
    """
    if not isinstance(raw, str) or raw.strip() == UNDISCLOSED_SALARY:
        return np.nan, np.nan

    text = raw.replace("Rp", "").replace(".", "").split("/")[0].strip()
    if not text:
        return np.nan, np.nan

    parts = [p.strip() for p in text.split(" - ")]
    try:
        if len(parts) == 2 and parts[0] and parts[1]:
            return float(parts[0]), float(parts[1])
        if len(parts) == 1 and parts[0]:
            value = float(parts[0])
            return value, value
    except ValueError:
        pass
    return np.nan, np.nan


# ---------------------------------------------------------------------------
# Experience parsing
# ---------------------------------------------------------------------------


_DIGIT_RE: Final[re.Pattern[str]] = re.compile(r"(\d+)")
_FRESH_GRAD_RE: Final[re.Pattern[str]] = re.compile(r"kurang dari 1|less than a year|fresh graduate", re.IGNORECASE)


def parse_experience(raw: str | float) -> int | None:
    """Extract the minimum experience years from a free-text experience field.

    "2-3 tahun" -> 2 (we surface the floor; range mid-point is a separate
    feature we don't track). "5+ tahun" -> 5. "fresh graduate" / "less than
    a year" -> 0. Closed listings are filtered earlier in the pipeline.
    """
    if not isinstance(raw, str):
        return None
    if _FRESH_GRAD_RE.search(raw):
        return 0
    match = _DIGIT_RE.search(raw)
    return int(match.group(1)) if match else None


# ---------------------------------------------------------------------------
# Education normalisation
# ---------------------------------------------------------------------------


def parse_education(raw: str | float) -> str:
    """Map recruiter spellings to one of ``S2 / S1 / D3-Diploma / SMA-SMK``.

    The first matching bucket wins, so ``S2`` patterns are checked before
    the broader ``S1`` family to avoid misclassification. Returns ``"Other"``
    when nothing matches.
    """
    if not isinstance(raw, str):
        return "Other"
    text = raw.lower()
    for label, patterns in EDUCATION_PATTERNS:
        for needle in patterns:
            if needle.lower() in text:
                return label
    return "Other"


# ---------------------------------------------------------------------------
# Employment classification
# ---------------------------------------------------------------------------


def parse_employment(raw: str | float) -> str:
    """Classify ``job_method`` into ``Full-time / Part-time / Contract / Intern / Freelance``.

    Returns ``"Other"`` when no keyword matches.
    """
    if not isinstance(raw, str):
        return "Other"
    text = raw
    for label, patterns in EMPLOYMENT_PATTERNS:
        for needle in patterns:
            if needle.lower() in text.lower():
                return label
    return "Other"


# ---------------------------------------------------------------------------
# Workplace classification
# ---------------------------------------------------------------------------


def parse_workplace(title: str | float, description: str | float) -> str:
    """Detect ``Remote`` / ``Hybrid`` from the title+description corpus.

    Defaults to ``"On-site"`` when neither keyword group is present. When
    both ``Remote`` and ``Hybrid`` keywords co-occur, ``Remote`` wins (the
    precedence order in :data:`WORKPLACE_KEYWORDS`).
    """
    title_text = title.lower() if isinstance(title, str) else ""
    desc_text = description.lower() if isinstance(description, str) else ""
    corpus = f"{title_text} {desc_text}"

    for label, keywords in WORKPLACE_KEYWORDS.items():
        for needle in keywords:
            if needle in corpus:
                return label
    return "On-site"


# ---------------------------------------------------------------------------
# Skill detection
# ---------------------------------------------------------------------------


def detect_skills(description: str | float, skill_tags: str | float) -> dict[str, bool]:
    """Return a ``{skill_<name>: bool}`` dict for one row's corpus.

    Both fields are coerced to ``str`` before lowercasing so ``NaN``/``None``
    inputs from upstream ``.fillna()`` paths are handled safely. The skill
    catalogue is curated so the false-positive rate from substring matching
    stays low.
    """
    desc = "" if not isinstance(description, str) else description
    tags = "" if not isinstance(skill_tags, str) else skill_tags
    corpus = f" {desc.lower()} {tags.lower()} "
    return {column: any(needle in corpus for needle in needles) for column, needles in SKILL_CATALOG.items()}


# ---------------------------------------------------------------------------
# City extraction
# ---------------------------------------------------------------------------

#: Mapping from raw ``job_location`` strings (lowercased) to canonical city
#: names. Kept as a function-level constant because the map is referenced
#: inside :func:`_extract_city`.
_CITY_ALIASES: Final[dict[str, str]] = {
    "jakarta": "Jakarta",
    "bandung": "Bandung",
    "surabaya": "Surabaya",
    "yogyakarta": "Yogyakarta",
    "yogya": "Yogyakarta",
    "jogja": "Yogyakarta",
    "medan": "Medan",
    "semarang": "Semarang",
    "makassar": "Makassar",
    "denpasar": "Denpasar",
    "bali": "Denpasar",
    "remote": "Remote",
}


def extract_city(raw: str | float) -> str | None:
    """Map a raw ``job_location`` string to one of the canonical cities.

    Returns ``None`` if no canonical city is recognised — the caller can
    decide whether to drop or recategorise the row.
    """
    if not isinstance(raw, str):
        return None
    text = raw.lower()
    for needle, canonical in _CITY_ALIASES.items():
        if needle in text:
            return canonical
    return None


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning + feature engineering pipeline.

    The returned frame has the canonical schema:

    ``keyword, job_title, company_name, city_clean, salary_avg,
    exp_min_years, workplace_type, job_education_clean, employment_type,
    skill_<name>...`` (32 boolean skill flags).

    The pipeline never mutates ``df`` in place; a copy is returned.
    """
    work = df.copy()

    # 1. Required-field filter.
    missing_mask = work[list(REQUIRED_COLUMNS)].isna().any(axis=1)
    if missing_mask.any():
        work = work.loc[~missing_mask].reset_index(drop=True)

    # 2. Salary parsing.
    salary_pairs = work["job_salary"].apply(parse_salary)
    work["salary_min"] = salary_pairs.str[0]
    work["salary_max"] = salary_pairs.str[1]
    work["salary_avg"] = (work["salary_min"] + work["salary_max"]) / 2.0

    # 3. Drop closed listings + parse experience.
    closed_mask = work["job_experience"].astype(str).str.contains(CLOSED_LISTING_MARKER, case=False, na=False)
    if closed_mask.any():
        work = work.loc[~closed_mask].reset_index(drop=True)
    work["exp_min_years"] = work["job_experience"].apply(parse_experience).astype("Int64")

    # 4. Skill detection.
    if len(work) > 0:
        skill_records = [
            detect_skills(desc, tags)
            for desc, tags in zip(work["job_description"].fillna(""), work["skill_tags"].fillna(""), strict=False)
        ]
        skill_frame = pd.DataFrame(skill_records, index=work.index).astype(bool)
        work = pd.concat([work, skill_frame], axis=1)
    else:
        # Empty input: still expose the canonical skill columns so downstream
        # code can rely on schema stability regardless of row count.
        for col in SKILL_CATALOG:
            work[col] = pd.Series(dtype=bool)

    # 5. Education normalisation.
    work["job_education_clean"] = work["job_education"].apply(parse_education)

    # 6. Employment type.
    work["employment_type"] = work["job_method"].apply(parse_employment)

    # 7. Workplace type.
    work["workplace_type"] = [
        parse_workplace(title, desc)
        for title, desc in zip(work["job_title"].fillna(""), work["job_description"].fillna(""), strict=False)
    ]

    # 8. City extraction (best-effort; keeps raw location for transparency).
    work["city_clean"] = work["job_location"].apply(extract_city) if "job_location" in work.columns else None

    # Drop redundant raw columns the master schema does not need.
    drop_cols = [
        c for c in ("job_salary", "job_education", "job_method", "job_experience", "job_description", "skill_tags")
        if c in work.columns
    ]
    work = work.drop(columns=drop_cols)

    # Canonical column order.
    core_cols = [
        "keyword", "job_title", "company_name", "city_clean",
        "salary_min", "salary_max", "salary_avg",
        "exp_min_years", "employment_type", "workplace_type",
        "job_education_clean",
    ]
    skill_cols = list(SKILL_CATALOG.keys())
    ordered = [c for c in core_cols if c in work.columns] + [c for c in skill_cols if c in work.columns]
    remaining = [c for c in work.columns if c not in ordered]
    return work[ordered + remaining]


__all__ = [
    "EDUCATION_PATTERNS",
    "EMPLOYMENT_PATTERNS",
    "SKILL_CATALOG",
    "WORKPLACE_KEYWORDS",
    "detect_skills",
    "extract_city",
    "parse_education",
    "parse_employment",
    "parse_experience",
    "parse_salary",
    "parse_workplace",
    "transform",
]
