"""Run the local, non-scraping portfolio pipeline."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

# Support direct execution from a fresh clone without requiring an editable
# package install first.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


RAW_PATH = PROJECT_ROOT / "data/raw/job_details.csv"
MASTER_PATH = PROJECT_ROOT / "data/processed/master_dataset_eda.csv"


def main() -> None:
    """Clean an existing raw scrape and rebuild generated portfolio assets."""
    from glints_scraper.transform import transform

    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing {RAW_PATH}. Run the optional scraping steps first, "
            "or use the committed demo snapshot."
        )

    master = transform(pd.read_csv(RAW_PATH))
    MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(MASTER_PATH, index=False)
    print(f"Saved {len(master):,} cleaned rows to {MASTER_PATH}")

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts/generate_assets.py")],
        check=True,
        cwd=PROJECT_ROOT,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--execute",
            "--ExecutePreprocessor.timeout=600",
            "--to",
            "html",
            str(PROJECT_ROOT / "eda.ipynb"),
            "--output",
            "eda_report.html",
            "--embed-images",
        ],
        check=True,
        cwd=PROJECT_ROOT,
    )


if __name__ == "__main__":
    main()
