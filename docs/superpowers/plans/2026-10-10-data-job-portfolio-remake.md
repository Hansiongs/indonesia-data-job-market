# Remake Portofolio Analisis Pasar Kerja Data Indonesia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merombak repositori analisis lowongan kerja Glints menjadi portofolio Data Analyst tingkat lanjut dengan narasi dua babak (Inversi Ekspektasi & Ilusi WFH), data segar hasil scraping mandiri khusus Indonesia, 4 visualisasi preview resolusi tinggi, dashboard naratif interaktif, dan dokumentasi Bahasa Indonesia industri yang higienis serta siap di-push ke GitHub.

**Architecture:** Pipa data modular yang terbagi menjadi: (1) Scraping Playwright dengan session cookie nyata (`glints_scraper.links` & `details`), (2) Transformasi dan pembersihan data murni dengan filter wilayah Indonesia (`glints_scraper.transform`), (3) Generator visualisasi terpusat (`app.charts` & `scripts.generate_assets`), (4) Pelaporan EDA (`eda.ipynb` & `eda_report.html`), (5) Aplikasi interaktif Streamlit (`app.dashboard`), dan (6) Showcase README & sanitasi Git.

**Tech Stack:** Python 3.13, Playwright, Parsel, Pandas, Matplotlib, Seaborn, Streamlit, Jupyter / nbconvert, Git.

**Spec:** `docs/superpowers/specs/2026-10-10-data-job-portfolio-remake-design.md`

## Global Constraints

- Semua teks narasi analisis, README, notebook, dan dashboard menggunakan Bahasa Indonesia profesional dengan istilah industri kerja Indonesia (*fresh graduate*, *tech stack*, *range gaji*, *on-site*, *hybrid*, *unicorn syndrome*).
- Seluruh angka dan metrik statistik wajib dihitung dinamis dari dataset hasil pembersihan (`data/processed/master_dataset_eda.csv`), tanpa ada angka statis fiktif.
- Data luar negeri (misal lowongan regional Vietnam) harus dibuang 100% pada proses cleaning; hanya data lowongan wilayah Indonesia yang dipertahankan.
- File sesi dan kredensial (`secrets/auth.json`, `.chrome_login_session`) tidak boleh terlacak oleh Git (`.gitignore` audit).

## Review Focus

1. **Foreign Location Leakage:** Lowongan dari Vietnam (misal "Quận Cầu Giấy", "Hà Nội", "Hồ Chí Minh") lolos dari filter; verifikasi bahwa seluruh lokasi yang tersisa di `city_clean` berada di Indonesia.
2. **Missing Salary Text Parsing:** Format gaji yang tidak terduga atau teks gaji per jam/tahun menyebabkan nilai null/NaN; verifikasi bahwa parser gaji hanya memproses format IDR bulanan yang valid dan menangani sentinel "Dirahasiakan".
3. **Division by Zero / Empty Slices in Charts:** Grafik gagal render jika salah satu filter (misal: lowongan Remote pada role tertentu) bernilai 0; verifikasi handling data kosong pada setiap builder chart.
4. **Secret Leaks in Git Staging:** `secrets/auth.json` tidak sengaja ter-stage oleh `git add .`; verifikasi `git status` dan aturan `.gitignore` sebelum commit.
5. **Chart Asset Resolution & Pathing:** Path gambar di `README.md` tidak cocok dengan output `assets/charts/`; verifikasi bahwa nama file persis sama dan gambar ter-render di GitHub preview.

---

### Task 1: Fresh Scraping Pipeline Execution (Tarik Data Segar)

**Files:**
- Modify: `src/glints_scraper/links.py`
- Modify: `src/glints_scraper/details.py`
- Output: `data/raw/glints_jobs.csv`, `data/raw/job_details.csv`

**Interfaces:**
- Consumes: `secrets/auth.json` (Playwright session)
- Produces: `data/raw/job_details.csv` (raw scraped job postings dengan detail lengkap)

