"""Glints Job Intel — Interactive Dashboard.

This is the Streamlit entry point for the Phase 4 deliverable. Run it
with::

    streamlit run app/dashboard.py

The app loads the cleaned master dataset produced by the upstream
pipeline, exposes sidebar filters (role, city, workplace type, experience,
salary, free-text search), and renders five tabs: Overview, Salary,
Skills & Market, Geography, and Data.

All heavy lifting — data loading, filtering, chart building, geographic
visualisation — lives in sibling modules. This file is intentionally
thin: it wires the UI controls to the helpers and handles a few
empty-state edge cases.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit call.
# ---------------------------------------------------------------------------
import streamlit as st

st.set_page_config(
    page_title="Glints Job Intel — Indonesian Data Job Market",
    page_icon="🇮🇩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS (must be defined before the first st.markdown that injects it).
# ---------------------------------------------------------------------------
#
# ``<style>`` blocks survive Streamlit's HTML sanitiser; inline
# ``style="..."`` attributes on most elements (including ``<span>``)
# get stripped, which is why the eyebrow can't just be written as
# ``<span style="color:#5EEAD4">``. Instead, every styled element gets
# a class and the rule lives here. Injected below right after the
# constants are defined.

_CUSTOM_CSS: str = (
    "<style>"
    # Eyebrow above the hero number. Bigger than default body text,
    # wide-tracked so it reads as a typographic eyebrow.
    ".gji-eyebrow{font-size:0.95rem;letter-spacing:0.14em;"
    "text-transform:uppercase;color:#5EEAD4;font-weight:600;"
    "display:block;}"
    # Footer band — clearly darker than the canvas so the bottom of the
    # page reads as a distinct section. ``#020617`` is two stops darker
    # than the slate-900 body, and we add a 3px teal top-border so the
    # band has a visible edge even if the colour difference is subtle.
    ".gji-footer{background:#020617;border-top:3px solid #2DD4BF;"
    "border-radius:8px;padding:1.25rem 1.4rem;margin-top:1.25rem;}"
    "</style>"
)

# Inject custom CSS once at module load so every Streamlit rerun
# reapplies the styles (Streamlit re-runs the whole script on
# interaction). Has to come right after ``set_page_config`` since
# that must be the first Streamlit call.
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Imports (kept after page_config per Streamlit docs).
# ---------------------------------------------------------------------------
import os  # noqa: E402
from typing import Final  # noqa: E402

import pandas as pd  # noqa: E402

from app.charts import (  # noqa: E402
    plot_experience_distribution,
    plot_remote_premium,
    plot_role_distribution,
    plot_salary_distribution,
    plot_salary_vs_experience,
    plot_skill_cooccurrence_heatmap,
    plot_skill_vs_salary,
    plot_top_companies,
    plot_top_skills_bar,
    plot_workplace_type_distribution,
    pretty_skill_label,
)
from app.data import (  # noqa: E402
    build_skill_columns,
    compute_market_insights,
    compute_summary_stats,
    filter_dataframe,
    load_master_dataset,
)
from app.geo import city_summary, plot_geo_map  # noqa: E402

# ``streamlit-folium`` is an optional dependency that gives us a nicer
# component binding for Folium maps. If it isn't installed we fall back
# to raw ``st.components.v1.html`` rendering.
try:  # pragma: no cover - exercised only when streamlit-folium is missing
    from streamlit_folium import st_folium as _st_folium
except ImportError:  # pragma: no cover
    _st_folium = None

# Columns surfaced in the Data tab and the CSV download.
_DATA_TAB_COLUMNS: Final[list[str]] = [
    "keyword",
    "job_title",
    "company_name",
    "city_clean",
    "salary_avg",
    "workplace_type",
    "exp_min_years",
    "job_education_clean",
]

# Public-facing metadata for the methodology links + footer. Replace this
# placeholder before publishing the repository or deploying the app.
_REPO_URL: Final[str] = os.getenv("GJI_REPO_URL", "")
_REPO_BLOB_URL: Final[str] = f"{_REPO_URL}/blob/main"


def _render_map(m: object) -> None:
    if _st_folium is not None:
        _st_folium(m, height=520, returned_objects=[])
        return
    html = getattr(m, "_repr_html_", lambda: str(m))()
    st.components.v1.html(html, height=520, scrolling=False)


def _format_salary_label(m_idr: float) -> str:
    return f"Rp {m_idr:,.1f}M"


def _format_skill_label(name: str) -> str:
    """Format a canonical skill name without exposing column conventions."""
    return pretty_skill_label(f"skill_{name}")


def _round_up_to(value: float, step: int) -> int:
    """Round ``value`` up to the nearest multiple of ``step``.

    Used to size the salary slider ceiling so it always lands on a clean
    M-IDR boundary instead of e.g. 47M.
    """
    if step <= 0:
        raise ValueError("step must be positive")
    return int((int(value) + step - 1) // step * step)


def _format_delta(curr: float, base: float) -> str | None:
    """Return a delta string vs the unfiltered baseline, or None when base is zero.

    Streamlit's ``st.metric`` treats ``None`` as "no delta to show" so we
    return ``None`` when the baseline is zero to avoid a ``NaN%`` arrow.
    """
    if base == 0:
        return None
    diff = (curr - base) / base * 100.0
    arrow = "▲" if diff >= 0 else "▼"
    return f"{arrow} {abs(diff):.1f}% vs all jobs"


def _render_hero(fdf: pd.DataFrame, df: pd.DataFrame) -> None:
    """Render the hero band: eyebrow, hero number, supporting meta line.

    The hero number is the most important single fact in the dashboard
    (filtered job count) — giving it space sets a clear focal point so
    the reader knows where to look first. The eyebrow surfaces when the
    dataset was last scraped so the reader knows how fresh the numbers
    are; the meta line surfaces the filtering ratio.

    Implementation note: the previous version used inline HTML ``<div>``s
    for the right-rail cards, which Streamlit's HTML sanitiser will
    quietly strip on some installs, leaving an empty white strip. The
    current version uses ``st.container(border=True)`` for the cards —
    it's a native primitive that survives sanitisation and picks up
    the theme's secondaryBackgroundColor automatically.
    """
    stats = compute_summary_stats(fdf)

    # Hero number + tagline side-by-side on wide layouts, stacked on narrow.
    # ``[1, 1]`` keeps the left text column narrower than the right cards
    # so the hero number doesn't get stretched out and lose its impact.
    left, right = st.columns([1, 1], vertical_alignment="center")
    with left:
        # Eyebrow uses the ``gji-eyebrow`` class declared in
        # ``_CUSTOM_CSS`` — inline ``style="..."`` attributes on
        # ``<span>`` get stripped by Streamlit's HTML sanitiser on
        # some installs, so the rule has to live in a ``<style>`` block
        # applied via ``class=``.
        st.markdown(
            "<span class='gji-eyebrow'>"
            "Glints Job Intel · Portfolio snapshot"
            "</span>",
            unsafe_allow_html=True,
            help="Cleaned Indonesian data-job postings from a Glints snapshot.",
        )
        # Native ``#`` heading — Streamlit's h1 picks up the theme's
        # heading font size without us touching inline styles (which the
        # HTML sanitiser can silently strip on some installs).
        st.markdown(f"# {stats['total_jobs']:,}")
        st.caption("jobs hiring now")
        if len(fdf) != len(df):
            st.caption(
                f"Filtered from {len(df):,} total postings · "
                f"{len(fdf) / len(df) * 100:.0f}% of dataset"
            )
        else:
            st.caption(f"Pulled from {len(df):,} total postings")

    with right:
        with st.container(border=True):
            st.caption("Median salary")
            st.markdown(
                f"### {_format_salary_label(stats['median_salary_idr'] / 1_000_000)}"
            )

        with st.container(border=True):
            st.caption("Top role · Top city")
            st.markdown(f"### {stats['top_role']} · {stats['top_city']}")


def _render_context(df: pd.DataFrame) -> None:
    """Set expectations for the snapshot and give first-time readers a path."""
    insights = compute_market_insights(df)
    with st.container(border=True):
        st.markdown("**How to read this dashboard**")
        st.caption(
            "Start with the overview, then use Salary, Skills & Hiring, and Location "
            "to investigate a specific question. Filters in the sidebar update every "
            "chart at once."
        )
        st.caption(
            f"This dashboard uses a cleaned portfolio snapshot. "
            f"{insights['salary_disclosure_pct']:.0f}% of rows disclose salary in "
            "the current view; salary charts exclude rows without a value, while "
            "those rows remain available in the Data tab."
        )


def _render_insight_cards(df: pd.DataFrame) -> None:
    """Show three plain-language takeaways above the detailed charts."""
    insights = compute_market_insights(df)
    top_skill = insights["top_skill"]
    top_skill_label = _format_skill_label(top_skill) if top_skill != "n/a" else "n/a"
    cards = [
        (
            "Most-mentioned skill",
            f"{top_skill_label} · {insights['top_skill_share_pct']:.0f}%",
            "Share of filtered postings mentioning the leading skill.",
        ),
        (
            "Largest job hub",
            f"{insights['top_city_share_pct']:.0f}% of postings",
            "Share belonging to the most common city in this view.",
        ),
        (
            "Fresh-graduate postings",
            f"{insights['fresh_graduate_share_pct']:.0f}%",
            "Postings with a minimum experience requirement of zero years.",
        ),
    ]
    columns = st.columns(3)
    for column, (label, value, explanation) in zip(columns, cards, strict=True):
        with column, st.container(border=True):
            st.caption(label)
            st.markdown(f"### {value}")
            st.caption(explanation)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

with st.spinner("Loading data..."):
    try:
        raw_df = load_master_dataset()
        df, skill_cols = build_skill_columns(raw_df)
    except FileNotFoundError as exc:
        st.error(
            f"**Dataset not found.**\n\n"
            f"{exc}\n\n"
            "The repository includes a demo snapshot, so this usually means the "
            "data file was moved or deleted. Restore it from the repository, or "
            "run `make pipeline` after preparing a raw scrape."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
#
# Filters are grouped into three expanders so the sidebar isn't a wall of
# controls on first paint. The "Match" expander is open by default
# (free-text search is the lowest-friction entry point); the two
# "Refine" expanders are collapsed.

with st.sidebar:
    st.header("Filters")

    role_options: list[str] = sorted(df["keyword"].dropna().astype(str).unique().tolist()) if "keyword" in df.columns else []
    city_options: list[str] = sorted(df["city_clean"].dropna().astype(str).unique().tolist()) if "city_clean" in df.columns else []
    work_options: list[str] = sorted(df["workplace_type"].dropna().astype(str).unique().tolist()) if "workplace_type" in df.columns else []

    with st.expander("Match", expanded=True):
        search = st.text_input(
            "Search job title or company",
            value="",
            placeholder="e.g. data engineer, Gojek",
            help="Case-insensitive substring match across title and company.",
        )

    with st.expander("Refine by segment", expanded=False):
        role_filter = st.multiselect(
            "Role",
            options=role_options,
            default=None,
            help="Filter by job family (keyword).",
        )
        city_filter = st.multiselect(
            "City",
            options=city_options,
            default=None,
            help="Filter by city.",
        )
        work_filter = st.multiselect(
            "Workplace Type",
            options=work_options,
            default=None,
            help="On-site / Remote / Hybrid.",
        )

    with st.expander("Refine by experience & pay", expanded=False):
        experience_values = (
            pd.to_numeric(df["exp_min_years"], errors="coerce").dropna()
            if "exp_min_years" in df.columns
            else pd.Series(dtype=float)
        )
        exp_min = int(experience_values.min()) if not experience_values.empty else 0
        exp_max = int(experience_values.max()) if not experience_values.empty else 10
        exp_slider_max = max(exp_max, exp_min + 1)
        exp_filter = st.slider(
            "Min experience (years)",
            min_value=exp_min,
            max_value=exp_slider_max,
            value=(exp_min, exp_slider_max),
            step=1,
            help="Inclusive range applied to the minimum-experience field.",
        )

        # Salary slider ceiling comes from the data so users don't silently
        # lose postings that pay above the old hardcoded 50M cap. We round
        # up to the nearest 5M for a clean slider step boundary.
        salary_cap_m = 50
        salary_values = (
            pd.to_numeric(df["salary_avg"], errors="coerce").dropna()
            if "salary_avg" in df.columns
            else pd.Series(dtype=float)
        )
        if not salary_values.empty:
            max_salary_m = float(salary_values.max() / 1_000_000)
            salary_cap_m = max(5, int(_round_up_to(max_salary_m, 5)))

        salary_range = st.slider(
            "Salary range (M IDR / month)",
            min_value=0,
            max_value=salary_cap_m,
            value=(0, salary_cap_m),
            step=1,
            help=f"Inclusive range in millions of IDR per month. Upper bound set to Rp {salary_cap_m}M based on the dataset's max.",
        )

    st.divider()
    st.caption(f"Loaded {len(df):,} rows · {len(skill_cols)} skill flags.")


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

fdf = filter_dataframe(
    df,
    role=role_filter,
    city=city_filter,
    work_method=work_filter,
    experience_band=None if exp_filter == (exp_min, exp_slider_max) else exp_filter,
    search_query=search,
)

# Salary range filter is applied separately so the slider's M-IDR units
# are explicit at the call site (no implicit unit conversion inside the
# helper).
if (
    "salary_avg" in fdf.columns
    and not fdf.empty
    and salary_range != (0, salary_cap_m)
):
    salary_low = salary_range[0] * 1_000_000
    salary_high = salary_range[1] * 1_000_000
    fdf = fdf[(fdf["salary_avg"] >= salary_low) & (fdf["salary_avg"] <= salary_high)]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

if fdf.empty:
    st.warning(
        "No jobs match the current filters. Try widening the salary range, "
        "clearing the role/city selections, or removing the search term."
    )
    st.stop()

_render_hero(fdf, df)
_render_context(df)
st.markdown("")  # breathing room before the tabs row


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_salary, tab_skills, tab_geo, tab_data = st.tabs(
    ["Overview", "Salary", "Skills & Hiring", "Location", "Data"]
)

# ---- Overview ------------------------------------------------------------
with tab_overview:
    stats = compute_summary_stats(fdf)
    base_stats = compute_summary_stats(df)

    st.subheader("Market at a glance")
    _render_insight_cards(fdf)
    st.caption(
        "These takeaways describe the selected postings. Clear the sidebar filters "
        "to return to the full snapshot."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Total Jobs",
        f"{stats['total_jobs']:,}",
        delta=_format_delta(stats["total_jobs"], base_stats["total_jobs"]) or None,
    )
    c2.metric(
        "Unique Companies",
        f"{stats['unique_companies']:,}",
        delta=_format_delta(stats["unique_companies"], base_stats["unique_companies"]) or None,
    )
    c3.metric(
        "Median Salary",
        _format_salary_label(stats["median_salary_idr"] / 1_000_000),
        delta=_format_delta(stats["median_salary_idr"], base_stats["median_salary_idr"]) or None,
    )
    c4.metric(
        "Remote Share",
        f"{stats['remote_share_pct']:.0f}%",
        delta=_format_delta(stats["remote_share_pct"], base_stats["remote_share_pct"]) or None,
    )

    st.subheader("Where the opportunities are")
    st.caption(
        "Role mix, workplace type, and experience requirements provide the quickest "
        "overview of the market shape."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Jobs by Role")
        st.plotly_chart(plot_role_distribution(fdf), use_container_width=True)
    with col_b:
        st.subheader("Jobs by Workplace Type")
        st.plotly_chart(plot_workplace_type_distribution(fdf), use_container_width=True)

    st.subheader("Jobs by Minimum Experience")
    st.plotly_chart(plot_experience_distribution(fdf), use_container_width=True)

# ---- Salary --------------------------------------------------------------
with tab_salary:
    st.caption(
        "Salary is shown in IDR per month and is calculated only for postings with a "
        "disclosed salary range."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Salary Distribution by Role")
        st.plotly_chart(
            plot_salary_distribution(fdf, by="keyword"),
            use_container_width=True,
        )
    with c2:
        st.subheader("Salary Distribution by Workplace Type")
        st.plotly_chart(
            plot_salary_distribution(fdf, by="workplace_type"),
            use_container_width=True,
        )

    st.subheader("Salary vs. Experience")
    st.plotly_chart(plot_salary_vs_experience(fdf), use_container_width=True)

# ---- Skills & Market -----------------------------------------------------
# Skills and Market Intel are merged: together they answer the single
# recruiter question "what should I learn / who is hiring / does remote pay
# better?". Splitting them across two tabs forces extra clicks without
# surfacing any extra insight.

with tab_skills:
    st.caption(
        "Skills are keyword mentions in job descriptions and tags, not verified "
        "requirements."
    )
    st.subheader("Top Skills in Demand")
    st.plotly_chart(plot_top_skills_bar(fdf, top_n=20), use_container_width=True)

    st.subheader("Skill Co-occurrence")
    st.caption(
        "Jaccard similarity between the top 12 most-requested skills. "
        "Higher values mean the two skills tend to appear together in postings."
    )
    st.plotly_chart(plot_skill_cooccurrence_heatmap(fdf, top_n=12), use_container_width=True)

    st.subheader("Which Skills Pay More?")
    st.caption(
        "Salary premium per skill: median salary of postings that *require* the skill "
        "vs. postings that don't. Positive (green) means the skill correlates with higher pay; "
        "negative (red) means the skill is associated with lower-tier postings."
    )
    st.plotly_chart(plot_skill_vs_salary(fdf, top_n=15), use_container_width=True)

    st.subheader("Top Companies Hiring Data Talent")
    st.plotly_chart(plot_top_companies(fdf, top_n=15), use_container_width=True)

    st.subheader("Remote Work Premium")
    st.caption(
        "Median salary by workplace type. The colour shows the percentage premium vs. "
        "the On-site baseline. **Note:** premium can be negative for Remote roles when "
        "remote postings are dominated by junior or contract positions."
    )
    st.plotly_chart(plot_remote_premium(fdf), use_container_width=True)

# ---- Geography -----------------------------------------------------------
with tab_geo:
    st.subheader("Jobs Across Indonesia")
    st.caption(
        "Locations are normalised from the scraped location text. Cities without a "
        "reference coordinate are included in the table but not plotted on the map."
    )

    # Map gets the full width — the previous [1, 2] split cramped the
    # city summary dataframe and truncated the median-salary column on
    # narrow viewports. Stack them instead: map up top, table below.
    _render_map(plot_geo_map(fdf))

    st.markdown("**City summary**")
    st.caption(
        "One row per city. Click a column header to sort; use the sidebar "
        "filters to drill into a single city."
    )
    st.dataframe(
        city_summary(fdf),
        use_container_width=True,
        hide_index=True,
        column_config={
            "count": st.column_config.NumberColumn("Jobs", format="%d"),
            "median_salary": st.column_config.NumberColumn(
                "Median Salary", format="Rp %.1fM"
            ),
            "remote_pct": st.column_config.NumberColumn("Remote %", format="%.0f%%"),
        },
    )

# ---- Data ----------------------------------------------------------------
with tab_data:
    st.subheader("Filtered Dataset")
    st.caption(
        "This table contains the cleaned fields used by the charts. Download the "
        "current filtered view for further exploration."
    )
    present_cols = [c for c in _DATA_TAB_COLUMNS if c in fdf.columns]
    table_df = fdf[present_cols].sort_values(
        "salary_avg" if "salary_avg" in present_cols else present_cols[0],
        ascending=False,
    )
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "salary_avg": st.column_config.NumberColumn(
                "Salary (IDR / month)", format="Rp %.0f"
            ),
            "exp_min_years": st.column_config.NumberColumn("Min exp (y)", format="%d"),
        },
    )

    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered CSV",
        data=csv_bytes,
        file_name="glints_filtered.csv",
        mime="text/csv",
        help="Saves the currently-filtered view as a CSV file.",
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
# The ``gji-footer`` styling lives in ``_CUSTOM_CSS`` (injected once at
# module load) — we only need to emit the wrapper div here.

with st.container():
    st.markdown('<div class="gji-footer">', unsafe_allow_html=True)

    # Methodology expander — collapsed by default so the dashboard doesn't end
    # with a wall of text, but always reachable for a recruiter who wants to
    # verify how the numbers were produced. The notebooks linked here are the
    # single biggest credibility signal in the project: they show the
    # decisions a recruiter can't see in a polished chart.
    with st.expander("Methodology & data provenance", expanded=False):
        st.markdown(
            "**Pipeline.** This dashboard is the last step of a four-stage "
            "pipeline:\n\n"
            "1. **Scrape** links & details from Glints Indonesia with Playwright + parsel.\n"
            "2. **Clean** raw postings — parse IDR salary strings, normalise "
            "city names, detect 32 skill flags.\n"
            "3. **EDA** in Jupyter to surface the five headline findings.\n"
            "4. **Serve** this filtered view via Streamlit + Plotly + Folium.\n\n"
            "Read `clean.ipynb` and `eda.ipynb` in the repository for the full "
            "reproducible analysis."
        )
        source_text = (
            "**Source & repo.** Data scraped from [Glints Indonesia]"
            "(https://glints.com/id). Code, notebooks, and the schema doc live "
            "in the public repository."
        )
        if _REPO_URL:
            source_text = source_text.replace(
                "the public repository", f"the [public repo]({_REPO_URL})"
            )
        st.markdown(source_text)
        st.markdown(
            "**Known limitations.** Single-source bias (Glints only); "
            "salary figures are conditional on disclosure; skill detection is "
            "substring-based so it counts mentions, not requirements."
        )

    # Keep repository links optional so a local clone does not show broken
    # links before the owner configures GJI_REPO_URL.
    footer = "Built with Streamlit, Plotly, and Folium"
    if _REPO_URL:
        footer += (
            f" · [repo]({_REPO_URL}) · "
            f"[clean.ipynb]({_REPO_BLOB_URL}/clean.ipynb) · "
            f"[eda.ipynb]({_REPO_BLOB_URL}/eda.ipynb)"
        )
    else:
        footer += " · repository links are configured for the deployed app"
    st.caption(footer)

    st.markdown("</div>", unsafe_allow_html=True)
