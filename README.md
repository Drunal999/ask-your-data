# Ask Your Data

Conversational analytics over a SQL database, through a **semantic layer**. Ask a business question in plain English; the app answers with a table and chart and shows exactly how.

The key design rule: **the LLM never writes SQL.** It only picks governed metric, dimension and filter names. SQL is compiled from the semantic layer and parameterised.

## How it works

```
question -> glossary retrieval (RAG) -> planner (Claude, or rule-based fallback)
         -> JSON plan {metric, dimension, filters}
         -> guardrail: validate against semantic layer
         -> compiled, parameterised SQL -> result
```

| File | Role |
|---|---|
| `semantic_layer.py` | Metric/dimension/filter definitions and the SQL compiler. Business rule: only `paid` orders count. |
| `rag.py` | TF-IDF retrieval over a business glossary (pure Python). |
| `agent.py` | Planner (Claude if `ANTHROPIC_API_KEY` is set, else rules) and the guardrail step. |
| `db.py` | Deterministic demo sales database (SQLite). |
| `app.py` | Streamlit chat UI. |
| `test_ask.py` | Pytest: guardrails, parameterised filters, paid-only revenue, retrieval. |

## Run

```
pip install -r requirements.txt
pytest
streamlit run app.py
```

Optional: set `ANTHROPIC_API_KEY` (and `ASK_MODEL`) to use Claude as the planner. Without it, the rule-based planner is used.

## Limits

Demo data is SQLite. Pointing `db.py` at another warehouse (e.g. Snowflake) would need the SQL dialect in `semantic_layer.py` adjusted (the month expression uses SQLite's `strftime`).
