"""Generate the clean, professional eda.ipynb without AI slop or emoji spam."""
from pathlib import Path
import nbformat as nbf

def create_eda_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13"
        }
    }

    cells = []

    # Cell 1: Title & Executive Summary
    cells.append(nbf.v4.new_markdown_cell("""# Analisis Pasar Kerja Profesi Data di Indonesia
### Riset Empiris Berbasis 430 Lowongan Kerja Glints Indonesia

Notebook ini menyajikan analisis empiris terhadap kondisi pasar tenaga kerja sektor data di Indonesia (*Data Analyst, Data Engineer, Data Scientist, ML Engineer*). Analisis dibangun di atas 430 lowongan kerja aktif dari Glints Indonesia yang telah melalui kurasi ketat (100% berbasis di Indonesia, deduplikasi, dan pembersihan data).

---

## Ringkasan Eksekutif

Dari 430 lowongan kerja data yang dianalisis (349 di antaranya mencantumkan estimasi gaji transparan):

1. **Paradoks Kualifikasi Entry-Level vs Pergeseran Senior:** Hanya **8,4%** lowongan (36 dari 430) yang terbuka bagi *Fresh Graduate* (0 tahun pengalaman), sedangkan **91,6%** mensyaratkan minimal 1 tahun pengalaman (1–2 tahun: 47,7%, 3+ tahun: 43,9%). Lowongan *Fresh Graduate* (<1 tahun) justru menuntut proporsi skill fundamental paling padat: **SQL (88,9%)**, **Python (77,8%)**, **Excel (72,2%)**, **Statistika (66,7%)**, dan **Machine Learning (50,0%)**, dengan **median gaji Rp 5,25 juta/bulan** (Q1 Rp 2,9 juta – Q3 Rp 5,86 juta). Sebaliknya, pada jenjang *Mid/Senior* (3+ tahun), kebutuhan bergeser ke arsitektur data produksi: **ETL / Pipeline melonjak dari 25,0% ke 46,0%** dan **Cloud naik dari 13,9% ke 28,0%**, dengan kompensasi yang melompat ke median **Rp 9,0 juta** (Mid-Level) dan **Rp 17,5 juta** (Senior 5+ tahun).
2. **Sentralisasi Geografis & Langkanya Kerja Remote (*Double Barrier*):** Pasar kerja data Indonesia sangat tersentralisasi: **93,0%** lowongan mewajibkan **On-site / WFO** (400 lowongan), **4,2% Hybrid** (18 lowongan), dan hanya **2,8% Full Remote** (12 lowongan). Secara geografis, **83,5% lowongan terpusat di Jabodetabek** (Jakarta 65,8%, Tangerang 13,0%, Depok/Bekasi/Bogor 4,7%), diikuti Bandung (4,9%) dan Surabaya (4,4%). Kombinasi ini menciptakan hambatan ganda (*double barrier*) bagi talenta di luar Jabodetabek. Meskipun sangat terbatas (2,8%), lowongan Full Remote menawarkan **median gaji Rp 12,5 juta/bulan**—premi **+78,6%** dibandingkan On-site dan Hybrid (keduanya di angka Rp 7,0 juta/bulan).
3. **Hierarki Tech Stack Industri (Fondasi Operasional vs Hype AI):** Tiga fondasi utama yang paling banyak diminta adalah **SQL (329 lowongan / 76,5%)**, **Python (243 lowongan / 56,5%)**, dan **Excel (190 lowongan / 44,2%)**. Lapis kedua ditempati ekosistem analytics & data pipeline: **Machine Learning (144 / 33,5%)**, **ETL (139 / 32,3%)**, **Power BI (139 / 32,3%)**, **Tableau (114 / 26,5%)**, dan **Statistika (114 / 26,5%)**. Sebaliknya, framework deep learning spesifik seperti **TensorFlow (20 lowongan / 4,7%)** dan **PyTorch (18 lowongan / 4,2%)** hanya muncul pada kurang dari 5% lowongan.
4. **Pintu Masuk Fresh Graduate:** Ketiadaan jalur masuk formal bagi 91,6% lowongan menegaskan bahwa portofolio proyek terapan end-to-end (ingestion, cleaning, modeling/dashboarding) adalah instrumen verifikasi mutlak bagi kandidat pemula untuk membuktikan kompetensi praktis."""))

    # Cell 2: Setup and Data Loading
    cells.append(nbf.v4.new_markdown_cell("""---

## Setup Environment & Data Loading

Pemuatan master dataset `data/processed/master_dataset_eda.csv` dan modul visualisasi terpusat dari `app.charts`."""))

    # Cell 3: Code - Imports & Data Loading
    cells.append(nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import plotly.io as pio

# Menggunakan renderer 'png' agar visualisasi grafik langsung tampil di GitHub notebook viewer
# (GitHub secara default memblokir eksekusi script JavaScript interaktif Plotly pada file .ipynb).
pio.renderers.default = "png"

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

from app.data import build_skill_columns
from app.charts import (
    plot_skill_burden_by_career_stage,
    plot_salary_reality_curve,
    plot_remote_luxury_comparison,
    plot_real_tech_stack_landscape,
    plot_experience_distribution,
    plot_education_distribution,
    plot_salary_distribution,
    plot_workplace_type_distribution,
    plot_skill_cooccurrence_heatmap,
    plot_salary_vs_experience,
    plot_skill_vs_salary,
    plot_top_companies,
    plot_remote_premium,
    plot_role_distribution,
    plot_top_skills_bar,
)

df = pd.read_csv("data/processed/master_dataset_eda.csv")
df, skill_cols = build_skill_columns(df)

disclosed_salaries = df["salary_avg"].notna().sum()
print(f"[DATA] Total lowongan terverifikasi: {len(df):,}")
print(f"[TECH STACK] Fitur skill terdeteksi: {len(skill_cols)}")
print(f"[GAJI] Tingkat transparansi gaji: {disclosed_salaries:,} ({disclosed_salaries/len(df):.1%})")"""))

    # Cell 4: Section 1 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 1. Beban Kualifikasi pada Posisi Entry-Level

Pemetaan tuntutan skill teknis berdasarkan kelompok pengalaman kerja yang dipersyaratkan:
- Fresh Graduate: Pengalaman < 1 tahun
- Junior: Pengalaman 1 – 2 tahun
- Mid / Senior: Pengalaman 3 tahun ke atas"""))

    # Cell 5: Skill Burden Chart
    cells.append(nbf.v4.new_code_cell("""fig_skill_burden = plot_skill_burden_by_career_stage(df)
fig_skill_burden.show()"""))

    # Cell 6: Skill Burden Insight
    cells.append(nbf.v4.new_markdown_cell("""### Analisis Temuan

1. **Beban Teori & Multi-role pada Posisi Pemula:** Posisi *Fresh Graduate* (<1 tahun) mencatatkan proporsi tuntutan skill teknis paling padat: SQL (88,9%), Python (77,8%), Excel (72,2%), Statistika (66,7%), dan Machine Learning (50,0%). Pola ini mencerminkan kecenderungan organisasi yang baru merintis kapabilitas data untuk merekrut *single-person data team* dengan alokasi anggaran entry-level.
2. **Pergeseran Kebutuhan pada Posisi Senior:** Pada jenjang Mid/Senior (3+ tahun), tuntutan pengolahan spreadsheet dasar dan teori menurun tajam (Excel turun dari 72,2% ke 30,2%, Statistika turun dari 66,7% ke 18,5%). Prioritas beralih ke stabilitas sistem data produksi: **ETL / Data Pipeline melonjak dari 25,0% ke 46,0%** dan **arsitektur Cloud (AWS/GCP/Azure) naik dari 13,9% ke 28,0%**."""))

    # Cell 7: Salary Curve Intro
    cells.append(nbf.v4.new_markdown_cell("""### Sebaran Kompensasi Aktual Berdasarkan Pengalaman Kerja"""))

    # Cell 8: Salary Curve Chart
    cells.append(nbf.v4.new_code_cell("""fig_reality_curve = plot_salary_reality_curve(df)
fig_reality_curve.show()"""))

    # Cell 9: Salary Curve Insight
    cells.append(nbf.v4.new_markdown_cell("""Distribusi gaji memperlihatkan kurva kompensasi riil pasar data Indonesia:
- **Fresh Graduate (0 tahun):** Median gaji berada di angka **Rp 5,25 juta/bulan** (rentang Q1 Rp 2,9 juta – Q3 Rp 5,86 juta).
- **Junior (1–2 tahun):** Median gaji naik moderat ke **Rp 6,5 juta/bulan**.
- **Inflection Point:** Lompatan kompensasi signifikan baru terjadi saat memasuki level **Mid-Level (3 tahun: median Rp 9,0 juta/bulan)** dan **Senior (5+ tahun: median Rp 17,5 juta/bulan)**."""))

    # Cell 10: Experience & Education Distribution Intro
    cells.append(nbf.v4.new_markdown_cell("""### Syarat Pengalaman Minimum dan Standar Akademis"""))

    # Cell 11: Code - Experience & Education Distribution
    cells.append(nbf.v4.new_code_cell("""plot_experience_distribution(df).show()
plot_education_distribution(df).show()"""))

    # Cell 12: Experience & Education Insight
    cells.append(nbf.v4.new_markdown_cell("""Sebanyak **91,6% lowongan** mensyaratkan minimal 1 tahun pengalaman kerja (1–2 tahun: 47,7%, 3+ tahun: 43,9%). Hanya **8,4% lowongan (36 dari 430)** yang terbuka bagi pelamar dengan pengalaman 0 tahun (*Fresh Graduate*). Dari sisi pendidikan, ijazah Sarjana (S1) tetap menjadi syarat utama industri, sedangkan kualifikasi Pascasarjana (S2) hanya muncul pada posisi spesialis riset."""))

    # Cell 13: Section 2 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 2. Model Kerja dan Disparitas Kompensasi Remote vs On-Site

