# Desain Remake Portofolio Analisis Pasar Kerja Data Indonesia (Glints Job Intel)

**Tanggal:** 2026-10-10  
**Status:** Disetujui untuk Eksekusi (Final Spec)  
**Tujuan Dokumen:** Spesifikasi desain proyek komprehensif untuk merombak portofolio Data Analyst sebelum git push ke GitHub.

---

## 1. Intent & The Why

### Mengapa Proyek Ini Dibuat?
Repositori ini dirancang sebagai **portofolio unggulan Data Analyst** yang ditujukan untuk *hiring manager*, tim rekrutmen, dan audiens umum. 

Banyak portofolio data analyst yang terjebak pada grafik deskriptif klise tanpa konteks bisnis (misal: ranking bahasa pemrograman biasa). Proyek ini membedakan diri dengan:
1. **Narasi Kritis & Fenomena Kontra-Intuitif (*"Woahh iya juga ya"*)**: Mengungkap dua paradoks nyata dalam bursa kerja lokal berdasarkan data empiris.
2. **Integritas Sumber (*Proof of Source*)**: Memperlihatkan pipa data scraping mandiri menggunakan Playwright yang rapi, transparan, dan beretika.
3. **Reproducibility Tinggi**: Menyediakan dataset snapshot bersih di repo sehingga siapa pun dapat mereproduksi analisis, laporan HTML, dan dashboard interaktif secara instan tanpa perlu akun Glints.
4. **Gaya Bahasa Industri Indonesia**: Menggunakan Bahasa Indonesia profesional yang lugas dengan terminologi standar industri kerja teknologi Indonesia (*fresh graduate*, *entry-level*, *tech stack*, *range gaji*, *on-site*, *hybrid*, *unicorn syndrome*).

---

## 2. Goals, Non-Goals, dan Anti-Goals

### Goals
1. **Fresh Scrape Data Aktual**:
   - Menjalankan scraping Glints terbaru menggunakan sesi Playwright yang sudah aktif (`secrets/auth.json`).
   - Mencakup 4 kata kunci utama: `data analyst`, `data scientist`, `data engineer`, `machine learning`.
   - Menerapkan filter ketat khusus wilayah Indonesia (mengeliminasi data luar negeri seperti Vietnam yang sempat bocor di masa lalu).
2. **Dua Babak Narasi Analisis Utama (Dihitung Dinamis dari Data Bersih)**:
   - **Babak 1 — "Inversi Ekspektasi / Unicorn Syndrome" (Ekspektasi Dewa, Budget UMR)**:
     Membongkar fenomena di mana lowongan level pemula (*fresh graduate* / `< 1 tahun`) justru menuntut proporsi *advanced/academic skills* yang tidak realistis (Python, Statistika, Machine Learning) dengan median gaji terendah (bahkan banyak di kisaran Rp 1,5–2,5 juta). Sebaliknya, lowongan Senior/Mid lebih terarah pada *practical industry tools* (ETL, Cloud, BI) dengan kompensasi yang sepadan.
   - **Babak 2 — "Ilusi Fleksibilitas WFH" (Remote Adalah Barang Mewah)**:
     Membantah anggapan bahwa fleksibilitas WFH adalah standar umum industri data di Indonesia: sebagian besar lowongan (~89%+) tetap mewajibkan *On-site* (WFO). Lowongan *Remote* hanya dinikmati segelintir talenta senior dengan kompensasi yang jauh lebih tinggi (+70-80% lebih tinggi dibanding *On-site*).
3. **4 Visualisasi Showcase di README (`assets/charts/`)**:
   - `01_skill-burden-by-career-stage.png`: Perbandingan tuntutan skill berat (*advanced/academic*) vs level karir.
   - `02_salary-reality-curve.png`: Kurva sebaran gaji terhadap pengalaman kerja (*The Reality Curve*).
   - `03_remote-luxury-comparison.png`: Proporsi WFO vs Remote beserta perbandingan median gajinya.
   - `04_real-tech-stack-landscape.png`: Ranking kebutuhan tools per role (dominasi SQL & Excel vs tools AI).
4. **Restrukturisasi Dashboard Streamlit (`app/dashboard.py`)**:
   - Menyelaraskan tampilan dashboard dengan alur cerita dua babak utama di README.
   - Menggunakan Bahasa Indonesia industri dengan penjelasan metrik yang ramah bagi *hiring team* dan orang awam.
