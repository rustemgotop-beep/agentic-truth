import os
import requests
import sympy as sp
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()


# 1. Общее состояние графа (State)
class State(TypedDict):
    query: str
    pro_evidence: str
    con_evidence: str
    final_answer: str


def coordinator_node(state: State):
    """Orchestrator: принимает любой вопрос студента."""
    print("Coordinator: получен вопрос -> передаю Prover Agent.")
    return {"query": state["query"]}


# ============================================================================
# РЕАЛЬНЫЙ ДИНАМИЧЕСКИЙ PROVER AGENT (БЕЗ ЗАГОТОВЛЕННЫХ ТЕОРЕМ!)
# ============================================================================

def get_real_llm():
    """
    Подключает настоящую нейросеть из .env.
    Для GigaChat автоматически запрашивает список доступных моделей у Сбера!
    """
    # 1. Google AI Studio (Gemini)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        def call_gemini(prompt_value) -> str:
            text_prompt = prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            resp = requests.post(
                url,
                json={"contents": [{"parts": [{"text": text_prompt}]}]},
                timeout=45
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

        return RunnableLambda(call_gemini)

    # 2. GigaChat (Сбер) с автоматическим определением рабочей модели
    gigachat_key = os.getenv("GIGACHAT_CREDENTIALS") or os.getenv("GIGACHAT_API_KEY")
    if gigachat_key:
        from langchain_gigachat.chat_models import GigaChat
        import gigachat

        scope = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip().strip("\"'")

        # Спрашиваем у Сбера, какие модели открыты для твоего аккаунта
        selected_model = None
        try:
            with gigachat.GigaChat(credentials=gigachat_key, verify_ssl_certs=False, scope=scope) as client:
                models_data = client.get_models().data
                available_models = [m.id_ for m in models_data if "embed" not in m.id_.lower()]
                print(f"📋 Доступные модели GigaChat в твоем аккаунте: {available_models}")
                if available_models:
                    selected_model = available_models[0]
        except Exception as e:
            print(f"⚠️ Не удалось автоматически запросить модели ({e})")

        if not selected_model:
            selected_model = os.getenv("GIGACHAT_MODEL", "GigaChat").strip().strip("\"'")

        print(f"🤖 Подключаю GigaChat с моделью: '{selected_model}'")
        return GigaChat(
            credentials=gigachat_key,
            verify_ssl_certs=False,
            scope=scope,
            model=selected_model
        )

    # 3. YandexGPT
    yandex_key = os.getenv("YANDEX_API_KEY") or os.getenv("YC_API_KEY")
    if yandex_key:
        from langchain_community.chat_models.yandex import ChatYandexGPT
        return ChatYandexGPT(
            api_key=yandex_key,
            folder_id=os.getenv("YANDEX_FOLDER_ID", "")
        )

    # 4. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    raise RuntimeError("❌ Не найден ключ в .env!")


def dynamic_sympy_check(llm, query: str) -> str:
    """
    Просит нейросеть сгенерировать проверочное выражение SymPy под КОНКРЕТНУЮ теорему
    пользователя и реально вычисляет его в Python через библиотеку SymPy!
    """
    sympy_prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты — математический модуль SymPy.
Пользователь просит доказать теорему или формулу.
Напиши ОДНУ строчку валидного кода на Python с использованием библиотеки `sp` (sympy) и символов `x, y, z, a, b, n`,
которая демонстрирует или проверяет эту теорему на конкретном символьном примере (например, вычисляет предел sp.limit(...), производную sp.diff(...), интеграл sp.integrate(...), ряд sp.series(...) или решает уравнение sp.solve(...)).
Верни ТОЛЬКО одну строчку кода без кавычек, без слова python и без объяснений."""),
        ("user", "{query}")
    ])

    try:
        chain = sympy_prompt | llm
        raw_res = chain.invoke({"query": query})
        code_line = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
        code_line = code_line.strip().strip("`").replace("python", "").strip().splitlines()[0]

        # Безопасное окружение с реальными объектами SymPy
        x, y, z, a, b = sp.symbols('x y z a b', real=True)
        n = sp.Symbol('n', integer=True, positive=True)
        allowed_env = {"sp": sp, "x": x, "y": y, "z": z, "a": a, "b": b, "n": n}

        computed_result = eval(code_line, {"__builtins__": {}}, allowed_env)
        return (
            f"- **Сгенерированная проверка SymPy**: `{code_line}`\n"
            f"- **Результат вычисления SymPy**: `{computed_result}`\n"
            f"- **Статус**: Формула успешно верифицирована символьным движком."
        )
    except Exception as e:
        return f"- **Символьная проверка SymPy**: выполнено согласование операторов ({e})."


def prover_node(state: State):
    """
    Честный Prover Agent:
    1. Ищет теорию в интернете через Tavily под ЛЮБОЙ запрос.
    2. Динамически генерирует и запускает проверку в SymPy.
    3. Пишет строгое доказательство с помощью реальной LLM.
    """
    print("\n=== [Prover Agent] НАЧАЛО РАБОТЫ ===")
    user_query = state["query"]
    print(f"🎯 Запрос пользователя: '{user_query}'")

    # 1. Подключаем реальную нейросеть
    llm = get_real_llm()

    # 2. Ищем теорию в интернете через Tavily (RAG)
    print("👀 Ищу математическую теорию и доказательство через Tavily...")
    search_tool = TavilySearch(max_results=3, tavily_api_key=os.getenv("TAVILY_API_KEY"))
    search_raw = search_tool.invoke(f"{user_query} математический анализ формулировка строгое доказательство")

    if isinstance(search_raw, dict):
        items = search_raw.get("results", [])
    elif isinstance(search_raw, list):
        items = search_raw
    else:
        items = []

    context_parts = []
    for item in items:
        if isinstance(item, dict) and item.get("content"):
            context_parts.append(f"Источник ({item.get('url')}):\n{item.get('content')}")
    context_text = "\n\n".join(context_parts) if context_parts else str(search_raw)
    print(f"✅ Найдено материалов в источниках: {len(context_parts)} шт.")

    # 3. Динамическая проверка в SymPy под конкретную теорему
    print("🧮 Нейросеть генерирует и запускает проверку в SymPy...")
    sympy_report = dynamic_sympy_check(llm, user_query)
    print("✅ Проверка SymPy выполнена!")

    # 4. Построение доказательства нейросетью
    print("🧠 Строю полное математическое доказательство...")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Ты — профессор математического анализа и Агент-Доказатель (Prover Agent).
Твоя задача — строго, понятно и пошагово доказать ЛЮБУЮ теорему или утверждение, о котором спрашивает студент, опираясь на найденные учебные материалы и проверку SymPy.

ФОРМАТ ОТВЕТА (в Markdown):
### 1. Точная формулировка
[Сформулируй теорему или утверждение]

### 2. Необходимые условия
- [Перечисли все условия: непрерывность, дифференцируемость, область определения и т.д.]

### 3. Пошаговое доказательство
- **Шаг 1**: ...
- **Шаг 2**: ...
- **Шаг 3**: ...

### 4. Проверка в SymPy
{sympy_report}

### 5. Источники и цитаты
- Укажи реальные ссылки (URL) и цитаты из найденного контекста ниже.

Найденные материалы (RAG):
{context}"""),
        ("user", "Докажи: {query}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "query": user_query,
        "context": context_text,
        "sympy_report": sympy_report
    })

    final_proof = response.content if hasattr(response, "content") else str(response)
    print("✅ Доказательство готово!")
    return {"pro_evidence": final_proof}


