# E-commerce Big Data Analytics (Python)

Simulated data lake, ML pipelines (fraud, sentiment, basket analysis, churn, recommendations), MapReduce-style rollups, optional PySpark, and a Streamlit dashboard.

## Quick start

```bash
python -m pip install -r requirements.txt
python main.py
streamlit run streamlit_app.py
```

- **Windows:** use `py -3` instead of `python` if needed.
- **PySpark batch job:** set `USE_PYSPARK=1` (requires Java). Default uses pandas chunked aggregation.
- **Faster / smaller run (e.g. Streamlit Cloud):** set **`STREAMLIT_QUICK=1`** or **`QUICK_MODE=1`** — uses smaller synthetic datasets and lighter steps (see `config.py`).

## Streamlit Community Cloud

Deploy with main file **`streamlit_app.py`** and **`requirements.txt`**.

On the **first visit**, the app runs the batch pipeline to create `data/`, `models/`, and `output/metrics.json`. Add a secret **`STREAMLIT_QUICK=true`** for smaller data and faster cold starts. **First load can still take a few minutes** on free tiers.

## Layout

| Path | Purpose |
|------|---------|
| `config.py` | Paths, `DataLakeSpec`, quick/full mode (`STREAMLIT_QUICK` / `QUICK_MODE`) |
| `pipeline/runner.py` | Orchestrates all batch steps (`run_full_pipeline`) |
| `project_summary.py` | Long-form “Big Data” learner summary text |
| `main.py` | CLI entrypoint (`python main.py`) |
| `analytics/` | Fraud, anomalies (Isolation Forest), sentiment, basket, churn, recommendations |
| `utils/` | Synthetic data, cleaning, MapReduce sim, streaming helpers |
| `spark_jobs/` | Optional PySpark + pandas chunked aggregation |
| `ecom_dashboard/` | Streamlit loaders, help text, UI theme (avoid `dashboard` name on Cloud) |
| `data/` | Simulated data lake (generated) |
| `output/` | Metrics and scored tables (generated) |
| `models/` | Saved models (generated) |
| `streamlit_app.py` | Dashboard |
| `.streamlit/config.toml` | Dark theme + accent colors (Cloud picks this up automatically) |

## Documentation

- **Full system reference** (every module, file, pipeline step, and output): **[docs/SYSTEM_REFERENCE.md](docs/SYSTEM_REFERENCE.md)**

## Presentation

Slide-style outline, architecture diagram (Mermaid), and speaker notes: **[docs/PRESENTATION.md](docs/PRESENTATION.md)**.

## Create a GitHub repository

1. On GitHub: **New repository** → choose a name → create **without** README (this folder already has one).
2. In this directory:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

Use SSH instead of HTTPS if you prefer: `git@github.com:YOUR_USERNAME/YOUR_REPO.git`.
