"""Tests for :mod:`glints_scraper.details`."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pandas as pd
import pytest

from glints_scraper import details as details_mod

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_input_df(n: int = 3) -> pd.DataFrame:
    """Build a small input frame for testing.

    Args:
        n: Number of rows to generate.

    Returns:
        A :class:`pandas.DataFrame` with one row per fake URL.
    """
    return pd.DataFrame(
        {
            "url": [f"https://glints.com/id/opportunities/jobs/{i}" for i in range(n)],
            "keyword": ["data analyst"] * n,
            "job_title": [f"Job {i}" for i in range(n)],
            "company_name": [f"Company {i}" for i in range(n)],
            "job_location": ["Jakarta"] * n,
        }
    )


def _write_auth(path: Path) -> None:
    """Write a minimal valid Playwright storage state to ``path``.

    Args:
        path: Destination path for the JSON file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"cookies": [], "origins": []}))


def _make_settings(
    auth_path: Path,
    tmp_path: Path,
    headless: bool = True,
) -> Any:
    """Build a :class:`Settings` instance pointing at ``tmp_path``.

    Args:
        auth_path: Where the auth JSON is written.
        tmp_path: Pytest fixture for a temporary directory.
        headless: Browser headless flag.

    Returns:
        A :class:`Settings` instance suitable for tests.
    """
    from glints_scraper.config import Settings

    return Settings(
        storage_state=auth_path,
        headless=headless,
        delay_sec=0.0,
        page_timeout_ms=5_000,
        scroll_timeout_ms=1_000,
        max_retries=2,
        log_level="DEBUG",
    )


