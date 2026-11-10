"""Проверка обработки кода SymPy, полученного от LLM."""
import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from agents.prover.agent import sympy_verification_node


class TestSympyGeneration(unittest.TestCase):
    def test_generated_code_is_used_in_verification(self):
        llm = RunnableLambda(lambda _: "```python\nsp.limit(sp.sin(x)/x, x, 0)\n```")
        with patch("agents.prover.agent.get_gigachat_llm", return_value=llm):
            result = sympy_verification_node({"query": "Проверка выражения"})

        self.assertEqual(result["sympy_code"], "sp.limit(sp.sin(x)/x, x, 0)")
        self.assertIn("`1`", result["sympy_result"])
