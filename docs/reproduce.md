# Reproduce From A Fresh Scrape

The dashboard and EDA do **not** require a Glints account. A cleaned demo
snapshot is committed at `data/processed/master_dataset_eda.csv` so a fresh
clone can be explored immediately.

This page is for the optional advanced path: collecting a new snapshot from
Glints and running the same cleaning and analysis pipeline locally.

## 1. Install The Optional Scraper Dependencies

Create and activate a virtual environment first, then install:

```bash
pip install -r requirements-scraper.txt
pip install -e ".[scraper]"
playwright install chromium
```

The scraper uses Playwright with a user-owned browser session. Do not use a
shared account, CI runner, or someone else's `auth.json`.

## 2. Create A Local Session

```bash
playwright codegen --storage-state=secrets/auth.json https://glints.com/id/login
```

Log in in the browser that opens, then close it. The generated file stays in
`secrets/`, which is ignored by Git. Never commit it or upload it anywhere.

## 3. Collect The Raw Data

```bash
make scrape-links
make scrape-details
```

The scraper writes resumable checkpoints to `data/raw/`. If a run stops, run
the same command again. The raw files are intentionally not part of the
public portfolio dataset.

## 4. Clean And Rebuild The Portfolio Outputs

```bash
make pipeline
```

This command transforms `data/raw/job_details.csv`, rebuilds the cleaned
dataset, regenerates chart previews, and rebuilds `eda_report.html`.

## Important Notes

- Glints may change its HTML structure or access requirements; a scrape can
  stop working without changes to this repository.
- Respect Glints' terms, robots rules, rate limits, and applicable law.
- The dashboard measures keyword mentions and posting volume, not verified
  skill requirements or the number of unique openings.
- Do not replace the public demo snapshot with raw scraped data before checking
  that it contains no credentials, session data, URLs, or unnecessary personal
  information.
