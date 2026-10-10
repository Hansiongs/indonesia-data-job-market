"""Tests for :mod:`glints_scraper.links` and :mod:`glints_scraper.cli.links`."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

import glints_scraper.links as links_mod
from glints_scraper.config import Settings
from glints_scraper.links import (
    _scrape_keyword,
    _scroll_until_exhausted,
    scrape_job_links,
)
from glints_scraper.parsers import parse_job_card

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_settings(auth_path: Path, *, headless: bool = True) -> Settings:
    """Return a Settings instance configured for tests."""
    return Settings(
        storage_state=auth_path,
        headless=headless,
        delay_sec=0.0,
        page_timeout_ms=10_000,
        scroll_timeout_ms=2_000,
        max_retries=1,
        log_level="DEBUG",
    )


def _write_auth_file(path: Path) -> Path:
    """Create a minimal valid Playwright storage_state JSON."""
    path.write_text(json.dumps({"cookies": [], "origins": []}), encoding="utf-8")
    return path


def _mock_browser_factory(nav_calls: list[str], content_html: str = "<html></html>"):
    """Return a factory producing a stack of mock Playwright objects.

    Args:
        nav_calls: Mutable list populated with the URLs passed to
            ``page.goto`` so tests can assert which keywords were visited.
        content_html: HTML returned by ``page.content()``. Defaults to
            an empty document (which yields zero ``CompactJobCard``
            elements so :func:`parse_job_card` is never invoked).

    Returns:
        A ``MockSyncPlaywright`` class.
    """

    class MockLocator:
        def count(self) -> int:
            return 0

    class MockPage:
        def goto(self, url: str, **kwargs: Any) -> None:
            nav_calls.append(url)

        def locator(self, selector: str) -> MockLocator:
            return MockLocator()

        def evaluate(self, *args: Any, **kwargs: Any) -> None:
            return None

        def content(self) -> str:
            return content_html

        def wait_for_function(self, *args: Any, **kwargs: Any) -> None:
            # Listings are immediately considered "exhausted".
            raise PlaywrightTimeoutError("no growth")

    class MockContext:
        def new_page(self) -> MockPage:
            return MockPage()

    class MockBrowser:
        def new_context(self, **kwargs: Any) -> MockContext:
            return MockContext()

        def close(self) -> None:
            return None

    class MockChromium:
        def launch(self, **kwargs: Any) -> MockBrowser:
            return MockBrowser()

    class MockSyncPlaywright:
        def __init__(self) -> None:
            self.chromium = MockChromium()

        def __enter__(self) -> MockSyncPlaywright:
            return self

        def __exit__(self, *args: Any) -> bool:
            return False

    return MockSyncPlaywright


# ---------------------------------------------------------------------------
# 1. parse_job_card fixture test
# ---------------------------------------------------------------------------


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "listing_page.html"


@pytest.mark.skipif(
    not FIXTURE_PATH.exists(),
    reason="tests/fixtures/listing_page.html is not present",
)
def test_scrape_keyword_parses_cards_from_fixture() -> None:
    """``parse_job_card`` extracts the canonical fields from a fixture card."""
    from parsel import Selector

    html = FIXTURE_PATH.read_text(encoding="utf-8")
    selector = Selector(text=html)
    cards = selector.xpath('//div[contains(@class, "CompactJobCard")]')
    assert cards, "Fixture must contain at least one CompactJobCard."

    try:
        record = parse_job_card(cards[0], base_url="https://glints.com")
    except NotImplementedError:
        pytest.skip("parse_job_card is not implemented yet.")
    except TypeError:
        # Phase 1 signature is parse_job_card(card); tolerate both.
        record = parse_job_card(cards[0])

    assert record.get("job_title")
    # parse_job_card returns the canonical 'job_url' key; the links pipeline
    # renames it to 'url' before saving to the DataFrame.
    assert record.get("job_url")
    assert record["job_url"].startswith("https://glints.com/")


# ---------------------------------------------------------------------------
# 2. _scroll_until_exhausted unit test
# ---------------------------------------------------------------------------


def test_scroll_until_exhausted_returns_final_count() -> None:
    """Scroll until no new cards appear, then return the final count."""
    page = MagicMock()
    locator = MagicMock()
    # Sequence: 10 (first count), 15 (after first scroll+wait), 15 (second count).
    locator.count.side_effect = [10, 15, 15]
    page.locator.return_value = locator
    page.evaluate.return_value = None

    # First wait_for_function succeeds, second raises TimeoutError.
    call_state = {"n": 0}

    def wait_side_effect(*args: Any, **kwargs: Any) -> None:
        call_state["n"] += 1
        if call_state["n"] >= 2:
            raise PlaywrightTimeoutError("no growth")

    page.wait_for_function.side_effect = wait_side_effect

    final = _scroll_until_exhausted(page, card_selector='a.JobCardTitle', timeout_ms=1000)
    assert final == 15
    assert locator.count.call_count == 3


# ---------------------------------------------------------------------------
# 3. Resume mode test
# ---------------------------------------------------------------------------


def test_scrape_job_links_resume_skips_completed_keywords(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``resume=True`` skips keywords already present in the checkpoint."""
    import playwright.sync_api

    auth = _write_auth_file(tmp_path / "auth.json")
    settings = _build_settings(auth)

    checkpoint = tmp_path / "_checkpoint_links.csv"
    pd.DataFrame(
        {
            "keyword": ["data scientist"],
            "job_title": ["Pre-existing"],
            "company_name": ["Acme"],
            "job_location": ["Jakarta"],
            "url": ["https://glints.com/id/opportunities/jobs/123"],
        }
    ).to_csv(checkpoint, index=False)
    monkeypatch.setattr(links_mod, "CHECKPOINT_PATH", checkpoint)

    nav_calls: list[str] = []
    mock_sp = _mock_browser_factory(nav_calls)
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", mock_sp)

    df = scrape_job_links(
        keywords=["data scientist", "data analyst"],
        settings=settings,
        resume=True,
    )

    # Only the unprocessed keyword should have been navigated.
    assert len(nav_calls) == 1
    assert "data+analyst" in nav_calls[0]
    # The pre-existing row must be preserved.
    assert "data scientist" in df["keyword"].tolist()
    # The processed (unscraped) keyword shows up in navigation but produces
    # zero cards in the mock, so it need not appear in the frame.


