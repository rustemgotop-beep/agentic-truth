from typing import List, Tuple
from core.state import SourceChunk
from core.config import config
from rag.qdrant_store import qdrant_store


def retrieve_math_knowledge(query: str, top_k: int = 3) -> Tuple[str, List[SourceChunk]]:
    """
    Гибридный RAG-ретривер:
    1. Выполняет семантический векторный поиск по локальной базе данных Qdrant.
    2. При наличии ключа TAVILY_API_KEY дополняет контекст внешним веб-поиском.
    3. Формирует строгий математический контекст с формулами и первоисточниками (Зорич, Фихтенгольц, Кудрявцев).
    """
    chunks: List[SourceChunk] = []

    # 1. Векторный поиск через Qdrant
    qdrant_results = qdrant_store.search(query, top_k=top_k)
    for res in qdrant_results:
        formula_part = f"Формула: {res['latex_formula']}\n" if res.get("latex_formula") else ""
        citation_part = f"Цитата: {res['citation']}\n" if res.get("citation") else ""
        content_text = f"Теорема: {res['theorem']}\n{formula_part}{citation_part}Содержание: {res['content']}"

        chunks.append({
            "source": res["source"],
            "content": content_text.strip(),
            "origin": f"Векторная БД Qdrant (score={res['score']:.2f})"
        })

    # 2. Поиск через Tavily (если сконфигурирован в .env)
    if config.tavily_api_key:
        try:
            from langchain_tavily import TavilySearch
            search_tool = TavilySearch(max_results=2, tavily_api_key=config.tavily_api_key)
            raw = search_tool.invoke(f"{query} математический анализ формулировка теорема доказательство")
            items = raw.get("results", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])

            for res in items:
                if isinstance(res, dict) and res.get("content"):
                    chunks.append({
                        "source": res.get("url", "Академический веб-источник"),
                        "content": res.get("content", "").strip(),
                        "origin": "Tavily Web Search"
                    })
        except Exception as e:
            print(f"⚠️ Ошибка внешнего Tavily RAG: {e}. Используется база Qdrant.")

    context_blocks = [
        f"[{c['origin']}]\nИсточник: {c['source']}\nФрагмент:\n{c['content']}"
        for c in chunks
    ]
    context_text = "\n\n---\n\n".join(context_blocks)
    return context_text, chunks
