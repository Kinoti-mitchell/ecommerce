"""
PySpark batch analytics over the simulated data lake (HDFS-style paths).

Hadoop ecosystem role (conceptual):
- **HDFS**: Durable, replicated storage for CSV/Parquet at rest. Spark executors
  read local replicas when possible (data locality).
- **YARN/K8s**: Allocate Spark executors across nodes (this script uses local[*]
  for laptops — one JVM, multiple threads).
- **MapReduce vs Spark**: Classic MR writes many intermediate files to disk between
  map and reduce; Spark keeps data in memory between transformations when possible,
  which speeds iterative ML and SQL-style pipelines.

Real e-commerce: nightly Spark jobs aggregate clicks, orders, and fraud features
into warehouse tables consumed by dashboards and ML training.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

# PySpark starts a local JVM; on some Windows setups that can block or require Java.
# Set USE_PYSPARK=1 to force the Spark code path when Java + Spark are configured.
USE_PYSPARK = os.environ.get("USE_PYSPARK", "").lower() in ("1", "true", "yes")

ROOT = Path(__file__).resolve().parent.parent
DATA_LAKE = ROOT / "data"


def run_spark_transaction_summary(csv_path: str | None = None) -> dict | None:
    """
    Distributed aggregation with Spark DataFrame API (similar outcomes to a
    MapReduce job that emits per-user totals).

    Returns a small JSON-serializable summary, or None if PySpark is unavailable.
    """
    path = csv_path or str(DATA_LAKE / "transactions.csv")
    if not Path(path).exists():
        return None
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql import functions as F
    except ImportError:
        return None

    spark = (
        SparkSession.builder.appName("EcommTxnSummary")
        .master("local[*]")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    try:
        df = spark.read.option("header", True).option("inferSchema", True).csv(path)
        summary = (
            df.groupBy("user_id")
            .agg(
                F.count("*").alias("txn_count"),
                F.sum("amount").alias("total_amount"),
                F.max("amount").alias("max_amount"),
            )
            .orderBy(F.desc("total_amount"))
            .limit(20)
        )
        rows = [r.asDict() for r in summary.collect()]
        spark.stop()
        return {"engine": "pyspark", "top_users_by_spend": rows}
    except Exception:
        try:
            spark.stop()
        except Exception:
            pass
        return None


def pandas_chunked_summary(csv_path: str | None = None, chunksize: int = 10_000) -> dict:
    """
    Same logical aggregation without Spark: read CSV in chunks (simulates
    distributed splits) and combine partial aggregates — the reduce side of MR.
    """
    path = csv_path or str(DATA_LAKE / "transactions.csv")
    partials: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, chunksize=chunksize):
        chunk["amount"] = pd.to_numeric(chunk["amount"], errors="coerce").fillna(0)
        g = chunk.groupby("user_id").agg(
            txn_count=("amount", "count"),
            total_amount=("amount", "sum"),
            max_amount=("amount", "max"),
        )
        partials.append(g)
    if not partials:
        return {"engine": "pandas_chunks", "top_users_by_spend": []}
    combined = pd.concat(partials).groupby(level=0).agg(
        {
            "txn_count": "sum",
            "total_amount": "sum",
            "max_amount": "max",
        }
    )
    combined = combined.sort_values("total_amount", ascending=False).head(20)
    rows = combined.reset_index().to_dict(orient="records")
    return {"engine": "pandas_chunks", "top_users_by_spend": rows}


def write_spark_summary_output() -> str:
    """Run Spark when USE_PYSPARK=1; otherwise pandas chunked reduce. Write JSON next to lake."""
    out = run_spark_transaction_summary() if USE_PYSPARK else None
    if out is None:
        out = pandas_chunked_summary()
    out_path = DATA_LAKE / "spark_batch_summary.json"
    DATA_LAKE.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
    return str(out_path)


if __name__ == "__main__":
    print(write_spark_summary_output())
