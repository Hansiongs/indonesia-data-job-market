"""Shared pytest fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the ``src`` layout importable without requiring an editable install.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from glints_scraper.config import Settings  # noqa: E402  (sys.path tweak)


@pytest.fixture()
def fixture_dir() -> Path:
    """Return the path to the ``tests/fixtures/`` directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def sample_settings(tmp_path: Path) -> Settings:
    """Return a :class:`Settings` instance with test-friendly overrides."""
    return Settings(
        storage_state=tmp_path / "auth.json",
        headless=True,
        delay_sec=0.0,
        page_timeout_ms=10_000,
        scroll_timeout_ms=2_000,
        max_retries=1,
        log_level="DEBUG",
    )


@pytest.fixture()
def job_card_html(fixture_dir: Path) -> str:
    """Return the contents of ``tests/fixtures/job_card.html``."""
    return (fixture_dir / "job_card.html").read_text(encoding="utf-8")


@pytest.fixture()
def job_detail_html(fixture_dir: Path) -> str:
    """Return the contents of ``tests/fixtures/job_detail.html``."""
    return (fixture_dir / "job_detail.html").read_text(encoding="utf-8")


@pytest.fixture()
def job_detail_reordered_html(fixture_dir: Path) -> str:
    """Return ``tests/fixtures/job_detail_reordered.html``.

    The overview panel in this fixture has its child fields in a
    non-default order so the label-based extractor can be tested.
    """
    return (fixture_dir / "job_detail_reordered.html").read_text(encoding="utf-8")


@pytest.fixture()
def listing_page_html(fixture_dir: Path) -> str:
    """Return the contents of ``tests/fixtures/listing_page.html``."""
    return (fixture_dir / "listing_page.html").read_text(encoding="utf-8")
