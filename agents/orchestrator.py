from core.state import State
from rag import retrieve_math_knowledge


def orchestrator_node(state: State):
    """[Member 1 — Orchestrator & RAG Node]"""
    query = state["query"]
    iteration = state.get("iteration", 0) + 1
    print(f"\n🎯 [Orchestrator] Принят запрос: '{query}' (Итерация #{iteration})")

    if not state.get("context_text"):
        print("📚 [RAG Engine] Извлекаю параграфы из учебников и Tavily...")
        context_text, chunks = retrieve_math_knowledge(query)
        print(f"✅ [RAG Engine] Найдено источников: {len(chunks)} шт.")
    else:
        context_text = state["context_text"]
        chunks = state.get("retrieved_chunks", [])

    return {
        "query": query,
        "task_type": "prove_theorem",
        "iteration": iteration,
        "context_text": context_text,
        "retrieved_chunks": chunks
    }
