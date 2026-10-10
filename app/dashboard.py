"""Glints Job Intel — Interactive Dashboard.

Dashboard eksplorasi pasar kerja profesi data di Indonesia berbasis dataset Glints.
Dijalankan dengan perintah::

    streamlit run app/dashboard.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Pasar Kerja Data Indonesia — Analisis Glints",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
_CUSTOM_CSS: str = (
    "<style>"
    ".gji-footer{background:#131B2E;border-top:1px solid #1E293B;"
    "border-radius:8px;padding:1.25rem 1.4rem;margin-top:2rem;}"
    ".gji-callout{background:#131B2E;border-left:3px solid #38BDF8;"
    "padding:0.85rem 1.15rem;border-radius:4px;margin-bottom:1rem;color:#E2E8F0;font-size:0.92rem;line-height:1.5;}"
    "</style>"
)
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
import os  # noqa: E402
from typing import Final  # noqa: E402

import pandas as pd  # noqa: E402

from app.charts import (  # noqa: E402
    plot_education_distribution,
    plot_experience_distribution,
    plot_real_tech_stack_landscape,
    plot_remote_luxury_comparison,
    plot_remote_premium,
    plot_role_distribution,
    plot_salary_distribution,
    plot_salary_reality_curve,
    plot_salary_vs_experience,
    plot_skill_burden_by_career_stage,
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

try:  # pragma: no cover
    from streamlit_folium import st_folium as _st_folium
except ImportError:  # pragma: no cover
    _st_folium = None

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

_REPO_URL: Final[str] = os.getenv("GJI_REPO_URL", "")


def _render_map(m: object) -> None:
    if _st_folium is not None:
        _st_folium(m, height=500, returned_objects=[])
        return
    html = getattr(m, "_repr_html_", lambda: str(m))()
    st.components.v1.html(html, height=500, scrolling=False)


def _format_salary_label(m_idr: float) -> str:
    return f"Rp {m_idr:,.1f} Juta"


def _format_skill_label(name: str) -> str:
    return pretty_skill_label(f"skill_{name}")


def _round_up_to(value: float, step: int) -> int:
    if step <= 0:
        raise ValueError("step must be positive")
    return int((int(value) + step - 1) // step * step)


def _format_delta(curr: float, base: float) -> str | None:
    if base == 0:
        return None
    diff = (curr - base) / base * 100.0
    arrow = "▲" if diff >= 0 else "▼"
    return f"{arrow} {abs(diff):.1f}% vs baseline"


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

with st.spinner("Memuat dataset..."):
    try:
        raw_df = load_master_dataset()
        df, skill_cols = build_skill_columns(raw_df)
    except FileNotFoundError as exc:
        st.error(
            f"**Dataset tidak ditemukan.**\n\n"
            f"{exc}\n\n"
            "Pastikan dataset olahan tersedia di `data/processed/master_dataset_eda.csv`."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Filter Analisis")

    role_options: list[str] = sorted(df["keyword"].dropna().astype(str).unique().tolist()) if "keyword" in df.columns else []
    city_options: list[str] = sorted(df["city_clean"].dropna().astype(str).unique().tolist()) if "city_clean" in df.columns else []
    work_options: list[str] = sorted(df["workplace_type"].dropna().astype(str).unique().tolist()) if "workplace_type" in df.columns else []

    with st.expander("Pencarian", expanded=True):
        search = st.text_input(
            "Posisi atau perusahaan",
            value="",
            placeholder="contoh: data analyst, Gojek",
            help="Pencarian substring pada judul lowongan dan nama perusahaan.",
        )

    with st.expander("Segmen & Lokasi", expanded=False):
        role_filter = st.multiselect(
            "Peran data",
            options=role_options,
            default=None,
            help="Filter berdasarkan rumpun profesi data.",
        )
        city_filter = st.multiselect(
            "Kota",
            options=city_options,
            default=None,
            help="Filter berdasarkan kota penempatan.",
        )
        work_filter = st.multiselect(
            "Model kerja",
            options=work_options,
            default=None,
            help="On-site / Remote / Hybrid.",
        )

    with st.expander("Pengalaman & Gaji", expanded=False):
        experience_values = (
            pd.to_numeric(df["exp_min_years"], errors="coerce").dropna()
            if "exp_min_years" in df.columns
            else pd.Series(dtype=float)
        )
        exp_min = int(experience_values.min()) if not experience_values.empty else 0
        exp_max = int(experience_values.max()) if not experience_values.empty else 10
        exp_slider_max = max(exp_max, exp_min + 1)
        exp_filter = st.slider(
            "Pengalaman minimal (tahun)",
            min_value=exp_min,
            max_value=exp_slider_max,
            value=(exp_min, exp_slider_max),
            step=1,
        )

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
            "Rentang gaji (juta IDR / bulan)",
            min_value=0,
            max_value=salary_cap_m,
            value=(0, salary_cap_m),
            step=1,
        )

    st.divider()
    st.caption(f"{len(df):,} lowongan terverifikasi · {len(skill_cols)} skill tags terdeteksi.")


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

if (
    "salary_avg" in fdf.columns
    and not fdf.empty
    and salary_range != (0, salary_cap_m)
):
    salary_low = salary_range[0] * 1_000_000
    salary_high = salary_range[1] * 1_000_000
    fdf = fdf[(fdf["salary_avg"] >= salary_low) & (fdf["salary_avg"] <= salary_high)]

if fdf.empty:
    st.warning("Tidak ada lowongan yang cocok dengan filter yang dipilih. Silakan reset filter.")
    st.stop()


# ---------------------------------------------------------------------------
# Header & KPI Metrics
# ---------------------------------------------------------------------------

stats = compute_summary_stats(fdf)
base_stats = compute_summary_stats(df)
insights = compute_market_insights(fdf)

st.title("Pasar Kerja Profesi Data di Indonesia")
st.caption(
    f"Analisis terhadap {len(df):,} lowongan kerja aktif Glints Indonesia "
    f"(100% berbasis di Indonesia · {insights['salary_disclosure_pct']:.0f}% mencantumkan nominal gaji transparan)."
)

kpi_cols = st.columns(4)
kpi_cols[0].metric(
    "Total Lowongan",
    f"{stats['total_jobs']:,}",
    delta=_format_delta(stats["total_jobs"], base_stats["total_jobs"]) or None,
)
kpi_cols[1].metric(
    "Median Gaji Pasar",
    _format_salary_label(stats["median_salary_idr"] / 1_000_000),
    delta=_format_delta(stats["median_salary_idr"], base_stats["median_salary_idr"]) or None,
)
kpi_cols[2].metric(
    "Peran Terbanyak",
    stats["top_role"],
)
kpi_cols[3].metric(
    "Porsi Kerja Remote",
    f"{stats['remote_share_pct']:.1f}%",
    delta=_format_delta(stats["remote_share_pct"], base_stats["remote_share_pct"]) or None,
)

st.markdown("")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_kualifikasi, tab_model_kerja, tab_tech, tab_geo, tab_data = st.tabs(
    [
        "Ringkasan",
        "Beban Kualifikasi",
        "Model Kerja & Gaji",
        "Tech Stack",
        "Sebaran Wilayah",
        "Dataset",
    ]
)

# ---- Tab: Ringkasan ------------------------------------------------------
with tab_overview:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Distribusi Peran Data")
        st.plotly_chart(plot_role_distribution(fdf), use_container_width=True)
    with col_b:
        st.subheader("Distribusi Model Kerja")
        st.plotly_chart(plot_workplace_type_distribution(fdf), use_container_width=True)

    st.subheader("Distribusi Gaji per Rumpun Profesi")
    st.plotly_chart(plot_salary_distribution(fdf, by="keyword"), use_container_width=True)


# ---- Tab: Beban Kualifikasi ----------------------------------------------
with tab_kualifikasi:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Disparitas Kualifikasi:</strong> Lowongan tingkat pemula (<1 tahun pengalaman) menuntut proporsi skill teoritis tertinggi "
        "(Python 70,6%, Statistik 58,8%, Machine Learning 47,1%) dengan median gaji Rp 4,2 juta. "
        "Sebaliknya, posisi di atas 3 tahun pengalaman lebih memprioritaskan integrasi operasional "
        "(ETL 41,5%, Power BI/Tableau 35,1%, Cloud 27,7%) dengan median gaji Rp 9,0 – 15,0+ juta."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Beban Kualifikasi Skill per Jenjang Pengalaman")
    st.caption("Perbandingan proporsi tuntutan skill teknis antara jenjang Fresh Graduate, Junior, dan Mid/Senior.")
    st.plotly_chart(plot_skill_burden_by_career_stage(fdf), use_container_width=True)

    st.subheader("Sebaran Gaji Aktual vs Tahun Pengalaman")
    st.caption("Korelasi antara tahun pengalaman kerja minimum dengan rata-rata kompensasi bulanan.")
    st.plotly_chart(plot_salary_reality_curve(fdf), use_container_width=True)

    col_exp, col_edu = st.columns(2)
    with col_exp:
        st.subheader("Syarat Pengalaman Minimum")
        st.plotly_chart(plot_experience_distribution(fdf), use_container_width=True)
    with col_edu:
        st.subheader("Standar Pendidikan")
        st.plotly_chart(plot_education_distribution(fdf), use_container_width=True)


# ---- Tab: Model Kerja & Gaji ---------------------------------------------
with tab_model_kerja:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Ketersediaan Kerja Remote:</strong> Sebanyak 90,7% lowongan mensyaratkan kerja On-site (WFO). "
        "Opsi Full Remote hanya mencakup 3,5% dari total lowongan, namun menawarkan median gaji Rp 12,5 juta "
        "dibandingkan On-site Rp 7,0 juta (+78,6% premi). Di pasar lokal, fasilitas remote umumnya diberikan kepada "
        "posisi spesialis atau perusahaan multinasional/regional."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Distribusi Model Kerja & Perbandingan Gaji Median")
    st.caption("Perbandingan proporsi jumlah lowongan dan median kompensasi antara On-site, Hybrid, dan Remote.")
    st.plotly_chart(plot_remote_luxury_comparison(fdf), use_container_width=True)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader("Pangsa Model Kerja")
        st.plotly_chart(plot_workplace_type_distribution(fdf), use_container_width=True)
    with col_w2:
        st.subheader("Premi Kompensasi Model Kerja")
        st.plotly_chart(plot_remote_premium(fdf), use_container_width=True)


# ---- Tab: Tech Stack -----------------------------------------------------
with tab_tech:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Prioritas Kebutuhan Tools:</strong> SQL (428 kemunculan) dan Excel (246 kemunculan) merupakan kebutuhan mutlak "
        "di hampir seluruh lowongan. Framework deep learning (PyTorch, TensorFlow) hanya muncul pada sebagian kecil posisi riset (<30 kemunculan)."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Frekuensi Kebutuhan Tools di Industri")
    st.caption("Peringkat kemunculan kata kunci tools teknis dalam deskripsi lowongan kerja data.")
    st.plotly_chart(plot_real_tech_stack_landscape(fdf), use_container_width=True)

    st.subheader("Ko-okurensi Keahlian (Jaccard Index)")
    st.caption("Tingkat kemunculan bersama antara 12 keahlian paling umum dalam satu lowongan pekerjaan.")
    st.plotly_chart(plot_skill_cooccurrence_heatmap(fdf, top_n=12), use_container_width=True)

    c_sk1, c_sk2 = st.columns(2)
    with c_sk1:
        st.subheader("Premi Median Gaji per Keahlian")
        st.plotly_chart(plot_skill_vs_salary(fdf, top_n=15), use_container_width=True)
    with c_sk2:
        st.subheader("Perusahaan dengan Lowongan Terbanyak")
        st.plotly_chart(plot_top_companies(fdf, top_n=15), use_container_width=True)


# ---- Tab: Sebaran Wilayah ------------------------------------------------
with tab_geo:
    st.subheader("Peta Persebaran Lowongan Data di Indonesia")
    _render_map(plot_geo_map(fdf))

    st.subheader("Ringkasan Data per Kota")
    st.dataframe(
        city_summary(fdf),
        use_container_width=True,
        hide_index=True,
        column_config={
            "count": st.column_config.NumberColumn("Jumlah Lowongan", format="%d"),
            "median_salary": st.column_config.NumberColumn("Median Gaji", format="Rp %.1f Jt"),
            "remote_pct": st.column_config.NumberColumn("Porsi Remote", format="%.1f%%"),
            "top_role": st.column_config.TextColumn("Peran Terbanyak"),
        },
    )


# ---- Tab: Dataset --------------------------------------------------------
with tab_data:
    st.subheader("Tabel Data Hasil Filter")
    st.caption("Data terverifikasi yang digunakan dalam dashboard. Data dapat diunduh dalam format CSV.")
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
            "job_title": st.column_config.TextColumn("Posisi"),
            "company_name": st.column_config.TextColumn("Perusahaan"),
            "city_clean": st.column_config.TextColumn("Kota"),
            "keyword": st.column_config.TextColumn("Peran"),
            "workplace_type": st.column_config.TextColumn("Tipe"),
            "salary_avg": st.column_config.NumberColumn("Gaji (IDR/Bulan)", format="Rp %.0f"),
            "exp_min_years": st.column_config.NumberColumn("Min Pengalaman (Thn)", format="%d"),
            "job_education_clean": st.column_config.TextColumn("Pendidikan"),
        },
    )

    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Unduh CSV",
        data=csv_bytes,
        file_name="glints_data_jobs_filtered.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

with st.container():
    st.markdown('<div class="gji-footer">', unsafe_allow_html=True)
    st.markdown(
        "**Metodologi Data:** Dikumpulkan via scraping terstruktur Playwright dari portal Glints Indonesia. "
        "Data disaring dengan standar ketat (100% lokasi Indonesia, normalisasi gaji Rupiah, deduplikasi, dan ekstraksi 32 fitur skill). "
        "Laporan analitis mandiri tersedia di berkas `eda_report.html`."
    )
    if _REPO_URL:
        st.caption(f"[GitHub Repository]({_REPO_URL})")
    st.markdown("</div>", unsafe_allow_html=True)
