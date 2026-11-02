import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Централизованные настройки приложения."""
    # GigaChat
    gigachat_credentials: str = os.getenv("GIGACHAT_CREDENTIALS", "").strip().strip("\"'")
    gigachat_scope: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip().strip("\"'")
    gigachat_model: str = os.getenv("GIGACHAT_MODEL", "GigaChat").strip().strip("\"'")
    verify_ssl_certs: bool = False

    # Tavily
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "").strip().strip("\"'")

    # Параметры графа
    max_research_iterations: int = 2


config = AppConfig()
