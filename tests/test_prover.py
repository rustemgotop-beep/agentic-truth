"""
Тесты для Prover Agent Subgraph и SymPy Verifier (Григорий Коценко).
Проверяют:
1. Безопасность AST-песочницы SafeSymPyRunner и блокировку инъекций.
2. Символьную верификацию классических теорем (Больцано-Коши, Ролль, Лагранж, Пределы, Интегралы).
3. Работу всех 3 узлов Prover Subgraph (Decompose -> SymPy -> Synthesize) и сборку Evidence Graph.
"""
import unittest
from tools.sympy_verifier import SafeSymPyRunner, run_model_verification
from agents.prover import (
    prover_subgraph,
    decompose_conditions_node,
    sympy_verification_node,
    synthesize_proof_node
)
from core.state import State


class TestProverAgentAndSymPy(unittest.TestCase):

    def test_01_sympy_ast_security(self):
        """Проверка блокировки вредоносных инъекций в SafeSymPyRunner."""
        ok_imp, msg_imp = SafeSymPyRunner.execute_expression("__import__('os').system('ls')")
        self.assertFalse(ok_imp)

        ok_attr, msg_attr = SafeSymPyRunner.execute_expression("x.__class__.__base__")
        self.assertFalse(ok_attr)

        ok_valid, res_valid = SafeSymPyRunner.execute_expression("sp.limit(sp.sin(x)/x, x, 0)")
        self.assertTrue(ok_valid)
        self.assertEqual(res_valid, "1")

    def test_02_model_verification_theorems(self):
        """Проверка символьного аудита ключевых теорем матанализа."""
        res_rolle = run_model_verification("Докажи теорему Ролля о нуле производной")
        self.assertIn("solve", res_rolle["code"])
        self.assertIn("a/2 + b/2", res_rolle["result"])

        res_lim = run_model_verification("Первый замечательный предел sin(x)/x")
        self.assertEqual(res_lim["result"], "1")

        res_lagrange = run_model_verification("Теорема Лагранжа о конечном приращении")
        self.assertIn("a/2 + b/2", res_lagrange["result"])

    def test_03_prover_subgraph_end_to_end(self):
        """Проверка сквозного прогона 3-стадийного подграфа Prover и генерации Evidence Graph."""
        initial_state: State = {
            "query": "Докажи теорему Ролля о нуле производной",
            "iteration": 1,
            "context_text": "Теорема Ролля: если f непрерывна на [a,b], дифференцируема на (a,b) и f(a)=f(b)...",
            "retrieved_chunks": [
                {
                    "source": "Г.М. Фихтенгольц, Т. 1",
                    "content": "Формулировка теоремы Ролля",
                    "origin": "Векторная БД Qdrant (score=0.85)"
                }
            ]
        }
        out = prover_subgraph.invoke(initial_state)

        self.assertIn("assumptions", out)
        self.assertGreaterEqual(len(out["assumptions"]), 2)
        self.assertIn("sympy_code", out)
        self.assertIn("sympy_result", out)
        self.assertIn("pro_evidence", out)
        self.assertIn("proof_graph", out)

        # Проверка структуры Evidence Graph
        p_graph = out["proof_graph"]
        node_ids = {n["id"] for n in p_graph["nodes"]}
        self.assertIn("Claim", node_ids)
        self.assertIn("Assumptions", node_ids)
        self.assertIn("SymPy", node_ids)
        self.assertIn("Proof", node_ids)
        self.assertIn("Source_1", node_ids)
        print(f"\n[Prover Test OK] Условий: {len(out['assumptions'])}, SymPy: {out['sympy_code']}, Узлов графа: {len(node_ids)}")


if __name__ == "__main__":
    unittest.main()
