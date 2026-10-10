"""Generate the updated eda.ipynb with narrative storytelling and execute it."""
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

    # Cell 1: Markdown - Title & Executive Summary
    cells.append(nbf.v4.new_markdown_cell("""# 🇮🇩 Exploratory Data Analysis (EDA): Realita Pasar Kerja Profesi Data Indonesia
### Analisis Empiris Berbasis 430 Lowongan Kerja Aktif Glints Indonesia

Notebook ini menyajikan riset analitis mendalam mengenai kondisi bursa kerja profesi data di Indonesia (*Data Analyst, Data Engineer, Data Scientist, & Machine Learning Engineer*). 

Berbeda dengan asumsi umum atau mitos yang sering beredar di media sosial, analisis ini didasarkan pada data aktual hasil scraping terstruktur dari platform **Glints Indonesia** yang telah melalui proses validasi dan pembersihan data ketat (*Indonesia-only location filter, deduplication, & parsing gaji standar*).

---

## 📌 Executive Summary (Temuan Kunci)

> *Berdasarkan 430 lowongan kerja data terverifikasi di Indonesia (349 lowongan dengan keterbukaan gaji aktual).*

1. **Inversi Ekspektasi / Unicorn Syndrome:** Lowongan tingkat pemula (*fresh graduate* / pengalaman < 1 tahun) menuntut tumpukan skill akademis dan teknis paling padat (Python 70,6%, Statistik 58,8%, Machine Learning 47,1%), namun median gaji yang ditawarkan berada di level terendah (**Rp 4,2 Juta**). Sebaliknya, posisi Mid/Senior (> 3 tahun) lebih terfokus pada integrasi tools industri (ETL, Power BI, SQL, Cloud) dengan median kompensasi **Rp 9,0 – 15,0+ Juta**.
2. **Ilusi Fleksibilitas WFH (Remote Adalah Barang Mewah):** Lebih dari **90%** lowongan data di Indonesia mewajibkan kerja **On-site (WFO)**. Kesempatan Full Remote hanya dinikmati segelintir posisi (~3,5%), tetapi menawarkan kompensasi dengan median **Rp 12,5 Juta** berbanding On-site **Rp 7,0 Juta** (+78,6% salary premium). WFH di Indonesia bukan benefit standar pemula, melainkan instrumen retensi eksklusif bagi talenta spesialis bergaji tinggi.
3. **Tulang Punggung Nyata Industri:** **SQL** (428 kemunculan) dan **Excel** (246 kemunculan) mendominasi bursa kerja nyata. Tools berbasis AI hype seperti PyTorch dan TensorFlow hanya muncul di sebagian kecil lowongan riset spesifik (< 30 kemunculan).
4. **Kesenjangan Karir Fresh Graduate:** Hanya **5,8%** lowongan yang secara eksplisit membuka pintu untuk kandidat dengan pengalaman 0 tahun (*fresh graduate* murni). Portofolio berbasis studi kasus nyata menjadi syarat wajib untuk menembus filter rekruiter."""))

    # Cell 2: Markdown - Setup and Data Loading
    cells.append(nbf.v4.new_markdown_cell("""---

## ⚙️ Setup Environment & Pemuatan Data

Kita memuat dataset bersih `data/processed/master_dataset_eda.csv` dan mengimpor modul visualisasi terpusat dari `app.charts`. Pendekatan arsitektur ini memastikan konsistensi metrik visual antara notebook analitis, dashboard Streamlit interaktif, dan laporan ringkasan."""))

    # Cell 3: Code - Imports & Data Loading
    cells.append(nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd
import plotly.io as pio

# Set default renderer agar grafik interaktif dapat dirender baik di notebook maupun ekspor HTML
pio.renderers.default = "notebook_connected"

# Pastikan path modul lokal terdaftar
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
print(f"[DATA] Data berhasil dimuat: {len(df):,} lowongan kerja data terverifikasi di Indonesia.")
print(f"[SKILLS] Fitur skill terdeteksi: {len(skill_cols)} kategori teknis.")
print(f"[SALARY] Transparansi kompensasi: {disclosed_salaries:,} lowongan ({disclosed_salaries/len(df):.1%}) mencantumkan estimasi gaji.")"""))

    # Cell 4: Markdown - Babak 1 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 🧩 Babak 1: Fenomena Inversi Ekspektasi / "Unicorn Syndrome"

### "Ekspektasi Dewa, Budget UMR"

Banyak pencari kerja pemula mengeluhkan kualifikasi lowongan junior yang terasa tidak masuk akal. Apakah keluhan ini hanya persepsi subjektif, atau terbukti secara empiris di pasar kerja?

Grafik di bawah ini memetakan persentase tuntutan skill berat (*Python, Statistik, Machine Learning*) vs tools rekayasa praktis (*ETL, Power BI, SQL, Cloud*) berdasarkan kelompok pengalaman kerja yang dipersyaratkan:
- **Fresh Graduate:** Pengalaman < 1 tahun (atau 0 tahun).
- **Junior:** Pengalaman 1 – 2 tahun.
- **Mid / Senior:** Pengalaman 3 tahun ke atas."""))

    # Cell 5: Code - Skill Burden Chart
    cells.append(nbf.v4.new_code_cell("""# 1. Visualisasi Inversi Beban Skill per Jenjang Karir
fig_skill_burden = plot_skill_burden_by_career_stage(df)
fig_skill_burden.show()"""))

    # Cell 6: Markdown - Skill Burden Insight
    cells.append(nbf.v4.new_markdown_cell("""### 💡 Analisis Temuan: Mengapa Terjadi Inversi Ekspektasi?

Data menunjukkan fenomena paradoks yang sangat mencolok:
1. **Beban Akademis di Posisi Entry-Level:** Posisi *Fresh Graduate* justru memiliki proporsi tuntutan **Python (70,6%)**, **Statistik (58,8%)**, dan **Machine Learning (47,1%)** tertinggi dibanding jenjang mana pun.
2. **Pergeseran Pragmatis di Level Senior:** Pada posisi Mid/Senior (>3 tahun), tuntutan Machine Learning justru turun ke angka **29,8%**. Sebaliknya, perusahaan memprioritaskan integrasi sistem nyata: **ETL (41,5%)**, **Power BI/Tableau (35,1%)**, dan arsitektur **Cloud (27,7%)**.

**Akar Penyebab di Industri (Unicorn Syndrome):**
Perusahaan yang baru mulai membangun divisi data kerap tidak memiliki pemahaman matang mengenai pembagian peran data. Mereka menginginkan *one-man data team*—seorang kandidat yang bisa membersihkan data, membangun pipeline, memodelkan machine learning, sekaligus membuat dashboard eksekutif—dengan anggaran gaji tingkat pemula."""))

    # Cell 7: Markdown - Salary Reality Curve Intro
    cells.append(nbf.v4.new_markdown_cell("""### Kurva Realitas Kompensasi (*The Salary Reality Curve*)

Bagaimana korelasi antara tahun pengalaman yang disyaratkan dengan gaji aktual yang ditawarkan di pasar kerja Indonesia?"""))

    # Cell 8: Code - Salary Reality Curve Chart
    cells.append(nbf.v4.new_code_cell("""# 2. Visualisasi Kurva Realitas Gaji vs Pengalaman
fig_reality_curve = plot_salary_reality_curve(df)
fig_reality_curve.show()"""))

    # Cell 9: Markdown - Reality Curve Insight
    cells.append(nbf.v4.new_markdown_cell("""### 💡 Dinamika Kompensasi: Titik Nol yang Tertekan

Kurva sebaran di atas memperlihatkan realitas kompensasi yang gamblang:
- **Rentang Masuk (< 1 Tahun):** Median gaji pemula berada di angka **Rp 4,2 Juta**, dengan sebaran terbanyak berada di rentang Rp 1,5 – 4,5 Juta. Angka ini menegaskan bahwa ekspektasi skill tingkat tinggi di jenjang awal tidak diimbangi dengan kompensasi proporsional.
- **Akselerasi Karir (Tahun ke-3+):** Titik lonjakan kompensasi riil terjadi setelah melewati batas 2–3 tahun pengalaman, di mana median gaji menanjak ke kisaran **Rp 9,0 – 15,0+ Juta**, bahkan mencapai Rp 25–35 Juta untuk posisi spesialis data architecture dan engineering."""))

    # Cell 10: Markdown - Experience & Education Intro
    cells.append(nbf.v4.new_markdown_cell("""### Hambatan Masuk Pasar (*Barrier to Entry*): Pengalaman & Standar Akademis"""))

    # Cell 11: Code - Experience & Education Distribution
    cells.append(nbf.v4.new_code_cell("""# 3. Distribusi Syarat Pengalaman & Standar Pendidikan
plot_experience_distribution(df).show()
plot_education_distribution(df).show()"""))

    # Cell 12: Markdown - Barrier to Entry Insight
    cells.append(nbf.v4.new_markdown_cell("""Hanya **5,8%** lowongan yang terbuka bagi kandidat tanpa pengalaman kerja sama sekali (0 tahun). Mayoritas lowongan (lebih dari 65%) menetapkan syarat minimal 1 hingga 3 tahun pengalaman, didampingi ijazah Sarjana (S1). Hal ini menegaskan bahwa lulusan baru wajib menyiasati barrier ini dengan membuktikan portofolio proyek terapan yang kredibel."""))

    # Cell 13: Markdown - Babak 2 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 🏖️ Babak 2: Ilusi Fleksibilitas WFH — "Remote Adalah Barang Mewah"

