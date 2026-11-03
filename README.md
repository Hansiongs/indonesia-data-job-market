# Analisis Pasar Kerja Profesi Data di Indonesia

Riset analitis terhadap 430 lowongan kerja aktif di sektor data (*Data Analyst, Data Engineer, Data Scientist, ML Engineer*) yang dikumpulkan langsung dari portal Glints Indonesia. 

Proyek ini memetakan dinamika kompensasi, kesenjangan kualifikasi antara level pemula dan profesional berpengalaman, serta kebutuhan riil *tech stack* di industri teknologi dan korporasi Indonesia saat ini.

- **Dashboard Interaktif:** Jalankan lokal via `streamlit run app/dashboard.py`
- **Laporan Lengkap Mandiri:** [`eda_report.html`](eda_report.html) (dapat dibuka langsung di browser tanpa Python)
- **Notebook Analisis:** [`eda.ipynb`](eda.ipynb) | **Pembersihan Data:** [`clean.ipynb`](clean.ipynb)

---

## Temuan Utama

### 1. Paradoks Kualifikasi Entry-Level vs Pergeseran Kebutuhan Senior

Hanya **8,4%** lowongan (36 dari 430) yang terbuka bagi *Fresh Graduate* (0 tahun pengalaman), sedangkan **91,6%** mensyaratkan minimal 1 tahun pengalaman kerja (1–2 tahun: 47,7%, 3+ tahun: 43,9%).

Menariknya, lowongan *Fresh Graduate* (<1 tahun) justru mencatatkan proporsi tuntutan skill fundamental & teoritis paling padat: **SQL (88,9%)**, **Python (77,8%)**, **Excel (72,2%)**, **Statistika (66,7%)**, dan **Machine Learning (50,0%)**, dengan **median gaji Rp 5,25 juta/bulan** (rentang Q1 Rp 2,9 juta – Q3 Rp 5,86 juta). Pada level *Junior* (1–2 tahun), median gaji naik moderat ke **Rp 6,5 juta/bulan**.

![Perbandingan Beban Kualifikasi Skill](assets/charts/01_skill-burden-by-career-stage.png)

Pola ini mencerminkan dinamika di mana organisasi yang baru merintis kapabilitas data kerap merekrut *single-person data team*—menuntut satu kandidat menangani seluruh alur analitik hingga modeling—dengan alokasi anggaran entry-level.

Sebaliknya, pada jenjang *Mid/Senior* (3+ tahun), tuntutan pengolahan spreadsheet dasar dan teori menurun (**Excel turun dari 72,2% ke 30,2%**, **Statistika turun dari 66,7% ke 18,5%**). Prioritas beralih ke stabilitas sistem data produksi: **ETL / Data Pipeline melonjak dari 25,0% ke 46,0%** dan **arsitektur Cloud (AWS/GCP/Azure) naik dari 13,9% ke 28,0%**. Titik lompatan kompensasi (*inflection point*) pasar data Indonesia terjadi pada level **Mid-Level (3 tahun: median Rp 9,0 juta/bulan)** dan **Senior (5+ tahun: median Rp 17,5 juta/bulan)**:

![Distribusi Gaji vs Pengalaman](assets/charts/02_salary-reality-curve.png)

---

### 2. Sentralisasi Geografis & Langkanya Kerja Remote (*Double Barrier*)

Pasar tenaga kerja data di Indonesia sangat tersentralisasi: **93,0%** lowongan mewajibkan kehadiran fisik penuh di kantor (On-site / WFO, 400 lowongan), skema Hybrid mencakup **4,2%** (18 lowongan), dan opsi Full Remote hanya **2,8%** (12 lowongan).

Secara geografis, **83,5% lowongan terpusat di wilayah metropolitan Jabodetabek** (Jakarta 65,8%, Tangerang 13,0%, Depok/Bekasi/Bogor 4,7%), diikuti Bandung (4,9%) dan Surabaya (4,4%). Kombinasi dominasi WFO (93,0%) dan konsentrasi Jabodetabek (83,5%) menciptakan hambatan ganda (*double barrier*) bagi talenta data di luar Jabodetabek.

![Porsi Model Kerja dan Median Gaji](assets/charts/03_remote-luxury-comparison.png)

Meskipun peluangnya sangat terbatas (2,8%), lowongan Full Remote menawarkan **median gaji Rp 12,5 juta/bulan**—premi kompensasi **+78,6%** dibandingkan posisi On-site dan Hybrid yang sama-sama memiliki median **Rp 7,0 juta/bulan**. Di pasar lokal, fasilitas remote bukan merupakan benefit umum untuk jenjang pemula, melainkan instrumen kompensasi premium bagi talenta spesialis senior atau perusahaan skala regional.

---

### 3. Hierarki Tech Stack Industri: Fondasi Operasional vs Hype AI

Di tengah pesatnya eksposur publik terhadap model AI mutakhir, kebutuhan operasional harian industri data di Indonesia bertumpu kuat pada fondasi kueri dan pelaporan bisnis:

![Kebutuhan Tech Stack Industri Data](assets/charts/04_real-tech-stack-landscape.png)

