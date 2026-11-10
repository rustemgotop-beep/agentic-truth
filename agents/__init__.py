"""
Пакет мультиагентной системы Agentic Truth (Команда № 14).
Каждый агент выделен в отдельный самостоятельный модуль с собственными промптами и логикой:
- agents/orchestrator/ : Рустем Галеев (Task Planning & Multi-Query RAG)
- agents/prover/       : Григорий Коценко (3-стадийный Prover Subgraph & SymPy)
- agents/skeptic/      : Степан Иванов (Red-Team Audit & Патологические контрпримеры)
- agents/judge/        : Сергей Галкин (Arbitrage & Self-Reflection Routing)
- agents/tester/       : Евгений Рудко (Evaluation Harness & КП3 Метрики)
"""
from agents.orchestrator import orchestrator_node
from agents.prover import prover_subgraph, prover_node
from agents.skeptic import skeptic_node
from agents.judge import judge_node, judge_router
from agents.tester import run_benchmark_suite, BENCHMARK_CASES, TesterAgent

__all__ = [
    "orchestrator_node",
    "prover_subgraph",
    "prover_node",
    "skeptic_node",
    "judge_node",
    "judge_router",
    "run_benchmark_suite",
    "BENCHMARK_CASES",
    "TesterAgent"
]
