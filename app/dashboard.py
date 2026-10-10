"""Glints Job Intel — Interactive Dashboard.

Aplikasi dashboard Streamlit untuk analisis bursa kerja profesi data Indonesia.
Dijalankan dengan perintah::

    streamlit run app/dashboard.py

Dashboard memuat dataset bersih hasil scraping Glints Indonesia, menyediakan
filter interaktif (peran, kota, tipe kerja, pengalaman, gaji, kata kunci),
dan menyajikan analisis dalam 6 tab:
1. Ringkasan Pasar
2. Babak 1: Inversi Ekspektasi (Unicorn Syndrome)
3. Babak 2: Ilusi WFH (Remote Luxury)
4. Lanskap Tech Stack & AI Hype
5. Sebaran Wilayah
6. Data Terfilter
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit call.
# ---------------------------------------------------------------------------
import streamlit as st

st.set_page_config(
    page_title="Glints Job Intel — Realita Pasar Kerja Data Indonesia",
    page_icon="🇮🇩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
_CUSTOM_CSS: str = (
    "<style>"
    ".gji-eyebrow{font-size:0.95rem;letter-spacing:0.14em;"
    "text-transform:uppercase;color:#5EEAD4;font-weight:600;"
    "display:block;}"
    ".gji-footer{background:#020617;border-top:3px solid #2DD4BF;"
    "border-radius:8px;padding:1.25rem 1.4rem;margin-top:1.25rem;}"
    ".gji-callout{background:#0f172a;border-left:4px solid #2DD4BF;"
    "padding:0.9rem 1.2rem;border-radius:4px;margin-bottom:1rem;color:#e2e8f0;}"
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

_REPO_URL: Final[str] = os.getenv("GJI_REPO_URL", "")
_REPO_BLOB_URL: Final[str] = f"{_REPO_URL}/blob/main"


def _render_map(m: object) -> None:
    if _st_folium is not None:
        _st_folium(m, height=520, returned_objects=[])
        return
    html = getattr(m, "_repr_html_", lambda: str(m))()
    st.components.v1.html(html, height=520, scrolling=False)


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
    return f"{arrow} {abs(diff):.1f}% vs total"


def _render_hero(fdf: pd.DataFrame, df: pd.DataFrame) -> None:
    stats = compute_summary_stats(fdf)
    left, right = st.columns([1, 1], vertical_alignment="center")
    with left:
        st.markdown(
            "<span class='gji-eyebrow'>"
            "Glints Job Intel · Riset Pasar Kerja Data Indonesia"
            "</span>",
            unsafe_allow_html=True,
            help="Analisis berbasis dataset lowongan kerja Glints Indonesia terverifikasi.",
        )
        st.markdown(f"# {stats['total_jobs']:,}")
        st.caption("lowongan kerja aktif")
        if len(fdf) != len(df):
            st.caption(
                f"Hasil filter dari {len(df):,} total lowongan · "
                f"{len(fdf) / len(df) * 100:.0f}% dataset"
            )
        else:
            st.caption(f"Dari total {len(df):,} lowongan terverifikasi")

    with right:
        with st.container(border=True):
            st.caption("Median Gaji Pasar")
            st.markdown(
                f"### {_format_salary_label(stats['median_salary_idr'] / 1_000_000)}"
            )

        with st.container(border=True):
            st.caption("Peran Dominan · Kota Terbanyak")
            st.markdown(f"### {stats['top_role']} · {stats['top_city']}")


def _render_context(df: pd.DataFrame) -> None:
    insights = compute_market_insights(df)
    with st.container(border=True):
        st.markdown("**Panduan Membaca Dashboard & Sumber Data**")
        st.caption(
            "Gunakan tab narasi untuk menyelami temuan kunci: Babak 1 (Inversi Ekspektasi), "
            "Babak 2 (Ilusi Fleksibilitas WFH), dan Lanskap Tech Stack. Filter di sidebar akan "
            "memperbarui seluruh grafik secara interaktif."
        )
        st.caption(
            f"Analisis berbasis data riil Glints Indonesia (100% berbasis di Indonesia). "
            f"{insights['salary_disclosure_pct']:.0f}% lowongan mencantumkan nominal gaji transparan. "
            "Grafik analisis kompensasi berfokus pada data yang terbuka tanpa imputasi sintesis."
        )


def _render_insight_cards(df: pd.DataFrame) -> None:
    insights = compute_market_insights(df)
    top_skill = insights["top_skill"]
    top_skill_label = _format_skill_label(top_skill) if top_skill != "n/a" else "n/a"
    cards = [
        (
            "Tuntutan Skill Teratas",
            f"{top_skill_label} · {insights['top_skill_share_pct']:.0f}%",
            "Proporsi lowongan yang mensyaratkan skill ini.",
        ),
        (
            "Pusat Karir Terbesar",
            f"{insights['top_city_share_pct']:.0f}% lowongan",
            "Pangsa lowongan di kota perekrut nomor satu.",
        ),
        (
            "Porsi Fresh Graduate",
            f"{insights['fresh_graduate_share_pct']:.0f}%",
            "Lowongan dengan syarat pengalaman kerja 0 tahun.",
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

    with st.expander("Pencarian Kata Kunci", expanded=True):
        search = st.text_input(
            "Cari posisi atau nama perusahaan",
            value="",
            placeholder="contoh: data analyst, Gojek, BCA",
            help="Pencarian substring pada judul lowongan dan nama perusahaan.",
        )

    with st.expander("Filter Segmen & Wilayah", expanded=False):
        role_filter = st.multiselect(
            "Peran / Bidang Data",
            options=role_options,
            default=None,
            help="Filter berdasarkan rumpun profesi (Data Analyst, Engineer, Scientist, ML).",
        )
        city_filter = st.multiselect(
            "Kota / Wilayah",
            options=city_options,
            default=None,
            help="Filter berdasarkan kota penempatan.",
        )
        work_filter = st.multiselect(
            "Model Kerja",
            options=work_options,
            default=None,
            help="On-site / Remote / Hybrid.",
        )

    with st.expander("Filter Pengalaman & Gaji", expanded=False):
        experience_values = (
            pd.to_numeric(df["exp_min_years"], errors="coerce").dropna()
            if "exp_min_years" in df.columns
            else pd.Series(dtype=float)
        )
        exp_min = int(experience_values.min()) if not experience_values.empty else 0
        exp_max = int(experience_values.max()) if not experience_values.empty else 10
        exp_slider_max = max(exp_max, exp_min + 1)
        exp_filter = st.slider(
            "Pengalaman Minimal (Tahun)",
            min_value=exp_min,
            max_value=exp_slider_max,
            value=(exp_min, exp_slider_max),
            step=1,
            help="Rentang tahun pengalaman kerja minimal yang disyaratkan.",
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
            "Rentang Gaji (Juta IDR / Bulan)",
            min_value=0,
            max_value=salary_cap_m,
            value=(0, salary_cap_m),
            step=1,
            help=f"Rentang kompensasi dalam juta Rupiah. Batas atas diatur hingga Rp {salary_cap_m} Juta.",
        )

    st.divider()
    st.caption(f"Termuat {len(df):,} baris data · {len(skill_cols)} skill tags terdeteksi.")


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


# ---------------------------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------------------------

if fdf.empty:
    st.warning(
        "Tidak ada lowongan yang sesuai dengan kriteria filter saat ini. "
        "Coba perluas rentang gaji, hilangkan seleksi kota/peran, atau ubah kata kunci pencarian."
    )
    st.stop()

_render_hero(fdf, df)
_render_context(df)
st.markdown("")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_act1, tab_act2, tab_act3, tab_geo, tab_data = st.tabs(
    [
        "Ringkasan Pasar",
        "Babak 1: Beban Kualifikasi Fresh Graduate",
        "Babak 2: Realita WFO & Premi Remote",
        "Lanskap Tech Stack",
        "Sebaran Wilayah",
        "Data Terfilter",
    ]
)

# ---- Ringkasan Pasar ------------------------------------------------------
with tab_overview:
    stats = compute_summary_stats(fdf)
    base_stats = compute_summary_stats(df)

    st.subheader("Ikhtisar Pasar Kerja")
    _render_insight_cards(fdf)
    st.caption(
        "Metrik di atas dihitung secara dinamis dari lowongan yang memenuhi kriteria filter."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Total Lowongan",
        f"{stats['total_jobs']:,}",
        delta=_format_delta(stats["total_jobs"], base_stats["total_jobs"]) or None,
    )
    c2.metric(
        "Perusahaan Unik",
        f"{stats['unique_companies']:,}",
        delta=_format_delta(stats["unique_companies"], base_stats["unique_companies"]) or None,
    )
    c3.metric(
        "Median Gaji",
        _format_salary_label(stats["median_salary_idr"] / 1_000_000),
        delta=_format_delta(stats["median_salary_idr"], base_stats["median_salary_idr"]) or None,
    )
    c4.metric(
        "Porsi Remote",
        f"{stats['remote_share_pct']:.1f}%",
        delta=_format_delta(stats["remote_share_pct"], base_stats["remote_share_pct"]) or None,
    )

    st.subheader("Distribusi Peluang Karir")
    st.caption(
        "Komposisi bidang peran dan model kerja memperlihatkan struktur penyerapan tenaga kerja saat ini."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Lowongan Berdasarkan Peran")
        st.plotly_chart(plot_role_distribution(fdf), use_container_width=True)
    with col_b:
        st.subheader("Lowongan Berdasarkan Model Kerja")
        st.plotly_chart(plot_workplace_type_distribution(fdf), use_container_width=True)

    st.subheader("Distribusi Gaji per Rumpun Profesi")
    st.plotly_chart(
        plot_salary_distribution(fdf, by="keyword"),
        use_container_width=True,
    )


# ---- Babak 1: Beban Kualifikasi Fresh Graduate ---------------------------
with tab_act1:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Temuan Empiris Babak 1 (Beban Kualifikasi Entry-Level):</strong><br>"
        "Posisi <em>Fresh Graduate</em> (< 1 tahun) justru menanggung tuntutan skill akademis paling padat "
        "(Python 70,6%, Statistik 58,8%, Machine Learning 47,1%) dengan median gaji <strong>Rp 4,2 Juta</strong>. "
        "Sebaliknya, posisi Mid/Senior (> 3 tahun) lebih terfokus pada integrasi pipeline terapan (ETL 41,5%, "
        "Power BI/Tableau 35,1%, Cloud 27,7%) dengan kompensasi berlipat ganda (<strong>Rp 9,0 – 15,0+ Juta</strong>)."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Beban Kualifikasi Skill: Fresh Graduate vs Mid/Senior")
    st.caption(
        "Persentase lowongan yang menuntut skill teoritis berat (Python, Stats, ML) vs tools integrasi praktis (ETL, BI, Cloud) "
        "berdasarkan kelompok jenjang pengalaman kerja."
    )
    st.plotly_chart(plot_skill_burden_by_career_stage(fdf), use_container_width=True)

    st.subheader("The Reality Curve: Sebaran Gaji Aktual vs Tahun Pengalaman")
    st.caption(
        "Kurva realitas gaji menunjukkan kompensasi pemula yang tertekan di kisaran UMR (< Rp 4,5 Juta) "
        "sebelum melonjak tajam setelah melewati masa kerja 2–3 tahun."
    )
    st.plotly_chart(plot_salary_reality_curve(fdf), use_container_width=True)

    st.subheader("Hambatan Masuk (Barrier to Entry): Pengalaman & Standar Akademis")
    st.caption(
        "Hanya sebagian kecil lowongan yang menerima pengalaman 0 tahun; mayoritas mensyaratkan ijazah S1."
    )
    col_exp, col_edu = st.columns(2)
    with col_exp:
        st.plotly_chart(plot_experience_distribution(fdf), use_container_width=True)
    with col_edu:
        st.plotly_chart(plot_education_distribution(fdf), use_container_width=True)


# ---- Babak 2: Realita WFO & Premi Remote ----------------------------------
with tab_act2:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Temuan Empiris Babak 2 (Disparitas Kompensasi Kerja Remote):</strong><br>"
        "Lebih dari <strong>90,7%</strong> lowongan data di Indonesia mewajibkan kerja <strong>On-site (WFO)</strong>. "
        "Full Remote hanya tersedia di 3,5% lowongan. Namun, posisi remote menawarkan median gaji <strong>Rp 12,5 Juta</strong> "
        "vs On-site <strong>Rp 7,0 Juta</strong> (+78,6% premium). Akses kerja remote di Indonesia masih sangat terbatas "
        "dan umumnya dialokasikan untuk talenta spesialis berpengalaman atau korporasi skala regional."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Distribusi Model Kerja vs Median Gaji (Premi Remote)")
    st.caption(
        "Perbandingan langsung antara pangsa pasar model kerja dan besaran kompensasi yang ditawarkan."
    )
    st.plotly_chart(plot_remote_luxury_comparison(fdf), use_container_width=True)

    st.subheader("Rincian Model Kerja & Premi Gaji Remote")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.plotly_chart(plot_workplace_type_distribution(fdf), use_container_width=True)
    with col_w2:
        st.plotly_chart(plot_remote_premium(fdf), use_container_width=True)


# ---- Lanskap Tech Stack ---------------------------------------------------
with tab_act3:
    st.markdown(
        "<div class='gji-callout'>"
        "<strong>Temuan Empiris Babak 3 (Fondasi Riil vs AI Hype):</strong><br>"
        "<strong>SQL</strong> (428 mentions) dan <strong>Excel</strong> (246 mentions) adalah fondasi nyata "
        "industri bisnis Indonesia. Tools berbasis AI canggih (PyTorch, TensorFlow) hanya menempati jajaran bawah "
        "(< 30 mentions). Perusahaan memprioritaskan otomatisasi pelaporan dan konsistensi data sebelum kecerdasan buatan."
        "</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Lanskap Kebutuhan Tech Stack Nyata")
    st.caption(
        "Frekuensi kemunculan kata kunci tools teknis di seluruh deskripsi lowongan kerja data di Indonesia."
    )
    st.plotly_chart(plot_real_tech_stack_landscape(fdf), use_container_width=True)

    st.subheader("Klasterisasi Hubungan Antar-Skill (Jaccard Co-occurrence)")
    st.caption(
        "Korelasi kemunculan bersama antar 12 skill teratas memperlihatkan klaster Analis (SQL/Excel/BI), "
        "Data Science (Python/Stats/ML), dan Data Engineering (SQL/ETL/Cloud)."
    )
    st.plotly_chart(plot_skill_cooccurrence_heatmap(fdf, top_n=12), use_container_width=True)

    st.subheader("Premi Kompensasi per Skill & Perusahaan Perekrut")
    c_sk1, c_sk2 = st.columns(2)
    with c_sk1:
        st.caption("Premi gaji per skill (selisih median lowongan yang mensyaratkan vs yang tidak).")
        st.plotly_chart(plot_skill_vs_salary(fdf, top_n=15), use_container_width=True)
    with c_sk2:
        st.caption("Perusahaan dengan volume perekrutan data terbanyak.")
        st.plotly_chart(plot_top_companies(fdf, top_n=15), use_container_width=True)


# ---- Sebaran Wilayah -----------------------------------------------------
with tab_geo:
    st.subheader("Peta Persebaran Peluang Kerja di Indonesia")
    st.caption(
        "Lokasi dinormalisasi dari teks alamat penempatan kerja pada data Glints. "
        "Jakarta dan wilayah Jabodetabek memegang konsentrasi lowongan kerja data tertinggi."
    )
    _render_map(plot_geo_map(fdf))

    st.markdown("**Ringkasan Lowongan per Kota**")
    st.caption(
        "Tabel agregasi data per kota. Klik judul kolom untuk mengurutkan data."
    )
    st.dataframe(
        city_summary(fdf),
        use_container_width=True,
        hide_index=True,
        column_config={
            "count": st.column_config.NumberColumn("Jumlah Lowongan", format="%d"),
            "median_salary": st.column_config.NumberColumn(
                "Median Gaji", format="Rp %.1f Jt"
            ),
            "remote_pct": st.column_config.NumberColumn("Porsi Remote", format="%.1f%%"),
            "top_role": st.column_config.TextColumn("Peran Terbanyak"),
        },
    )


# ---- Data Terfilter ------------------------------------------------------
with tab_data:
    st.subheader("Dataset Hasil Filter")
    st.caption(
        "Tabel data terverifikasi yang digunakan dalam visualisasi. "
        "Anda dapat mengunduh data dalam format CSV untuk analisis lanjutan."
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
            "job_title": st.column_config.TextColumn("Judul Posisi"),
            "company_name": st.column_config.TextColumn("Perusahaan"),
            "city_clean": st.column_config.TextColumn("Kota"),
            "keyword": st.column_config.TextColumn("Peran"),
            "workplace_type": st.column_config.TextColumn("Tipe Kerja"),
            "salary_avg": st.column_config.NumberColumn(
                "Estimasi Gaji (IDR / Bulan)", format="Rp %.0f"
            ),
            "exp_min_years": st.column_config.NumberColumn("Min Pengalaman (Thn)", format="%d"),
            "job_education_clean": st.column_config.TextColumn("Pendidikan"),
        },
    )

    csv_bytes = fdf.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Unduh CSV Terfilter",
        data=csv_bytes,
        file_name="glints_data_jobs_filtered.csv",
        mime="text/csv",
        help="Simpan tampilan data saat ini ke dalam file CSV.",
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

with st.container():
    st.markdown('<div class="gji-footer">', unsafe_allow_html=True)

    with st.expander("Metodologi & Validasi Data (Data Provenance)", expanded=False):
        st.markdown(
            "**Pipeline Scraping & Pembersihan Data:**\n\n"
            "1. **Scraping Terstruktur:** Mengambil data tautan dan detail lowongan kerja dari portal Glints Indonesia "
            "menggunakan Playwright + Parsel dengan teknik bypassing bot yang higienis.\n"
            "2. **Standardisasi & Validasi:** Memfilter 100% lowongan kerja berbasis di Indonesia (membuang data regional luar negeri), "
            "mengurai nominal gaji Rupiah ke format numerik standar, serta mengekstrak 32 tag kompetensi teknis.\n"
            "3. **Analisis Lanjutan:** Disajikan secara interaktif menggunakan Streamlit, Plotly, dan Folium.\n\n"
            "Seluruh langkah eksplorasi dan replikasi dapat dilihat pada notebook `clean.ipynb` dan `eda.ipynb`."
        )
        source_text = (
            "**Sumber Data:** Data lowongan aktif dari [Glints Indonesia](https://glints.com/id). "
            "Seluruh kode sumber dan dataset tersedia di repositori publik."
        )
        if _REPO_URL:
            source_text = source_text.replace(
                "repositori publik", f"[repositori publik]({_REPO_URL})"
            )
        st.markdown(source_text)

    footer = "Dibuat dengan Streamlit, Plotly, dan Folium"
    if _REPO_URL:
        footer += f" · [Repositori]({_REPO_URL})"
    st.caption(footer)

    st.markdown("</div>", unsafe_allow_html=True)
