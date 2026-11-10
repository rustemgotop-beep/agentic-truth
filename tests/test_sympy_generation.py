"""Проверка обработки кода SymPy, полученного от LLM."""
import unittest
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda

from agents.prover.agent import sympy_verification_node
from agents.prover import prover_subgraph
from agents.judge.agent import judge_node


class TestSympyGeneration(unittest.TestCase):
    def test_generated_code_is_used_in_verification(self):
        llm = RunnableLambda(lambda _: "```python\nsp.limit(sp.sin(x)/x, x, 0)\n```")
        with patch("agents.prover.agent.get_gigachat_llm", return_value=llm):
            result = sympy_verification_node({"query": "Проверка выражения"})

        self.assertEqual(result["sympy_code"], "sp.limit(sp.sin(x)/x, x, 0)")
        self.assertIn("`1`", result["sympy_result"])
        self.assertEqual(result["sympy_status"], "success")

    def test_invalid_code_is_repaired_using_traceback(self):
        prompts = []

        def respond(prompt):
            prompts.append(prompt)
            if len(prompts) == 1:
                return "```python\nsp.limit(sp.sin(x)/missing, x, 0)\n```"
            return "sp.limit(sp.sin(x)/x, x, 0)"

        llm = RunnableLambda(respond)
        with patch("agents.prover.agent.get_gigachat_llm", return_value=llm):
            result = sympy_verification_node({"query": "Проверка выражения"})

        self.assertEqual(result["sympy_status"], "success")
        self.assertEqual(result["sympy_code"], "sp.limit(sp.sin(x)/x, x, 0)")
        self.assertEqual(len(prompts), 2)
        self.assertIn("Traceback (most recent call last)", prompts[1])
        self.assertIn("NameError", prompts[1])
        self.assertIn("Предыдущий код: ```python\nsp.limit(sp.sin(x)/missing, x, 0)\n```", prompts[1])

    def test_security_error_is_sent_to_reflection_prompt(self):
        prompts = []

        def respond(prompt):
            prompts.append(prompt)
            return "sp.open('secret')" if len(prompts) == 1 else "sp.diff(x**2, x)"

        with patch("agents.prover.agent.get_gigachat_llm", return_value=RunnableLambda(respond)):
            result = sympy_verification_node({"query": "Производная"})

        self.assertEqual(result["sympy_status"], "success")
        self.assertEqual(result["sympy_code"], "sp.diff(x**2, x)")
        self.assertEqual(len(prompts), 2)
        self.assertIn(
            "SecurityError: Использование системных вызовов запрещено, используй только SymPy",
            prompts[1],
        )

    def test_multiline_unsafe_import_is_not_dropped(self):
        prompts = []

        def respond(prompt):
            prompts.append(prompt)
            return "import os\nsp.diff(x**2, x)" if len(prompts) == 1 else "sp.diff(x**2, x)"

        with patch("agents.prover.agent.get_gigachat_llm", return_value=RunnableLambda(respond)):
            result = sympy_verification_node({"query": "Производная"})
        self.assertEqual(len(prompts), 2)
        self.assertIn("SecurityError:", prompts[1])
        self.assertEqual(result["sympy_status"], "success")

    def test_three_failures_propagate_through_graph(self):
        prompts = []

        def respond(prompt):
            prompts.append(prompt)
            return "sp.limit(sp.sin(x)/missing, x, 0)"

        llm = RunnableLambda(respond)
        with patch("agents.prover.agent.get_gigachat_llm", return_value=llm):
            result = sympy_verification_node({"query": "Проверка выражения"})

        self.assertEqual(len(prompts), 3)
        self.assertEqual(result["sympy_status"], "failed")
        self.assertNotIn("ПОДТВЕРЖДЕНО", result["sympy_result"])

        # Отказ должен сохраняться в LangGraph, не выдавая формальную проверку.
        with patch("agents.prover.agent.get_gigachat_llm", return_value=llm):
            graph_state = prover_subgraph.invoke({
                "query": "Проверка выражения", "context_text": "",
                "retrieved_chunks": [],
            })
        self.assertEqual(graph_state["sympy_status"], "failed")
        self.assertEqual(graph_state["proof_graph"]["metadata"]["status"], "verification_failed")
        self.assertFalse(any(edge["relation"] == "formally_verifies"
                             for edge in graph_state["proof_graph"]["edges"]))

        with patch("agents.judge.agent.get_gigachat_llm", return_value=RunnableLambda(
            lambda _: '{"verdict": "ACCEPT", "confidence_score": 0.99, "review_summary": "OK"}'
        )):
            verdict = judge_node(graph_state)
        self.assertEqual(verdict["verdict"], "REVISE")
        self.assertLessEqual(verdict["confidence_score"], 0.5)

    def test_empty_code_is_repaired(self):
        prompts = []

        def respond(prompt):
            prompts.append(prompt)
            return " " if len(prompts) == 1 else "sp.diff(x**2, x)"

        with patch("agents.prover.agent.get_gigachat_llm", return_value=RunnableLambda(respond)):
            result = sympy_verification_node({"query": "Производная"})

        self.assertEqual(len(prompts), 2)
        self.assertIn("ValueError: Пустое выражение", prompts[1])
        self.assertEqual(result["sympy_status"], "success")
        self.assertEqual(result["sympy_code"], "sp.diff(x**2, x)")

    def test_critical_failure_at_second_graph_iteration_is_not_accepted(self):
        with patch("agents.judge.agent.get_gigachat_llm", return_value=RunnableLambda(
            lambda _: '{"verdict": "ACCEPT", "confidence_score": 0.99, "review_summary": "OK"}'
        )):
            verdict = judge_node({
                "query": "Проверка выражения", "iteration": 2,
                "sympy_status": "failed", "sympy_result": "Проверка SymPy не выполнена.",
            })
        self.assertEqual(verdict["verdict"], "REVISE")

    def test_offline_fallback_is_preserved(self):
        with patch("agents.prover.agent.get_gigachat_llm", return_value=RunnableLambda(
            lambda _: (_ for _ in ()).throw(RuntimeError("offline"))
        )):
            result = sympy_verification_node({"query": "Теорема Ролля"})
        self.assertEqual(result["sympy_status"], "success")
        self.assertIn("sp.solve", result["sympy_code"])
