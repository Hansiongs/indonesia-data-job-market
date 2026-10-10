"""Scrape job listing links from Glints search pages.

This module wraps the Playwright + parsel pipeline that walks the Glints
``/id/opportunities/jobs/explore`` listing for each configured keyword,
infinitely scrolls until the result list is exhausted, parses every job
card, and returns a tidy :class:`pandas.DataFrame`.

The implementation is a clean rewrite of the legacy ``1_scrape_links.py``
script. Compared to the original it adds:

* structured logging with English messages,
* atomic checkpoint persistence after every keyword,
* a resume mode that skips keywords already present in the checkpoint,
* bounded retries for navigation, and
* type-hinted helpers that are unit-testable in isolation.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .config import Settings, get_settings
from .parsers import parse_job_card
from .utils import (
    get_logger,
    load_checkpoint,
    polite_delay,
    save_checkpoint,
)

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Default keywords used when none are supplied at runtime.
DEFAULT_KEYWORDS: list[str] = [
    "data analyst",
    "data scientist",
    "data engineer",
    "machine learning",
]

#: Base URL prefix for Glints keyword searches (kept for backwards
#: compatibility; the runtime value lives in :attr:`Settings.glints_base_url`).
GLINTS_SEARCH_URL: str = "https://glints.com/id/opportunities/jobs/explore?keyword="

#: Path to the checkpoint CSV used for resume support.
CHECKPOINT_PATH: Path = Path("data/raw/glints_jobs.csv")

#: Default viewport used for the Playwright context.
_VIEWPORT: dict[str, int] = {"width": 1280, "height": 800}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_keyword(keyword: str) -> str:
    return keyword.replace(" ", "+")


def _build_search_url(base_url: str, keyword: str) -> str:
    separator = "" if base_url.endswith("=") else "="
    return f"{base_url}{separator}{_format_keyword(keyword)}"


def _scroll_until_exhausted(page: Page, card_selector: str, timeout_ms: int) -> int:
    """Scroll the page until no new cards appear."""
    last_count = -1
    while True:
        current_count = page.locator(card_selector).count()
        if current_count == last_count and last_count > 0:
            # No growth observed in the previous iteration; bail out.
            return current_count
        last_count = current_count

        # Scroll to the bottom of the page.
        page.evaluate("scrollTo(0, document.body.scrollHeight)")

        try:
            page.wait_for_function(
                "([sel, cnt]) => document.querySelectorAll(sel).length > cnt",
                arg=[card_selector, current_count],
                timeout=timeout_ms,
            )
        except PlaywrightTimeoutError:
            logger.debug(
                "Scroll exhausted after %d card(s) (timeout=%dms).",
                current_count,
                timeout_ms,
            )
            return current_count

        new_count = page.locator(card_selector).count()
        logger.debug("Scroll grew card count from %d to %d.", current_count, new_count)


def _navigate_to_search(page: Page, url: str, timeout_ms: int) -> None:
    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)


def _scrape_keyword(
    page: Page,
    keyword: str,
    settings: Settings,
) -> list[dict[str, str | None]]:
    """Scrape every job card returned for a single keyword."""
    target_url = _build_search_url(GLINTS_SEARCH_URL, keyword)
    logger.info("Navigating to search URL for keyword=%s", keyword)

    try:
        _navigate_to_search(page, target_url, settings.page_timeout_ms)
    except PlaywrightTimeoutError:
        logger.error(
            "Failed to load listing page for keyword=%s after retries: %s",
            keyword,
            target_url,
        )
        return []

    _scroll_until_exhausted(
        page,
        card_selector='a[class*="JobCardTitle"]',
        timeout_ms=settings.scroll_timeout_ms,
    )

    # Render the final DOM with parsel and extract cards.
    html = page.content()
    selector = _build_selector(html)
    cards = selector.xpath('//div[contains(@class, "CompactJobCard")]')

    rows: list[dict[str, str | None]] = []
    for card in cards:
        # ``parse_job_card`` produces ``job_url``; rename to the canonical
        # ``url`` column expected by callers.
        record = parse_job_card(card, base_url="https://glints.com")
        record["keyword"] = keyword
        record["url"] = record.pop("job_url", None)
        rows.append(record)

    logger.info("Scraped %d card(s) for keyword=%s", len(rows), keyword)
    return rows


def _build_selector(html: str):
    from parsel import Selector

    return Selector(text=html)


def _resume_completed_keywords(checkpoint: Path) -> set[str]:
    if not checkpoint.exists():
        return set()
    try:
        df = pd.read_csv(checkpoint)
    except Exception as exc:
        logger.warning("Could not read checkpoint %s: %s", checkpoint, exc)
        return set()
    if "keyword" not in df.columns:
        return set()
    return set(df["keyword"].dropna().astype(str).unique())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scrape_job_links(
    keywords: list[str] | None = None,
    settings: Settings | None = None,
    resume: bool = True,
) -> pd.DataFrame:
    """Scrape job listing links from Glints for the given keywords."""
    settings = settings or get_settings()

    auth_path: Path = settings.storage_state
    if not auth_path.exists():
        raise FileNotFoundError(
            f"Authentication file not found at {auth_path}. "
            "Run the login helper first to generate secrets/auth.json."
        )

    resolved_keywords = list(keywords) if keywords else list(settings.keywords)
    if not resolved_keywords:
        logger.warning("No keywords supplied and no defaults configured; returning empty frame.")
        return pd.DataFrame(
            columns=["keyword", "job_title", "company_name", "job_location", "url"]
        )

    completed: set[str] = _resume_completed_keywords(CHECKPOINT_PATH) if resume else set()
    if resume and completed:
        logger.info(
            "Resuming: skipping %d already-completed keyword(s): %s",
            len(completed),
            sorted(completed),
        )

    work = [kw for kw in resolved_keywords if kw not in completed]
    skipped = [kw for kw in resolved_keywords if kw in completed]
    if skipped:
        logger.warning("Skipping %d keyword(s) already in checkpoint: %s", len(skipped), skipped)

    if not work:
        logger.info("Nothing to do; existing checkpoint already covers all keywords.")
        existing = load_checkpoint(CHECKPOINT_PATH) or pd.DataFrame()
        if existing.empty:
            return pd.DataFrame(
                columns=["keyword", "job_title", "company_name", "job_location", "url"]
            )
        return existing

    logger.info(
        "Starting link scrape for %d keyword(s) (headless=%s)",
        len(work),
        settings.headless,
    )

    # Start from the existing checkpoint so resume preserves prior rows.
    accumulated: list[dict[str, str | None]] = []
    existing_df = load_checkpoint(CHECKPOINT_PATH) if resume else None
    if existing_df is not None and not existing_df.empty:
        accumulated.extend(existing_df.to_dict(orient="records"))

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:  # type: ignore[assignment]
        playwright: Playwright = p  # type: ignore[assignment]
        browser: Browser = playwright.chromium.launch(
            headless=settings.headless,
            slow_mo=0,
        )
        try:
            context: BrowserContext = browser.new_context(
                storage_state=str(auth_path),
                viewport=_VIEWPORT,
            )
            page: Page = context.new_page()

            for keyword in work:
                rows = _scrape_keyword(page, keyword, settings)
                if not rows:
                    logger.warning(
                        "Zero results scraped for keyword=%s; continuing.",
                        keyword,
                    )
                accumulated.extend(rows)

                # Persist the checkpoint after every keyword.
                checkpoint_df = pd.DataFrame(accumulated)
                save_checkpoint(checkpoint_df, CHECKPOINT_PATH)

                # Polite delay between keywords to avoid hammering the server.
                polite_delay(settings.delay_sec)
        finally:
            browser.close()

    df = pd.DataFrame(accumulated)
    # Ensure canonical column order even when no rows were collected.
    expected_cols = ["keyword", "job_title", "company_name", "job_location", "url"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = None
    df = df[expected_cols]
    logger.info("Finished link scrape. Collected %d row(s) in total.", len(df))
    return df


__all__ = [
    "CHECKPOINT_PATH",
    "DEFAULT_KEYWORDS",
    "GLINTS_SEARCH_URL",
    "_scrape_keyword",
    "_scroll_until_exhausted",
    "scrape_job_links",
]


if __name__ == "__main__":  # pragma: no cover
    scrape_job_links()
