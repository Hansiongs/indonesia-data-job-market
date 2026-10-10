"""Scrape detailed job information for each job URL.

This module is the Phase 2 replacement for the legacy
``3_scrape_details.py`` script. It uses Playwright to load each job
detail page, parses the rendered HTML via :func:`parse_job_detail`, and
merges the parsed fields with the original input row.

The implementation supports:

* resume via an atomic checkpoint file (``data/raw/job_details.csv``)
* polite delays between requests
* retry on transient failures for both navigation and parsing
* graceful per-URL skip when a page fails to load
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from playwright._impl._errors import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .config import Settings, get_settings
from .parsers import parse_job_detail
from .utils import load_checkpoint, polite_delay, save_checkpoint

if TYPE_CHECKING:
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)


#: Default input CSV path used when ``input_df`` is ``None``.
_DEFAULT_INPUT_CANDIDATES: tuple[Path, ...] = (
    Path("data/raw/glints_jobs.csv"),
    Path("filtered_links.csv"),
)

#: Checkpoint file path used for resume.
CHECKPOINT_PATH: Path = Path("data/raw/job_details.csv")

#: All canonical columns produced by :func:`scrape_job_details`.
OUTPUT_COLUMNS: tuple[str, ...] = (
    "url",
    "keyword",
    "job_title",
    "company_name",
    "job_location",
    "job_description",
    "skill_tags",
    "job_salary",
    "job_education",
    "job_method",
    "job_experience",
)


def _resolve_input(
    input_df: pd.DataFrame | Path | None,
    project_root: Path | None = None,
) -> pd.DataFrame:
    if input_df is None:
        candidates = _DEFAULT_INPUT_CANDIDATES
        if project_root is not None:
            candidates = tuple(project_root / p for p in candidates)
        for candidate in candidates:
            if candidate.exists():
                logger.info("Loading default input CSV from %s", candidate)
                return pd.read_csv(candidate)
        searched = ", ".join(str(c) for c in candidates)
        raise FileNotFoundError(
            "No input CSV provided and none of the default candidates "
            f"exist. Searched: {searched}. Pass input_df explicitly."
        )
    if isinstance(input_df, Path):
        if not input_df.exists():
            raise FileNotFoundError(f"Input CSV does not exist: {input_df}")
        return pd.read_csv(input_df)
    if isinstance(input_df, pd.DataFrame):
        return input_df.copy()
    raise TypeError(
        "input_df must be a DataFrame, a Path, or None; "
        f"got {type(input_df).__name__}"
    )


def _validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in OUTPUT_COLUMNS if col not in df.columns]
    if missing:
        logger.warning(
            "Input is missing expected columns: %s. They will be filled "
            "with empty strings.",
            ", ".join(missing),
        )
    result = df.copy()
    for col in missing:
        result[col] = ""
    return result


def _scrape_url(
    page: Page,
    row: dict[str, Any],
    settings: Settings,
) -> dict[str, Any]:
    url = row.get("url")
    if not isinstance(url, str) or not url:
        raise ValueError(f"Row is missing a usable 'url' field: {row!r}")

    timeout_ms = settings.page_timeout_ms
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    polite_delay(0.5)

    html = page.content()
    selector = _make_selector(html)
    parsed = parse_job_detail(selector)

    merged: dict[str, Any] = dict(row)
    for field in (
        "job_description",
        "skill_tags",
        "job_salary",
        "job_education",
        "job_method",
        "job_experience",
    ):
        merged[field] = parsed.get(field)
    return merged


def _make_selector(html: str) -> Any:
    from parsel import Selector

    return Selector(text=html)


def _load_checkpoint_df(
    settings: Settings | None = None,
    checkpoint_path: Path | None = None,
) -> pd.DataFrame | None:
    path = checkpoint_path if checkpoint_path is not None else CHECKPOINT_PATH
    return load_checkpoint(path)


def _scraped_urls_from_checkpoint(
    df: pd.DataFrame | None,
) -> set[str]:
    if df is None:
        return set()
    if "url" not in df.columns:
        return set()
    return {u for u in df["url"].dropna().astype(str).tolist() if u}


def scrape_job_details(
    input_df: pd.DataFrame | Path | None = None,
    settings: Settings | None = None,
    resume: bool = True,
    checkpoint_every: int = 25,
) -> pd.DataFrame:
    """Scrape detailed info for each job URL."""
    if settings is None:
        settings = get_settings()

    df = _resolve_input(input_df)
    df = _validate_columns(df)

    if not settings.storage_state.exists():
        logger.error(
            "Auth file not found at %s. Run the login codegen first.",
            settings.storage_state,
        )
        raise FileNotFoundError(
            f"Auth file not found: {settings.storage_state}"
        )

    checkpoint_df: pd.DataFrame | None = None
    scraped_urls: set[str] = set()
    if resume:
        checkpoint_df = _load_checkpoint_df(settings=settings)
        scraped_urls = _scraped_urls_from_checkpoint(checkpoint_df)
        if scraped_urls:
            logger.info(
                "Resuming: %d URL(s) already scraped; will skip them.",
                len(scraped_urls),
            )

    rows_total = len(df)
    rows_to_process = [
        (idx, row)
        for idx, row in df.iterrows()
        if str(row.get("url", "")) not in scraped_urls
    ]
    rows_skipped = rows_total - len(rows_to_process)
    logger.info(
        "Starting detail scrape: %d total, %d to process, %d skipped (resume).",
        rows_total,
        len(rows_to_process),
        rows_skipped,
    )

    new_results: list[dict[str, Any]] = []
    if rows_to_process:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.headless)
            context = browser.new_context(
                storage_state=str(settings.storage_state),
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            try:
                for i, (_, row) in enumerate(rows_to_process, start=1):
                    row_dict = row.to_dict()
                    url = row_dict.get("url")
                    company = row_dict.get("company_name") or "<unknown>"
                    try:
                        scraped = _scrape_url(page, row_dict, settings)
                    except PlaywrightTimeoutError as exc:
                        logger.warning(
                            "Timeout while scraping %s (%s): %s",
                            url,
                            company,
                            exc,
                        )
                        continue
                    except PlaywrightError as exc:
                        logger.warning(
                            "Playwright error while scraping %s (%s): %s",
                            url,
                            company,
                            exc,
                        )
                        continue
                    except Exception as exc:
                        logger.warning(
                            "Generic error while scraping %s (%s): %s",
                            url,
                            company,
                            exc,
                        )
                        continue

                    if scraped is None:
                        continue

                    logger.debug(
                        "Scraped %s [%d/%d] %s",
                        company,
                        i,
                        len(rows_to_process),
                        url,
                    )
                    new_results.append(scraped)

                    if len(new_results) % checkpoint_every == 0:
                        _flush_checkpoint(
                            checkpoint_df,
                            new_results,
                        )
                        logger.info(
                            "Checkpoint saved after %d new row(s).",
                            len(new_results),
                        )

                    polite_delay(settings.delay_sec)
            finally:
                context.close()
                browser.close()

    _flush_checkpoint(checkpoint_df, new_results)
    final_df = _combine_with_checkpoint(checkpoint_df, new_results)
    logger.info(
        "Finished detail scrape. %d new row(s); %d total in output.",
        len(new_results),
        len(final_df),
    )
    return final_df


def _flush_checkpoint(
    checkpoint_df: pd.DataFrame | None,
    new_results: list[dict[str, Any]],
) -> None:
    combined = _combine_with_checkpoint(checkpoint_df, new_results)
    save_checkpoint(combined, CHECKPOINT_PATH)


def _combine_with_checkpoint(
    checkpoint_df: pd.DataFrame | None,
    new_results: list[dict[str, Any]],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    if checkpoint_df is not None and not checkpoint_df.empty:
        frames.append(checkpoint_df)
    if new_results:
        frames.append(pd.DataFrame(new_results))
    if not frames:
        return pd.DataFrame(columns=list(OUTPUT_COLUMNS))
    combined = pd.concat(frames, ignore_index=True, sort=False)
    # Ensure canonical column order, adding missing ones as empty.
    for col in OUTPUT_COLUMNS:
        if col not in combined.columns:
            combined[col] = ""
    return combined


__all__ = [
    "CHECKPOINT_PATH",
    "_scrape_url",
    "scrape_job_details",
]


if __name__ == "__main__":  # pragma: no cover
    scrape_job_details(input_df=Path("data/raw/glints_jobs.csv"))
