"""Long-form learner summary (imported by main.py and streamlit_app.py)."""

FINAL_SUMMARY_TEXT = """
================================================================================
BIG DATA IN E-COMMERCE — SUMMARY (FOR LEARNERS)
================================================================================

How Big Data improves e-commerce
-------------------------------
• Personalization: Mining clicks, purchases, and reviews at scale lets retailers
  tailor recommendations and content (collaborative filtering, segment models).
• Fraud prevention: High-volume transaction streams feed models that flag
  anomalous spend, devices, and locations in near real time.
• Customer retention: Behavioral features (tenure, engagement, support load)
  power churn models so teams can intervene with offers or fixes.
• Revenue growth: Basket analysis surfaces cross-sell bundles; sentiment
  tracks product quality and NPS drivers across huge review corpora.

Opportunities
-------------
• Dynamic pricing: Demand, inventory, and competitor signals updated frequently.
• Targeted marketing: Audience building from unified lake + streaming events.
• Scalability: Horizontal storage (HDFS/object store) and compute (Spark/K8s)
  absorb peak traffic and seasonal loads.

Challenges
----------
• Data privacy: GDPR/CCPA, consent, and minimizing PII in analytical zones.
• System complexity: Many moving parts (ingest, catalog, jobs, serving).
• Infrastructure cost: Storage replication and always-on clusters need tuning
  (spot instances, autoscaling, lakehouse patterns).

Role of Hadoop-era components vs Spark
--------------------------------------
• HDFS: Cheap, fault-tolerant storage for massive files; today often complemented
  by object stores (S3, ADLS) with table formats (Iceberg, Delta).
• MapReduce: Batch map/shuffle/reduce paradigm for parallel aggregation; still
  the conceptual backbone of distributed "split-process-combine" workloads.
• Apache Spark: In-memory (where possible) DataFrame/RDD APIs, SQL, MLlib, and
  Structured Streaming — common successor to MapReduce for analytics and ML.

This project simulates HDFS with the `data/` lake, MapReduce-style Python
aggregations in `utils/mapreduce_helpers.py`, optional PySpark in
`spark_jobs/batch_processing.py`, supervised fraud scoring in `analytics/fraud.py`,
and unsupervised transaction anomalies (Isolation Forest, no fraud label) in
`analytics/anomalies.py`.
================================================================================
"""
