# Analisis Pasar Kerja Profesi Data di Indonesia

Riset analitis terhadap 430 lowongan kerja aktif di sektor data (*Data Analyst, Data Engineer, Data Scientist, ML Engineer*) yang dikumpulkan langsung dari portal Glints Indonesia. 

Proyek ini memetakan dinamika kompensasi, kesenjangan kualifikasi antara level pemula dan profesional berpengalaman, serta kebutuhan riil *tech stack* di industri teknologi dan korporasi Indonesia saat ini.

- **Dashboard Interaktif:** Jalankan lokal via `streamlit run app/dashboard.py`
- **Laporan Lengkap Mandiri:** [`eda_report.html`](eda_report.html) (dapat dibuka langsung di browser tanpa Python)
- **Notebook Analisis:** [`eda.ipynb`](eda.ipynb) | **Pembersihan Data:** [`clean.ipynb`](clean.ipynb)

---

## Temuan Utama

### 1. Disparitas Beban Kualifikasi pada Posisi Entry-Level

Lowongan tingkat pemula (<1 tahun pengalaman kerja) mencatatkan proporsi tuntutan skill teoritis tertinggi dibanding jenjang mana pun: Python (70,6%), Statistik (58,8%), dan Machine Learning (47,1%). Namun, median kompensasi yang ditawarkan berada di level terendah bursa kerja, yaitu **Rp 4,2 juta/bulan**.

Sebaliknya, pada posisi dengan syarat pengalaman di atas 3 tahun (Mid/Senior), tuntutan Machine Learning justru menurun ke angka **29,8%**. Perusahaan beralih memprioritaskan integrasi sistem operasional riil: ETL (41,5%), Power BI/Tableau (35,1%), dan arsitektur Cloud (27,7%), dengan median kompensasi **Rp 9,0 – 15,0+ juta/bulan**.

![Perbandingan Beban Kualifikasi Skill](assets/charts/01_skill-burden-by-career-stage.png)

Fenomena ini mencerminkan dinamika di mana organisasi yang baru mulai membangun inisiatif data kerap merekrut *single-person data team*—menuntut satu orang menyelesaikan seluruh siklus data dari analitik hingga machine learning—dengan alokasi anggaran staf pemula.

Kurva regresi sebaran gaji terhadap pengalaman kerja memperlihatkan bahwa titik percepatan kompensasi riil baru terjadi setelah kandidat melewati batas 2–3 tahun pengalaman kerja:

![Distribusi Gaji vs Pengalaman](assets/charts/02_salary-reality-curve.png)

---

### 2. Ketersediaan Kerja Remote dan Disparitas Kompensasi

Sebanyak **90,7%** lowongan kerja data di Indonesia mensyaratkan kehadiran fisik penuh di kantor (On-site / WFO). Skema Hybrid mencakup **5,8%**, dan opsi Full Remote hanya mencakup **3,5%** dari total lowongan aktif.

Meskipun ketersediaannya sangat terbatas, lowongan remote menawarkan median kompensasi **Rp 12,5 juta**, berbanding On-site sebesar **Rp 7,0 juta** (premi sebesar +78,6%).

![Porsi Model Kerja dan Median Gaji](assets/charts/03_remote-luxury-comparison.png)

Di pasar tenaga kerja Indonesia, fasilitas kerja jarak jauh (remote) bukan benefit standar tempat kerja yang umum dinegosiasikan untuk jenjang pemula. Model remote berfungsi sebagai instrumen kompensasi untuk talenta spesialis senior atau perusahaan multinasional dan regional yang merekrut kandidat Indonesia.

---

### 3. Kebutuhan Tech Stack Industri: Fondasi vs Tren

Di tengah ramainya diskusi publik mengenai AI generatif dan model bahasa besar, kebutuhan operasional harian bursa kerja Indonesia tetap berpusat pada penarikan data dasar dan otomatisasi pelaporan:

![Kebutuhan Tech Stack Industri Data](assets/charts/04_real-tech-stack-landscape.png)

- **SQL** (428 kemunculan) dan **Excel** (246 kemunculan) merupakan syarat mutlak yang mendominasi hampir seluruh deskripsi pekerjaan.
- **Python** (189 kemunculan) dan **ETL** (168 kemunculan) menjadi tulang punggung rekayasa dan pipeline data.
- Framework deep learning murni seperti PyTorch dan TensorFlow hanya muncul pada ceruk riset spesifik (<30 kemunculan). Prioritas utama rekrutmen tetap bertumpu pada konsistensi metrik dan keandalan data operasional.

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
