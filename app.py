import pandas as pd
import streamlit as st

from agent import answer
from db import get_conn
from rag import Glossary

st.set_page_config(page_title="Ask Your Data", page_icon="💬")
st.title("💬 Ask Your Data")
st.caption("Conversational analytics over a SQL database, through a semantic layer. "
           "The model picks governed metrics; it never writes SQL.")


@st.cache_resource
def load():
    return get_conn(), Glossary()


conn, glossary = load()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Try")
    for ex in ["revenue by region", "orders by product", "average order value by segment",
               "revenue by month for Enterprise", "unique customers in North"]:
        if st.button(ex):
            st.session_state.pending = ex

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["q"])
    with st.chat_message("assistant"):
        r = turn["r"]
        if r["error"]:
            st.warning(r["error"])
        else:
            df = pd.DataFrame(r["rows"], columns=r["columns"])
            st.dataframe(df, use_container_width=True)
            if len(df.columns) == 2 and len(df) > 1:
                st.bar_chart(df.set_index(df.columns[0]))
            with st.expander(f"How this was answered ({r['planner']})"):
                st.json(r["plan"])
                st.code(r["sql"], language="sql")
                for t, d in r["sources"]:
                    st.caption(f"**{t}**: {d}")

q = st.chat_input("Ask about revenue, orders, customers...") or st.session_state.pop("pending", None)
if q:
    st.session_state.history.append({"q": q, "r": answer(q, conn, glossary)})
    st.rerun()
