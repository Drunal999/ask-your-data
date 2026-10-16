"""Question -> structured plan -> validated SQL. Uses Claude if ANTHROPIC_API_KEY is set, else a rule-based fallback."""
import json
import os
import re

from semantic_layer import DIMENSIONS, FILTERS, METRICS, compile_query
from db import PRODUCTS, REGIONS, SEGMENTS

MODEL = os.environ.get("ASK_MODEL", "claude-sonnet-5-5")

SYSTEM = f"""You turn a business question into a JSON plan. Reply with JSON only:
{{"metric": str, "dimension": str|null, "filters": {{col: value}}}}
metrics: {sorted(METRICS)}
dimensions: {sorted(DIMENSIONS)}
filter columns: {sorted(FILTERS)}
If the question cannot be answered with these, reply {{"error": "short reason"}}.
Never write SQL."""

ALIASES = {
    "sales": "revenue", "revenue": "revenue", "income": "revenue",
    "aov": "avg_order_value", "average order": "avg_order_value", "avg order": "avg_order_value",
    "customers": "unique_customers", "buyers": "unique_customers",
    "orders": "orders", "order count": "orders",
}


def plan_rules(question):
    """Offline fallback planner."""
    q = question.lower()
    metric = next((m for k, m in sorted(ALIASES.items(), key=lambda x: -len(x[0])) if k in q), None)
    if not metric:
        return {"error": "I couldn't find a metric in your question (try revenue, orders, customers, AOV)."}
    dim = None
    for d in DIMENSIONS:
        if re.search(rf"\b(by|per|each)\s+{d}\b", q) or f"by {d}" in q:
            dim = d
    filters = {}
    for col, vals in (("region", REGIONS), ("segment", SEGMENTS), ("product", PRODUCTS)):
        for v in vals:
            if v.lower() in q:
                filters[col] = v
    return {"metric": metric, "dimension": dim, "filters": filters}


def plan_llm(question, context):
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=MODEL, max_tokens=300, system=SYSTEM,
        messages=[{"role": "user", "content": f"Glossary:\n{context}\n\nQuestion: {question}"}],
    )
    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    return json.loads(text)


def answer(question, conn, glossary):
    """Returns dict(plan, sql, rows, columns, sources, error, planner)."""
    hits = glossary.search(question)
    sources = [(t, d) for _, t, d in hits]
    context = "\n".join(f"- {t}: {d}" for t, d in sources)
    planner = "claude" if os.environ.get("ANTHROPIC_API_KEY") else "rules"
    try:
        plan = plan_llm(question, context) if planner == "claude" else plan_rules(question)
    except Exception as e:  # network, bad JSON, etc.: degrade to rules instead of failing
        planner, plan = "rules (llm failed)", plan_rules(question)
    out = {"plan": plan, "sources": sources, "planner": planner, "error": None,
           "sql": None, "rows": [], "columns": []}
    if "error" in plan:
        out["error"] = plan["error"]
        return out
    try:  # guardrail: plan is validated against the semantic layer before any SQL exists
        sql, params = compile_query(plan.get("metric"), plan.get("dimension"), plan.get("filters"))
    except (ValueError, TypeError) as e:
        out["error"] = f"Blocked by guardrail: {e}"
        return out
    cur = conn.execute(sql, params)
    out.update(sql=sql, rows=cur.fetchall(), columns=[c[0] for c in cur.description])
    return out
