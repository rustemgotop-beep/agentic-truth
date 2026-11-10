from typing import TypedDict, List, Dict, Optional, Literal


class SourceChunk(TypedDict):
    source: str
    content: str
    origin: str


class State(TypedDict, total=False):
    # Базовые поля (совместимость с изначальным контрактом)
    query: str
    pro_evidence: str
    con_evidence: str
    final_answer: str

    # 1. Поля Orchestrator & RAG (Member 1 — Рустем Галеев)
    task_type: str
    iteration: int
    sub_queries: List[str]
    hypotheses: List[str]
    retrieved_chunks: List[SourceChunk]
    context_text: str

    # 2. Поля Prover Subgraph (Member 2 — Григорий)
    assumptions: List[str]
    sympy_code: str
    sympy_result: str
    sympy_status: Literal["success", "failed"]
    proof_graph: Dict[str, List]

    # 3. Поля Skeptic Agent (Member 3)
    logical_gaps: List[str]
    counterexample: Optional[str]

    # 4. Поля Judge Agent (Member 4)
    verdict: Literal["ACCEPT", "REVISE"]
    confidence_score: float
    judge_feedback: str