- [ ] **Step 1: Verifikasi sesi autentikasi Playwright**
Run: `python -c "import json; assert len(json.load(open('secrets/auth.json'))['cookies']) > 0; print('Auth valid')"`
Expected: PASS dengan output "Auth valid"

- [ ] **Step 2: Jalankan scraper tautan pencarian Glints (`scrape-links`)**
Jalankan pengumpulan tautan lowongan aktif untuk 4 kata kunci: `data analyst`, `data scientist`, `data engineer`, `machine learning`.
Run: `python -m glints_scraper.links`
Expected: File `data/raw/glints_jobs.csv` terisi ribuan link lowongan aktif.

- [ ] **Step 3: Jalankan scraper detail lowongan Glints (`scrape-details`)**
Jalankan ekstraksi detail (job description, salary, experience, education, workplace type, skills) dengan checkpointing otomatis.
Run: `python -m glints_scraper.details`
Expected: File `data/raw/job_details.csv` terisi baris detail lowongan baru.

- [ ] **Step 4: Verifikasi integritas raw data yang terkumpul**
Run: `python -c "import pandas as pd; df = pd.read_csv('data/raw/job_details.csv'); assert len(df) > 0; print('Collected rows:', len(df))"`
Expected: PASS menampilkan jumlah baris data mentah yang terkumpul.

---

### Task 2: Data Cleaning & Strict Indonesia Location Filter

**Files:**
- Modify: `src/glints_scraper/transform.py`
- Test: `tests/test_transform.py`
- Output: `data/processed/master_dataset_eda.csv`

**Interfaces:**
- Consumes: `data/raw/job_details.csv`
- Produces: `data/processed/master_dataset_eda.csv` (skema kanonikal bersih khusus Indonesia)

- [ ] **Step 1: Tulis test untuk memastikan lowongan non-Indonesia dibuang**
Di `tests/test_transform.py`, tambahkan unit test `test_filter_foreign_locations` yang memvalidasi bahwa lokasi seperti "Quận Cầu Giấy , Vietnam" atau "Singapore" menghasilkan baris yang dibuang atau ditandai non-Indonesia.
```python
def test_filter_foreign_locations():
    raw = pd.DataFrame([{
        "keyword": "data analyst",
        "job_title": "Data Analyst",
        "company_name": "Test Co",
        "job_location": "Quận Cầu Giấy , Vietnam",
        "job_description": "SQL and Python",
        "skill_tags": "SQL, Python",
        "job_salary": "Rp 10.000.000 / Bulan",
        "job_education": "S1",
        "job_method": "Penuh Waktu",
        "job_experience": "1 - 3 tahun",
        "url": "https://glints.com/1"
    }])
    result = transform(raw)
    assert len(result) == 0 or "Vietnam" not in result["city_clean"].values
```

- [ ] **Step 2: Jalankan test untuk memverifikasi kegagalan awal**
Run: `pytest tests/test_transform.py::test_filter_foreign_locations -v`
Expected: FAIL jika filter wilayah belum menyaring Vietnam.

- [ ] **Step 3: Perbarui fungsi normalisasi lokasi di `src/glints_scraper/transform.py`**
Implementasikan pemfilteran ketat: hanya simpan lokasi yang cocok dengan kota/wilayah Indonesia (Jakarta, Bandung, Surabaya, Yogyakarta, Medan, Bali/Denpasar, Semarang, Tangerang, Bekasi, Depok, dll.), dan buang lokasi luar negeri.

- [ ] **Step 4: Jalankan test transform untuk memverifikasi kelulusan**
Run: `pytest tests/test_transform.py -v`
Expected: PASS seluruh test transformasi.

