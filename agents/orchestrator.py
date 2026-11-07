"""
Orchestrator / Coordinator Agent (Рустем Галеев: Task Planning & Multi-Query RAG).
Реализует координацию мультиагентной системы по теоретическому матанализу:
1. Классификация типа математической задачи (доказательство, поиск контрпримера, тождество).
2. Генерация математических подзапросов (Sub-queries) и рабочих гипотез (Hypotheses) по ТЗ.
3. Multi-Query RAG-поиск в векторной базе данных Qdrant со слиянием и дедупликацией первоисточников.
4. Управление итеративным циклом рефлексии (Self-Reflection Handling).
"""
import json
import re
from typing import Dict, Any, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from core.state import State
from core.llm import get_gigachat_llm
from rag import retrieve_multi_query_knowledge, retrieve_math_knowledge

ORCHESTRATOR_SYSTEM_PROMPT = """Ты — Ведущий Координатор и Архитектор рассуждений (Orchestrator Agent) в мультиагентной системе Agentic Truth.
Твоя задача — проанализировать входящий математический запрос, классифицировать тип задачи, выдвинуть рабочие гипотезы и сгенерировать точные поисковые подзапросы (Sub-queries) для извлечения вспомогательных лемм и теорем из базы первоисточников (Зорич, Фихтенгольц).

ФОРМАТ ОТВЕТА (СТРОГО ВАЛИДНЫЙ JSON БЕЗ ЛИШНЕГО ТЕКСТА):
{{
  "task_type": "prove_theorem",
  "hypotheses": [
    "Утверждение справедливо при выполнении условий непрерывности и гладкости",
    "Доказательство опирается на теорему о среднем значении или принцип полноты"
  ],
  "sub_queries": [
    "Точная формулировка теоремы и условия применимости",
    "Вспомогательная лемма или теорема-опора",
    "Формальные определения граничных условий"
  ],
  "plan_summary": "Краткий план работы подграфа Prover и Skeptic"
}}

ТИПЫ ЗАДАЧ (task_type):
- "prove_theorem": Строгое аналитическое доказательство теоремы
- "find_counterexample": Фальсификация неверного утверждения и построение контрпримера
- "verify_identity": Формальная символьная проверка тождества через SymPy
- "concept_explanation": Разбор и объяснение фундаментального понятия"""

ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", ORCHESTRATOR_SYSTEM_PROMPT),
    ("user", """Проанализируй математический запрос:
ЗАПРОС: {query}
ИТЕРАЦИЯ: #{iteration}
ОТЗЫВ СУДЬИ (если итерация > 1): {judge_feedback}

Сформируй план, гипотезы и поисковые подзапросы строго в формате JSON.""")
])


def _parse_orchestrator_json(raw_text: str) -> Dict[str, Any]:
    """Извлекает и валидирует структурированный JSON из ответа модели."""
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
        return json.loads(clean_text)
    except Exception:
        return {}


