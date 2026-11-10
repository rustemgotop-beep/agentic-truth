import streamlit as st
from main import graph
from rag.qdrant_store import qdrant_store
from agents.tester import run_benchmark_suite, BENCHMARK_CASES

st.set_page_config(
    page_title="Agentic Truth — Математический Анализ",
    page_icon=None,
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
    """Формирует готовый компилируемый LaTeX-документ (.tex) с конвертацией Markdown-тегов."""
    import re
    body = pro_evidence
    body = re.sub(r"^###\s+(.+)$", r"\\subsection*{\1}", body, flags=re.MULTILINE)
    body = re.sub(r"^##\s+(.+)$", r"\\section*{\1}", body, flags=re.MULTILINE)
    body = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", body)
    body = re.sub(r"^- (.+)$", r"\\noindent $\\bullet$ \1\\\\", body, flags=re.MULTILINE)
    safe_sympy = sympy_code.replace("_", "\\_")

    return rf"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T2A]{{fontenc}}
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
\textbf{{Символьный аудит SymPy}}: \texttt{{{safe_sympy}}}

{body}

\end{{document}}
"""


# --- Боковая панель: Векторная БД Qdrant & Настройки ---
with st.sidebar:
    st.header("Векторная БД Qdrant")
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
    with st.expander("Добавить новую теорему в Qdrant"):
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
                    st.success("Теорема добавлена и проиндексирована!")
                    st.rerun()
                else:
                    st.error("Ошибка добавления теоремы.")

# --- Основной заголовок ---
st.title("Agentic Truth: Верификация Теоретического Матанализа")
st.markdown(
    "**Распределенная мультиагентная система (Clean Architecture)**: "
    "LangGraph + GigaChat + SymPy AST + Векторная база Qdrant (40+ теорем)  \n"
    "**Команда**: *Р. Галеев* (Orchestrator & Multi-Query RAG) · "
    "*Г. Коценко* (Prover Subgraph & SymPy) · "
    "*С. Иванов* (Skeptic Red-Team) · "
    "*С. Галкин* (Judge Arbitrage) · "
    "*Е. Рудко* (QA & Benchmark)"
)

main_tab1, main_tab2 = st.tabs([
    "Интерактивная верификация теорем",
    "Академический бенчмарк (QA Lead: Евгений Рудко)"
])

# ==========================================
# Вкладка 1: Интерактивная верификация теорем
# ==========================================
with main_tab1:
    if "proof_result" not in st.session_state:
        st.session_state.proof_result = None
    if "proof_query" not in st.session_state:
        st.session_state.proof_query = ""

    col_q1, col_q2 = st.columns([4, 1])
    with col_q1:
        query_input = st.text_input(
            "Введите теорему или задачу математического анализа для доказательства:",
            value=selected_query.replace("Докажи: ", "")
        )
    with col_q2:
        st.write("")
        st.write("")
        run_btn = st.button("Доказать", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("Работает мультиагентная система (Orchestrator  ->  Prover Subgraph  ->  Skeptic  ->  Judge)..."):
            st.session_state.proof_query = query_input
            st.session_state.proof_result = graph.invoke({
                "query": query_input,
                "pro_evidence": "",
                "con_evidence": "",
                "final_answer": ""
            })

    result = st.session_state.proof_result
    active_query = st.session_state.proof_query

    if result:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Доказательство (Prover Subgraph)",
            "Символьный аудит SymPy",
            "Аудит Скептика и Судьи",
            "Векторная база Qdrant (RAG)",
            "Граф обоснования (Evidence Graph)"
        ])

        with tab1:
            st.subheader("Строгое аналитическое доказательство")
            st.markdown(result.get("pro_evidence", ""))

            st.divider()
            col_down1, col_down2 = st.columns(2)
            with col_down1:
                tex_content = export_to_latex(
                    query=active_query,
                    pro_evidence=result.get("pro_evidence", ""),
                    sympy_code=result.get("sympy_code", ""),
                    verdict=result.get("verdict", "ACCEPT")
                )
                st.download_button(
                    label="Скачать документ LaTeX (.tex)",
                    data=tex_content,
                    file_name="proof.tex",
                    mime="text/plain"
                )
            with col_down2:
                st.download_button(
                    label="Скачать отчет Markdown (.md)",
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
                st.success(f"Вердикт Судьи: **{verdict}** (Все условия согласованы на итерации #{result.get('iteration', 1)})")
            else:
                st.warning(f"Вердикт Судьи: **{verdict}** (Требуется доработка)")

        with tab4:
            st.subheader("Найденные фрагменты из академических первоисточников")
            retrieved = result.get("retrieved_chunks", [])
            if retrieved:
                for idx, chunk in enumerate(retrieved, 1):
                    with st.expander(f"Источник #{idx}: {chunk.get('source', '')} | {chunk.get('origin', '')}"):
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
                col1.markdown("**Source**: Первоисточники (RAG)")
                col2.markdown("**Evidence**: Условия и доказательство")
                col3.markdown("**Verification**: Аудит SymPy")
                col4.markdown("**Claim**: Целевая теорема")

                st.divider()
                with st.expander("Посмотреть структуру графа в формате JSON"):
                    st.json(p_graph)
            else:
                st.info("Граф связей пока не сгенерирован.")

# ==========================================
# Вкладка 2: Академический бенчмарк (Рудко)
# ==========================================
with main_tab2:
    st.subheader("Evaluation Harness & Автоматизированный бенчмарк (QA Lead: Евгений Рудко)")
    st.markdown(
        "Комплексный стенд сквозной оценки мультиагентного графа в соответствии с разделом 9 ТЗ.  \n"
        "Замеряет время ответа (**Latency**), долю корректных символьных вычислений (**SymPy Rate**), "
        "степень привязки к первоисточникам (**Groundedness**) и строгость арбитража (**Judge Confidence**)."
    )

    if "benchmark_report" not in st.session_state:
        st.session_state.benchmark_report = None

    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        num_cases = st.slider(
            "Количество тестовых кейсов для прогона:",
            min_value=1,
            max_value=len(BENCHMARK_CASES),
            value=min(3, len(BENCHMARK_CASES))
        )
    with col_b2:
        st.write("")
        st.write("")
        run_bench_btn = st.button("Запустить бенчмарк", type="primary", use_container_width=True)

    if run_bench_btn:
        with st.spinner(f"Запуск сквозного тестирования {num_cases} академических кейсов..."):
            st.session_state.benchmark_report = run_benchmark_suite(graph, max_cases=num_cases)

    bench_rep = st.session_state.benchmark_report
    if bench_rep:
        m = bench_rep.get("metrics", {})
        st.divider()
        st.subheader("Итоговые метрики качества (KPI)")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Тестовых кейсов", f"{m.get('total_cases', 0)} шт.")
        m_col2.metric("Средняя задержка", f"{m.get('avg_latency_sec', 0.0)} с")
        m_col3.metric("SymPy аудит", f"{m.get('sympy_verification_rate', 0.0)}%")
        m_col4.metric("Достоверность RAG", f"{m.get('groundedness_rate', 0.0)}%")

        st.divider()
        st.subheader("Академический отчет тестирования")
        st.markdown(bench_rep.get("report_markdown", ""))

        st.download_button(
            label="Скачать отчет бенчмарка (.md)",
            data=bench_rep.get("report_markdown", ""),
            file_name="benchmark_report.md",
            mime="text/markdown"
        )

        st.divider()
        st.subheader("Детальный разбор кейсов")
        for res in bench_rep.get("results", []):
            status_icon = "PASS" if res.get("success") else "FAIL"
            with st.expander(f"{status_icon} [{res.get('id')}] {res.get('query')} — Вердикт: {res.get('verdict')} ({res.get('latency_sec')}c)"):
                st.write(f"**Раздел**: {res.get('category')}")
                st.write(f"**Источников RAG**: {res.get('sources_count')} шт. | **Замечаний Скептика**: {res.get('gaps_count')}")
                st.write(f"**Уверенность Судьи**: {int(res.get('confidence_score', 0) * 100)}%")
                if res.get("sympy_code"):
                    st.code(res.get("sympy_code"), language="python")
