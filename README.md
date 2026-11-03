# Analisis Pasar Kerja Profesi Data di Indonesia

Proyek ini menganalisis 400 lowongan kerja aktif di bidang data (*Data Analyst, Data Engineer, Data Scientist, ML Engineer*) dari portal Glints Indonesia. Fokus utamanya melihat sebaran gaji, perbandingan syarat masuk untuk pemula dan level senior, serta *tech stack* yang paling banyak dicari perusahaan di Indonesia.

- Dashboard interaktif bisa dijalankan secara lokal lewat `streamlit run app/dashboard.py`
- Laporan lengkap tersedia di [`eda_report.html`](eda_report.html) dan bisa dibuka langsung di browser tanpa instalasi Python
- Notebook analisis ada di [`eda.ipynb`](eda.ipynb) dan proses pembersihan data ada di [`clean.ipynb`](clean.ipynb)

---

## Temuan Utama

### 1. Tuntutan Kualifikasi Entry-Level dan Pergeseran di Level Senior

Hanya 3,5% lowongan (14 dari 400) yang terbuka untuk *Fresh Graduate* tanpa pengalaman kerja. Sebanyak 96,5% sisanya mensyaratkan minimal 1 tahun pengalaman, terbagi menjadi 53,5% untuk pengalaman 1 sampai 2 tahun dan 43,0% untuk pengalaman 3 tahun ke atas.

Lowongan untuk *Fresh Graduate* (kurang dari 1 tahun) dan *Junior* (1 sampai 2 tahun) langsung meminta penguasaan teknis inti sejak awal. Di level *Fresh Graduate*, permintaan SQL dan Python sama-sama mencapai 78,6% serta Machine Learning 42,9%. Di level *Junior*, beban kualifikasi melebar ke SQL (78,0%), Python (59,3%), Excel (44,4%), dan Statistika (34,6%). Baik posisi *Fresh Graduate* maupun *Junior* memiliki median gaji yang sama di angka Rp 7,0 juta/bulan.

![Perbandingan Beban Kualifikasi Skill](assets/charts/01_skill-burden-by-career-stage.png)

Kondisi ini terjadi karena banyak perusahaan yang baru membangun tim data langsung mencari kandidat tingkat awal yang siap mengurus kueri, pelaporan, hingga pengolahan data sekaligus dengan anggaran gaji standar pemula.

Di level *Mid* dan *Senior* (3 tahun ke atas), syarat penguasaan spreadsheet dan statistika dasar mulai turun dibanding level *Junior*. Permintaan Excel turun dari 44,4% ke 20,3% dan Statistika turun dari 34,6% ke 12,2%. Kebutuhan perusahaan bergeser ke pengelolaan infrastruktur data produksi, terlihat dari permintaan ETL atau Data Pipeline yang naik dua kali lipat dari 18,2% di level *Junior* menjadi 37,8% di level *Senior*. Kenaikan gaji baru terasa saat masuk ke pengalaman minimal 3 tahun (median Rp 8,6 juta/bulan) dan pengalaman 5 tahun ke atas (median Rp 13,5 juta/bulan).

![Distribusi Gaji vs Pengalaman](assets/charts/02_salary-reality-curve.png)

---

### 2. Terpusatnya Lokasi Kerja dan Perbandingan Model Kerja

Lowongan kerja data di Indonesia masih didominasi sistem kerja di kantor. Sebanyak 83,2% lowongan (333 posisi) mewajibkan kehadiran penuh di kantor (On-site atau WFO), diikuti skema Hybrid sebesar 11,8% (47 lowongan) dan Full Remote sebesar 5,0% (20 lowongan).

Dari sisi wilayah, 78,0% lowongan menumpuk di area Jabodetabek (Jakarta 66,8%, Tangerang 9,8%, serta Bekasi dan Depok 1,5%), diikuti Bandung (6,0%), Surabaya (3,8%), Denpasar (3,5%), dan Yogyakarta (3,5%). Wajibnya WFO dan terpusatnya lowongan di Jabodetabek membuat pelamar dari luar daerah harus siap pindah domisili jika mencari kerja.

![Porsi Model Kerja dan Median Gaji](assets/charts/03_remote-luxury-comparison.png)

Dari sisi kompensasi, skema Hybrid menawarkan median gaji tertinggi di angka Rp 7,8 juta/bulan, disusul posisi On-site dengan median Rp 7,5 juta/bulan. Sementara itu, posisi Full Remote memiliki median Rp 5,9 juta/bulan karena sebagian lowongan remote yang mencantumkan gaji didominasi posisi kontrak dan paruh waktu.

---

### 3. Kebutuhan Tech Stack di Industri

Kebutuhan operasional harian untuk posisi data di Indonesia masih berfokus pada pengelolaan kueri dan pembuatan laporan bisnis.

![Kebutuhan Tech Stack Industri Data](assets/charts/04_real-tech-stack-landscape.png)

