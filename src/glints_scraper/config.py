"""Runtime settings as a frozen dataclass."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the Glints scraper."""

    storage_state: Path = Path("secrets/auth.json")
    headless: bool = True
    delay_sec: float = 2.0
    page_timeout_ms: int = 30_000
    scroll_timeout_ms: int = 8_000
    max_retries: int = 3
    keywords: tuple[str, ...] = field(
        default=("data analyst", "data scientist", "data engineer", "machine learning")
    )
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings()
