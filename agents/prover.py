"""
Модуль Prover Agent (Григорий Коценко).
Реэкспортирует компоненты из специализированного пакета agents.prover.
"""
from agents.prover.agent import (
    prover_subgraph,
    prover_node,
    build_prover_subgraph,
    decompose_conditions_node,
    sympy_verification_node,
    synthesize_proof_node
)

__all__ = [
    "prover_subgraph",
    "prover_node",
    "build_prover_subgraph",
    "decompose_conditions_node",
    "sympy_verification_node",
    "synthesize_proof_node"
]
