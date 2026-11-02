"""
Точка входа и сборки графа Agentic Truth:
Мультиагентная верификация доказательств по теоретическому матанализу.
Архитектура: LangGraph + Prover Subgraph + SymPy Tools + GigaChat.
"""
from langgraph.graph import END, START, StateGraph
from core.state import State
from agents import (
    orchestrator_node,
    prover_subgraph,
    skeptic_node,
    judge_node,
    judge_router
)


def build_main_graph():
    """
    Сборка основного графа системы.
    Координатор -> Подграф Prover -> Скептик -> Судья (с условным роутингом).
    """
    builder = StateGraph(State)

    # 1. Регистрация узлов (Prover подключается как полноценный подграф!)
    builder.add_node("coordinator", orchestrator_node)
    builder.add_node("prover", prover_subgraph)
    builder.add_node("skeptic", skeptic_node)
    builder.add_node("verifier", judge_node)

    # 2. Основной линейный поток
    builder.add_edge(START, "coordinator")
    builder.add_edge("coordinator", "prover")
    builder.add_edge("prover", "skeptic")
    builder.add_edge("skeptic", "verifier")

    # 3. Условный переход после Судьи (завершение или ревизия)
    builder.add_conditional_edges(
        "verifier",
        judge_router,
        {
            "finish": END,
            "retry": "coordinator",
        },
    )

    return builder.compile()


# Скомпилированный граф для импорта в Streamlit / FastAPI
graph = build_main_graph()


if __name__ == "__main__":
    test_query = "Сформулируй и строго докажи теорему Больцано-Коши об обращении непрерывной функции в ноль"

    initial_state: State = {
        "query": test_query,
        "pro_evidence": "",
        "con_evidence": "",
        "final_answer": "",
    }

    print("=" * 80)
    print("🚀 AGENTIC TRUTH: ЗАПУСК МУЛЬТИАГЕНТНОЙ СИСТЕМЫ ПО МАТАНАЛИЗУ")
    print("🤖 Движок рассуждений: GigaChat (Сбер) | Формальный аудит: SymPy")
    print("=" * 80)

    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 80)
    print("📋 РЕЗУЛЬТАТ РАБОТЫ ТВОЕГО PROVER AGENT (ГРИГОРИЙ КОЦЕНКО):")
    print("=" * 80)
    print(final_state.get("pro_evidence", "Нет данных"))

    print("\n" + "=" * 80)
    print("🧮 СИМВОЛЬНЫЙ АУДИТ SYMPY TOOLS:")
    print("=" * 80)
    print(final_state.get("sympy_result", "Символьный аудит не сформирован"))

    print("\n" + "=" * 80)
    print("🏁 ИТОГОВЫЙ ОТВЕТ СИСТЕМЫ:")
    print("=" * 80)
    print(final_state.get("final_answer", ""))
