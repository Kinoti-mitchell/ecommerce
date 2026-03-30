"""
Short learner-facing blurbs for the Streamlit dashboard (what each part does).
"""

SYSTEM_OVERVIEW = """
This app is the **front end** for a batch analytics pipeline. **Behind the scenes**, Python
generates a synthetic **data lake** (`data/`), cleans messy fields, trains several **ML models**,
writes scores and metrics to **`output/`**, and saves trained objects under **`models/`**.
You are viewing those results here—charts and tables update from the files produced by
`main.py` / `pipeline/runner.py`.
""".strip()

SIDEBAR_METRICS = """
**Fraud ROC‑AUC** measures how well the model ranks risky vs normal transactions (higher is
better, max 1). We show **two models**: the full pipeline (clean data + engineered features)
vs a **baseline** that only uses transaction amount—so you can see why features matter.

**Churn ROC‑AUC** measures how well we separate users who will leave vs stay.
""".strip()

TAB_FRAUD = """
**Fraud detection** scores card-like transactions using a **Random Forest**. The pipeline
engineers signals such as unusual location, high spend vs that user’s pattern, and first-time
device use. Charts here use a **sample** of rows; the full scored file lives in `output/`.
Comparing **full model vs amount-only baseline** shows the value of cleaning and feature work.
""".strip()

TAB_SENTIMENT = """
**Sentiment analysis** reads **product review text** and labels each review **positive,
negative, or neutral** using **TextBlob** polarity. This helps monitor product satisfaction
and quality at scale. Accuracy shown is vs **synthetic** labels in our demo data (for teaching).
""".strip()

TAB_RECOMMENDATIONS = """
**Recommendations** use **collaborative filtering**: we compare users by their past **ratings**
and suggest products that **similar users** liked. Pick a **user ID** to see top‑K product
scores. In production, catalogs are huge and systems often use **matrix factorization** or
**Spark ALS** instead of dense similarity matrices.
""".strip()

TAB_CHURN = """
**Churn prediction** estimates the probability that a customer **stops using the service**,
using behaviour features (tenure, spend, sessions, support tickets). Teams use these scores
for **retention campaigns** or proactive support. The histogram compares predicted probability
for users who **did vs did not** churn in the synthetic dataset.
""".strip()

TAB_BASKET = """
**Market basket analysis** mines **association rules** from order line items (e.g. “if basket
contains A, often also B”). Rules show **support** (how often the pattern appears), **confidence**
(how often B appears when A appears), and **lift** (how much more likely than random). Retailers
use this for **cross-sell**, **bundle offers**, and **store layout**.
""".strip()

TAB_SUMMARY = """
This tab ties the demo to **big-data tooling**: **`data/`** stands in for **HDFS-style**
bulk storage; **MapReduce-style** code shows map/shuffle/reduce; **PySpark** (optional) runs a
real Spark aggregation, or **pandas chunks** mimic the same logic without a JVM. The text
below summarises **business value**, **opportunities**, and **challenges** (privacy, cost,
complexity).
""".strip()
