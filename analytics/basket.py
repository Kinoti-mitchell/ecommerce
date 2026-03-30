"""
Market basket analysis — Apriori association rules (mlxtend).

At scale, FP-Growth in Spark MLlib is common for huge transaction logs on HDFS.

If `mlxtend` is not installed, a small pandas-only miner produces pairwise rules
so the rest of the pipeline still runs.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations

import pandas as pd

try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder

    _HAS_MLXTEND = True
except ImportError:
    _HAS_MLXTEND = False


def orders_to_transactions(df: pd.DataFrame) -> list[list[str]]:
    """Group line items into baskets (lists of product_id strings)."""
    g = df.groupby("order_id")["product_id"].apply(list)
    return g.tolist()


def _mine_pairs_fallback(
    transactions: list[list[str]], min_support: float, min_confidence: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Single- and two-item rules only; enough for teaching dashboards."""
    n = len(transactions)
    if n == 0:
        return pd.DataFrame(), pd.DataFrame()
    single: Counter = Counter()
    pair: Counter = Counter()
    for basket in transactions:
        items = sorted({str(x) for x in basket if str(x).strip()})
        for a in items:
            single[a] += 1
        for a, b in combinations(items, 2):
            pair[frozenset((a, b))] += 1

    freq_rows = [{"itemsets": frozenset([k]), "support": v / n} for k, v in single.items()]
    for fs, c in pair.items():
        freq_rows.append({"itemsets": fs, "support": c / n})
    freq = pd.DataFrame(freq_rows)
    freq = freq[freq["support"] >= min_support]

    rules_rows = []
    for fs, c in pair.items():
        sup = c / n
        if sup < min_support:
            continue
        a, b = tuple(sorted(fs))
        conf_ab = c / single[a] if single[a] else 0
        conf_ba = c / single[b] if single[b] else 0
        p_b = single[b] / n
        p_a = single[a] / n
        if conf_ab >= min_confidence and p_b > 0:
            rules_rows.append(
                {
                    "antecedents": frozenset([a]),
                    "consequents": frozenset([b]),
                    "support": sup,
                    "confidence": conf_ab,
                    "lift": conf_ab / p_b,
                }
            )
        if conf_ba >= min_confidence and p_a > 0:
            rules_rows.append(
                {
                    "antecedents": frozenset([b]),
                    "consequents": frozenset([a]),
                    "support": sup,
                    "confidence": conf_ba,
                    "lift": conf_ba / p_a,
                }
            )
    rules = pd.DataFrame(rules_rows)
    if not rules.empty:
        rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
    return freq, rules


def mine_association_rules(
    df: pd.DataFrame, min_support: float = 0.02, min_threshold: float = 0.35
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (frequent_itemsets, rules).
    min_threshold is confidence for mlxtend; same interpretation in fallback.
    """
    transactions = orders_to_transactions(df)
    if _HAS_MLXTEND:
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        ohe = pd.DataFrame(te_ary, columns=te.columns_)
        freq = apriori(ohe, min_support=min_support, use_colnames=True)
        if freq.empty:
            return freq, pd.DataFrame()
        rules = association_rules(freq, metric="confidence", min_threshold=min_threshold)
        rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
        return freq, rules

    return _mine_pairs_fallback(transactions, min_support, min_threshold)
