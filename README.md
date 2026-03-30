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

## Streamlit Community Cloud

Deploy with main file **`streamlit_app.py`** and **`requirements.txt`**.

On the **first visit**, the app runs the full **`main.py`** pipeline to create `data/`, `models/`, and `output/metrics.json` (nothing is committed for those paths). **First load can take several minutes**; free tiers may time out on very heavy runs. If deploy fails, run `python main.py` locally and temporarily commit `output/` + `models/` + `data/` (remove those lines from `.gitignore`) for a smaller static demo.

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