# ---------------------------------------------------------------------------
# 4. No-resume mode test
# ---------------------------------------------------------------------------


def test_scrape_job_links_no_resume_reprocesses_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``resume=False`` re-processes every keyword even if checkpoint exists."""
    import playwright.sync_api

    auth = _write_auth_file(tmp_path / "auth.json")
    settings = _build_settings(auth)

    checkpoint = tmp_path / "_checkpoint_links.csv"
    pd.DataFrame(
        {
            "keyword": ["data scientist"],
            "job_title": ["Pre-existing"],
            "company_name": ["Acme"],
            "job_location": ["Jakarta"],
            "url": ["https://glints.com/id/opportunities/jobs/123"],
        }
    ).to_csv(checkpoint, index=False)
    monkeypatch.setattr(links_mod, "CHECKPOINT_PATH", checkpoint)

    nav_calls: list[str] = []
    mock_sp = _mock_browser_factory(nav_calls)
    monkeypatch.setattr(playwright.sync_api, "sync_playwright", mock_sp)

    scrape_job_links(
        keywords=["data scientist", "data analyst"],
        settings=settings,
        resume=False,
    )

    # Both keywords should have been navigated when resume is disabled.
    assert len(nav_calls) == 2
    joined = " ".join(nav_calls)
    assert "data+scientist" in joined
    assert "data+analyst" in joined


# ---------------------------------------------------------------------------
# 5. Settings default keywords test
# ---------------------------------------------------------------------------


def test_settings_default_keywords() -> None:
    """The default keyword tuple contains sensible data roles."""
    settings = Settings()
    keywords = settings.keywords
    assert isinstance(keywords, tuple)
    assert len(keywords) >= 1
    assert all(isinstance(kw, str) and kw.strip() for kw in keywords)
    # Should contain at least one common data role.
    joined = " ".join(keywords).lower()
    assert any(role in joined for role in ("data", "machine", "engineer"))


# ---------------------------------------------------------------------------
# Bonus: _scrape_keyword handles navigation timeout gracefully
# ---------------------------------------------------------------------------


def test_scrape_keyword_returns_empty_on_navigation_timeout(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """If every navigation retry fails, ``_scrape_keyword`` returns ``[]``."""
    auth = _write_auth_file(tmp_path / "auth.json")
    settings = _build_settings(auth)

    class FlakyPage:
        def goto(self, url: str, **kwargs: Any) -> None:
            raise PlaywrightTimeoutError("nope")

        def locator(self, selector: str) -> MagicMock:
            mock = MagicMock()
            mock.count.return_value = 0
            return mock

        def evaluate(self, *args: Any, **kwargs: Any) -> None:
            return None

        def content(self) -> str:
            return "<html></html>"

        def wait_for_function(self, *args: Any, **kwargs: Any) -> None:
            return None

    with caplog.at_level(logging.ERROR, logger="glints_scraper.links"):
        rows = _scrape_keyword(FlakyPage(), keyword="data analyst", settings=settings)

    assert rows == []
