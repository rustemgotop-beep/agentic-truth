"""
Метрики качества и аналитики для Test / QA Agent (Евгений Рудко).
Реализует замеры параметров по разделу 8 ТЗ:
- Faithfulness / Groundedness (наличие и релевантность первоисточников)
- SymPy Verification Rate (процент символьной верификации)
- Skeptic Coverage (эффективность работы Скептика)
- Latency (время ответа)
- Confidence (оценка Судьи)
"""
from typing import List, Dict, Any


def compute_evaluation_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Вычисляет сводные аналитические метрики по результатам прогона бенчмарка."""
    total = len(results)
    if total == 0:
        return {}

    sympy_success = sum(1 for r in results if r.get("has_sympy", False))
    sources_present = sum(1 for r in results if r.get("sources_count", 0) > 0)
    skeptic_active = sum(1 for r in results if r.get("gaps_count", 0) > 0)
    accept_count = sum(1 for r in results if r.get("verdict") == "ACCEPT")
    total_latency = sum(r.get("latency_sec", 0.0) for r in results)
    avg_confidence = sum(r.get("confidence_score", 0.0) for r in results) / total

    return {
        "total_cases": total,
        "avg_latency_sec": round(total_latency / total, 2),
        "sympy_verification_rate": round((sympy_success / total) * 100, 1),
        "groundedness_rate": round((sources_present / total) * 100, 1),
        "skeptic_coverage_rate": round((skeptic_active / total) * 100, 1),
        "accept_rate": round((accept_count / total) * 100, 1),
        "avg_confidence_score": round(avg_confidence, 2)
    }


def format_markdown_report(metrics: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
    """Генерирует академический отчет в формате Markdown для защиты проекта (КП3)."""
    md = [
        "# 🧪 Академический отчет тестирования (QA Lead: Евгений Рудко)",
        f"**Общее число тест-кейсов**: {metrics.get('total_cases', 0)} | **Среднее время ответа**: {metrics.get('avg_latency_sec', 0)} сек.\n",
        "### 📊 Сводные метрики надежности (КП3 Acceptance Criteria)",
        f"- **Символьная точность (SymPy Verification)**: `{metrics.get('sympy_verification_rate', 0)}%`",
        f"- **Опора на первоисточники (Groundedness / RAG)**: `{metrics.get('groundedness_rate', 0)}%`",
        f"- **Эффективность Скептика (Skeptic Coverage)**: `{metrics.get('skeptic_coverage_rate', 0)}%`",
        f"- **Средняя достоверность вердикта Судьи**: `{int(metrics.get('avg_confidence_score', 0) * 100)}%`",
        f"- **Доля принятых доказательств (Accept Rate)**: `{metrics.get('accept_rate', 0)}%`\n",
        "### 📋 Таблица результатов прогона бенчмарка",
        "| ID | Задача | SymPy | Источников | Скептик (брешей) | Вердикт | Время (с) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
    ]

    for r in results:
        sympy_mark = "✅" if r.get("has_sympy") else "❌"
        md.append(
            f"| `{r.get('id')}` | {r.get('query')[:45]}... | {sympy_mark} | "
            f"{r.get('sources_count', 0)} | {r.get('gaps_count', 0)} | "
            f"**{r.get('verdict')}** ({int(r.get('confidence_score', 0)*100)}%) | {r.get('latency_sec', 0):.2f} |"
        )

    return "\n".join(md)
