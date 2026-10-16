"""Semantic layer: business metrics and dimensions defined once, on top of raw tables.

The LLM never writes SQL. It only picks names from this layer, and SQL is
compiled from these definitions. That is the main guardrail.
"""

METRICS = {
    "revenue": "SUM(o.amount)",
    "orders": "COUNT(*)",
    "avg_order_value": "ROUND(AVG(o.amount), 2)",
    "unique_customers": "COUNT(DISTINCT o.customer_id)",
}

DIMENSIONS = {
    "region": "c.region",
    "segment": "c.segment",
    "product": "o.product",
    "month": "strftime('%Y-%m', o.order_date)",
}

# Business rule applied to every query: only paid orders count.
BASE_FROM = "FROM orders o JOIN customers c ON c.id = o.customer_id"
BASE_WHERE = "o.status = 'paid'"

# Allowed filter columns (value is bound as a parameter, never interpolated).
FILTERS = {"region": "c.region", "segment": "c.segment", "product": "o.product"}


def compile_query(metric, dimension=None, filters=None, limit=20):
    """Build a parameterised SELECT from layer definitions. Raises ValueError on anything unknown."""
    if metric not in METRICS:
        raise ValueError(f"Unknown metric: {metric!r}. Allowed: {sorted(METRICS)}")
    if dimension is not None and dimension not in DIMENSIONS:
        raise ValueError(f"Unknown dimension: {dimension!r}. Allowed: {sorted(DIMENSIONS)}")
    where, params = [BASE_WHERE], []
    for col, val in (filters or {}).items():
        if col not in FILTERS:
            raise ValueError(f"Cannot filter on {col!r}. Allowed: {sorted(FILTERS)}")
        where.append(f"{FILTERS[col]} = ?")
        params.append(val)
    limit = max(1, min(int(limit), 100))
    select = f"{METRICS[metric]} AS {metric}"
    sql = f"SELECT {select} {BASE_FROM} WHERE {' AND '.join(where)}"
    if dimension:
        d = DIMENSIONS[dimension]
        sql = (f"SELECT {d} AS {dimension}, {select} {BASE_FROM} "
               f"WHERE {' AND '.join(where)} GROUP BY 1 ORDER BY 2 DESC LIMIT {limit}")
    return sql, params
