# Panduan Reproduksi Pipeline Scraping & Analisis Mandiri

Repositori ini telah menyertakan dataset bersih terverifikasi di `data/processed/master_dataset_eda.csv`, sehingga Anda **tidak wajib** melakukan scraping untuk menjalankan dashboard atau membaca laporan analisis.

Panduan ini ditujukan bagi praktisi yang ingin menjalankan pipeline scraping mandiri dari nol langsung dari portal Glints Indonesia.

---

## 1. Persiapan Dependensi

Pastikan virtual environment telah aktif, lalu pasang dependensi scraper:

```bash
pip install -r requirements-scraper.txt
pip install -e ".[scraper]"
playwright install chromium
```

---

## 2. Autentikasi Sesi Glints (Aman & Bebas Blokir Bot)

Google Sign-In dan proteksi Cloudflare memblokir proses otomasi standar seperti `playwright codegen`. Untuk itu, proyek ini menggunakan script autentikasi khusus di `scripts/login.py` yang menghubungkan Playwright ke browser Google Chrome asli Anda via port debugging:

```bash
# Jalankan helper login
python scripts/login.py
```

### Langkah yang Terjadi:
1. Skrip akan membuka peramban Google Chrome asli.
2. Anda dapat melakukan proses masuk (Login) ke akun Glints secara normal (baik melalui Google Sign-In maupun email).
3. Setelah berhasil masuk ke halaman Glints, tekan tombol **Enter** pada terminal.
4. Skrip akan secara otomatis mengekstraksi seluruh session cookies ke dalam berkas `secrets/auth.json`.
5. Berkas `secrets/auth.json` disimpan secara lokal dan **otomatis diabaikan oleh Git** (`.gitignore`). Jangan pernah membagikan atau mengunggah berkas ini ke repositori publik.

---

## 3. Ekstraksi Data Mentah (Scraping)

Setelah sesi tersimpan di `secrets/auth.json`, jalankan modul scraper:

### A. Pengambilan Tautan Lowongan Kerja (`links.py`)
```bash
python -m glints_scraper.links
```
Skrip ini akan mencari lowongan untuk 4 kata kunci utama (*data analyst, data scientist, data engineer, machine learning*) di Indonesia dan menyimpannya secara inkremental ke `data/raw/glints_jobs.csv`.

### B. Pengambilan Rincian Lowongan Kerja (`details.py`)
```bash
python -m glints_scraper.details
```
Skrip ini membaca tautan dari `data/raw/glints_jobs.csv`, mengunjungi halaman rincian lowongan kerja, dan mengekstrak deskripsi lengkap, tag kompetensi, serta rentang kompensasi ke `data/raw/job_details.csv`. Skrip dilengkapi mekanisme jeda (*polite rate-limiting*) dan penyimpanan checkpoint berkala.

---

## 4. Pembersihan & Rekayasa Fitur Data (`transform.py`)

Setelah data mentah terkumpul, jalankan modul transformasi data:

```bash
python -m glints_scraper.transform
```

### Tahapan Transformasi:
1. **Validasi Lokasi Ketat:** Memfilter 100% lowongan kerja berbasis di Indonesia dan membuang data lokasi luar negeri/regional (seperti Vietnam).
2. **Standardisasi Gaji:** Mengurai string gaji IDR menjadi nilai numerik standar (`salary_min`, `salary_max`, `salary_avg`).
3. **Ekstraksi Skill Flag:** Mengekstrak 32 kolom boolean kompetensi teknis dari deskripsi pekerjaan dan tag skill.
4. **Pembersihan Metadata:** Menormalisasi jenjang pendidikan, jenis kontrak kerja, dan tipe model kerja (*On-site / Remote / Hybrid*).
5. **Penyimpanan:** Menghasilkan dataset bersih siap analisis di `data/processed/master_dataset_eda.csv`.

---

## 5. Eksekusi Notebook, Laporan Mandiri & Aset Visual

Untuk memperbarui notebook analisis dan laporan HTML mandiri dari dataset yang baru dibuat:

```bash
# Eksekusi notebook secara otomatis
jupyter nbconvert --execute --to notebook --inplace eda.ipynb

# Ekspor notebook ke laporan HTML mandiri (embed images)
jupyter nbconvert --to html eda.ipynb --output eda_report.html --embed-images

# Generate ulang aset grafik resolusi tinggi
python scripts/generate_assets.py
```

---

## 6. Pengujian Unit (Test Suite)

Jalankan pengujian unit untuk memastikan seluruh parser dan grafik bekerja tanpa kendala:

```bash
pytest -v
```

Seluruh pengujian berjalan secara offline dan tidak membutuhkan koneksi internet.

---

## ⚠️ Etika Scraping & Keterbatasan Data

- **Etika Scraping:** Hormati aturan robots.txt, batasan frekuensi kueri (*rate limits*), dan ketentuan layanan Glints Indonesia. Jangan menjalankan proses scraping dengan beban konkurensi agresif.
- **Keterbatasan Data:** Data mencerminkan frekuensi kemunculan kata kunci pada satu rentang waktu snapshot dan bergantung pada keterbukaan perusahaan dalam mencantumkan nominal kompensasi.