5. **Dokumentasi & Higienitas Repositori**:
   - README.md baru dalam Bahasa Indonesia industri yang tajam, interaktif, dan informatif.
   - Panduan reproduksi eksplisit (`docs/reproduce.md`) yang membedakan *fast-path* dan *scratch scraping*.
   - Sanitasi repositori: verifikasi `.gitignore` agar file rahasia (`secrets/auth.json`) tidak bocor, riwayat git yang bersih, dan siap untuk `git push`.

### Non-Goals
- Tidak mencakup peran di luar rumpun data (Web Dev, Mobile Dev, UI/UX, dsb).
- Tidak membangun model machine learning prediktif (fokus pada analisis pasar, EDA, visualisasi, dan business insight).
- Tidak menggunakan framework frontend eksternal yang rumit; tetap menggunakan Streamlit.

### Anti-Goals
- **Anti-Visualisasi Dangkal**: Menolak visualisasi tanpa interpretasi bisnis.
- **Anti-Data Dummy/Sintetis**: Menghapus ketergantungan pada dataset tiruan; seluruh metrik harus murni berasal dari data Glints aktual.
- **Anti-Kebocoran Kredensial**: Tidak ada data otentikasi atau cookie yang boleh masuk ke commit Git.
- **Anti-Data Asing**: Tidak mengikutsertakan lowongan luar negeri ke dalam dataset pasar kerja Indonesia.

---

## 3. Batasan Teknis & Lingkungan (Constraints)

- **OS / Platform**: Windows, PowerShell.
- **Runtime**: Python 3.13.
- **Library**: `playwright`, `parsel`, `pandas`, `matplotlib`, `seaborn`, `streamlit`, `jupyter`.
- **Autentikasi**: `secrets/auth.json` yang telah disimpan melalui sesi Chrome resmi.
- **Polite Scraping**: Menggunakan delay sopan 2.0 detik per request untuk menjaga stabilitas scraping.

---

## 4. Keputusan Arsitektur yang Telah Dikunci

| Aspek | Keputusan |
|---|---|
| **Bahasa & Terminologi** | Bahasa Indonesia profesional dengan istilah industri yang lazim (*fresh graduate*, *tech stack*, *entry-level*, *range gaji*, *on-site*, *hybrid*, *unicorn syndrome*). |
| **Integritas Metrik** | Semua angka dan persentase dihitung dinamis dari hasil olah dataset bersih (tidak ada angka statis palsu). |
| **Definisi Inversi Ekspektasi** | Mengukur tingginya tuntutan keahlian akademis lanjutan (Python, Stats, ML) pada lowongan pemula vs keahlian praktis infrastruktur (ETL, Cloud, BI) pada posisi berpengalaman. |
| **Dashboard Streamlit** | Ditata ulang mengikuti alur naratif dua babak utama dengan bahasa Indonesia industri, dilengkapi eksplorasi interaktif pendukung. |
| **Reproducibility** | Jalur Cepat (menggunakan snapshot bersih di repo tanpa perlu scraping) dan Jalur Penuh (scraping mandiri dengan Playwright). |

---

## 5. Rencana Tahapan Eksekusi (Implementation Steps)

1. **Tahap 1: Eksekusi Scraping Data Baru (Fresh Data Collection)**
   - Jalankan pengambilan link lowongan Glints aktif untuk 4 keyword data.
   - Jalankan ekstraksi detail lowongan (deskripsi, kualifikasi, skill tags, lokasi, gaji, pengalaman) ke `data/raw/job_details.csv`.
2. **Tahap 2: Data Cleaning & Filtering Indonesia**
   - Update `src/glints_scraper/transform.py` untuk membuang entri non-Indonesia.
   - Jalankan proses transformasi menghasilkan `data/processed/master_dataset_eda.csv`.
3. **Tahap 3: Analisis EDA & Pembuatan 4 Visualisasi Utama**
   - Update `scripts/generate_assets.py` untuk merender 4 grafik preview di `assets/charts/`.
   - Update `eda.ipynb` dan generate ulang `eda_report.html`.
4. **Tahap 4: Restrukturisasi Dashboard Streamlit**
   - Perbarui `app/dashboard.py` dan `app/charts.py` sesuai alur narasi dua babak dan istilah industri Indonesia.
5. **Tahap 5: Dokumentasi README & Git Hygiene**
   - Tulis ulang `README.md` dengan gaya bahasa yang disepakati.
   - Perbarui `docs/reproduce.md`.
   - Inisialisasi git repository (`git init`), audit `.gitignore`, dan siapkan commit bersih pertama siap push ke GitHub.
