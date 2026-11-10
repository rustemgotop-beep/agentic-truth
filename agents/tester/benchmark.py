"""
Evaluation Harness & Benchmark Suite (Евгений Рудко: QA Lead).
Автоматизированный запуск сквозного тестирования графа мультиагентной системы:
1. Прогон тестового набора BENCHMARK_CASES через скомпилированный граф LangGraph.
2. Замер времени выполнения (Latency) и сбор промежуточных артефактов (SymPy, RAG, Skeptic, Judge).
3. Расчет метрик качества и генерация сводного отчета.
"""
import time
from typing import List, Dict, Any, Optional
from agents.tester.dataset import BENCHMARK_CASES
from agents.tester.metrics import compute_evaluation_metrics, format_markdown_report


def run_benchmark_suite(
    graph,
    cases: Optional[List[Dict[str, Any]]] = None,
    max_cases: Optional[int] = None
) -> Dict[str, Any]:
    """
    Запускает пакетное тестирование мультиагентного графа.
    Возвращает детальные логи кейсов, сводные метрики и Markdown-отчет.
    """
    test_cases = cases or BENCHMARK_CASES
    if max_cases and max_cases > 0:
        test_cases = test_cases[:max_cases]

    print(f"\n[QA Agent (Евгений Рудко)] Запуск пакета бенчмарков ({len(test_cases)} кейсов)...")

    detailed_results: List[Dict[str, Any]] = []

    for idx, case in enumerate(test_cases, 1):
        cid = case.get("id", f"case_{idx}")
        query = case.get("query", "")
        print(f"\n--- [{idx}/{len(test_cases)}] Тест: '{cid}' | '{query[:50]}' ---")

        start_time = time.time()
        try:
            out = graph.invoke({
                "query": query,
                "pro_evidence": "",
                "con_evidence": "",
                "final_answer": ""
            })
            duration = time.time() - start_time
            has_sympy = bool(out.get("sympy_code") and "sp." in str(out.get("sympy_code")))
            sources_count = len(out.get("retrieved_chunks", []))
            gaps_count = len(out.get("logical_gaps", []))
            verdict = out.get("verdict", "ACCEPT")
            confidence = float(out.get("confidence_score", 0.90))

            print(f"Результат: Вердикт {verdict} ({int(confidence * 100)}%), SymPy: {has_sympy}, Время: {duration:.2f}c")

            detailed_results.append({
                "id": cid,
                "query": query,
                "category": case.get("category", "Матанализ"),
                "has_sympy": has_sympy,
                "sympy_code": out.get("sympy_code", ""),
                "sources_count": sources_count,
                "gaps_count": gaps_count,
                "verdict": verdict,
                "confidence_score": confidence,
                "iterations": out.get("iteration", 1),
                "latency_sec": round(duration, 2),
                "success": True
            })
        except Exception as e:
            duration = time.time() - start_time
            print(f"Ошибка в кейсе {cid}: {e}")
            detailed_results.append({
                "id": cid,
                "query": query,
                "category": case.get("category", "Матанализ"),
                "has_sympy": False,
                "sources_count": 0,
                "gaps_count": 0,
                "verdict": "ERROR",
                "confidence_score": 0.0,
                "iterations": 0,
                "latency_sec": round(duration, 2),
                "error": str(e),
                "success": False
            })

    # Расчет сводных показателей
    metrics = compute_evaluation_metrics(detailed_results)
    report_md = format_markdown_report(metrics, detailed_results)

    print("\n[QA Agent] Пакет бенчмарков успешно завершен!")
    print(f"   Средняя задержка: {metrics.get('avg_latency_sec')} сек. | SymPy: {metrics.get('sympy_verification_rate')}% | Достоверность: {int(metrics.get('avg_confidence_score', 0) * 100)}%")

    return {
        "results": detailed_results,
        "metrics": metrics,
        "report_markdown": report_md
    }
