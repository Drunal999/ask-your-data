import os

import pytest

os.environ.pop("ANTHROPIC_API_KEY", None)

from agent import answer
from db import get_conn
from rag import Glossary
from semantic_layer import compile_query

conn, gl = get_conn(), Glossary()


def test_revenue_by_region_only_counts_paid():
    r = answer("revenue by region", conn, gl)
    assert r["error"] is None and r["columns"] == ["region", "revenue"]
    paid = conn.execute("SELECT SUM(amount) FROM orders WHERE status='paid'").fetchone()[0]
    assert round(sum(row[1] for row in r["rows"]), 2) == round(paid, 2)


def test_filter_is_parameterised():
    sql, params = compile_query("orders", "product", {"region": "North"})
    assert "North" not in sql and params == ["North"]


@pytest.mark.parametrize("bad", [
    dict(metric="revenue; DROP TABLE orders"),
    dict(metric="revenue", dimension="password"),
    dict(metric="revenue", filters={"amount": 1}),
])
def test_guardrail_rejects_unknown_names(bad):
    with pytest.raises(ValueError):
        compile_query(**bad)


def test_unanswerable_question_returns_error_not_sql():
    r = answer("what is the weather", conn, gl)
    assert r["error"] and r["sql"] is None


def test_rag_retrieves_definition():
    assert gl.search("what counts as revenue")[0][1] == "revenue"
