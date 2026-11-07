"""
Тесты для Evaluation Harness & Benchmark Suite (Евгений Рудко).
Проверяют:
1. Запуск бенчмарк-раннера на тестовом кейсе.
2. Корректность вычисления метрик качества (SymPy rate, Groundedness, Latency, Confidence).
3. Форматирование Markdown-отчета для защиты проекта.
"""
import unittest
from agents.tester import run_benchmark_suite, BENCHMARK_CASES, compute_evaluation_metrics, format_markdown_report
from main import graph


class TestEvaluationHarness(unittest.TestCase):

    def test_01_metrics_calculation(self):
        """Проверка формул расчета метрик качества."""
        dummy_results = [
            {
                "id": "test_1",
                "query": "Докажи Ролля",
                "has_sympy": True,
                "sources_count": 3,
                "gaps_count": 2,
                "verdict": "ACCEPT",
                "confidence_score": 0.95,
                "latency_sec": 1.5
            },
            {
                "id": "test_2",
                "query": "Докажи Тейлора",
                "has_sympy": True,
                "sources_count": 2,
                "gaps_count": 1,
                "verdict": "ACCEPT",
                "confidence_score": 0.90,
                "latency_sec": 2.5
            }
        ]
        metrics = compute_evaluation_metrics(dummy_results)
        self.assertEqual(metrics["total_cases"], 2)
        self.assertEqual(metrics["sympy_verification_rate"], 100.0)
        self.assertEqual(metrics["groundedness_rate"], 100.0)
        self.assertEqual(metrics["avg_latency_sec"], 2.0)
        self.assertAlmostEqual(metrics["avg_confidence_score"], 0.93, places=2)

        # Проверка формирования Markdown отчета
        report_md = format_markdown_report(metrics, dummy_results)
        self.assertIn("Академический отчет тестирования", report_md)
        self.assertIn("100.0%", report_md)

    def test_02_benchmark_single_case_run(self):
        """Проверка работы бенчмарк-раннера на 1 реальном кейсе через LangGraph."""
        single_case = [BENCHMARK_CASES[0]]  # Больцано-Коши
        report = run_benchmark_suite(graph, cases=single_case, max_cases=1)

        self.assertIn("metrics", report)
        self.assertIn("results", report)
        self.assertIn("report_markdown", report)
        self.assertEqual(len(report["results"]), 1)
        self.assertTrue(report["results"][0]["success"])
        print(f"\n[QA Test OK] Прогон завершен: Вердикт {report['results'][0]['verdict']}, Latency: {report['results'][0]['latency_sec']}c")


if __name__ == "__main__":
    unittest.main()
