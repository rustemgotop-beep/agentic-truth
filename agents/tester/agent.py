"""
QA / Tester Agent (Евгений Рудко).
Модуль тестирования, оценки качества (Evaluation Harness) и валидации мультиагентной системы.
Отвечает за:
1. Запуск тестовых сценариев математических доказательств (BENCHMARK_CASES).
2. Замер задержки (Latency), точности SymPy-верификации и привязки к источникам (Groundedness).
3. Формирование академического отчета по метрикам КП2/КП3.
"""
from typing import Dict, Any, List, Optional
from agents.tester.benchmark import run_benchmark_suite
from agents.tester.dataset import BENCHMARK_CASES
from agents.tester.metrics import compute_evaluation_metrics, format_markdown_report


class TesterAgent:
    """
    Агент контроля качества и бенчмаркинга (Евгений Рудко).
    """

    def __init__(self, graph=None):
        self.graph = graph

    def run_benchmark(self, max_cases: Optional[int] = None) -> Dict[str, Any]:
        """Запуск сквозного бенчмарка для графа LangGraph."""
        if not self.graph:
            from main import graph
            target_graph = graph
        else:
            target_graph = self.graph
        return run_benchmark_suite(target_graph, max_cases=max_cases)

    @staticmethod
    def evaluate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет метрик качества."""
        return compute_evaluation_metrics(results)

    @staticmethod
    def generate_report(metrics: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
        """Генерация Markdown-отчета."""
        return format_markdown_report(metrics, results)