def _patched_parse_job_detail(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Install a working fake for :func:`parse_job_detail`.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        A mutable dict that the fake parser writes into for each call.
        Tests can assert on its contents.
    """
    captured: dict[str, Any] = {}

    def fake_parse(selector: Any) -> dict[str, Any]:
        captured["calls"] = captured.get("calls", 0) + 1
        return {
            "job_description": "desc-text",
            "skill_tags": "Python, SQL",
            "job_salary": "IDR 10M",
            "job_education": "S1",
            "job_method": "Remote",
            "job_experience": "2 years",
        }

    monkeypatch.setattr(details_mod, "parse_job_detail", fake_parse)
    return captured


def _patched_playwright(
    monkeypatch: pytest.MonkeyPatch,
    *,
    goto_side_effect: Any = None,
    content_return: str = "<html><body>fake</body></html>",
    goto_calls: list[str] | None = None,
) -> dict[str, MagicMock]:
    """Patch :func:`sync_playwright` and the playwright context manager.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        goto_side_effect: Optional side effect for ``page.goto`` (e.g.
            an exception to raise).
        content_return: HTML returned by ``page.content()``.
        goto_calls: Optional list to which every URL passed to
            ``page.goto`` is appended.

    Returns:
        A dictionary of the created mocks (page, browser, context,
        playwright) for further assertions.
    """
    mocks: dict[str, MagicMock] = {}

    page = MagicMock(name="page")
    page.content.return_value = content_return
    if goto_side_effect is not None:
        page.goto.side_effect = goto_side_effect
    if goto_calls is not None:
        original_goto = page.goto

        def tracking_goto(url: str, *args: Any, **kwargs: Any) -> Any:
            goto_calls.append(url)
            if goto_side_effect is not None:
                raise goto_side_effect
            return None

        page.goto.side_effect = tracking_goto
        page.goto.return_value = None
        _ = original_goto

    context = MagicMock(name="context")
    context.new_page.return_value = page
    browser = MagicMock(name="browser")
    browser.new_context.return_value = context
    playwright = MagicMock(name="playwright")
    playwright.chromium.launch.return_value = browser
    mocks["page"] = page
    mocks["context"] = context
    mocks["browser"] = browser
    mocks["playwright"] = playwright

    cm = MagicMock(name="sync_playwright_cm")
    cm.__enter__.return_value = playwright
    cm.__exit__.return_value = False
    monkeypatch.setattr(details_mod, "sync_playwright", lambda: cm)
    return mocks


# ---------------------------------------------------------------------------
# _scrape_url behaviour
# ---------------------------------------------------------------------------


def test_scrape_url_handles_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """When ``page.goto`` raises a Playwright ``TimeoutError`` the helper raises.

    The outer ``scrape_job_details`` loop catches the exception and
    skips the row. This test mirrors that behaviour.
    """
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    page = MagicMock(name="page")
    page.goto.side_effect = PlaywrightTimeoutError("boom")

    row = {"url": "https://glints.com/id/opportunities/jobs/1", "company_name": "Acme"}
    settings = _make_settings(Path("/dev/null/auth.json"), Path("/tmp"))

    with pytest.raises(PlaywrightTimeoutError):
        details_mod._scrape_url(page, row, settings)


def test_scrape_url_handles_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A generic exception during ``page.content`` also propagates and is skipped.

    The CLI/outer loop is expected to catch ``Exception`` and continue
    with the next URL. This test verifies that the exception is not
    swallowed by :func:`_scrape_url` itself.
    """
    page = MagicMock(name="page")
    page.content.side_effect = RuntimeError("parse blew up")

    row = {"url": "https://glints.com/id/opportunities/jobs/1", "company_name": "Acme"}
    settings = _make_settings(Path("/dev/null/auth.json"), Path("/tmp"))

    with pytest.raises(RuntimeError):
        details_mod._scrape_url(page, row, settings)


def test_scrape_url_merges_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Returned dict contains both the input row fields and parsed fields."""
    from parsel import Selector

    page = MagicMock(name="page")
    page.content.return_value = "<html><body>x</body></html>"

    # Neutralise the polite delay so the test is fast.
    monkeypatch.setattr(details_mod, "polite_delay", lambda *_a, **_k: None)

    def fake_parse(_sel: Selector) -> dict[str, Any]:
        return {
            "job_description": "desc",
            "skill_tags": "Python",
            "job_salary": "IDR 1",
            "job_education": "S1",
            "job_method": "Remote",
            "job_experience": "2 years",
        }

    monkeypatch.setattr(details_mod, "parse_job_detail", fake_parse)

    row = {
        "url": "https://glints.com/id/opportunities/jobs/9",
        "keyword": "data",
        "job_title": "Engineer",
        "company_name": "Acme",
        "job_location": "Jakarta",
    }
    settings = _make_settings(Path("/dev/null/auth.json"), Path("/tmp"))

    result = details_mod._scrape_url(page, row, settings)
    assert result is not None
    # Input fields preserved.
    assert result["url"] == row["url"]
    assert result["job_title"] == row["job_title"]
    assert result["company_name"] == row["company_name"]
    # Parsed fields merged in.
    assert result["job_description"] == "desc"
    assert result["skill_tags"] == "Python"
    assert result["job_salary"] == "IDR 1"
    assert result["job_education"] == "S1"
    assert result["job_method"] == "Remote"
    assert result["job_experience"] == "2 years"


# ---------------------------------------------------------------------------
# scrape_job_details integration behaviour
# ---------------------------------------------------------------------------


def test_checkpoint_saved_every_n_rows(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``save_checkpoint`` is invoked at least once per N scraped rows."""
    auth_path = tmp_path / "auth.json"
    _write_auth(auth_path)
    settings = _make_settings(auth_path, tmp_path)

    df_in = _make_input_df(n=5)
    captured = _patched_parse_job_detail(monkeypatch)
    mocks = _patched_playwright(monkeypatch)

    save_calls: list[Path] = []
    original_save = details_mod.save_checkpoint

    def tracking_save(df: pd.DataFrame, path: Path) -> None:
        save_calls.append(path)
        original_save(df, path)

    monkeypatch.setattr(details_mod, "save_checkpoint", tracking_save)

    result = details_mod.scrape_job_details(
        input_df=df_in,
        settings=settings,
        resume=False,
        checkpoint_every=2,
    )

    assert len(result) == 5
    assert captured.get("calls") == 5
    # With 5 rows and checkpoint_every=2 we expect saves at 2, 4, and the
    # final flush, so at least 2 invocations (the strict requirement is >= 2).
    assert len(save_calls) >= 2
    mocks["page"].goto.assert_called()


def test_resume_skips_already_scraped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Already-scraped URLs in the checkpoint are skipped."""
    auth_path = tmp_path / "auth.json"
    _write_auth(auth_path)
    settings = _make_settings(auth_path, tmp_path)

    df_in = _make_input_df(n=5)

    # Pre-populate checkpoint with the first 2 URLs.
    ckpt_dir = tmp_path / "data" / "raw"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ckpt_dir / "_checkpoint_details.csv"
    pd.DataFrame(
        {
            "url": df_in["url"].iloc[:2].tolist(),
            "keyword": ["data analyst"] * 2,
            "job_title": ["Job 0", "Job 1"],
            "company_name": ["Company 0", "Company 1"],
            "job_location": ["Jakarta"] * 2,
            "job_description": ["d0", "d1"],
            "skill_tags": ["s0", "s1"],
            "job_salary": ["m0", "m1"],
            "job_education": ["e0", "e1"],
            "job_method": ["r0", "r1"],
            "job_experience": ["x0", "x1"],
        }
    ).to_csv(ckpt_path, index=False)

    monkeypatch.setattr(details_mod, "CHECKPOINT_PATH", ckpt_path)
    _patched_parse_job_detail(monkeypatch)
    goto_calls: list[str] = []
    _patched_playwright(monkeypatch, goto_calls=goto_calls)

    monkeypatch.setattr(details_mod, "polite_delay", lambda *_a, **_k: None)

    result = details_mod.scrape_job_details(
        input_df=df_in,
        settings=settings,
        resume=True,
        checkpoint_every=2,
    )

    # 3 new URLs should have been navigated to (5 - 2 already done).
    assert len(goto_calls) == 3
    # Output should contain all 5 rows (2 from checkpoint + 3 new).
    assert len(result) == 5


def test_input_df_none_loads_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When ``input_df`` is ``None``, the default CSV path is resolved."""
    # Drop a default-style CSV in cwd using monkeypatch.chdir.
    monkeypatch.chdir(tmp_path)
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    default_csv = raw_dir / "glints_jobs.csv"
    _make_input_df(n=2).to_csv(default_csv, index=False)

    resolved = details_mod._resolve_input(None)
    assert len(resolved) == 2
    assert "url" in resolved.columns


def test_input_df_none_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A clear ``FileNotFoundError`` is raised when no default CSV exists."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        details_mod._resolve_input(None)


# ---------------------------------------------------------------------------
# Defensive behaviour
# ---------------------------------------------------------------------------


def test_auth_missing_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A missing auth.json raises ``FileNotFoundError`` before launching the browser."""
    settings = _make_settings(tmp_path / "does_not_exist.json", tmp_path)

    df_in = _make_input_df(n=1)

    with pytest.raises(FileNotFoundError):
        details_mod.scrape_job_details(
            input_df=df_in,
            settings=settings,
            resume=False,
            checkpoint_every=10,
        )
