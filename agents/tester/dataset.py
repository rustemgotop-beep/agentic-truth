"""
Бенчмарк-датасет для автоматизированного тестирования мультиагентной системы (Евгений Рудко).
Охватывает различные типы задач:
- Классические теоремы анализа 1D
- Замечательные пределы
- Интегральное исчисление
- Векторный анализ 2D
- Тест на выявление ошибок / фальсификацию
"""
from typing import List, Dict, Any

BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "id": "CASE_01_BOLZANO",
        "category": "Непрерывность",
        "query": "Докажи теорему Больцано-Коши об обращении непрерывной функции в ноль",
        "expected_verdict": "ACCEPT",
        "expected_tool": "solve"
    },
    {
        "id": "CASE_02_ROLLE",
        "category": "Дифференцируемость",
        "query": "Сформулируй и строго докажи теорему Ролля о нуле производной",
        "expected_verdict": "ACCEPT",
        "expected_tool": "diff"
    },
    {
        "id": "CASE_03_LAGRANGE",
        "category": "Теоремы о среднем",
        "query": "Докажи теорему Лагранжа о конечном приращении",
        "expected_verdict": "ACCEPT",
        "expected_tool": "diff"
    },
    {
        "id": "CASE_04_LIMIT",
        "category": "Пределы",
        "query": "Докажи Первый замечательный предел для sin(x)/x при x стремящемся к 0",
        "expected_verdict": "ACCEPT",
        "expected_tool": "limit"
    },
    {
        "id": "CASE_05_INTEGRAL",
        "category": "Интегралы",
        "query": "Докажи формулу Ньютона-Лейбница для определенного интеграла",
        "expected_verdict": "ACCEPT",
        "expected_tool": "integrate"
    },
    {
        "id": "CASE_06_GREEN",
        "category": "Векторный анализ",
        "query": "Докажи формулу Грина, связывающую криволинейный интеграл с двойным интегралом",
        "expected_verdict": "ACCEPT",
        "expected_tool": "integrate"
    }
]
