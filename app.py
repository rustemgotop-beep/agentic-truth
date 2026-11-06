import streamlit as st
from main import graph
from rag.qdrant_store import qdrant_store

st.set_page_config(
    page_title="Agentic Truth — Математический Анализ",
    page_icon="🧮",
    layout="wide"
)

# --- Боковая панель: Векторная БД Qdrant & Настройки ---
with st.sidebar:
    st.header("🗄️ Векторная БД Qdrant")
    stats = qdrant_store.stats()
    st.metric("Количество теорем в БД", f"{stats['points_count']} теорем")
    st.metric("Размерность эмбеддингов", f"{stats['vector_dimension']} dims")
    st.caption("Режим: Embedded Local (без внешних зависимостей и Docker)")
    st.caption("Метрика: Cosine Distance | Char-WB TF-IDF (3-5 n-grams)")

    st.divider()
    st.subheader("Разделы математики")
    categories = ["Все разделы"] + qdrant_store.get_categories()
    selected_cat = st.selectbox("Выбрать раздел:", categories)

    all_theorems = qdrant_store.list_theorems()
    if selected_cat != "Все разделы":
        filtered_theorems = [t for t in all_theorems if t.get("category") == selected_cat]
    else:
        filtered_theorems = all_theorems

    theorem_titles = [f"Докажи: {t['theorem']}" for t in filtered_theorems]
    selected_query = st.selectbox(
        "Примеры теорем из базы:",
        theorem_titles if theorem_titles else ["Докажи теорему Больцано-Коши об обращении непрерывной функции в ноль"]
    )

    st.divider()
    with st.expander("➕ Добавить новую теорему в Qdrant"):
        new_cat = st.selectbox("Раздел:", qdrant_store.get_categories())
        new_title = st.text_input("Название теоремы:")
        new_source = st.text_input("Первоисточник (учебник, автор):")
        new_formula = st.text_input("Формула (LaTeX):")
        new_content = st.text_area("Формулировка и доказательство:")
        if st.button("Индексировать в Qdrant", type="secondary"):
            if new_title and new_content:
                added = qdrant_store.add_theorem({
                    "category": new_cat,
                    "theorem": new_title,
                    "source": new_source or "Пользовательский ввод",
                    "latex_formula": new_formula,
                    "content": new_content,
                    "tags": [new_title.lower(), new_cat.lower()]
                })
                if added:
                    st.success("✅ Теорема добавлена и проиндексирована!")
                    st.rerun()
                else:
                    st.error("Ошибка добавления теоремы.")

# --- Основной заголовок ---
st.title("🧮 Agentic Truth: Верификация Теоретического Матанализа")
st.markdown(
    "**Архитектура**: LangGraph + Subgraph Prover (Григорий Коценко) + "
    "SymPy AST Formal Engine + Векторная база данных Qdrant (40+ теорем) + GigaChat"
)

query = st.text_input(
    "Введите теорему или задачу математического анализа для доказательства:",
    value=selected_query.replace("Докажи: ", "")
)

if st.button("🚀 Доказать и верифицировать", type="primary"):
    with st.spinner("Работает мультиагентная система (Orchestrator ➔ Prover Subgraph ➔ Skeptic ➔ Judge)..."):
        result = graph.invoke({
            "query": query,
            "pro_evidence": "",
            "con_evidence": "",
            "final_answer": ""
        })

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📐 Доказательство (Prover Subgraph)",
        "🧮 Символьный аудит SymPy",
        "🕵️ Аудит Скептика и Судьи",
        "📚 Векторная база Qdrant (RAG)",
        "🌐 Граф рассуждений (JSON)"
    ])

    with tab1:
        st.subheader("Строгое аналитическое доказательство")
        st.markdown(result.get("pro_evidence", ""))

    with tab2:
        st.subheader("Формальная символьная верификация (SymPy Tools)")
        code = result.get("sympy_code", "")
        if code:
            st.code(code, language="python")
        st.markdown(result.get("sympy_result", ""))

    with tab3:
        st.subheader("Проверка граничных условий и контрпримеры (Skeptic)")
        st.info(result.get("con_evidence", ""))
        verdict = result.get("verdict", "ACCEPT")
        if verdict == "ACCEPT":
            st.success(f"⚖️ Вердикт Судьи: **{verdict}** (Все условия согласованы на итерации #{result.get('iteration', 1)})")
        else:
            st.warning(f"⚖️ Вердикт Судьи: **{verdict}** (Требуется доработка)")

    with tab4:
        st.subheader("Найденные фрагменты из академических источников")
        retrieved = result.get("retrieved_chunks", [])
        if retrieved:
            for idx, chunk in enumerate(retrieved, 1):
                with st.expander(f"📖 Источник #{idx}: {chunk.get('source', '')} | {chunk.get('origin', '')}"):
                    st.markdown(chunk.get("content", ""))
        else:
            st.write("Источники не найдены.")

        st.divider()
        st.subheader(f"Каталог базы знаний Qdrant ({len(filtered_theorems)} теорем)")
        for idx, thm in enumerate(filtered_theorems, 1):
            with st.expander(f"{idx}. [{thm.get('category', 'Матанализ')}] {thm['theorem']}"):
                st.caption(f"**Источник**: {thm.get('source', '')}")
                if thm.get("latex_formula"):
                    st.latex(thm["latex_formula"])
                st.markdown(thm.get("content", ""))
                if thm.get("tags"):
                    st.write(f"Теги: `{'`, `'.join(thm['tags'])}`")

    with tab5:
        st.subheader("Proof Graph & State Dump")
        st.json(result.get("proof_graph", {}))
