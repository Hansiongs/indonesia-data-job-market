# Rencana Implementasi: Lokalisasi Penuh Bahasa Indonesia untuk Notebooks & Visualisasi

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Mengubah seluruh konten, narasi, komentar kode, print output, dan label visualisasi chart di `clean.ipynb`, `eda.ipynb`, `eda_report.html`, dan `app/charts.py` menjadi 100% Bahasa Indonesia profesional dan natural (standar Senior Data Analyst), serta mengeksekusi ulang notebook agar output visualnya terisi penuh saat dibuka di GitHub.

**Architecture:** 
1. Penyelarasan bahasa di fondasi chart (`app/charts.py`) mencakup judul grafik, label sumbu (X & Y), nama legenda, hover template, dan kategori ordinal (*Fresh Graduate, 1-2 Tahun, dll.*).
2. Penerjemahan menyeluruh dan peremajaan `clean.ipynb` (seluruh teks markdown, penjelasan pipeline transformasi, komentar kode, dan pesan terminal).
3. Pengecekan dan penyempurnaan generator `scripts/build_eda_notebook.py` untuk memastikan seluruh sel markdown, output stdout, dan kode di `eda.ipynb` bebas dari teks bahasa Inggris.
4. Eksekusi ulang notebook secara *in-place* (`jupyter nbconvert --execute`), ekspor laporan mandiri `eda_report.html`, dan regenerasi aset chart PNG di `assets/charts/`.
5. Verifikasi pengujian unit komprehensif (`pytest`) dan sinkronisasi ke repositori remote GitHub.

**Tech Stack:** Python 3.13, Pandas, Plotly, Jupyter / nbconvert, Pytest, Git.

**Spec:** Permintaan pengguna per 14 Oktober 2026: Mengeliminasi sisa bahasa Inggris pada seluruh file notebook `.ipynb` dan menyelaraskan dengan dokumentasi portofolio berbahasa Indonesia.

## Global Constraints

- Seluruh teks penjelasan, judul grafik, label sumbu, tooltip, dan pesan log menggunakan Bahasa Indonesia baku dan profesional. Istilah teknis universal yang lazim di industri data (*SQL, Python, Cloud, Machine Learning, ETL, Pipeline, Jaccard Index*) tetap dipertahankan sesuai konvensi.
- Master dataset terverifikasi (`data/processed/master_dataset_eda.csv`, 430 baris) tidak boleh terhapus atau tertimpa oleh data sampel 5 baris saat `clean.ipynb` dijalankan.
- Seluruh 166 unit test pada test suite wajib tetap lulus 100% (`166 passed, 0 failures`).
- Seluruh grafik yang ter-embed di `eda.ipynb` dan diekspor ke `eda_report.html` serta `assets/charts/` harus menampilkan label Bahasa Indonesia baru yang konsisten.

## Review Focus

1. **Notebook Execution Outputs:** Memastikan `clean.ipynb` dan `eda.ipynb` memiliki output sel (`outputs` tidak kosong) sehingga saat dilihat langsung di preview GitHub atau Jupyter Viewer, grafik dan tabel langsung terlihat tanpa harus dijalankan ulang oleh reviewer.
2. **Chart Label Consistency:** Memastikan label sumbu dan tooltip pada 15+ fungsi grafik di `app/charts.py` menggunakan Bahasa Indonesia seragam (misal: "Jumlah Lowongan", "Gaji Rata-rata (IDR / Bulan)", "Pengalaman Minimum (Tahun)").
3. **Dataset Safety in clean.ipynb:** Memastikan cell penyimpanan data pada `clean.ipynb` memproteksi 430 baris master dataset agar tidak ter-overwrite oleh 5 baris data mentah sampel lokal.
4. **Interactive HTML Report Integrity:** Memastikan `eda_report.html` (standalone viewer) ter-generate ulang dengan ukuran penuh (~490KB+) dan semua grafik interaktif berfungsi offline.
5. **Test Suite Regressions:** Memastikan tidak ada pengujian di `tests/` yang gagal akibat perubahan label atau kategori string.

---

### Task 1: Lokalisasi Label, Judul, dan Tooltip Grafik di `app/charts.py`

**Files:**
- Modify: `app/charts.py`
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Fungsi grafik: `plot_salary_distribution`, `plot_salary_vs_experience`, `plot_top_skills_bar`, `plot_skill_cooccurrence_heatmap`, `plot_role_distribution`, `plot_experience_distribution`, `plot_education_distribution`, `plot_workplace_type_distribution`, `plot_top_companies`, `plot_remote_premium`, `plot_skill_vs_salary`, dll.