### Mitos Kerja Data dari Mana Saja

Industri teknologi kerap diidentikkan dengan fleksibilitas kerja *Work from Home* (WFH) atau *Work from Anywhere* (WFA). Apakah lowongan data di Indonesia benar-benar menawarkan kebebasan tersebut?"""))

    # Cell 14: Code - Remote Luxury Chart
    cells.append(nbf.v4.new_code_cell("""# 4. Visualisasi Komparasi Model Kerja & Premi Gaji Remote
fig_remote_luxury = plot_remote_luxury_comparison(df)
fig_remote_luxury.show()"""))

    # Cell 15: Markdown - Remote Luxury Insight
    cells.append(nbf.v4.new_markdown_cell("""### 💡 Pembongkaran Mitos: Realita On-Site vs Remote Luxury

1. **Dominasi Mutlak WFO:** Lebih dari **90,7%** lowongan data di Indonesia mewajibkan kerja **On-site (WFO)**. Opsi Hybrid berada di angka **5,8%**, sementara lowongan yang menawarkan **Full Remote hanya 3,5%**.
2. **Premi Gaji Remote (+78,6%):** Meskipun porsinya sangat kecil, posisi Remote menawarkan median gaji **Rp 12,5 Juta**, dibandingkan posisi On-site sebesar **Rp 7,0 Juta** (+78,6% premium).

