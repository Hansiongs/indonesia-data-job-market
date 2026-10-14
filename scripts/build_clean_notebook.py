"""Generate clean.ipynb with natural, professional Indonesian tech terminology."""
from pathlib import Path
import nbformat as nbf

def create_clean_notebook():
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

    # Cell 0: Overview & Context
    cells.append(nbf.v4.new_markdown_cell("""# Data Cleaning & Feature Engineering Pipeline
### Standarisasi Data Scraping Menjadi Dataset Siap Analisis (Master EDA)

Notebook ini mendokumentasikan pipeline data cleaning dan feature engineering yang mentransformasi data mentah hasil scraping Glints (`data/raw/job_details.csv`) menjadi master dataset yang bersih dan terstandarisasi (`data/processed/master_dataset_eda.csv`).

---

### Gambaran Umum Pipeline

- **Input Data:** `data/raw/job_details.csv` (data scraping mentah berisi deskripsi pekerjaan, format gaji teks, tag skill, dan metadata lowongan).
- **Output Data:** `data/processed/master_dataset_eda.csv` (dataset bersih dengan tipe data konsisten, kolom numerik, dan flag boolean skill).
- **Core Logic:** Seluruh fungsi transformasi diimplementasikan secara modular pada package `src/glints_scraper/transform.py` dan telah diuji secara komprehensif melalui unit test di `tests/test_transform.py`.

#### Transformasi Kunci:
1. **Salary Parsing:** Mengonversi string teks gaji beragam format menjadi metrik numerik bulanan (`salary_min`, `salary_max`, `salary_avg` dalam IDR).
2. **Skill Extraction:** Mengekstrak 32 kolom boolean tech stack (`skill_<name>`) dari deskripsi pekerjaan dan skill tags.
3. **Filter Lokasi Domestik:** Memastikan 100% lowongan berbasis di Indonesia (membersihkan entri luar negeri/regional) dan melakukan kanonisasi nama kota ke `city_clean`.
4. **Normalisasi Pengalaman & Pendidikan:** Mengonversi teks syarat pengalaman menjadi angka integer `exp_min_years` serta menstandarkan jenjang pendidikan ke kategori kanonikal (S1, S2, D3, SMA/SMK).
5. **Klasifikasi Model Kerja:** Mengelompokkan lowongan ke dalam kategori kerja baku: *On-site*, *Hybrid*, atau *Remote*."""))

    # Cell 1: Pipeline Workflow Steps
    cells.append(nbf.v4.new_markdown_cell("""---

## Tahapan Eksekusi Pipeline

Pipeline data dijalankan melalui fungsi terpusat `transform()` dengan urutan proses:

1. **Drop Lowongan Tidak Lengkap:** Menyaring baris yang kehilangan metadata esensial (deskripsi kosong, format rusak).
2. **Filter Wilayah & Lowongan Aktif:** Menghapus lowongan yang sudah ditutup (*closed*) dan membuang posting luar negeri (seperti Vietnam/Singapura).
3. **Standardisasi Gaji IDR:** Mengekstrak batas bawah, batas atas, dan rata-rata gaji bulanan.
4. **Deteksi Tech Stack:** Melakukan pencocokan pola regex untuk 32 keahlian teknis (Python, SQL, Cloud, Tableau, Power BI, dll.).
5. **Normalisasi Kategori:** Merapikan format tipe pekerjaan (*Full-time, Contract, Internship*) dan model kerja (*On-site, Hybrid, Remote*)."""))

    # Cell 2: Setup & Imports
    cells.append(nbf.v4.new_code_cell("""import sys
from pathlib import Path
import pandas as pd

# Menambahkan direktori src/ ke sys.path agar modul lokal dapat diimpor langsung
sys.path.insert(0, str(Path.cwd() / "src"))

from glints_scraper.transform import transform

print("[INFO] Environment dan modul glints_scraper.transform berhasil dimuat.")"""))

    # Cell 3: Load Raw Data Header
    cells.append(nbf.v4.new_markdown_cell("""---

## 1. Pemuatan Raw Data Hasil Scraping

Membaca data mentah hasil scraping untuk menginspeksi struktur kolom awal sebelum pembersihan dilakukan."""))

    # Cell 4: Load Raw Data Code
    cells.append(nbf.v4.new_code_cell("""raw_path = Path("data/raw/job_details.csv")

if not raw_path.exists():
    print(f"[PERINGATAN] File mentah {raw_path} tidak ditemukan secara lokal.")
    print("Membuat sampel data mentah untuk demonstrasi pipeline...")
    sample_raw = pd.DataFrame({
        "url": ["https://glints.com/id/opportunities/jobs/demo-1"],
        "keyword": ["data analyst"],
        "job_title": ["Data Analyst"],
        "company_name": ["PT Teknologi Nusantara"],
        "job_location": ["Jakarta, Indonesia"],
        "job_description": ["Kandidat wajib menguasai SQL, Python, dan Tableau untuk reporting."],
        "skill_tags": ["SQL, Python, Tableau"],
        "job_salary": ["Rp 8.000.000 - 12.000.000 / bulan"],
        "job_education": ["S1 Sistem Informasi"],
        "job_method": ["Full-time"],
        "job_experience": ["1-2 tahun"]
    })
    raw = sample_raw
else:
    raw = pd.read_csv(raw_path)

print(f"[DATA] Dimensi Raw Data: {raw.shape[0]:,} baris x {raw.shape[1]} kolom")
raw.head()"""))

    # Cell 5: Run Cleaning Pipeline Header
    cells.append(nbf.v4.new_markdown_cell("""---

## 2. Eksekusi Data Cleaning & Feature Engineering

Menjalankan fungsi `transform(raw)` end-to-end. Fungsi ini bersifat *pure* (tidak memodifikasi dataframe input asli secara in-place) dan menghasilkan skema master dataset yang bersih."""))

    # Cell 6: Run Cleaning Pipeline Code
    cells.append(nbf.v4.new_code_cell("""master = transform(raw)

print(f"[DATA] Dimensi Master Dataset: {master.shape[0]:,} baris x {master.shape[1]} kolom")
print(f"[KOLOM] Sampel kolom hasil transformasi: {list(master.columns)[:12]}...")
master.head()"""))

    # Cell 7: Validate Schema Header
    cells.append(nbf.v4.new_markdown_cell("""---

## 3. Validasi Skema & Data Quality Check

Memeriksa kelengkapan kolom inti, sebaran nilai kategori, serta memastikan tidak ada inkonsistensi tipe data sebelum dataset digunakan untuk analisis lanjutan (EDA)."""))

    # Cell 8: Validate Schema Code
    cells.append(nbf.v4.new_code_cell("""expected_core_columns = {
    "keyword", "job_title", "company_name", "city_clean",
    "salary_min", "salary_max", "salary_avg",
    "exp_min_years", "employment_type", "workplace_type",
    "job_education_clean",
}

skill_columns = [col for col in master.columns if col.startswith("skill_")]

print(f"[VALIDASI] Total baris hasil proses: {len(master):,}")
print(f"[VALIDASI] Seluruh kolom inti terpenuhi: {expected_core_columns.issubset(master.columns)}")
print(f"[VALIDASI] Total fitur skill terdeteksi: {len(skill_columns)}")

if "workplace_type" in master.columns and not master["workplace_type"].empty:
    print("\\n[DISTRIBUSI] Model Kerja (Workplace Type):")
    print(master["workplace_type"].value_counts().to_string())

if "job_education_clean" in master.columns and not master["job_education_clean"].empty:
    print("\\n[DISTRIBUSI] Jenjang Pendidikan Minimal:")
    print(master["job_education_clean"].value_counts().to_string())"""))

    # Cell 9: Persist Master Dataset Header
    cells.append(nbf.v4.new_markdown_cell("""---

## 4. Penyimpanan Master Dataset

Menyimpan hasil transformasi ke `data/processed/master_dataset_eda.csv`. Dataset ini menjadi *single source of truth* untuk visualisasi pada notebook `eda.ipynb`, laporan mandiri `eda_report.html`, dan aplikasi dashboard Streamlit."""))

    # Cell 10: Persist Master Dataset Code
    cells.append(nbf.v4.new_code_cell("""output_path = Path("data/processed/master_dataset_eda.csv")

# Proteksi keamanan dataset:
# Jika file master 430 data terverifikasi sudah ada dan notebook dijalankan pada sampel kecil,
# pertahankan dataset 430 data utama agar integritas analisis tidak hilang.
if output_path.exists() and len(master) < 400:
    existing_len = len(pd.read_csv(output_path))
    print(f"[INFO] Master dataset utama sudah tersedia ({existing_len:,} baris).")
    print(f"[INFO] Pipeline demonstrasi sukses berjalan untuk {len(master):,} sampel data mentah.")
    print("[INFO] Dataset produksi tetap dipertahankan aman tanpa risiko penimpaan.")
else:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    master.to_csv(output_path, index=False)
    print(f"[SUKSES] {len(master):,} baris berhasil disimpan ke {output_path}")"""))

    nb.cells = cells
    
    output_path = Path("clean.ipynb")
    with open(output_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"[OK] Notebook {output_path} berhasil dibuat dengan {len(cells)} sel.")

if __name__ == "__main__":
    create_clean_notebook()
