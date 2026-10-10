"""Plotly chart builders for the Glints Job Intel dashboard.

Every function in this module returns a fully-formed ``plotly.graph_objects.Figure``
that the Streamlit layer renders via ``st.plotly_chart``. The functions never
call ``fig.show()`` — display is the host application's responsibility.

The module follows the dashboard's visual rules:

* **Categorical encoding** uses ``plotly.express.colors.qualitative.Set2`` for
  identity (role, workplace type, education).
* **Sequential encoding** uses the **Viridis** ramp for magnitude (skill
  counts, co-occurrence).
* **Single axis** per chart — never a dual-axis chart.
* **Direct labels** when the number of categories is small (≤ 5); otherwise
  a legend is included.
* **Interactive tooltips** on every mark (Plotly's default).
"""
from __future__ import annotations

from typing import Any, Final

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

CATEGORICAL_PALETTE: Final[list[str]] = list(px.colors.qualitative.Set2)
SEQUENTIAL_PALETTE: Final[str] = "Viridis"

# Reusable layout defaults so every chart looks like part of the same system.
# ``plotly_dark`` matches the dark slate theme in ``.streamlit/config.toml``;
# gridlines, axes, and labels are auto-themed so we don't have to override
# them per chart.
_BASE_LAYOUT: Final[dict[str, Any]] = {
    "template": "plotly_dark",
    "margin": {"l": 40, "r": 20, "t": 60, "b": 40},
    "font": {"family": "Inter, system-ui, -apple-system, sans-serif", "size": 12},
    "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
}


def _apply_base_layout(fig: go.Figure, height: int = 450, title: str | None = None) -> go.Figure:
    fig.update_layout(height=height, **_BASE_LAYOUT)
    if title:
        fig.update_layout(title={"text": title, "x": 0.0, "xanchor": "left"})
    return fig


def _discrete_colors(n: int) -> list[str]:
    if n <= 0:
        return []
    return [CATEGORICAL_PALETTE[i % len(CATEGORICAL_PALETTE)] for i in range(n)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_linear_trendline(fig: go.Figure, df: pd.DataFrame) -> None:
    work = df[["exp_min_years", "salary_avg"]].dropna()
    if len(work) < 2:
        return
    x = work["exp_min_years"].to_numpy(dtype=float)
    y = work["salary_avg"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, deg=1)
    xs = np.linspace(x.min(), x.max(), 50)
    ys = slope * xs + intercept
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            # Light grey so the trendline stays visible against the dark
            # slate canvas without competing with the data points.
            line={"color": "rgba(200,200,210,0.55)", "width": 2, "dash": "dash"},
            name="Overall trend",
            hoverinfo="skip",
            showlegend=True,
        )
    )


def _skill_columns(df: pd.DataFrame) -> list[str]:
    return sorted(c for c in df.columns if c.startswith("skill_") or c.startswith("is_"))


def _skill_frequency(df: pd.DataFrame, skill_cols: list[str]) -> pd.Series:
    if not skill_cols:
        return pd.Series(dtype=int)
    return df[skill_cols].astype(bool).sum(axis=0).sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Skill label pretty-printing
# ---------------------------------------------------------------------------

#: Curated overrides for skill names whose canonical label is not just
#: title-cased. Without these, "r" would render as "R" (fine) but
#: "power_bi" would render as "Power Bi" (wrong). Keep this map small —
#: everything else falls back to title-cased ``name.replace('_', ' ')``.
_SKILL_LABEL_OVERRIDES: Final[dict[str, str]] = {
    "r": "R",
    "sql": "SQL",
    "aws": "AWS",
    "gcp": "GCP",
    "etl": "ETL",
    "nlp": "NLP",
    "dbt": "DBT",
    "postgres": "Postgres",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "numpy": "NumPy",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit_learn": "Scikit-learn",
    "power_bi": "Power BI",
}