- [ ] **Step 1: Update judul grafik dan label sumbu di `app/charts.py`**
  - Ubah judul dari bahasa Inggris ke Bahasa Indonesia:
    - `"Salary Distribution by {by}"` -> `"Distribusi Gaji Berdasarkan {by}"`
    - `"Salary vs. Experience"` -> `"Sebaran Gaji vs. Pengalaman Minimum"`
    - `"Top {n} Most-Requested Skills"` -> `"Top {n} Keahlian Paling Banyak Diminta"`
    - `"Skill Co-occurrence (Jaccard Similarity)"` -> `"Korelasi Kemunculan Bersama Keahlian (Indeks Jaccard)"`
    - `"Job Distribution by Role"` -> `"Distribusi Lowongan Berdasarkan Peran"`
    - `"Distribution by Minimum Experience"` -> `"Distribusi Berdasarkan Syarat Pengalaman Kerja"`
    - `"Distribution by Required Education"` -> `"Distribusi Berdasarkan Syarat Pendidikan Minimal"`
    - `"Distribution by Workplace Type"` -> `"Distribusi Berdasarkan Model Kerja"`
    - `"Top {n} Companies Hiring Data Talent"` -> `"Top {n} Perusahaan Perekrut Talenta Data"`
    - `"Median Salary by Workplace Type"` -> `"Perbandingan Median Gaji Berdasarkan Model Kerja"`
  - Ubah nama label sumbu:
    - `"Jobs"` / `"Job count"` -> `"Jumlah Lowongan"`
    - `"Min experience (years)"` -> `"Pengalaman Minimum (Tahun)"`
    - `"Salary (IDR / month)"` -> `"Gaji (IDR / Bulan)"`
    - `"Role"` -> `"Peran"`
    - `"Company"` -> `"Perusahaan"`
  - Ubah bucket kategori pengalaman kerja di `plot_experience_distribution`:
    - `["Fresher", "1-2 years", "3-5 years", "6+ years"]` -> `["Fresh Grad (< 1 Thn)", "1-2 Tahun", "3-5 Tahun", "6+ Tahun"]`
  - Ubah trendline & hover template:
    - `"Overall trend"` -> `"Tren Keseluruhan"`
    - `"Experience: %{x}y<br>Salary: Rp %{y:,.0f}"` -> `"Pengalaman: %{x} Thn<br>Gaji: Rp %{y:,.0f}"`
    - `"Median (with skill)"` -> `"Median (dengan skill)"`
    - `"Salary premium (IDR / month)"` -> `"Premi Gaji (IDR / Bulan)"`

- [ ] **Step 2: Jalankan test suite untuk memvalidasi tidak ada regresi**
  - Run: `pytest -v tests/test_dashboard.py`
  - Expected: Semua test lulus (`100% pass`).

---

### Task 2: Perombakan Penuh `clean.ipynb` ke Bahasa Indonesia & Eksekusi

**Files:**
- Modify: `clean.ipynb`

**Interfaces:**
- Input: `data/raw/job_details.csv`
- Output: `clean.ipynb` dengan seluruh sel markdown, komentar kode, print terminal, dan output sel terisi lengkap dalam Bahasa Indonesia.

- [ ] **Step 1: Tulis ulang sel markdown dan sel kode di `clean.ipynb`**
  - Cell 0 (Markdown): `# Pipeline Pembersihan & Rekayasa Fitur Data`
    - Penjelasan arsitektur ETL pengolahan data mentah scraping menjadi dataset terstandarisasi.
    - Input, Output, dan modul logika di `glints_scraper.transform`.
    - Daftar rekayasa fitur utama (Standardisasi gaji IDR, 32 flag boolean skill, kanonisasi kota, ekstraksi tahun pengalaman, dan normalisasi model kerja).
  - Cell 1 (Markdown): `## Tahapan Pembersihan Data`
    - 7 langkah sistematis pipeline transformasi data.
  - Cell 2 (Code): Setup environment path dan import fungsi `transform` (komentar dalam Bahasa Indonesia).
  - Cell 3 (Markdown): `## 1. Pemuatan Data Mentah (Raw Scraped Data)`
  - Cell 4 (Code): Pemuatan file `data/raw/job_details.csv` dan preview sampel.
  - Cell 5 (Markdown): `## 2. Eksekusi Pipeline Transformasi Data`
  - Cell 6 (Code): Eksekusi `master = transform(raw)` dan inspeksi dimensi serta kolom yang dihasilkan.
  - Cell 7 (Markdown): `## 3. Validasi Skema dan Kualitas Data`
  - Cell 8 (Code): Pengecekan kolom inti, jumlah skill flag, distribusi model kerja, dan jenjang pendidikan (output cetak Bahasa Indonesia).
  - Cell 9 (Markdown): `## 4. Penyimpanan Master Dataset Bersih`
  - Cell 10 (Code): Logika penyimpanan yang aman (memvalidasi dan mempertahankan 430 baris master dataset terverifikasi).

