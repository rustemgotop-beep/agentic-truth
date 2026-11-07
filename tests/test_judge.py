"""
Тесты для Judge / Verifier Agent (Сергей Галкин).
Проверяют:
1. Вычисление уверенности (confidence_score) и вынесение вердикта.
2. Логику маршрутизации (judge_router): 'retry' при REVISE (итерация 1), 'finish' при ACCEPT или итерация 2.
3. Надежность парсера JSON.
"""
import unittest
from agents.judge import judge_node, judge_router, _parse_judge_json
from core.state import State


class TestJudgeAgent(unittest.TestCase):

    def test_01_parse_judge_json(self):
        """Проверка парсера JSON из ответов модели."""
        raw_valid = '```json\n{"verdict": "ACCEPT", "confidence_score": 0.95, "review_summary": "Отлично"}\n```'
        res = _parse_judge_json(raw_valid)
        self.assertEqual(res["verdict"], "ACCEPT")
        self.assertEqual(res["confidence_score"], 0.95)

        # Проверка сырого текста без markdown
        raw_raw = '{"verdict": "REVISE", "confidence_score": 0.65, "review_summary": "Пробелы"}'
        res2 = _parse_judge_json(raw_raw)
        self.assertEqual(res2["verdict"], "REVISE")
        self.assertEqual(res2["confidence_score"], 0.65)

    def test_02_judge_router_logic(self):
        """Проверка условного роутинга судьи (петля рефлексии)."""
        # 1. ACCEPT на итерации 1 -> finish
        state_accept: State = {"verdict": "ACCEPT", "iteration": 1}
        self.assertEqual(judge_router(state_accept), "finish")

        # 2. REVISE на итерации 1 -> retry (возврат на доработку)
        state_revise_1: State = {"verdict": "REVISE", "iteration": 1}
        self.assertEqual(judge_router(state_revise_1), "retry")

        # 3. REVISE на итерации 2 -> finish (достигнут лимит 2 раундов по ТЗ)
        state_revise_2: State = {"verdict": "REVISE", "iteration": 2}
        self.assertEqual(judge_router(state_revise_2), "finish")

    def test_03_judge_node_execution(self):
        """Проверка вызова judge_node на готовом стейте."""
        sample_state: State = {
            "query": "Докажи теорему Ролля о нуле производной",
            "iteration": 1,
            "assumptions": ["f непрерывна на [a, b]", "f дифференцируема на (a, b)", "f(a) = f(b)"],
            "pro_evidence": "Шаг 1: По второй теореме Вейерштрасса... Шаг 2: По лемме Ферма f'(c) = 0. \\blacksquare",
            "sympy_result": "✅ СУЩЕСТВОВАНИЕ КОРНЯ ПОДТВЕРЖДЕНО",
            "con_evidence": "Замечание: проверить краевые точки.",
            "retrieved_chunks": []
        }
        res = judge_node(sample_state)
        self.assertIn("verdict", res)
        self.assertIn("confidence_score", res)
        self.assertIn("final_answer", res)
        self.assertGreaterEqual(res["confidence_score"], 0.5)
        print(f"\n[Judge Test OK] Вердикт: {res['verdict']}, Оценка: {res['confidence_score']}")


if __name__ == "__main__":
    unittest.main()
