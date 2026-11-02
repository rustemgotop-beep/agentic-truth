"""
Обратная совместимость: реэкспорт get_llm из core.llm (только GigaChat).
"""
from core.llm import get_llm, get_gigachat_llm

__all__ = ["get_llm", "get_gigachat_llm"]