Perbandingan proporsi model kerja (On-site, Hybrid, Remote) dan besaran kompensasi yang ditawarkan di pasar tenaga kerja data Indonesia."""))

    # Cell 14: Remote Comparison Chart
    cells.append(nbf.v4.new_code_cell("""fig_remote = plot_remote_luxury_comparison(df)
fig_remote.show()"""))

    # Cell 15: Remote Comparison Insight
    cells.append(nbf.v4.new_markdown_cell("""### Analisis Temuan

1. **Dominasi On-Site & Hambatan Geografis:** Sebanyak **93,0% lowongan** mewajibkan kerja fisik di kantor (On-site / WFO), skema Hybrid hanya **4,2%**, dan opsi Full Remote hanya **2,8%**. Ditambah dengan **83,5% lowongan yang terpusat di Jabodetabek** (Jakarta 65,8%, Tangerang 13,0%, Depok/Bekasi/Bogor 4,7%), talenta di luar wilayah metropolitan menghadapi hambatan ganda (*double barrier*).
2. **Premi Kompensasi Remote (+78,6%):** Meskipun langka, posisi Full Remote mencatatkan median kompensasi **Rp 12,5 juta/bulan**, berbanding posisi On-site dan Hybrid yang sama-sama memiliki median **Rp 7,0 juta/bulan**. Di industri data Indonesia, opsi kerja remote bukan benefit umum untuk jenjang pemula, melainkan instrumen kompensasi premium bagi talenta spesialis senior atau perusahaan skala regional."""))

    # Cell 16: Additional Workplace Charts
    cells.append(nbf.v4.new_code_cell("""plot_workplace_type_distribution(df).show()
