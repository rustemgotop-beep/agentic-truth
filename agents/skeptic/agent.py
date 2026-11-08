"""
Skeptic / Red-Team Agent (Степан Иванов: Critique & Counterexamples).
Реализует глубокий критический аудит математических доказательств:
1. Поиск скрытых логических скачков (Logical Gaps) и неоговоренных предпосылок.
2. Проверка граничных условий (замкнутость отрезков, непрерывность vs дифференцируемость).
3. Построение патологических контрпримеров при ослаблении условий теоремы.
4. Оценка критичности уязвимостей для передачи Судье и Prover Subgraph.
"""
import json
import re
from typing import Dict, Any, List, Optional
from core.state import State
from core.llm import get_gigachat_llm
from agents.skeptic.prompts import SKEPTIC_PROMPT
from agents.skeptic.catalog import get_catalog_counterexample


def _parse_skeptic_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Парсит структурированный JSON из ответа модели."""
    clean_text = raw_text.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
    if match:
        clean_text = match.group(1)
    else:
        start = clean_text.find("{")
        end = clean_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean_text = clean_text[start:end+1]

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def skeptic_node(state: State) -> Dict[str, Any]:
    """
    Узел Скептика (Member 3 — Степан Иванов):
    Проводит Red-Team тестирование доказательства Prover и формирует контрпримеры.
    """
    iteration = state.get("iteration", 1)
    print(f"\n🕵️ [Skeptic Agent (Степан Иванов)] Аудит доказательства на уязвимости и контрпримеры (Итерация #{iteration})...")

    query = state.get("query", "")
    pro_evidence = state.get("pro_evidence", "")
    sympy_result = state.get("sympy_result", "")
    assumptions = state.get("assumptions", [])

    gaps: List[str] = []
    counterexample_str = ""
    severity = "LOW"
    summary = ""

    # 1. Попытка вызвать LLM (GigaChat) с защитой по таймауту
    llm = get_gigachat_llm(temperature=0.2)
    parsed: Optional[Dict[str, Any]] = None

    try:
        chain = SKEPTIC_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "assumptions": "\n".join([f"- {a}" for a in assumptions]),
            "pro_evidence": pro_evidence,
            "sympy_result": sympy_result
        })
        content = response.content if hasattr(response, "content") else str(response)
        parsed = _parse_skeptic_json(content)
    except Exception as e:
        print(f"ℹ️ Вызов LLM в Skeptic пропущен ({e}). Задействован аналитический реестр контрпримеров.")

    # 2. Обработка результатов LLM или fallback на каталог патологий
    if parsed and parsed.get("gaps"):
        gaps = parsed.get("gaps", [])
        ce_obj = parsed.get("counterexample", {})
        if isinstance(ce_obj, dict):
            ce_name = ce_obj.get("name", "Математический контрпример")
            ce_formula = ce_obj.get("formula", "")
            ce_exp = ce_obj.get("explanation", "")
            ce_viol = ce_obj.get("violated_condition", "")
            counterexample_str = (
                f"**Контрпример**: {ce_name}\n"
                f"- **Формула**: ${ce_formula}$\n"
                f"- **Нарушенное условие**: {ce_viol}\n"
                f"- **Обоснование**: {ce_exp}"
            )
        else:
            counterexample_str = str(ce_obj)
        severity = parsed.get("severity", "MEDIUM")
        summary = parsed.get("summary", "Обнаружены потенциальные краевые оговорки.")
    else:
        # Надежный академический каталог
        matched = get_catalog_counterexample(query)
        gaps = matched["gaps"]
        counterexample_str = (
            f"**Контрпример**: {matched['counterexample_name']}\n"
            f"- **Формула**: $${matched['formula']}$$\n"
            f"- **Нарушенное условие**: {matched['violated_condition']}\n"
            f"- **Обоснование**: {matched['explanation']}"
        )
        severity = matched["severity"]
        summary = f"Выявлены критические предпосылки: {matched['violated_condition']}."

    print(f"⚠️ [Skeptic Agent] Найдено замечаний: {len(gaps)} шт. | Критичность: {severity}")

    # 3. Формирование структурированного отчета контрдоказательств (con_evidence)
    con_report = (
        f"### 🕵️ Экспертный аудит Скептика (Степан Иванов):\n"
        f"**Критичность замечаний**: `{severity}`\n\n"
        f"**1. Потенциальные логические бреши (Logical Gaps):**\n"
        + "\n".join([f"- {g}" for g in gaps])
        + f"\n\n**2. Патологический контрпример при ослаблении условий:**\n"
        + f"{counterexample_str}\n\n"
        f"**3. Резюме для Судьи:**\n"
        f"> {summary}"
    )

    return {
        "logical_gaps": gaps,
        "counterexample": counterexample_str,
        "con_evidence": con_report
    }
