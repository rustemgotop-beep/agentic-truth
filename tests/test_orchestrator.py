"""
Тесты для Orchestrator / Coordinator Agent (Рустем Галеев).
Проверяют:
1. Классификацию типов математических задач.
2. Генерацию подзапросов (Sub-queries) и рабочих гипотез (Hypotheses) по ТЗ.
3. Multi-Query RAG-поиск в базе данных Qdrant со слиянием источников.
"""
import unittest
from agents.orchestrator import orchestrator_node, _generate_fallback_plan, _parse_orchestrator_json
from core.state import State


class TestOrchestratorAgent(unittest.TestCase):

    def test_01_fallback_plan_generation(self):
        """Проверка детерминированного генератора подзапросов."""
        # 1. Теорема Ролля -> Вейерштрасс и Ферма
        plan_rolle = _generate_fallback_plan("Сформулируй теорему Ролля", 1)
        self.assertEqual(plan_rolle["task_type"], "prove_theorem")
        self.assertGreaterEqual(len(plan_rolle["sub_queries"]), 2)
        sq_text = " ".join(plan_rolle["sub_queries"]).lower()
        self.assertTrue("ферма" in sq_text or "вейерштрасс" in sq_text)

        # 2. Поиск контрпримера
        plan_ce = _generate_fallback_plan("Найди контрпример к утверждению", 1)
        self.assertEqual(plan_ce["task_type"], "find_counterexample")

    def test_02_parse_orchestrator_json(self):
        """Проверка парсера JSON ответа планировщика."""
        raw = '''```json
        {
          "task_type": "prove_theorem",
          "hypotheses": ["Гипотеза 1"],
          "sub_queries": ["Подзапрос 1", "Подзапрос 2"]
        }
        ```'''
        res = _parse_orchestrator_json(raw)
        self.assertEqual(res["task_type"], "prove_theorem")
        self.assertEqual(len(res["sub_queries"]), 2)

    def test_03_orchestrator_node_execution(self):
        """Проверка исполнения orchestrator_node и связывания с Qdrant."""
        state: State = {
            "query": "Докажи теорему Ролля о нуле производной",
            "iteration": 0
        }
        res = orchestrator_node(state)
        self.assertEqual(res["iteration"], 1)
        self.assertIn("sub_queries", res)
        self.assertIn("hypotheses", res)
        self.assertIn("retrieved_chunks", res)
        self.assertTrue(len(res["sub_queries"]) >= 1)
        self.assertTrue(len(res["retrieved_chunks"]) >= 1)
        print(f"\n[Orchestrator Test OK] Подзапросов: {len(res['sub_queries'])}, Источников: {len(res['retrieved_chunks'])}")


if __name__ == "__main__":
    unittest.main()