plot_remote_premium(df).show()"""))

    # Cell 17: Section 3 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 3. Kebutuhan Tech Stack Industri

Frekuensi kemunculan kata kunci teknis dalam deskripsi pekerjaan untuk memetakan kebutuhan operasional industri."""))

    # Cell 18: Tech Stack Landscape Chart
    cells.append(nbf.v4.new_code_cell("""fig_tech_stack = plot_real_tech_stack_landscape(df)
fig_tech_stack.show()"""))

    # Cell 19: Tech Stack Insight
    cells.append(nbf.v4.new_markdown_cell("""### Analisis Kebutuhan Tools

- **Fondasi Operasional Mutlak:** **SQL (329 lowongan / 76,5%)**, **Python (243 / 56,5%)**, dan **Excel (190 / 44,2%)** merupakan kebutuhan dasar yang mendominasi bursa kerja.
- **Ekosistem Analytics & Data Pipeline:** Lapis kedua ditempati oleh **Machine Learning (144 / 33,5%)**, **ETL (139 / 32,3%)**, **Power BI (139 / 32,3%)**, **Tableau (114 / 26,5%)**, dan **Statistika (114 / 26,5%)**.
- **Realitas Adopsi AI:** Di tengah antusiasme publik terhadap AI, framework *Deep Learning* spesifik seperti **TensorFlow (20 lowongan / 4,7%)** dan **PyTorch (18 lowongan / 4,2%)** hanya muncul pada kurang dari 5% lowongan, menegaskan bahwa mayoritas bisnis di Indonesia berfokus pada keandalan pelaporan data operasional dan rekayasa pipeline sebelum mengadopsi AI tingkat lanjut."""))

    # Cell 20: Co-occurrence Intro
    cells.append(nbf.v4.new_markdown_cell("""### Struktur Kemunculan Bersama Antar-Skill (Jaccard Index)"""))

    # Cell 21: Heatmap
    cells.append(nbf.v4.new_code_cell("""plot_skill_cooccurrence_heatmap(df, top_n=12).show()"""))

    # Cell 22: Heatmap Insight
    cells.append(nbf.v4.new_markdown_cell("""Matriks ko-okurensi memperlihatkan tiga klaster profesi yang jelas:
1. **Business Intelligence / Analytics:** Keterkaitan kuat antara SQL, Excel, Power BI, dan Tableau.
2. **Data Science & ML:** Pasangan erat antara Python, Statistika, Machine Learning, dan eksplorasi data.
3. **Data Engineering:** Integrasi teknis antara SQL, ETL, Cloud (AWS/GCP/Azure), dan pipeline data."""))

    # Cell 23: Section 4 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 4. Sebaran Role, Kompensasi per Skill, dan Top Hiring Companies"""))

    # Cell 24: Role & Salary Charts
    cells.append(nbf.v4.new_code_cell("""plot_skill_vs_salary(df, top_n=15).show()
plot_role_distribution(df).show()
plot_top_companies(df, top_n=15).show()"""))

    # Cell 25: Section 4 Insight
    cells.append(nbf.v4.new_markdown_cell("""Posisi Data Analyst dan Data Engineer mendominasi volume rekrutmen data di Indonesia. Dari segi premi kompensasi, keahlian infrastruktur Cloud dan rekayasa pipeline data (ETL) memberikan selisih median kompensasi positif tertinggi di atas rata-rata pasar."""))

    # Cell 26: Conclusion
    cells.append(nbf.v4.new_markdown_cell("""---

## Kesimpulan dan Implikasi Praktis

### Untuk Pencari Kerja / Fresh Graduate
1. **Kuasai Fondasi Terlebih Dahulu:** Prioritaskan kemahiran kueri SQL tingkat lanjut, manipulasi data via Python/Pandas, Excel bisnis, dan satu tools BI (Power BI / Tableau) sebelum mempelajari framework deep learning yang jarang diminta di awal karir.
2. **Bangun Portofolio Terapan Terverifikasi:** Menyadari bahwa 91,6% lowongan mensyaratkan pengalaman, buktikan kompetensi teknis melalui portofolio end-to-end yang dapat diuji (ingestion data mentah, pembersihan, pipeline otomatisasi, dan visualisasi interaktif).
3. **Antisipasi Hambatan Geografis:** Pahami bahwa kerja remote masih menjadi komoditas langka (2,8%); persiapkan diri untuk penempatan On-site terutama di kawasan Jabodetabek (83,5%).

### Untuk Tim Perekrut / Hiring Manager
1. **Rasionalisasi Kualifikasi Entry-Level:** Hindari membebankan kualifikasi multi-role (analis, engineer, saintis sekaligus) pada kandidat pemula dengan standar kompensasi junior.
2. **Perjelas Kebutuhan Posisi:** Bedakan secara tegas antara kebutuhan pelaporan metrik bisnis rutin (Data Analyst) dan kebutuhan arsitektur infrastruktur data (Data Engineer) guna mengoptimalkan efisiensi rekrutmen."""))

    nb.cells = cells
    
    output_path = Path("eda.ipynb")
    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"[OK] Notebook {output_path} berhasil dibuat dengan {len(cells)} sel.")

if __name__ == "__main__":
    create_eda_notebook()
