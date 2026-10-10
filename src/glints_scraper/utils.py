"""Shared utilities: logging, delays, checkpointing."""
from __future__ import annotations

import contextlib
import logging
import os
import random
import tempfile
import time
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        # Reconfigure existing handlers (e.g. when called repeatedly in tests).
        for handler in root.handlers:
            handler.setFormatter(
                logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
            )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format=_LOG_FORMAT,
            datefmt=_DATE_FORMAT,
        )
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


# ---------------------------------------------------------------------------
# Delays
# ---------------------------------------------------------------------------


def polite_delay(seconds: float | None = None) -> None:
    if seconds is None:
        time.sleep(0)
        return
    jitter = seconds * 0.2
    delay = seconds + random.uniform(-jitter, jitter)
    delay = max(0.0, delay)
    time.sleep(delay)


# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------


def save_checkpoint(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            df.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        # Best-effort cleanup of the temp file on failure.
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


def load_checkpoint(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path)


__all__ = [
    "get_logger",
    "load_checkpoint",
    "polite_delay",
    "save_checkpoint",
    "setup_logging",
]
