from typing import List, Dict

BENCHMARK_CASES: List[Dict[str, str]] = [
    {"id": "calc_01", "query": "Докажи теорему Больцано-Коши об обращении непрерывной функции в ноль"},
    {"id": "calc_02", "query": "Докажи теорему Ролля и приведи пример, когда производная на концах не существует"},
    {"id": "calc_03", "query": "Докажи правило Лопиталя для неопределенности 0/0"}
]


def run_benchmark_suite(graph) -> List[Dict]:
    """[Member 5 — Test Agent / QA Lead]"""
    results = []
    for case in BENCHMARK_CASES:
        out = graph.invoke({"query": case["query"]})
        results.append({
            "id": case["id"],
            "query": case["query"],
            "has_sympy": bool(out.get("sympy_code")),
            "verdict": out.get("verdict", "UNKNOWN")
        })
    return results