- **Fondasi Operasional Mutlak:** Tiga tools yang paling banyak diminta adalah **SQL (329 lowongan / 76,5%)**, **Python (243 lowongan / 56,5%)**, dan **Excel (190 lowongan / 44,2%)**.
- **Ekosistem Analytics & Data Pipeline:** Lapis kedua didominasi oleh keahlian pipeline dan visualisasi: **Machine Learning (144 / 33,5%)**, **ETL (139 / 32,3%)**, **Power BI (139 / 32,3%)**, **Tableau (114 / 26,5%)**, dan **Statistika (114 / 26,5%)**.
- **Realitas Adopsi AI:** Framework *Deep Learning* spesifik seperti **TensorFlow (20 lowongan / 4,7%)** dan **PyTorch (18 lowongan / 4,2%)** hanya muncul pada kurang dari 5% lowongan. Mayoritas bisnis memprioritaskan konsistensi metrik dan integrasi data operasional sebelum mengimplementasikan machine learning tingkat lanjut.

---

## Metodologi dan Kualitas Data

Data dikumpulkan melalui pipeline scraping berbasis Playwright dan Parsel yang dirancang khusus untuk portal Glints Indonesia.

```text
Glints Indonesia Portal
       │
       ▼
Playwright Scraper (links & details)
       │
       ▼
Data Cleaning & Feature Engineering (src/glints_scraper/transform.py)
  ├── Filter Lokasi: 100% Indonesia (data luar negeri/regional dibuang)
  ├── Parsing Gaji IDR (salary_min, salary_max, salary_avg)
  ├── Deteksi 32 fitur boolean skill dari deskripsi & tag
  └── Normalisasi pengalaman, pendidikan, dan model kerja
       │
       ▼
data/processed/master_dataset_eda.csv (430 lowongan terverifikasi)
       │
       ├── eda_report.html & eda.ipynb
       └── Streamlit Interactive Dashboard
```

- **Sampel Akhir:** 430 lowongan kerja data terverifikasi (162 Data Analyst, 127 Data Engineer, 103 Data Scientist, 38 Machine Learning).
- **Transparansi Gaji:** 349 lowongan (81,2%) mencantumkan nominal estimasi gaji transparan. Analisis kompensasi dihitung langsung dari data terbuka tanpa imputasi sintetis.
- **Higienitas Kredensial:** Seluruh sesi browser dan token lokal (`secrets/auth.json`) diabaikan oleh Git via `.gitignore`.

---

## Panduan Menjalankan Proyek

### 1. Menjalankan Dashboard (Tanpa Scraping)

Dataset bersih sudah disertakan di dalam repositori sehingga Anda dapat langsung menjalankan dashboard secara lokal:

```bash
# Clone repositori
git clone https://github.com/Hansiongs/indonesia-data-job-market.git
cd indonesia-data-job-market

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Pasang dependensi dan jalankan
pip install -r requirements.txt
streamlit run app/dashboard.py
```

Dashboard akan terbuka di peramban pada alamat `http://localhost:8501`.

### 2. Membuka Laporan Mandiri

Laporan analitis mandiri telah diekspor ke file [`eda_report.html`](eda_report.html). File ini dapat dibuka langsung di peramban apa pun tanpa memerlukan instalasi Python.

### 3. Replikasi Scraping Mandiri (Opsional)

Jika ingin memperbarui dataset dari portal Glints secara mandiri:

```bash
pip install -r requirements-scraper.txt
pip install -e ".[scraper]"
playwright install chromium

# Login sesi peramban lokal aman
python scripts/login.py

# Jalankan pipeline
python -m glints_scraper.links
python -m glints_scraper.details
python -m glints_scraper.transform
```

Instruksi detail mengenai mekanisme jeda rate-limit dan checkpoint scraper dapat dilihat pada [docs/reproduce.md](docs/reproduce.md).

---

## Pengujian Unit

Proyek ini dilengkapi 166 unit test otomatis untuk memvalidasi parser HTML, normalisasi data, fungsi analitis, dan pembuatan grafik Plotly:

```bash
pip install -r requirements-dev.txt
pytest -v
```

Hasil pengujian: **166 passed, 0 failures**.

---

## Struktur Direktori

```text
├── app/
│   ├── charts.py            # Modul pembuatan grafik Plotly
│   ├── dashboard.py         # Aplikasi dashboard Streamlit
│   ├── data.py              # Pemuatan data & fungsi kalkulasi
│   └── geo.py               # Pemetaan wilayah & visualisasi Folium
├── assets/
│   └── charts/              # Cuplikan resolusi tinggi grafik analitis
├── data/
│   ├── processed/           # Dataset bersih terverifikasi (master_dataset_eda.csv)
│   └── raw/                 # Checkpoint scraping lokal (.gitignore)
├── docs/
│   ├── reproduce.md         # Panduan detail replikasi scraping
│   └── schema.md            # Dokumentasi skema kamus data
├── scripts/
│   ├── generate_assets.py   # Script otomasi ekspor grafik PNG
│   └── login.py             # Script login sesi Chrome aman
├── src/glints_scraper/      # Pipeline scraping & transformasi data
│   ├── details.py           # Ekstraksi detail deskripsi lowongan
│   ├── links.py             # Pengambilan tautan kartu lowongan
│   ├── parsers.py           # Parser HTML Parsel
│   └── transform.py         # Pembersihan, normalisasi & validasi data
├── tests/                   # 166 unit test komprehensif
├── clean.ipynb              # Notebook data cleaning & feature engineering
├── eda.ipynb                # Notebook analisis data
├── eda_report.html          # Laporan analitis interaktif mandiri
└── requirements.txt         # Daftar dependensi utama
```

---

## Lisensi

Proyek ini dirilis di bawah lisensi [MIT](LICENSE). Data dikumpulkan dari lowongan kerja publik di Glints Indonesia untuk kepentingan riset analitis dan edukasi.