- Lima tool utama yang paling banyak diminta adalah SQL (303 lowongan atau 75,8%), Python (213 lowongan atau 53,2%), Power BI (144 lowongan atau 36,0%), Excel (132 lowongan atau 33,0%), dan Tableau (120 lowongan atau 30,0%).
- Kelompok berikutnya diisi oleh kebutuhan infrastruktur dan analitik seperti Redis (107 lowongan atau 26,8%), ETL (104 lowongan atau 26,0%), Statistika (95 lowongan atau 23,8%), Data Visualization (93 lowongan atau 23,2%), dan Machine Learning (75 lowongan atau 18,8%).
- Framework *Deep Learning* seperti PyTorch (20 lowongan atau 5,0%) dan TensorFlow (19 lowongan atau 4,8%) hanya muncul di kisaran 5% dari total lowongan. Mayoritas perusahaan masih fokus merapikan metrik dan alur data operasional sebelum masuk ke penerapan pemodelan tingkat lanjut.

---

## Metodologi dan Kualitas Data

Pengumpulan data dilakukan menggunakan pipeline scraping berbasis Playwright dan Parsel untuk mengambil lowongan dari portal Glints Indonesia.

```text
Glints Indonesia Portal
       │
       ▼
Playwright Scraper (links & details)
       │
       ▼
Data Cleaning & Feature Engineering (src/glints_scraper/transform.py)
  ├── Filter lokasi khusus Indonesia (data luar negeri dibuang)
  ├── Parsing gaji IDR (salary_min, salary_max, salary_avg)
  ├── Deteksi 32 fitur boolean skill dari deskripsi & tag
  └── Normalisasi pengalaman, pendidikan, dan model kerja
       │
       ▼
data/processed/master_dataset_eda.csv (400 lowongan terverifikasi)
       │
       ├── eda_report.html & eda.ipynb
       └── Streamlit Interactive Dashboard
```

- Sampel akhir terdiri dari 400 lowongan kerja data (138 Data Analyst, 121 Data Engineer, 108 Data Scientist, dan 33 Machine Learning).
- Sebanyak 253 lowongan (63,2%) mencantumkan angka estimasi gaji. Analisis gaji dihitung langsung dari data yang tersedia tanpa pengisian nilai kosong secara buatan.
- Seluruh sesi browser dan token lokal (`secrets/auth.json`) otomatis diabaikan oleh Git melalui `.gitignore`.

---

## Panduan Menjalankan Proyek

### 1. Menjalankan Dashboard (Tanpa Scraping)

Dataset yang sudah dibersihkan tersedia langsung di dalam repositori. Anda bisa langsung menjalankan dashboard secara lokal lewat perintah berikut.

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

Dashboard akan terbuka di browser pada alamat `http://localhost:8501`.

### 2. Membuka Laporan Mandiri

Hasil analisis lengkap sudah diekspor ke [`eda_report.html`](eda_report.html). File ini bisa langsung dibuka di browser tanpa perlu memasang Python.

### 3. Menjalankan Ulang Scraping (Opsional)

Jika Anda ingin mengambil data terbaru dari portal Glints secara mandiri, jalankan urutan perintah berikut.

```bash
pip install -r requirements-scraper.txt
pip install -e ".[scraper]"
playwright install chromium

# Login sesi browser lokal
python scripts/login.py

# Jalankan pipeline
python -m glints_scraper.links
python -m glints_scraper.details
python -m glints_scraper.transform
```

Penjelasan lengkap mengenai pengaturan jeda request dan penyimpanan checkpoint bisa dibaca di [docs/reproduce.md](docs/reproduce.md).

---

## Pengujian Unit

Proyek ini memiliki 166 unit test otomatis untuk mengecek fungsi parser HTML, pembersihan data, perhitungan statistik, dan pembuatan grafik Plotly.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Seluruh 166 pengujian berjalan lancar tanpa error (166 passed, 0 failures).

---

## Struktur Direktori

```text
├── app/
│   ├── charts.py            # Modul pembuatan grafik Plotly
│   ├── dashboard.py         # Aplikasi dashboard Streamlit
│   ├── data.py              # Pemuatan data & fungsi kalkulasi
│   └── geo.py               # Pemetaan wilayah & visualisasi Folium
├── assets/
│   └── charts/              # File gambar grafik hasil analisis
├── data/
│   ├── processed/           # Dataset bersih (master_dataset_eda.csv)
│   └── raw/                 # Checkpoint hasil scraping lokal (.gitignore)
├── docs/
│   ├── reproduce.md         # Panduan menjalankan ulang scraping
│   └── schema.md            # Penjelasan kolom dan skema data
├── scripts/
│   ├── generate_assets.py   # Script ekspor grafik ke format PNG
│   └── login.py             # Script login sesi Chrome lokal
├── src/glints_scraper/      # Pipeline scraping & transformasi data
│   ├── details.py           # Pengambilan detail deskripsi lowongan
│   ├── links.py             # Pengambilan tautan kartu lowongan
│   ├── parsers.py           # Parser HTML menggunakan Parsel
│   └── transform.py         # Pembersihan, normalisasi & validasi data
├── tests/                   # 166 unit test otomatis
├── clean.ipynb              # Notebook pembersihan data & feature engineering
├── eda.ipynb                # Notebook analisis data
├── eda_report.html          # Laporan analisis mandiri format HTML
└── requirements.txt         # Daftar dependensi utama
```

---

## Lisensi

Proyek ini menggunakan lisensi [MIT](LICENSE). Data diambil dari lowongan kerja publik di Glints Indonesia untuk keperluan riset dan pembelajaran.
