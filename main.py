from langchain_tavily import TavilySearch
import os
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import FakeListLLM
from dotenv import load_dotenv, dotenv_values


load_dotenv()

# 1. Shared state used by every node
class State(TypedDict):
    query: str
    pro_evidence: str
    con_evidence: str
    final_answer: str


# 2. Dummy node functions


def coordinator_node(state: State):
    """Receives the question and coordinates the workflow."""
    print("Coordinator: received the question.")

    # The Coordinator has no special field in our simple State,
    # so we return the query unchanged.
    return {"query": state["query"]}


def prover_node(state: State):
    print("\n=== [Prover] НАЧАЛО РАБОТЫ ===")
    user_query = state["query"]

    # --- ШАГ 1: РЕАЛЬНЫЙ ПОИСК В ИНТЕРНЕТЕ ---
    print(f"👀 Ищу в интернете информацию по запросу: '{user_query}'...")

    # Инициализируем поиск
    search_tool = TavilySearch(max_results=2, tavily_api_key=os.getenv("TAVILY_API_KEY"))

    try:
        search_results = search_tool.invoke(user_query)

        # УМНАЯ ОБРАБОТКА РЕЗУЛЬТАТОВ (Пуленепробиваемый вариант)
        if isinstance(search_results, str):
            # Если Tavily сразу вернул готовый текст
            context_text = search_results
        elif isinstance(search_results, list) and len(search_results) > 0 and isinstance(search_results[0], dict):
            # Если Tavily вернул список словарей
            context_text = "\n\n".join(
                [f"Источник: {res.get('url', 'Нет URL')}\nТекст: {res.get('content', '')}" for res in search_results])
        elif isinstance(search_results, list) and len(search_results) > 0 and hasattr(search_results[0],
                                                                                      'page_content'):
            # Если Tavily вернул объекты документов LangChain
            context_text = "\n\n".join([f"Текст: {res.page_content}" for res in search_results])
        else:
            # На крайний случай просто превращаем результат в строку
            context_text = str(search_results)

        print("✅ Поиск успешен! Вот что нашлось (фрагмент):")
        print(context_text[:300] + "...\n")

    except Exception as e:
        print(f"❌ Ошибка поиска: {e}")
        return {"pro_evidence": "Ошибка поиска"}

    # --- ШАГ 2: АНАЛИЗ НЕЙРОСЕТЬЮ ---
    print("🧠 Передаю найденный текст нейросети для анализа...")

    fake_responses = [
        "Найдено доказательство: Python отлично подходит для новичков, так как имеет простой синтаксис (согласно найденным статьям)."]
    llm = FakeListLLM(responses=fake_responses)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Ты Агент-Доказатель. Найди плюсы в тексте: {context}"),
        ("user", "Запрос: {query}")
    ])

    chain = prompt | llm

    # Запускаем!
    response = chain.invoke({
        "query": user_query,
        "context": context_text
    })

    print("✅ Нейросеть сформировала ответ!")
    return {"pro_evidence": response}


def skeptic_node(state: State):
    """Pretends to find evidence opposing the query."""
    print("Skeptic: looking for opposing evidence.")

    return {
        "con_evidence": "Found some opposing facts."
    }


def verifier_node(state: State):
    """Pretends to check both sides and create a final answer."""
    print("Verifier: checking the evidence.")

    final_answer = (
        f"Mock answer for: {state['query']}\n"
        f"Supporting evidence: {state['pro_evidence']}\n"
        f"Opposing evidence: {state['con_evidence']}"
    )

    return {
        "final_answer": final_answer
    }


# 3. Conditional routing function


def verifier_router(state: State):
    """
    Decide what happens after the Verifier.

    If a final answer exists, end the graph.
    Otherwise, send the workflow back to the Coordinator.
    """
    if state["final_answer"]:
        print("Verifier: final answer is ready -> ending graph.")
        return "finish"

    print("Verifier: no final answer yet -> retrying.")
    return "retry"


# 4. Build the graph

builder = StateGraph(State)

builder.add_node("coordinator", coordinator_node)
builder.add_node("prover", prover_node)
builder.add_node("skeptic", skeptic_node)
builder.add_node("verifier", verifier_node)

# Normal edges
builder.add_edge(START, "coordinator")
builder.add_edge("coordinator", "prover")
builder.add_edge("prover", "skeptic")
builder.add_edge("skeptic", "verifier")

# Conditional edge from the Verifier
builder.add_conditional_edges(
    "verifier",
    verifier_router,
    {
        "finish": END,
        "retry": "coordinator",
    },
)

# Compile the graph
graph = builder.compile()


# 5. Run the graph with a test question
#
if __name__ == "__main__":
    initial_state: State = {
        "query": "Is Python a good language for beginners?",
        "pro_evidence": "",
        "con_evidence": "",
        "final_answer": "",
    }

    # final_state = graph.invoke(initial_state)
    result = prover_node(initial_state)

    print("\n--- FINAL ANSWER ---")
    # print(final_state["final_answer"])
    print(result["pro_evidence"])
