# Partitioned data lakes (concept)

This demo stores flat files under `data/` (e.g. `transactions.csv`). In production **object stores** (S3, ADLS) and **table formats** (Iceberg, Delta) often use **directory partitioning**, for example:

```text
transactions/year=2024/month=01/day=15/part-000.parquet
```

**Why partition?** Queries and Spark jobs can **prune** directories and read only relevant days, cutting I/O and cost.

**This repo:** generation still writes single CSV/JSON paths so `pipeline/runner.py` and the Streamlit app keep working unchanged. For your talk, you can describe partitioning as the **next scaling step** after the flat `data/` layout.