- [ ] **Step 2: Eksekusi `clean.ipynb` secara in-place**
  - Run: `jupyter nbconvert --execute --to notebook --inplace clean.ipynb`
  - Expected: `clean.ipynb` berhasil dieksekusi dan memiliki output sel terisi (tidak ada sel kosong).

---

### Task 3: Penyempurnaan `scripts/build_eda_notebook.py`, Regenerasi `eda.ipynb` & Ekspor Laporan

**Files:**
- Modify: `scripts/build_eda_notebook.py`
- Modify: `eda.ipynb`
- Modify: `eda_report.html`

**Interfaces:**
- Script `build_eda_notebook.py` membangun struktur notebook `eda.ipynb`
- Eksekusi nbconvert mengisi seluruh output interaktif Plotly
- Ekspor nbconvert menghasilkan standalone report `eda_report.html`

- [ ] **Step 1: Audit teks kode dan print di `scripts/build_eda_notebook.py`**
  - Pastikan semua string print, komentar kode, dan markdown sel di generator sudah 100% Bahasa Indonesia.
  - Contoh:
    - `print(f"[DATA] Total lowongan terverifikasi: {len(df):,}")`
    - `print(f"[KEAHLIAN] Fitur skill terdeteksi: {len(skill_cols)}")`
    - `print(f"[GAJI] Keterbukaan informasi gaji: {disclosed_salaries:,} ({disclosed_salaries/len(df):.1%})"`
  - Jalankan generator: `python scripts/build_eda_notebook.py`
  - Expected: File `eda.ipynb` ter-generate ulang dengan konfigurasi terbaru.

- [ ] **Step 2: Eksekusi `eda.ipynb` secara in-place**
  - Run: `jupyter nbconvert --execute --to notebook --inplace eda.ipynb`
  - Expected: Seluruh 26 sel berhasil dieksekusi dengan output grafik interaktif Plotly terisi.

- [ ] **Step 3: Ekspor laporan HTML mandiri `eda_report.html`**
  - Run: `jupyter nbconvert --to html eda.ipynb --output eda_report.html --embed-images`
  - Expected: File `eda_report.html` terbarui (~490KB+) dengan visualisasi berbahasa Indonesia.

---

### Task 4: Regenerasi Aset Visual PNG & Validasi Test Suite

**Files:**
- Modify: `assets/charts/*.png`
- Test: `pytest`

**Interfaces:**
- Script `scripts/generate_assets.py` membaca `master_dataset_eda.csv` dan memanggil `app/charts.py` untuk mengekspor 11 file PNG resolusi tinggi.

- [ ] **Step 1: Jalankan generator aset gambar PNG**
  - Run: `python scripts/generate_assets.py`
  - Expected: Seluruh 11 grafik di `assets/charts/` ter-update dengan label Bahasa Indonesia.

- [ ] **Step 2: Jalankan full test suite**
  - Run: `pytest -v`
  - Expected: Seluruh 166 test lulus (`166 passed, 0 failures`).

---

### Task 5: Git Commit & Remote Push ke GitHub

**Files:**
- Git tree: `app/charts.py`, `clean.ipynb`, `eda.ipynb`, `eda_report.html`, `scripts/build_eda_notebook.py`, `assets/charts/*.png`, `docs/superpowers/plans/`

- [ ] **Step 1: Audit git status dan sanitasi kredensial**
  - Run: `git status`
  - Pastikan tidak ada file `secrets/` atau cache sementara yang tidak diinginkan.

- [ ] **Step 2: Commit perubahan**
  - Run: `git add .`
  - Run: `git commit -m "docs: localize all notebooks, chart labels, and reports to Indonesian"`

- [ ] **Step 3: Push ke GitHub remote**
  - Run: `git push origin master`
  - Run: `git push origin main`
  - Expected: Kedua branch di GitHub remote ter-update sempurna.