**Kesimpulan Strategis:**
Kerja remote di sektor data Indonesia bukanlah fasilitas umum atau opsi gaya hidup bagi entry-level. Remote adalah **instrumen kompensasi premium** yang diberikan perusahaan kepada talenta spesialis senior atau perusahaan multinasional yang merekrut talenta Indonesia dengan standar kompensasi regional."""))

    # Cell 16: Code - Workplace & Remote Premium
    cells.append(nbf.v4.new_code_cell("""# 5. Rincian Distribusi Workplace Type & Premi Remote
plot_workplace_type_distribution(df).show()
plot_remote_premium(df).show()"""))

    # Cell 17: Markdown - Babak 3 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 🛠️ Babak 3: Bedah Nyata Tech Stack — SQL & Excel vs AI Hype

### Memisahkan Kebutuhan Industri Riil dari Tren Media Sosial

Media sosial dipenuhi konten tentang *Generative AI, Large Language Models (LLM),* dan *Deep Learning*. Namun, tools apa yang sebenarnya paling banyak diminta dalam deskripsi lowongan kerja data di Indonesia?"""))

    # Cell 18: Code - Real Tech Stack Landscape Chart
    cells.append(nbf.v4.new_code_cell("""# 6. Visualisasi Lanskap Kebutuhan Tech Stack Nyata
fig_tech_stack = plot_real_tech_stack_landscape(df)
fig_tech_stack.show()"""))

    # Cell 19: Markdown - Tech Stack Insight
    cells.append(nbf.v4.new_markdown_cell("""### 💡 Analisis Stack: Kebutuhan Riil Operasional Bisnis

- **Fondasi Abadi:** **SQL** menduduki peringkat pertama dengan **428 kemunculan**, diikuti **Excel** dengan **246 kemunculan**. Keduanya merupakan bahasa komunikasi data universal di hampir setiap korporasi dan startup di Indonesia.
- **Python & Data Engineering:** Python memegang peranan krusial (189 kemunculan) berdampingan dengan ETL (168 kemunculan) dan infrastruktur Cloud.
- **Kesenjangan AI Hype:** Tools deep learning murni seperti PyTorch dan TensorFlow berada di jajaran terbawah (< 30 kemunculan). Bisnis lokal memprioritaskan penyelesaian masalah operasional harian, standarisasi metrik, dan otomatisasi pelaporan sebelum melangkah ke pemodelan AI tingkat lanjut."""))

    # Cell 20: Markdown - Co-occurrence Intro
    cells.append(nbf.v4.new_markdown_cell("""### Struktur Hubungan Antar-Skill (*Skill Co-occurrence Matrix*)

Bagaimana tools-tools ini berpasangan dalam satu lowongan kerja? Melalui perhitungan matriks *Jaccard Similarity*, kita dapat mengidentifikasi klaster kompetensi yang saling melengkapi."""))

    # Cell 21: Code - Heatmap
    cells.append(nbf.v4.new_code_cell("""# 7. Heatmap Klasterisasi Hubungan Antar Skill (Jaccard Index)
plot_skill_cooccurrence_heatmap(df, top_n=12).show()"""))

    # Cell 22: Markdown - Heatmap Insight
    cells.append(nbf.v4.new_markdown_cell("""Dari heatmap di atas, terlihat 3 klaster dominan:
1. **Klaster Business Intelligence:** Excel, SQL, Tableau, dan Power BI memiliki korelasi tinggi—menjadi fondasi utama peran Data Analyst.
2. **Klaster Data Science:** Python, Pandas, Machine Learning, dan Statistik berpasangan erat.
3. **Klaster Data Engineering:** SQL, ETL, Cloud (AWS/GCP), dan integrasi pipeline data."""))

    # Cell 23: Markdown - Babak 4 Intro
    cells.append(nbf.v4.new_markdown_cell("""---

## 💰 Babak 4: Sebaran Peran, Kompensasi & Top Employers

Bagaimana sebaran peran di bursa kerja, dan skill apa saja yang memberikan dampak kompensasi positif tertinggi?"""))

    # Cell 24: Code - Skill vs Salary & Role Distribution
    cells.append(nbf.v4.new_code_cell("""# 8. Premi Kompensasi per Skill & Distribusi Peran
plot_skill_vs_salary(df, top_n=15).show()
plot_role_distribution(df).show()
plot_top_companies(df, top_n=15).show()"""))

    # Cell 25: Markdown - Babak 4 Insight
    cells.append(nbf.v4.new_markdown_cell("""Posisi **Data Analyst** dan **Data Engineer** mendominasi volume perekrutan di Indonesia. Dari segi premi gaji, penguasaan infrastruktur *Cloud, ETL pipeline skala besar,* dan *arsitektur data modern* memberikan lonjakan median gaji paling signifikan di atas baseline pasar."""))

    # Cell 26: Markdown - Actionable Conclusion
    cells.append(nbf.v4.new_markdown_cell("""---

## 🎯 Kesimpulan & Rekomendasi Karir Berbasis Data

### 1. Untuk Fresh Graduate & Job Seeker
- **Prioritaskan Fondasi:** Jangan terintimidasi oleh daftar skill yang panjang pada lowongan entry-level. Kuasai **SQL**, **Excel lanjutan**, dan salah satu tools visualisasi (**Power BI / Tableau**) hingga mahir sebelum terjebak mempelajari framework AI canggih yang jarang dibutuhkan di awal karir.
- **Bangun Portofolio Berbasis Masalah Riil:** Karena 94%+ lowongan mensyaratkan pengalaman, tunjukkan kompetensi melalui portofolio end-to-end yang dapat diuji (seperti pipeline data engineering, web scraping terstruktur, dan dashboard analitis interaktif).
- **Bersiap untuk On-site di Pusat Bisnis:** Pahami bahwa kesempatan kerja jarak jauh (Remote) sangat langka untuk jenjang awal. Mayoritas kesempatan berpusat pada model On-site di kota-kota industri utama (khususnya wilayah Jabodetabek dan Bandung).

### 2. Untuk Rekruiter & Hiring Manager
- **Hindari "Unicorn Job Description":** Menuntut penguasaan *full data stack* (arsitektur pipeline data + riset machine learning + analisis bisnis) untuk lowongan tingkat pemula dengan standar kompensasi UMR hanya menciptakan *mismatch* ekspektasi dan memperpanjang proses rekrutmen.
- **Spesifikasikan Kebutuhan Riil:** Definisikan masalah operasional utama yang ingin diselesaikan: apakah perusahaan membutuhkan pembersihan & integrasi data (Data Engineer), atau pelaporan metrik bisnis harian (Data Analyst)."""))

    nb.cells = cells
    
    output_path = Path("eda.ipynb")
    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"[OK] Notebook {output_path} berhasil dibuat dengan {len(cells)} sel.")

if __name__ == "__main__":
    create_eda_notebook()
