"""Generate portfolio-grade PNG previews of every dashboard chart.

Renders each helper in :mod:`app.charts` to a 150-DPI PNG that the README
links to. The chart *logic* lives in :mod:`app.charts`; this script is
just a thin wrapper that calls each function and exports the resulting
``plotly.graph_objects.Figure`` to ``assets/charts/``.

This is the single source of truth for static previews: the notebook
(``eda.ipynb``), the dashboard (``app/dashboard.py``), and this script
all render through the same Plotly builders, so labels, palettes, and
titles stay in lockstep.

Outputs
-------
- ``assets/charts/01_top-skills.png``
- ``assets/charts/02_salary-by-role.png``
- ``assets/charts/03_skill-cooccurrence-heatmap.png``
- ``assets/charts/04_salary-vs-experience.png``
- ``assets/charts/05_top-companies.png``
- ``assets/charts/06_median-salary-by-workplace.png``
- ``assets/charts/07_skill-vs-salary.png``
- ``assets/charts/08_experience-vs-salary-money-plot.png``
- ``assets/charts/09_role-vs-salary.png``
- ``assets/charts/10_company-vs-remote.png``

PNG export requires ``kaleido`` (``pip install 'glints-job-intel[viz]'``).

Usage
-----
::

    python scripts/generate_assets.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Support direct execution from a fresh clone without an editable install.
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_DATA_PATH: Path = PROJECT_ROOT / "data/processed/master_dataset_eda.csv"
SAMPLE_DATA_PATH: Path = PROJECT_ROOT / "data/sample/sample_master_dataset.csv"
OUT_DIR: Path = PROJECT_ROOT / "assets/charts"
PNG_HEIGHT: int = 520
PNG_WIDTH: int = 1100


def load_data() -> pd.DataFrame:
    """Prefer the real master dataset; fall back to the anonymised sample.

    The sample lives in version control so this script can run on a fresh
    clone without scraping. Both files use the canonical schema produced
    by :mod:`glints_scraper.transform`.
    """
    if DEFAULT_DATA_PATH.exists():
        return pd.read_csv(DEFAULT_DATA_PATH)
    if SAMPLE_DATA_PATH.exists():
        print(f"[INFO] {DEFAULT_DATA_PATH} missing; using {SAMPLE_DATA_PATH}.")
        return pd.read_csv(SAMPLE_DATA_PATH)
    raise FileNotFoundError(
        "No data available. Run `make pipeline` or commit the sample CSV."
    )


def main() -> list[Path]:
    """Generate chart previews from the dashboard chart builders."""
    from app.charts import (
        plot_remote_premium,
        plot_role_distribution,
        plot_salary_distribution,
        plot_salary_vs_experience,
        plot_skill_cooccurrence_heatmap,
        plot_skill_vs_salary,
        plot_top_companies,
        plot_top_skills_bar,
    )
    from app.data import build_skill_columns

    df, _ = build_skill_columns(load_data())
    written: list[Path] = []

    written.append(_write(plot_top_skills_bar(df, top_n=15), OUT_DIR / "01_top-skills.png"))
    written.append(_write(plot_salary_distribution(df, by="keyword"), OUT_DIR / "02_salary-by-role.png"))
    written.append(_write(plot_skill_cooccurrence_heatmap(df, top_n=12), OUT_DIR / "03_skill-cooccurrence-heatmap.png"))
    written.append(_write(plot_salary_vs_experience(df), OUT_DIR / "04_salary-vs-experience.png"))
    written.append(_write(plot_top_companies(df, top_n=15), OUT_DIR / "05_top-companies.png"))
    written.append(_write(plot_remote_premium(df), OUT_DIR / "06_median-salary-by-workplace.png"))
    written.append(_write(plot_skill_vs_salary(df, top_n=15), OUT_DIR / "07_skill-vs-salary.png"))

    fig_money = plot_salary_vs_experience(df)
    fig_money.update_layout(title="Salary vs. Experience — Money Plot")
    written.append(_write(fig_money, OUT_DIR / "08_experience-vs-salary-money-plot.png"))
    written.append(_write(plot_salary_distribution(df, by="keyword"), OUT_DIR / "09_role-vs-salary.png"))
    written.append(_write(plot_role_distribution(df), OUT_DIR / "10_company-vs-remote.png"))

    print(f"[INFO] wrote {len(written)} PNGs to {OUT_DIR}")
    return written


def _write(fig, out_path: Path) -> Path:
    """Render a Plotly figure to PNG at the configured size."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.update_layout(width=PNG_WIDTH, height=PNG_HEIGHT)
    fig.write_image(out_path, scale=1.5)
    return out_path


if __name__ == "__main__":
    main()
