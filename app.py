import streamlit as st
from main import graph
from rag.qdrant_store import qdrant_store

st.set_page_config(
    page_title="Agentic Truth — Математический Анализ",
    page_icon="🧮",
    layout="wide"
)


def build_dot_graph(graph_data: dict) -> str:
    """Генерирует граф DOT для интерактивной визуализации Evidence Graph по разделу 6 ТЗ."""
    lines = [
        "digraph EvidenceGraph {",
        "  rankdir=LR;",
        '  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize="12", margin="0.2,0.1"];',
        '  edge [fontname="Helvetica", fontsize="10", color="#455A64"];'
    ]
    color_map = {
        "Source": ('#E1F5FE', '#0288D1'),        # Голубой: первоисточники (Зорич, Фихтенгольц)
        "Evidence": ('#E8F5E9', '#2E7D32'),      # Зеленый: условия и шаги доказательства
        "Verification": ('#FFF9C4', '#F57F17'),  # Желтый: аудит SymPy
        "Claim": ('#EDE7F6', '#512DA8')          # Фиолетовый: целевая теорема
    }

    nodes = graph_data.get("nodes", [])
    for n in nodes:
        nid = str(n.get("id", ""))
        label = str(n.get("label", nid)).replace('"', '\\"').replace("\n", " ")
        ntype = n.get("type", "Evidence")
        bg, border = color_map.get(ntype, ('#F5F5F5', '#616161'))
        lines.append(f'  "{nid}" [label="{label}", fillcolor="{bg}", color="{border}"];')

    edges = graph_data.get("edges", [])
    for e in edges:
        u = str(e.get("from", ""))
        v = str(e.get("to", ""))
        rel = str(e.get("relation", ""))
        lines.append(f'  "{u}" -> "{v}" [label="{rel}"];')

    lines.append("}")
    return "\n".join(lines)


def export_to_latex(query: str, pro_evidence: str, sympy_code: str, verdict: str) -> str:
    """Формирует готовый компилируемый LaTeX-документ (.tex)."""
    return rf"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[russian]{{babel}}
\usepackage{{amsmath, amssymb, amsthm}}
\usepackage{{geometry}}
\geometry{{margin=2cm}}

\title{{Академическое доказательство: {query}}}
\author{{Agentic Truth AI (Prover Agent: Григорий Коценко)}}
\date{{\today}}

\begin{{document}}
\maketitle

\section*{{Результат верификации}}
\textbf{{Итоговый вердикт}}: {verdict} \\
\textbf{{Символьный аудит SymPy}}: \texttt{{{sympy_code}}}

\section*{{Текст доказательства}}
{pro_evidence}

\end{{document}}
"""


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
        "🌐 Граф обоснования (Evidence Graph)"
    ])

    with tab1:
        st.subheader("Строгое аналитическое доказательство")
        st.markdown(result.get("pro_evidence", ""))

        st.divider()
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            tex_content = export_to_latex(
                query=query,
                pro_evidence=result.get("pro_evidence", ""),
                sympy_code=result.get("sympy_code", ""),
                verdict=result.get("verdict", "ACCEPT")
            )
            st.download_button(
                label="📥 Скачать документ LaTeX (.tex)",
                data=tex_content,
                file_name="proof.tex",
                mime="text/plain"
            )
        with col_down2:
            st.download_button(
                label="📄 Скачать отчет Markdown (.md)",
                data=result.get("pro_evidence", ""),
                file_name="proof.md",
                mime="text/markdown"
            )

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
        st.subheader("Найденные фрагменты из академических первоисточников")
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
        st.subheader("Интерактивная визуализация Evidence Graph (Раздел 6 ТЗ)")
        p_graph = result.get("proof_graph", {})
        if p_graph and p_graph.get("nodes"):
            dot_code = build_dot_graph(p_graph)
            st.graphviz_chart(dot_code)

            col1, col2, col3, col4 = st.columns(4)
            col1.markdown("🔵 **Source**: Первоисточники (RAG)")
            col2.markdown("🟢 **Evidence**: Условия и доказательство")
            col3.markdown("🟡 **Verification**: Аудит SymPy")
            col4.markdown("🟣 **Claim**: Целевая теорема")

            st.divider()
            with st.expander("🔍 Посмотреть структуру графа в формате JSON"):
                st.json(p_graph)
        else:
            st.info("Граф связей пока не сгенерирован.")
