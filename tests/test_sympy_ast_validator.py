"""Статическая проверка кода, предлагаемого агентом Prover."""
import ast
import unittest
from unittest.mock import patch

from tools.sympy_verifier import SecurityError, SafeSymPyRunner, SymPyASTValidator


class TestSymPyASTValidator(unittest.TestCase):
    def test_only_allowed_imports_pass_validation(self):
        SymPyASTValidator().visit(ast.parse("import sympy as sp\nfrom math import sqrt"))
        for code in (
            "import os",
            "import sympy, subprocess",
            "import sympy.external",
            "from pathlib import Path",
            "from . import math",
        ):
            with self.subTest(code=code), self.assertRaises(SecurityError):
                SymPyASTValidator().visit(ast.parse(code))

    def test_blocked_calls_and_dunder_access(self):
        for code in (
            "open('secret')",
            "eval('1')",
            "exec('1')",
            "__import__('os')",
            "sp.open('secret')",
            "sp.diff(x, x) + eval('2')",
            "sp.__dict__",
            "(lambda: 1)()",
            "[sp.diff(x, x) for x in (1,)]",
        ):
            with self.subTest(code=code), self.assertRaises(SecurityError):
                SymPyASTValidator().visit(ast.parse(code))

    def test_execution_rejects_before_eval_but_accepts_sympy(self):
        with patch("tools.sympy_verifier.eval", create=True) as evaluate:
            with self.assertRaisesRegex(
                SecurityError,
                "Использование системных вызовов запрещено, используй только SymPy",
            ):
                SafeSymPyRunner.execute_expression("sp.open('secret')", raise_on_error=True)
            evaluate.assert_not_called()

        ok, message = SafeSymPyRunner.execute_expression("sp.open('secret')")
        self.assertFalse(ok)
        self.assertIn("SecurityError:", message)
        self.assertEqual(SafeSymPyRunner.execute_expression("sp.diff(x**2, x)"), (True, "2*x"))

    def test_only_one_expression_is_executed(self):
        ok, _ = SafeSymPyRunner.execute_expression("import sympy; sp.diff(x**2, x)")
        self.assertFalse(ok)
        with self.assertRaises(SecurityError):
            SafeSymPyRunner.execute_expression("import os\nsp.diff(x**2, x)", raise_on_error=True)
        self.assertEqual(
            SafeSymPyRunner.execute_expression("```python\nsp.diff(x**2, x)\n```"),
            (True, "2*x"),
        )