def _generate_fallback_plan(query: str, iteration: int) -> Dict[str, Any]:
    """Детерминированная генерация подзапросов и гипотез на основе анализа ключевых концепций."""
    q_lower = query.lower()
    task_type = "prove_theorem"
    if "контрпример" in q_lower or "опроверг" in q_lower:
        task_type = "find_counterexample"
    elif "вычисли" in q_lower or "равенство" in q_lower:
        task_type = "verify_identity"

    sub_queries = [query]
    hypotheses = ["Утверждение выводимо из аксиом анализа и классических лемм о непрерывности."]

    if "ролл" in q_lower:
        sub_queries.extend([
            "Вторая теорема Вейерштрасса о достижении максимума и минимума",
            "Лемма Ферма о равенстве нулю производной в точке экстремума"
        ])
        hypotheses.append("Если функция постоянна, f'(x) = 0 тривиально; если нет — экстремум внутри отрезка дает нуль производной.")
    elif "лагранж" in q_lower:
        sub_queries.extend([
            "Теорема Ролля о нуле производной",
            "Теорема о конечном приращении вспомогательная секущая"
        ])
        hypotheses.append("Доказательство сводится к теореме Ролля для вспомогательной функции F(x) = f(x) - f(a) - k*(x - a).")
    elif "коши" in q_lower and "средн" in q_lower:
        sub_queries.extend([
            "Обобщенная теорема о среднем Коши",
            "Теорема Ролля о нуле производной"
        ])
        hypotheses.append("Сводится к теореме Ролля для линейной комбинации f(x) и g(x).")
    elif "тейлор" in q_lower:
        sub_queries.extend([
            "Формула Тейлора с остаточным членом в форме Лагранжа",
            "Многочлен Тейлора локальное полиномиальное приближение"
        ])
        hypotheses.append("Остаточный член выводится с помощью многократного интегрирования или теоремы Коши о среднем.")
    elif "предел" in q_lower or "sin" in q_lower:
        sub_queries.extend([
            "Первый замечательный предел синус на дугу",
            "Теорема о зажатой функции двух милиционеров"
        ])
        hypotheses.append("Опирается на тригонометрическое неравенство cos(x) < sin(x)/x < 1 на интервале (0, pi/2).")
    elif "интеграл" in q_lower or "ньютон" in q_lower:
        sub_queries.extend([
            "Формула Ньютона Лейбница определенный интеграл",
            "Теорема о дифференцировании интеграла по верхнему пределу"
        ])
        hypotheses.append("Интеграл от непрерывной функции выражается через разность значений любой первообразной.")
    else:
        sub_queries.extend([
            "Непрерывность функций на замкнутом отрезке",
            "Условия дифференцируемости и теоремы о среднем"
        ])

    return {
        "task_type": task_type,
        "hypotheses": hypotheses,
        "sub_queries": sub_queries,
        "plan_summary": f"План исследования для '{query}' сформирован на базе опорных лемм."
    }


def orchestrator_node(state: State) -> Dict[str, Any]:
    """
    Узел Координатора (Member 1 — Рустем Галеев):
    1. Классифицирует задачу.
    2. Генерирует подзапросы и гипотезы.
    3. Осуществляет Multi-Query RAG-поиск в Qdrant.
    4. Передает структурированный стейт в Prover Subgraph.
    """
    query = state["query"]
    iteration = state.get("iteration", 0) + 1
    judge_feedback = state.get("judge_feedback", "")

    print(f"\n🎯 [Orchestrator (Рустем Галеев)] Принят запрос: '{query}' (Итерация #{iteration})")

    # 1. Анализ запроса и генерация подзапросов через GigaChat или fallback
    plan_data: Dict[str, Any] = {}
    llm = get_gigachat_llm(temperature=0.1)

    try:
        chain = ORCHESTRATOR_PROMPT | llm
        response = chain.invoke({
            "query": query,
            "iteration": iteration,
            "judge_feedback": judge_feedback or "Первичный запуск"
        })
        content = response.content if hasattr(response, "content") else str(response)
        plan_data = _parse_orchestrator_json(content)
    except Exception as e:
        print(f"ℹ️ Обращение к LLM в Orchestrator пропущено ({e}). Задействован аналитический планировщик.")

    if not plan_data or not plan_data.get("sub_queries"):
        plan_data = _generate_fallback_plan(query, iteration)

    task_type = plan_data.get("task_type", "prove_theorem")
    sub_queries = plan_data.get("sub_queries", [query])
    hypotheses = plan_data.get("hypotheses", ["Базовая рабочая гипотеза"])

    print(f"📋 [Orchestrator] Тип задачи: '{task_type}'")
    print(f"🔍 [Orchestrator] Сгенерировано подзапросов: {len(sub_queries)} шт.")
    for idx, sq in enumerate(sub_queries[:3], 1):
        print(f"   ↳ #{idx}: {sq}")

    # 2. Multi-Query RAG-поиск через Qdrant
    # Если это первая итерация или контекст еще не собран — выполняем глубокий поиск
    if not state.get("context_text") or iteration > 1:
        print("📚 [RAG Multi-Query] Поиск первоисточников по комплексу подзапросов в Qdrant...")
        context_text, chunks = retrieve_multi_query_knowledge(sub_queries, max_total_chunks=3)
        print(f"✅ [RAG Multi-Query] Успешно извлечено и дедуплицировано источников: {len(chunks)} шт.")
    else:
        context_text = state["context_text"]
        chunks = state.get("retrieved_chunks", [])

    return {
        "query": query,
        "task_type": task_type,
        "iteration": iteration,
        "sub_queries": sub_queries,
        "hypotheses": hypotheses,
        "context_text": context_text,
        "retrieved_chunks": chunks
    }
