"""
Тесты для Skeptic / Red-Team Agent (Степан Иванов).
Проверяют:
1. Выявление логических брешей (gaps).
2. Построение математических контрпримеров (f(x)=|x|, sgn(x), 1/x, гармонический ряд, функция Пеано-Шварца).
3. Работу узла skeptic_node и генерацию структурированного отчета con_evidence.
"""
import unittest
from agents.skeptic import skeptic_node, _get_catalog_counterexample, _parse_skeptic_json
from core.state import State


class TestSkepticAgent(unittest.TestCase):

    def test_01_catalog_counterexamples(self):
        """Проверка подбора контрпримеров по ключевым темам анализа."""
        # 1. Ролль -> функция модуля |x|
        rolle_ce = _get_catalog_counterexample("Теорема Ролля о нуле производной")
        self.assertIn("дифференцируемост", rolle_ce["violated_condition"].lower())
        self.assertIn("|x|", rolle_ce["formula"])

        # 2. Вейерштрасс -> полуинтервал 1/x
        weier_ce = _get_catalog_counterexample("Вторая теорема Вейерштрасса о максимуме")
        self.assertIn("frac{1}{x}", weier_ce["formula"])
        self.assertIn("замкнутост", weier_ce["violated_condition"].lower())

        # 3. Шварц -> функция Пеано-Шварца в ФНП
        schwarz_ce = _get_catalog_counterexample("Теорема Шварца о смешанных производных")
        self.assertIn("Шварц", schwarz_ce["counterexample_name"])

    def test_02_parse_skeptic_json(self):
        """Проверка парсера JSON ответа модели."""
        raw_json = '''```json
        {
          "gaps": ["Уточнить дифференцируемость на (a, b)"],
          "counterexample": {
            "name": "Модуль",
            "violated_condition": "Гладкость в нуле",
            "formula": "f(x) = |x|",
            "explanation": "В нуле угловая точка"
          },
          "severity": "MEDIUM",
          "summary": "Требуется уточнение"
        }
        ```'''
        res = _parse_skeptic_json(raw_json)
        self.assertIsNotNone(res)
        self.assertEqual(len(res["gaps"]), 1)
        self.assertEqual(res["severity"], "MEDIUM")

    def test_03_skeptic_node_execution(self):
        """Проверка вызова skeptic_node на входном стейте."""
        state: State = {
            "query": "Докажи теорему Ролля о нуле производной",
            "iteration": 1,
            "assumptions": ["f непрерывна на [a, b]", "f(a) = f(b)"],
            "pro_evidence": "Доказательство опирается на теорему Вейерштрасса...",
            "sympy_result": "SymPy: подтверждено"
        }
        res = skeptic_node(state)
        self.assertIn("logical_gaps", res)
        self.assertIn("counterexample", res)
        self.assertIn("con_evidence", res)
        self.assertTrue(len(res["logical_gaps"]) > 0)
        self.assertIn("Контрпример", res["counterexample"])
        print(f"\n[Skeptic Test OK] Скептик нашел брешей: {len(res['logical_gaps'])}, Контрпример сформирован.")


if __name__ == "__main__":
    unittest.main()