- [ ] **Step 5: Eksekusi pipeline pembersihan untuk menghasilkan master dataset bersih**
Run: `python -c "import sys; sys.path.insert(0, 'src'); import pandas as pd; from glints_scraper.transform import transform; raw = pd.read_csv('data/raw/job_details.csv'); clean = transform(raw); clean.to_csv('data/processed/master_dataset_eda.csv', index=False); print('Master saved:', clean.shape)"`
Expected: PASS menghasilkan `data/processed/master_dataset_eda.csv` tanpa data non-Indonesia.

---

### Task 3: Core Analytical Charts Engine (`app/charts.py` & `scripts/generate_assets.py`)

**Files:**
- Modify: `app/charts.py`
- Modify: `scripts/generate_assets.py`
- Test: `tests/test_charts.py`
- Output: `assets/charts/01_skill-burden-by-career-stage.png`, `02_salary-reality-curve.png`, `03_remote-luxury-comparison.png`, `04_real-tech-stack-landscape.png`

**Interfaces:**
- Consumes: `data/processed/master_dataset_eda.csv`
- Produces: 4 fungsi chart di `app/charts.py` dan 4 aset gambar di `assets/charts/`

- [ ] **Step 1: Tulis unit test untuk 4 chart utama di `tests/test_charts.py`**
Tambahkan test `test_chart_skill_burden`, `test_chart_salary_reality_curve`, `test_chart_remote_luxury`, dan `test_chart_tech_stack_landscape` yang memverifikasi bahwa masing-masing builder mengembalikan objek `matplotlib.figure.Figure`.

- [ ] **Step 2: Jalankan test untuk memverifikasi fungsi belum ada**
Run: `pytest tests/test_charts.py -v`
Expected: FAIL dengan ImportError atau AttributeError pada fungsi baru.

- [ ] **Step 3: Implementasikan 4 fungsi visualisasi di `app/charts.py`**
1. `plot_skill_burden_by_career_stage(df)`: Menghitung dan memplot perbandingan persentase tuntutan skill berat (Python, Stats, ML) pada Fresh Grad (<1 thn) vs Junior (1-2 thn) vs Mid/Senior (3+ thn).
2. `plot_salary_reality_curve(df)`: Scatter plot + trendline sebaran gaji aktual per tahun pengalaman kerja (*The Reality Curve*).
3. `plot_remote_luxury_comparison(df)`: Bar chart ganda yang menampilkan persentase distribusi WFO vs Remote vs Hybrid dan perbandingan median gajinya (menunjukkan *premium +70-80%* gaji Remote).
4. `plot_real_tech_stack_landscape(df)`: Horizontal bar chart ranking kebutuhan tools di seluruh profesi data (SQL & Excel vs tools AI).

- [ ] **Step 4: Jalankan unit test chart untuk memastikan PASS**
Run: `pytest tests/test_charts.py -v`
Expected: PASS seluruh fungsi chart menghasilkan objek figure yang valid.

- [ ] **Step 5: Perbarui `scripts/generate_assets.py` dan generate aset gambar**
Run: `python scripts/generate_assets.py`
Expected: 4 file PNG baru tersimpan dengan resolusi tajam di `assets/charts/`.

---

### Task 4: EDA Notebook & Standalone HTML Report

**Files:**
- Modify: `eda.ipynb`
- Output: `eda_report.html`

**Interfaces:**
- Consumes: `data/processed/master_dataset_eda.csv`, `app/charts.py`
- Produces: `eda_report.html` (laporan interaktif mandiri bebas server)

- [ ] **Step 1: Perbarui markdown & alur naratif di `eda.ipynb`**
Sesuaikan sel-sel di `eda.ipynb` agar menggunakan Bahasa Indonesia profesional, terstruktur rapi ke dalam:
1. Babak 1: Fenomena Inversi Ekspektasi / Unicorn Syndrome pada Fresh Graduate.
2. Babak 2: Ilusi Fleksibilitas WFH dan Realita On-Site.
3. Bedah Tech Stack: SQL & Excel sebagai Tulang Punggung Nyata Industri.
4. Analisis Kompensasi & Korelasi Antar Skill.

