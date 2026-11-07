"""
Обратная совместимость: реэкспорт Evaluation Harness из пакета agents.tester (Евгений Рудко).
"""
from agents.tester import (
    run_benchmark_suite,
    BENCHMARK_CASES,
    compute_evaluation_metrics,
    format_markdown_report
)

__all__ = [
    "run_benchmark_suite",
    "BENCHMARK_CASES",
    "compute_evaluation_metrics",
    "format_markdown_report"
]
