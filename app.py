import streamlit as st
from main import graph

st.set_page_config(page_title="Agentic Math Analysis", page_icon="🧮", layout="wide")

st.title("🧮 AI-Ассистент по Теоретическому Матанализу")
st.caption("Архитектура: LangGraph + Prover Subgraph + SymPy Formal Verification + Hybrid RAG")

query = st.text_input(
    "Введите любую теорему или утверждение математического анализа:",
    value="Докажи теорему Больцано-Коши об обращении непрерывной функции в ноль"
)

if st.button("🚀 Доказать и верифицировать", type="primary"):
    with st.spinner("Работает подграф Prover (Декомпозиция ➔ SymPy ➔ Синтез доказательства)..."):
        result = graph.invoke({
            "query": query,
            "pro_evidence": "",
            "con_evidence": "",
            "final_answer": ""
        })

    tab1, tab2, tab3, tab4 = st.tabs([
        "📐 Доказательство (Prover Subgraph)",
        "🧮 SymPy & Граф Логики",
        "🕵️ Аудит Скептика и Судьи",
        "📚 Источники RAG"
    ])

    with tab1:
        st.markdown(result.get("pro_evidence", ""))

    with tab2:
        st.subheader("Символьная верификация SymPy")
        st.code(result.get("sympy_code", ""), language="python")
        st.markdown(result.get("sympy_result", ""))
        st.subheader("Структура графа доказательства (Proof Graph)")
        st.json(result.get("proof_graph", {}))

    with tab3:
        st.info(result.get("con_evidence", ""))
        st.success(f"Вердикт Судьи: {result.get('verdict', 'ACCEPT')} (Итераций: {result.get('iteration', 1)})")

    with tab4:
        for idx, chunk in enumerate(result.get("retrieved_chunks", []), 1):
            with st.expander(f"Источник #{idx}: {chunk['source']} ({chunk['origin']})"):
                st.write(chunk["content"])
