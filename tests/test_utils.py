"""Tests for :mod:`glints_scraper.utils`."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from glints_scraper.utils import (
    load_checkpoint,
    save_checkpoint,
)


def test_save_checkpoint_atomic(tmp_path: Path) -> None:
    """``save_checkpoint`` creates the target file without leaving temp files."""
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    target = tmp_path / "data" / "out.csv"
    save_checkpoint(df, target)
    assert target.exists()
    leftovers = [p for p in target.parent.iterdir() if p.name != "out.csv"]
    assert leftovers == []


def test_load_checkpoint_missing(tmp_path: Path) -> None:
    """``load_checkpoint`` returns ``None`` when the file is absent."""
    assert load_checkpoint(tmp_path / "missing.csv") is None