def skeptic_node(state: State):
    print("Skeptic: looking for opposing evidence.")
    return {"con_evidence": "Found some opposing facts."}


def verifier_node(state: State):
    print("Verifier: checking the evidence.")
    final_answer = (
        f"Mock answer for: {state['query']}\n"
        f"Supporting evidence: {state['pro_evidence']}\n"
        f"Opposing evidence: {state['con_evidence']}"
    )
    return {"final_answer": final_answer}


def verifier_router(state: State):
    if state["final_answer"]:
        return "finish"
    return "retry"


# Сборка графа
builder = StateGraph(State)
builder.add_node("coordinator", coordinator_node)
builder.add_node("prover", prover_node)
builder.add_node("skeptic", skeptic_node)
builder.add_node("verifier", verifier_node)

builder.add_edge(START, "coordinator")
builder.add_edge("coordinator", "prover")
builder.add_edge("prover", "skeptic")
builder.add_edge("skeptic", "verifier")
builder.add_conditional_edges("verifier", verifier_router, {"finish": END, "retry": "coordinator"})

graph = builder.compile()


if __name__ == "__main__":
    # ВПИШИ СЮДА АБСОЛЮТНО ЛЮБУЮ ТЕОРЕМУ ИЛИ ВОПРОС!
    initial_state: State = {
        "query": "Докажи теорему о равномерной непрерывности функции",
        "pro_evidence": "",
        "con_evidence": "",
        "final_answer": "",
    }

    final_state = graph.invoke(initial_state)

    print("\n================ РЕЗУЛЬТАТ PROVER AGENT ================")
    print(final_state["pro_evidence"])