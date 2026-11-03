# Skema Master Dataset

Dataset publik yang sudah dibersihkan tersimpan di `data/processed/master_dataset_eda.csv`. Setiap baris mewakili satu lowongan kerja dan menjadi sumber data utama untuk dashboard maupun notebook analisis (`eda.ipynb`).

Teks deskripsi mentah, tautan asli, format gaji teks, dan data sesi login tidak disertakan di dalam file publik ini. Data mentah tersebut hanya dipakai pada tahap scraping lokal sebelum diolah menjadi skema bersih di bawah ini.

## Daftar Kolom Dataset Publik

### Identitas Lowongan

| Kolom | Tipe | Boleh Kosong | Keterangan |
|---|---|---|---|
| `keyword` | string | tidak | Kata kunci pencarian yang memunculkan lowongan |
| `job_title` | string | tidak | Judul posisi pekerjaan yang sudah dirapikan |
| `company_name` | string | tidak | Nama perusahaan pemasang lowongan |
| `city_clean` | string | ya | Nama kota yang sudah diseragamkan dari lokasi asli |

### Kompensasi

| Kolom | Tipe | Boleh Kosong | Keterangan |
|---|---|---|---|
| `salary_avg` | number | ya | Rata-rata gaji bulanan yang dicantumkan dalam IDR |

Kolom gaji bisa bernilai kosong (*null*) karena sebagian perusahaan tidak mencantumkan nominal gaji di iklan lowongan. Perhitungan median dan grafik gaji hanya mengolah baris data yang memiliki nilai gaji.

### Pola Kerja dan Kualifikasi

| Kolom | Tipe | Boleh Kosong | Keterangan |
|---|---|---|---|
| `exp_min_years` | integer | ya | Batas pengalaman kerja minimal dalam hitungan tahun |
| `workplace_type` | string | ya | Kategori model kerja (`On-site`, `Remote`, atau `Hybrid`) |
| `job_education_clean` | string | ya | Kategori pendidikan minimal seperti `S1`, `S2`, `D3`, atau `SMA/SMK` |

### Keahlian Teknis (Skills)

Dataset ini memiliki 32 kolom boolean dengan format `skill_<nama>`. Nilai `1` menandakan keahlian tersebut ditemukan di dalam deskripsi pekerjaan atau tag skill, sedangkan nilai `0` berarti tidak disebutkan.

Daftar lengkap ke-32 kolom skill tersebut mencakup item berikut.

```text
skill_python, skill_sql, skill_r, skill_tableau, skill_power_bi,
skill_excel, skill_aws, skill_gcp, skill_azure, skill_spark, skill_hadoop,
skill_kafka, skill_tensorflow, skill_pytorch, skill_scikit_learn,
skill_pandas, skill_numpy, skill_etl, skill_airflow, skill_dbt,
skill_postgres, skill_mongodb, skill_redis, skill_docker, skill_kubernetes,
skill_git, skill_statistics, skill_machine_learning, skill_deep_learning,
skill_nlp, skill_computer_vision, skill_data_visualization
```

## Kolom Data Mentah (Lokal)

Sebelum dibersihkan oleh `transform.py`, file mentah `data/raw/job_details.csv` memuat kolom asli seperti `job_description`, `skill_tags`, `job_salary`, `job_education`, `job_method`, `job_experience`, dan `url`. File mentah ini hanya tersimpan di komputer lokal dan diabaikan oleh Git. Panduan lengkap pengambilan data mentah tersedia di [`docs/reproduce.md`](reproduce.md).
