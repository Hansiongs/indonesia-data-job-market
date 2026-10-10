"""Tests for :mod:`glints_scraper.config`."""
from __future__ import annotations

from pathlib import Path

from glints_scraper.config import Settings


def test_default_settings() -> None:
    """Verify that :class:`Settings` dataclass defaults match the spec."""
    s = Settings()
    assert s.storage_state == Path("secrets/auth.json")
    assert s.headless is True
    assert s.delay_sec == 2.0
    assert s.page_timeout_ms == 30_000
    assert s.scroll_timeout_ms == 8_000
    assert s.max_retries == 3
    assert s.log_level == "INFO"
    assert "data analyst" in s.keywords
