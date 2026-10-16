"""Tiny RAG over a business glossary: TF-IDF retrieval in pure Python (no external service)."""
import math
import re
from collections import Counter

GLOSSARY = [
    ("revenue", "Revenue is the sum of order amounts for paid orders only. Refunded and pending orders are excluded."),
    ("orders", "Orders counts paid orders. A refunded or pending order is not counted."),
    ("avg_order_value", "Average order value is revenue divided by paid orders, rounded to 2 decimals."),
    ("unique_customers", "Unique customers is the number of distinct customers with at least one paid order."),
    ("region", "Region is the customer's sales region: North, South, East or West."),
    ("segment", "Segment is the customer type: Enterprise, SMB or Consumer."),
    ("month", "Month groups orders by order date as YYYY-MM."),
]


def _tok(text):
    return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))


class Glossary:
    def __init__(self, docs=GLOSSARY):
        self.docs = docs
        self.tokens = [_tok(f"{t} {d}") for t, d in docs]
        n = len(docs)
        df = Counter(w for toks in self.tokens for w in set(toks))
        self.idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}

    def search(self, query, k=3):
        q = Counter(_tok(query))
        scored = []
        for (term, text), toks in zip(self.docs, self.tokens):
            tf = Counter(toks)
            score = sum(q[w] * tf[w] * self.idf.get(w, 0) for w in q)
            if score > 0:
                scored.append((score, term, text))
        return sorted(scored, reverse=True)[:k]
