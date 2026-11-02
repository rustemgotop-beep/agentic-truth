from typing import List, Tuple
from core.state import SourceChunk
from core.config import config
from rag.corpus import MATH_SEED_CORPUS


def retrieve_math_knowledge(query: str) -> Tuple[str, List[SourceChunk]]:
    """
    Гибридный RAG-ретривер:
    1. Ищет соответствия в академическом локальном мини-корпусе (Зорич, Фихтенгольц, Кудрявцев).
    2. При наличии ключа TAVILY_API_KEY выполняет внешний поиск первоисточников в сети.
    3. Формирует структурированный контекст для агентов.
    """
    chunks: List[SourceChunk] = []
    q_words = [w.lower() for w in query.split() if len(w) > 3]

    # 1. Поиск в академическом корпусе
    for item in MATH_SEED_CORPUS:
        if any(w in item["content"].lower() or w in item["theorem"].lower() for w in q_words):
            chunks.append({
                "source": item["source"],
                "content": item["content"],
                "origin": "Академический учебный корпус (Seed)"
            })

    # Если точных совпадений нет — берем релевантный дефолт для матанализа
    if not chunks:
        chunks.append({
            "source": MATH_SEED_CORPUS[0]["source"],
            "content": MATH_SEED_CORPUS[0]["content"],
            "origin": "Академический учебный корпус (Seed)"
        })

    # 2. Поиск через Tavily (если сконфигурирован)
    if config.tavily_api_key:
        try:
            from langchain_tavily import TavilySearch
            search_tool = TavilySearch(max_results=3, tavily_api_key=config.tavily_api_key)
            raw = search_tool.invoke(f"{query} математический анализ формулировка теорема доказательство")
            items = raw.get("results", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])

            for res in items:
                if isinstance(res, dict) and res.get("content"):
                    chunks.append({
                        "source": res.get("url", "Внешний веб-источник"),
                        "content": res.get("content", "").strip(),
                        "origin": "Tavily Web RAG"
                    })
        except Exception as e:
            print(f"⚠️ Ошибка внешнего Tavily RAG: {e}. Используется локальный корпус.")

    context_blocks = [
        f"[{c['origin']}] Источник: {c['source']}\nФрагмент: {c['content']}"
        for c in chunks
    ]
    context_text = "\n\n".join(context_blocks)
    return context_text, chunks