def pretty_skill_label(column: str) -> str:
    """Convert a ``skill_<name>`` / ``is_<name>`` column to a chart label.

    Strips the canonical prefix, applies the curated override map for
    acronyms and compound names, and falls back to title case for the
    rest. Centralised so every chart (bar, heatmap, salary premium) shows
    the same human-readable name.
    """
    name = column
    for prefix in ("skill_", "is_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name in _SKILL_LABEL_OVERRIDES:
        return _SKILL_LABEL_OVERRIDES[name]
    return name.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Salary charts
# ---------------------------------------------------------------------------


def plot_salary_distribution(df: pd.DataFrame, *, by: str = "keyword") -> go.Figure:
    """Box plot of salary distribution grouped by ``by``.

    Individual points are rendered only when the total is small enough to
    stay legible. Above 50 postings the swarm becomes noise, so we fall
    back to box-only and surface the n in the legend via the trace name.
    """
    if df.empty or by not in df.columns:
        return _empty_figure("No data to display")

    n = len(df)
    show_points = "all" if n <= 50 else False

    palette = _discrete_colors(df[by].nunique())
    fig = px.box(
        df,
        x=by,
        y="salary_avg",
        color=by,
        points=show_points,
        color_discrete_sequence=palette,
        labels={"salary_avg": "Salary (IDR / month)", by: by.replace("_", " ").title()},
        title=f"Salary Distribution by {by.replace('_', ' ').title()}",
    )
    fig.update_traces(
        jitter=0.5,
        pointpos=0,
        marker={"opacity": 0.35, "size": 4},
        hovertemplate="%{x}<br>Rp %{y:,.0f}<extra></extra>",
    )
    fig.update_yaxes(tickformat=",.0s")
    fig.update_xaxes(showgrid=False)
    return _apply_base_layout(fig, height=480)


def plot_salary_vs_experience(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of salary vs minimum experience, coloured by role."""
    if df.empty:
        return _empty_figure("No data to display")

    palette = _discrete_colors(df["keyword"].nunique()) if "keyword" in df.columns else CATEGORICAL_PALETTE

    # The OLS trendline requires statsmodels, which is not always installed in
    # lightweight dashboards. We attempt it and fall back to a manual linear
    # fit computed with numpy.
    try:
        fig = px.scatter(
            df,
            x="exp_min_years",
            y="salary_avg",
            color="keyword",
            color_discrete_sequence=palette,
            trendline="ols",
            trendline_scope="overall",
            labels={
                "exp_min_years": "Min experience (years)",
                "salary_avg": "Salary (IDR / month)",
                "keyword": "Role",
            },
            title="Salary vs. Experience",
            opacity=0.55,
        )
    except Exception:  # pragma: no cover - exercised when statsmodels missing
        fig = px.scatter(
            df,
            x="exp_min_years",
            y="salary_avg",
            color="keyword",
            color_discrete_sequence=palette,
            labels={
                "exp_min_years": "Min experience (years)",
                "salary_avg": "Salary (IDR / month)",
                "keyword": "Role",
            },
            title="Salary vs. Experience",
            opacity=0.55,
        )
        _add_linear_trendline(fig, df)
    fig.update_traces(marker={"size": 6, "line": {"width": 0}}, selector={"mode": "markers"})
    fig.update_traces(
        hovertemplate="Experience: %{x}y<br>Salary: Rp %{y:,.0f}<extra>%{fullData.name}</extra>",
        selector={"mode": "markers"},
    )
    fig.update_yaxes(tickformat=",.0s")
    return _apply_base_layout(fig, height=480)


# ---------------------------------------------------------------------------
# Skill charts
# ---------------------------------------------------------------------------


def plot_top_skills_bar(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of the top N most-requested skills."""
    skill_cols = _skill_columns(df)
    if not skill_cols or df.empty:
        return _empty_figure("No skill data available")

    freq = _skill_frequency(df, skill_cols).head(top_n)
    if freq.empty:
        return _empty_figure("No skill data available")

    # Map raw ``skill_<name>`` / ``is_<name>`` column IDs to pretty labels
    # so the y-axis reads "Python" rather than "skill_python".
    pretty_index = freq.sort_values().rename(index=pretty_skill_label)
    ordered = pretty_index.sort_values()

    fig = px.bar(
        ordered,
        x=ordered.values,
        y=ordered.index,
        orientation="h",
        color=ordered.values,
        color_continuous_scale=SEQUENTIAL_PALETTE,
        labels={"x": "Job count", "y": "Skill", "color": "Jobs"},
        title=f"Top {min(top_n, len(freq))} Most-Requested Skills",
    )
    fig.update_traces(
        hovertemplate="%{y}<br>%{x:,} jobs<extra></extra>",
        marker_line_width=0,
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes()
    fig.update_yaxes(showgrid=False)
    return _apply_base_layout(fig, height=480)


def plot_skill_cooccurrence_heatmap(df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Heatmap of Jaccard similarity between the top N most-requested skills."""
    skill_cols = _skill_columns(df)
    if not skill_cols or df.empty:
        return _empty_figure("No skill data available")

    freq = _skill_frequency(df, skill_cols).head(top_n)
    if freq.empty:
        return _empty_figure("No skill data available")

    top_cols = list(freq.index)
    bool_mat = df[top_cols].astype(bool).to_numpy()
    n_skills = len(top_cols)

    # Compute the Jaccard matrix.
    jaccard = np.zeros((n_skills, n_skills), dtype=float)
    for i in range(n_skills):
        a = bool_mat[:, i]
        for j in range(n_skills):
            b = bool_mat[:, j]
            union = np.logical_or(a, b).sum()
            jaccard[i, j] = float(np.logical_and(a, b).sum()) / float(union) if union else 0.0

    pretty_labels = [pretty_skill_label(c) for c in top_cols]

    fig = go.Figure(
        data=go.Heatmap(
            z=jaccard,
            x=pretty_labels,
            y=pretty_labels,
            colorscale=SEQUENTIAL_PALETTE,
            showscale=True,
            colorbar={"title": "Jaccard", "thickness": 12, "len": 0.9},
            hovertemplate="%{y} ∩ %{x}<br>Jaccard: %{z:.2f}<extra></extra>",
            zmin=0.0,
            zmax=1.0,
        )
    )

    # Per-cell text colour: dark on bright cells (high Jaccard), white on
    # dark cells (low Jaccard). Plotly's Heatmap only supports a single
    # textfont colour, so we render the values as annotations instead.
    # Threshold 0.5 is the Viridis perceptual midpoint — cells at/below
    # are dark enough that white text wins.
    annotations = []
    for i, row_label in enumerate(pretty_labels):
        for j, col_label in enumerate(pretty_labels):
            v = float(jaccard[i, j])
            annotations.append(
                {
                    "x": col_label,
                    "y": row_label,
                    "text": f"{v:.2f}",
                    "showarrow": False,
                    "font": {
                        "color": "white" if v < 0.5 else "#1F2933",
                        "size": 10,
                    },
                    "xref": "x",
                    "yref": "y",
                }
            )

    fig.update_xaxes(side="bottom", tickangle=-40)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        title="Skill Co-occurrence (Jaccard Similarity)",
        annotations=annotations,
    )
    return _apply_base_layout(fig, height=520)


# ---------------------------------------------------------------------------
# Distribution charts
# ---------------------------------------------------------------------------


def _count_bar(
    df: pd.DataFrame,
    column: str,
    title: str,
    *,
    hide_legend: bool = False,
) -> go.Figure:
    if df.empty or column not in df.columns:
        return _empty_figure(f"No data for {column}")

    counts = df[column].astype(str).value_counts().reset_index()
    counts.columns = [column, "count"]

    n_cats = len(counts)
    palette = _discrete_colors(n_cats)
    fig = px.bar(
        counts,
        x=column,
        y="count",
        color=column,
        color_discrete_sequence=palette,
        text="count",
        labels={"count": "Jobs", column: column.replace("_", " ").title()},
        title=title,
    )
    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        hovertemplate="%{x}<br>%{y:,} jobs<extra></extra>",
        marker_line_width=0,
    )
    if hide_legend:
        # Small category sets don't need a colour legend — the x-axis
        # already names each bar, so the legend only repeats info.
        # Colour stays as visual variety.
        fig.update_layout(showlegend=False)
    fig.update_xaxes(showgrid=False, categoryorder="total descending")
    fig.update_yaxes()
    return _apply_base_layout(fig, height=420)


def plot_role_distribution(df: pd.DataFrame) -> go.Figure:
    return _count_bar(df, "keyword", "Job Distribution by Role")


def plot_experience_distribution(df: pd.DataFrame) -> go.Figure:
    """Bar chart of job counts by minimum-experience bucket."""
    if df.empty or "exp_min_years" not in df.columns:
        return _empty_figure("No experience data")

    work = df.copy()
    # Buckets chosen so every label is either "Fresher" or an "N-M years"
    # range. We collapsed the old single-year "3" bucket into "3-5 years"
    # so the x-axis reads as a uniform ordinal scale rather than mixing
    # a single year next to two ranges.
    def _bucket(v: int) -> str:
        if v <= 0:
            return "Fresher"
        if v <= 2:
            return "1-2 years"
        if v <= 5:
            return "3-5 years"
        return "6+ years"

    work["exp_bucket"] = work["exp_min_years"].astype(int).apply(_bucket)
    order = ["Fresher", "1-2 years", "3-5 years", "6+ years"]
    counts = work["exp_bucket"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["exp_bucket", "count"]

    fig = px.bar(
        counts,
        x="exp_bucket",
        y="count",
        color="exp_bucket",
        color_discrete_sequence=_discrete_colors(len(counts)),
        text="count",
        labels={"count": "Jobs", "exp_bucket": "Min Experience"},
        title="Distribution by Minimum Experience",
    )
    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
        hovertemplate="%{x}<br>%{y:,} jobs<extra></extra>",
        marker_line_width=0,
    )
    fig.update_xaxes(categoryorder="array", categoryarray=order, showgrid=False)
    fig.update_yaxes()
    return _apply_base_layout(fig, height=420)


def plot_education_distribution(df: pd.DataFrame) -> go.Figure:
    """Bar chart of job counts by required education level."""
    return _count_bar(df, "job_education_clean", "Distribution by Required Education")


def plot_workplace_type_distribution(df: pd.DataFrame) -> go.Figure:
    """Bar chart of job counts by workplace type (on-site / hybrid / remote).

    Hides the colour legend: the category set is small and stable
    (≤ 3 values), so the legend duplicates what the x-axis already says.
    """
    return _count_bar(df, "workplace_type", "Distribution by Workplace Type", hide_legend=True)


# ---------------------------------------------------------------------------
# Market intelligence charts
# ---------------------------------------------------------------------------


def plot_top_companies(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar chart of the top N companies by job-posting count."""
    if df.empty or "company_name" not in df.columns:
        return _empty_figure("No company data")

    counts = df["company_name"].value_counts().head(top_n)
    if counts.empty:
        return _empty_figure("No company data")

    fig = px.bar(
        counts.sort_values(),
        x=counts.sort_values().values,
        y=counts.sort_values().index,
        orientation="h",
        color=counts.sort_values().values,
        color_continuous_scale=SEQUENTIAL_PALETTE,
        labels={"x": "Job postings", "y": "Company", "color": "Jobs"},
        title=f"Top {min(top_n, len(counts))} Companies Hiring Data Talent",
    )
    fig.update_traces(
        hovertemplate="%{y}<br>%{x:,} postings<extra></extra>",
        marker_line_width=0,
        text=counts.sort_values().values,
        texttemplate="%{text:,}",
        textposition="outside",
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes()
    fig.update_yaxes(showgrid=False)
    return _apply_base_layout(fig, height=480)


def plot_skill_vs_salary(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Bar chart of median salary for postings that require each top skill.

    The plot answers the question "which skills pay?". For every boolean
    skill column we compute the median salary of postings that have it
    versus the global median, then sort by the absolute premium (postings
    that *have* the skill minus postings that do not). This gives the reader
    a clean ranking of skills that correlate with higher pay.
    """
    skill_cols = _skill_columns(df)
    if not skill_cols or df.empty or "salary_avg" not in df.columns:
        return _empty_figure("No skill / salary data")

    df["salary_avg"].median()
    rows = []
    for col in skill_cols:
        has = df.loc[df[col].astype(bool), "salary_avg"].dropna()
        lacks = df.loc[~df[col].astype(bool), "salary_avg"].dropna()
        if len(has) < 5 or len(lacks) < 5:
            continue
        rows.append(
            {
                "skill": pretty_skill_label(col),
                "median_with": float(has.median()),
                "median_without": float(lacks.median()),
                "premium": float(has.median() - lacks.median()),
                "count": len(has),
            }
        )

    if not rows:
        return _empty_figure("Insufficient skill data")

    table = pd.DataFrame(rows).sort_values("premium", ascending=False).head(top_n)
    if table.empty:
        return _empty_figure("Insufficient skill data")

    # Use horizontal bar coloured by premium (red = pays less, green = pays more).
    table = table.iloc[::-1]  # so largest premium renders at the top of the bar chart

    fig = px.bar(
        table,
        x="premium",
        y="skill",
        orientation="h",
        color="premium",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text="median_with",
        labels={"premium": "Median salary premium (IDR)", "skill": "Skill", "median_with": "Median salary"},
        title=f"Which Skills Pay More? Top {len(table)} by Median Salary Premium",
        hover_data={"median_without": True, "count": True, "premium": False, "median_with": False},
    )
    fig.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Median (with skill): Rp %{customdata[1]:,.0f}<br>Median (without): Rp %{customdata[0]:,.0f}<br>Premium: Rp %{customdata[2]:,.0f}<br>Postings: %{customdata[3]}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(title="Salary premium (IDR / month)")
    fig.update_yaxes(showgrid=False)
    return _apply_base_layout(fig, height=520)


def plot_remote_premium(df: pd.DataFrame) -> go.Figure:
    """Bar chart of median salary by workplace type, with on-site baseline.

    The chart computes median salary for each ``workplace_type`` category and
    shows the difference versus the On-site median so viewers can see at a
    glance whether remote roles actually pay a premium.
    """
    if df.empty or "workplace_type" not in df.columns or "salary_avg" not in df.columns:
        return _empty_figure("No workplace / salary data")

    work = df.dropna(subset=["salary_avg", "workplace_type"]).copy()
    if work.empty:
        return _empty_figure("No workplace / salary data")

    summary = (
        work.groupby("workplace_type")["salary_avg"]
        .agg(median="median", count="count")
        .reset_index()
        .sort_values("median", ascending=False)
    )
    if summary.empty or "On-site" not in set(summary["workplace_type"]):
        return _empty_figure("Cannot compute baseline (no On-site rows)")

    baseline = float(summary.loc[summary["workplace_type"] == "On-site", "median"].iloc[0])
    summary["premium_pct"] = (summary["median"] - baseline) / baseline * 100.0

    fig = px.bar(
        summary,
        x="workplace_type",
        y="median",
        color="premium_pct",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        text="median",
        labels={
            "median": "Median salary (IDR / month)",
            "workplace_type": "Workplace type",
            "premium_pct": "vs. On-site (%)",
        },
        title="Median Salary by Workplace Type",
        custom_data=["premium_pct", "count"],
    )
    fig.update_traces(
        texttemplate="Rp %{text:,.0f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Median: Rp %{y:,.0f}<br>Premium vs. On-site: %{customdata[0]:+.1f}%%<br>Postings: %{customdata[1]}<extra></extra>",
    )
    fig.update_layout(coloraxis_showscale=True, coloraxis_colorbar={"title": "Premium %"})
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes()
    return _apply_base_layout(fig, height=480)


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------


def _empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 14, "color": "rgba(80,80,80,1)"},
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _apply_base_layout(fig, height=400)


def plot_skill_burden_by_career_stage(df: pd.DataFrame) -> go.Figure:
    """Grouped bar chart showing percentage demand for heavy/advanced skills across career stages."""
    if df.empty or "exp_min_years" not in df.columns:
        return _empty_figure("Tidak ada data pengalaman untuk ditampilkan")

    def _exp_tier(y: Any) -> str:
        if pd.isna(y):
            return "Tidak Disebutkan"
        try:
            val = float(y)
            if val == 0:
                return "Fresh Grad (< 1 Thn)"
            if val <= 2:
                return "Junior (1-2 Thn)"
            return "Mid/Senior (3+ Thn)"
        except (ValueError, TypeError):
            return "Tidak Disebutkan"

    work = df.copy()
    work["tier"] = work["exp_min_years"].apply(_exp_tier)
    tiers = ["Fresh Grad (< 1 Thn)", "Junior (1-2 Thn)", "Mid/Senior (3+ Thn)"]
    valid_work = work[work["tier"].isin(tiers)]
    if valid_work.empty:
        return _empty_figure("Data pengalaman tidak memadai")

    focus_skills = [
        ("skill_python", "Python"),
        ("skill_statistics", "Statistika"),
        ("skill_machine_learning", "Machine Learning"),
        ("skill_deep_learning", "Deep Learning"),
        ("skill_sql", "SQL"),
        ("skill_excel", "Excel"),
    ]

    records = []
    for tier in tiers:
        sub = valid_work[valid_work["tier"] == tier]
        n_tier = len(sub)
        if n_tier == 0:
            continue
        for col, label in focus_skills:
            pct = (sub[col].sum() / n_tier * 100) if col in sub.columns else 0.0
            records.append({"Tier": tier, "Skill": label, "Persentase": round(pct, 1)})

    chart_df = pd.DataFrame(records)
    if chart_df.empty:
        return _empty_figure("Katalog skill tidak ditemukan")

    fig = px.bar(
        chart_df,
        x="Skill",
        y="Persentase",
        color="Tier",
        barmode="group",
        color_discrete_sequence=["#FF7F0E", "#1F77B4", "#2CA02C"],
        text="Persentase",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_yaxes(title="Proporsi Lowongan yang Menuntut Skill (%)", range=[0, 105])
    fig.update_xaxes(title="Keahlian / Tools")
    return _apply_base_layout(fig, height=480, title="Perbandingan Beban Kualifikasi Skill per Jenjang Karir")


def plot_salary_reality_curve(df: pd.DataFrame) -> go.Figure:
    """Scatter and trendline of real salary distribution vs years of experience."""
    if df.empty or "salary_avg" not in df.columns or "exp_min_years" not in df.columns:
        return _empty_figure("Data gaji atau pengalaman tidak ditemukan")

    sub = df.dropna(subset=["salary_avg", "exp_min_years"]).copy()
    sub = sub[sub["exp_min_years"] <= 12]
    if sub.empty:
        return _empty_figure("Tidak ada data gaji yang dicantumkan")

    sub["salary_juta"] = sub["salary_avg"] / 1_000_000.0

    has_sm = False
    try:
        import statsmodels  # noqa: F401
        has_sm = True
    except ImportError:
        pass

    color_col = "keyword" if "keyword" in sub.columns else None
    fig = px.scatter(
        sub,
        x="exp_min_years",
        y="salary_juta",
        color=color_col,
        color_discrete_sequence=CATEGORICAL_PALETTE,
        hover_data={c: True for c in ["job_title", "company_name", "salary_juta", "exp_min_years"] if c in sub.columns},
        opacity=0.75,
        trendline="ols" if (has_sm and len(sub) >= 3) else None,
    )
    fig.update_xaxes(title="Syarat Pengalaman Minimum (Tahun)", dtick=1)
    fig.update_yaxes(title="Estimasi Gaji Rata-rata (Juta IDR / Bulan)")
    return _apply_base_layout(fig, height=480, title="Kurva Realita: Kompensasi vs Pengalaman Kerja di Indonesia")


def plot_remote_luxury_comparison(df: pd.DataFrame) -> go.Figure:
    """Side-by-side comparison of workplace distribution and median salary premium."""
    if df.empty or "workplace_type" not in df.columns:
        return _empty_figure("Data model kerja tidak ditemukan")

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Distribusi Model Kerja (%)", "Median Gaji (Juta IDR / Bulan)"),
    )

    types = ["On-site", "Hybrid", "Remote"]
    counts = [df["workplace_type"].value_counts(normalize=True).get(t, 0.0) * 100 for t in types]

    fig.add_trace(
        go.Bar(
            x=types,
            y=counts,
            text=[f"{c:.1f}%" for c in counts],
            textposition="outside",
            marker_color=["#4C78A8", "#F58518", "#E45756"],
            name="Porsi Lowongan",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    if "salary_avg" in df.columns and df["salary_avg"].notna().any():
        med_salaries = []
        for t in types:
            s = df[df["workplace_type"] == t]["salary_avg"].dropna()
            med_salaries.append((s.median() / 1_000_000.0) if not s.empty else 0.0)

        fig.add_trace(
            go.Bar(
                x=types,
                y=med_salaries,
                text=[f"Rp {m:.1f} Jt" for m in med_salaries],
                textposition="outside",
                marker_color=["#4C78A8", "#F58518", "#E45756"],
                name="Median Gaji",
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    fig.update_yaxes(title="Porsi Lowongan (%)", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title="Gaji Rata-rata (Juta IDR)", row=1, col=2)
    return _apply_base_layout(fig, height=450, title="Dominasi On-Site vs Premi Gaji Kerja Remote")


def plot_real_tech_stack_landscape(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bar chart showing the real ranking of required tools across data professions."""
    skill_cols = [c for c in df.columns if c.startswith("skill_")]
    if not skill_cols or df.empty:
        return _empty_figure("Data skill tidak ditemukan")

    sums = df[skill_cols].sum().sort_values(ascending=False).head(top_n)
    labels = [pretty_skill_label(c) for c in sums.index]

    chart_df = pd.DataFrame({
        "Skill": labels,
        "Jumlah Lowongan": sums.values,
    }).sort_values("Jumlah Lowongan", ascending=True)

    fig = px.bar(
        chart_df,
        x="Jumlah Lowongan",
        y="Skill",
        orientation="h",
        text="Jumlah Lowongan",
        color="Jumlah Lowongan",
        color_continuous_scale="Viridis",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(title="Jumlah Lowongan yang Menyebutkan Skill")
    fig.update_yaxes(title="")
    return _apply_base_layout(fig, height=520, title="Peta Kebutuhan Tech Stack Riil: Fondasi SQL & Excel vs Hype AI")


__all__ = [
    "CATEGORICAL_PALETTE",
    "SEQUENTIAL_PALETTE",
    "plot_education_distribution",
    "plot_experience_distribution",
    "plot_real_tech_stack_landscape",
    "plot_remote_luxury_comparison",
    "plot_remote_premium",
    "plot_role_distribution",
    "plot_salary_distribution",
    "plot_salary_reality_curve",
    "plot_salary_vs_experience",
    "plot_skill_burden_by_career_stage",
    "plot_skill_cooccurrence_heatmap",
    "plot_skill_vs_salary",
    "plot_top_companies",
    "plot_top_skills_bar",
    "plot_workplace_type_distribution",
    "pretty_skill_label",
]

