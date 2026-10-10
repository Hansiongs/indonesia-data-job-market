.PHONY: help test dashboard eda-report assets pipeline scrape-links scrape-details clean

help:  ## Show this help
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

test:  ## Run pytest
	pytest

dashboard:  ## Launch Streamlit dashboard
	python -m streamlit run app/dashboard.py

eda-report:  ## Build standalone HTML report from eda.ipynb (HR-friendly)
	python -m jupyter nbconvert --to html eda.ipynb --output eda_report.html --embed-images

assets:  ## Regenerate README chart previews
	python scripts/generate_assets.py

pipeline:  ## Clean local raw data and rebuild report/assets
	python scripts/run_pipeline.py

scrape-links:  ## Collect job links (requires scraper dependencies and auth)
	python -m glints_scraper.links

scrape-details:  ## Collect job details (requires scraper dependencies and auth)
	python -m glints_scraper.details

clean:  ## Remove build/cache artifacts
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