- [ ] **Step 2: Jalankan eksekusi notebook dari terminal**
Run: `jupyter nbconvert --execute --to notebook --inplace eda.ipynb`
Expected: Seluruh sel notebook berhasil dieksekusi tanpa error.

- [ ] **Step 3: Ekspor notebook menjadi laporan mandiri `eda_report.html`**
Run: `jupyter nbconvert --to html eda.ipynb --output eda_report.html --embed-images`
Expected: File `eda_report.html` terbuat dan dapat dibuka di peramban mana pun secara instan.

---

### Task 5: Restrukturisasi Dashboard Streamlit (`app/dashboard.py`)

**Files:**
- Modify: `app/dashboard.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `data/processed/master_dataset_eda.csv`, `app/charts.py`
- Produces: Antarmuka dashboard interaktif yang selaras dengan cerita di README

- [ ] **Step 1: Tulis test untuk dashboard baru di `tests/test_dashboard.py`**
Pastikan modul dashboard dapat di-import dan memuat dataset processed tanpa error.

- [ ] **Step 2: Susun ulang antarmuka `app/dashboard.py`**
Tata layout dashboard:
- Header & Ringkasan Pasar Kerja Data Indonesia.
- Bagian 1: Narasi Inversi Ekspektasi (metrik dinamis + filter role).
- Bagian 2: Narasi Mitos WFH & Gaji Remote (perbandingan visual + filter kota).
- Bagian 3: Eksplorasi Interaktif Tech Stack & Estimasi Gaji (filter kustom kandidat).

- [ ] **Step 3: Jalankan test dashboard untuk memastikan PASS**
Run: `pytest tests/test_dashboard.py -v`
Expected: PASS seluruh unit test dashboard.

---

### Task 6: Dokumentasi README, Panduan Reproduksi, dan Git Hygiene

**Files:**
- Modify: `README.md`
- Modify: `docs/reproduce.md`
- Verify: `.gitignore`

**Interfaces:**
- Consumes: Semua aset grafik, laporan, dan hasil analisis
- Produces: Repositori GitHub profesional yang siap dipamerkan

- [ ] **Step 1: Tulis ulang `README.md` dengan gaya naratif tajam**
Struktur README:
1. Judul & Hook Pembuka yang menarik bagi recruiter.
2. Babak 1: "Inversi Ekspektasi — Makin Murah Gajinya, Makin Rakus Tuntutan Skill-nya" (dengan sematan gambar `01_skill-burden-by-career-stage.png` & `02_salary-reality-curve.png`).
3. Babak 2: "Ilusi Fleksibilitas WFH — Remote Adalah Barang Mewah" (dengan sematan gambar `03_remote-luxury-comparison.png` & `04_real-tech-stack-landscape.png`).
4. Proof of Source & Metodologi Scraping (penjelasan etika scraping Glints).
5. Panduan Reproduksi Singkat (Jalur Cepat Streamlit & Jalur Scraping Mandiri).
6. Tautan ke `eda_report.html` dan live app Streamlit.

- [ ] **Step 2: Perbarui panduan `docs/reproduce.md`**
Perbarui instruksi agar mencantumkan langkah scraping terbaru tanpa devtools recorder dan cara menjalankan pipeline data mandiri.

- [ ] **Step 3: Audit keamanan dan higienitas Git**
Periksa `.gitignore` dan pastikan file `secrets/auth.json`, `.chrome_login_session/`, cache notebook, dan file temporer diabaikan.
Run: `git status`
Expected: `secrets/auth.json` tidak muncul di status git staging.

- [ ] **Step 4: Inisialisasi Git dan buat commit pertama yang bersih**
Run: `git init`, `git add .`, `git commit -m "feat: complete portfolio remake with indonesian data market insights and reproducible pipeline"`
Expected: Commit riwayat pertama rapi dan siap untuk di-hubungkan ke GitHub remote (`git remote add origin ...` & `git push`).
