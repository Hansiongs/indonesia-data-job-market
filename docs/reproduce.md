# Panduan Menjalankan Ulang Scraping dan Analisis

Repositori ini sudah menyertakan dataset bersih di `data/processed/master_dataset_eda.csv`. Anda tidak perlu melakukan scraping ulang jika hanya ingin menjalankan dashboard atau membaca laporan analisis.

Panduan ini ditujukan bagi Anda yang ingin mengambil ulang data mentah dari nol lewat portal Glints Indonesia.

---

## 1. Persiapan Dependensi

Pastikan virtual environment sudah aktif, lalu pasang paket tambahan untuk scraper.

```bash
pip install -r requirements-scraper.txt
pip install -e ".[scraper]"
playwright install chromium
```

---

## 2. Login Sesi Glints

Proses login Google dan proteksi Cloudflare sering memblokir browser otomatis bawaan seperti `playwright codegen`. Untuk mengatasinya, gunakan script `scripts/login.py` yang menghubungkan Playwright ke browser Google Chrome asli di komputer Anda lewat port debugging.

```bash
# Jalankan script bantu login
python scripts/login.py
```

### Cara Kerja Script
1. Script akan membuka jendela Google Chrome asli.
2. Silakan login ke akun Glints seperti biasa menggunakan akun Google atau email.
3. Setelah berhasil masuk ke halaman utama Glints, kembali ke terminal lalu tekan tombol **Enter**.
4. Script akan menyimpan session cookies ke file `secrets/auth.json`.
5. File `secrets/auth.json` tersimpan di komputer lokal dan sudah masuk daftar `.gitignore`. Jangan pernah mengunggah atau membagikan file ini ke repositori publik.

---

## 3. Pengambilan Data Mentah (Scraping)

Setelah sesi login tersimpan di `secrets/auth.json`, jalankan kedua modul scraper secara berurutan.

### A. Mengambil Daftar Tautan Lowongan (`links.py`)
```bash
python -m glints_scraper.links
```
Script ini mencari lowongan untuk 4 kata kunci utama (*data analyst, data scientist, data engineer, machine learning*) di Indonesia dan menyimpan daftarnya secara bertahap ke `data/raw/glints_jobs.csv`.

### B. Mengambil Detail Lowongan (`details.py`)
```bash
python -m glints_scraper.details
```
Script ini membaca daftar tautan dari `data/raw/glints_jobs.csv`, membuka tiap halaman lowongan, lalu mengambil deskripsi lengkap, tag skill, dan informasi gaji ke `data/raw/job_details.csv`. Proses ini sudah dilengkapi jeda antar-request dan penyimpanan checkpoint berkala agar aman dilanjutkan jika terputus.

---

## 4. Pembersihan dan Pembuatan Fitur (`transform.py`)

Setelah pengumpulan data mentah selesai, jalankan modul pembersihan data.

```bash
python -m glints_scraper.transform
```

### Tahapan Pembersihan Data
1. Menyaring khusus lowongan yang berlokasi di Indonesia dan membuang data luar negeri seperti Vietnam atau Singapura.
2. Mengubah teks gaji IDR menjadi angka numerik pada kolom `salary_min`, `salary_max`, dan `salary_avg`.
3. Membuat 32 kolom boolean skill teknis dari hasil pembacaan deskripsi pekerjaan dan tag skill.
4. Menyeragamkan penulisan jenjang pendidikan, jenis kontrak kerja, dan model kerja (*On-site, Remote, Hybrid*).
5. Menyimpan hasil akhirnya ke `data/processed/master_dataset_eda.csv`.

---

## 5. Memperbarui Notebook, Laporan HTML, dan Gambar Grafik

Untuk memperbarui output notebook, laporan HTML mandiri, dan gambar grafik dari dataset baru, jalankan perintah berikut.

```bash
# Menjalankan ulang seluruh sel di notebook
jupyter nbconvert --execute --to notebook --inplace eda.ipynb

# Mengekspor notebook ke file HTML mandiri
jupyter nbconvert --to html eda.ipynb --output eda_report.html --embed-images

# Membuat ulang gambar grafik di folder assets/charts/
python scripts/generate_assets.py
```

---

## 6. Menjalankan Unit Test

Jalankan pengujian otomatis untuk memastikan seluruh fungsi parser, transformasi data, dan grafik berjalan normal.

```bash
pytest -v
```

Semua pengujian berjalan secara lokal tanpa koneksi internet.

---

## Etika Scraping dan Batasan Data

- Patuhi aturan `robots.txt`, batasan frekuensi request (*rate limit*), dan ketentuan layanan Glints Indonesia. Hindari menjalankan scraper secara agresif dalam waktu bersamaan.
- Dataset ini merupakan potret pada satu waktu pengambilan (*snapshot*). Angka gaji yang dianalisis bergantung pada keterbukaan masing-masing perusahaan saat memasang iklan lowongan.
