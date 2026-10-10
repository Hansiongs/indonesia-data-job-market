# Master Dataset Schema

The public cleaned snapshot lives at
`data/processed/master_dataset_eda.csv`. It contains one row per scraped job
posting and is the input for both the dashboard and EDA.

Raw descriptions, URLs, salary strings, and session data are not included in
the public cleaned snapshot. The optional scraping pipeline uses those fields
before transforming them into this schema.

## Public Snapshot Columns

### Identity

| Column | Type | Nullable | Description |
|---|---|---|---|
| `keyword` | string | no | Search keyword that surfaced the posting |
| `job_title` | string | no | Cleaned job title |
| `company_name` | string | no | Company name from the posting |
| `city_clean` | string | yes | Canonical city mapped from the source location |

### Compensation

| Column | Type | Nullable | Description |
|---|---|---|---|
| `salary_avg` | number | yes | Average disclosed salary, IDR/month |

Salary is nullable because job boards often allow employers to hide the
salary. Salary charts and medians ignore null values.

### Work Pattern

| Column | Type | Nullable | Description |
|---|---|---|---|
| `exp_min_years` | integer | yes | Minimum experience requested by the posting |
| `workplace_type` | string | yes | `On-site`, `Remote`, or `Hybrid` |
| `job_education_clean` | string | yes | Normalised education bucket such as `S1` or `S2` |

### Skills

The snapshot contains 32 boolean `skill_<name>` columns. A value of `1` means
the skill catalogue term was detected in the source description and/or skill
tags. It measures mentions, not a verified mandatory requirement.

Current skill columns include:

```text
skill_python, skill_sql, skill_r, skill_tableau, skill_power_bi,
skill_excel, skill_aws, skill_gcp, skill_azure, skill_spark, skill_hadoop,
skill_kafka, skill_tensorflow, skill_pytorch, skill_scikit_learn,
skill_pandas, skill_numpy, skill_etl, skill_airflow, skill_dbt,
skill_postgres, skill_mongodb, skill_redis, skill_docker, skill_kubernetes,
skill_git, skill_statistics, skill_machine_learning, skill_deep_learning,
skill_nlp, skill_computer_vision, skill_data_visualization
```

## Raw Pipeline Fields

Before cleaning, `data/raw/job_details.csv` contains fields such as
`job_description`, `skill_tags`, `job_salary`, `job_education`, `job_method`,
`job_experience`, and `url`. Those files are local-only and are ignored by
Git. See [`docs/reproduce.md`](reproduce.md) for the optional scrape flow.
