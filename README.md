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

## Layout

| Path | Purpose |
|------|---------|
| `data/` | Simulated HDFS-style datasets (created by `main.py`) |
| `output/` | Metrics, scored tables, streaming demos |
| `models/` | Saved models (created by `main.py`) |
| `main.py` | Full batch pipeline |
| `streamlit_app.py` | Dashboard |

## Create a GitHub repository

1. On GitHub: **New repository** → choose a name → create **without** README (this folder already has one).
2. In this directory:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

Use SSH instead of HTTPS if you prefer: `git@github.com:YOUR_USERNAME/YOUR_REPO.git`.
