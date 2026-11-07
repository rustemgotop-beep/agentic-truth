# 🧮 Agentic Truth — Помощник по теоретическому матанализу

[![CI / Evaluation Suite](https://github.com/rustemgotop-beep/agentic-truth/actions/workflows/tests.yml/badge.svg)](https://github.com/rustemgotop-beep/agentic-truth/actions/workflows/tests.yml)
[![Tests Passing](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)](https://github.com/rustemgotop-beep/agentic-truth)
[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![Qdrant Vector DB](https://img.shields.io/badge/Qdrant-40%2B%20theorems-red.svg)](https://qdrant.tech/)
[![Clean Architecture](https://img.shields.io/badge/architecture-5%20agents%20modular-orange.svg)](https://github.com/rustemgotop-beep/agentic-truth)

> **Проект Команды № 14 (КП1 / КП2 / КП3)**  
> Мультиагентная верификация доказательств, Citation-First RAG и формальный символьный аудит логики на базе **LangGraph**, **GigaChat** и **SymPy**.

---

## 🏛 Новая архитектура проекта (Clean Architecture)

Вместо монолитного файла проект разбит на четкие модули с разделением ответственности по ролям команды:

```
agentic-truth/
├── .github/workflows/          # Автоматический CI/CD (GitHub Actions)
│   └── tests.yml               # Прогон 18 тестов и бенчмарка на Python 3.10 и 3.11
├── .gitignore                  # Игнорирование .venv, .env, __pycache__, архивов
├── .env.example                # Шаблон конфигурации для GigaChat и Tavily
├── requirements.txt            # Фиксированные зависимости (GigaChat, LangGraph, SymPy)
├── README.md                   # Документация архитектуры и руководство запуска
│
├── core/                       # Ядро системы
│   ├── state.py                # Общий контракт состояния графа (State TypedDict)
│   ├── llm.py                  # Фабрика моделей: СТРОГО GigaChat (Сбер)
│   └── config.py               # Конфигурационные параметры и чтение .env
│
├── tools/                      # Инструменты агентов
│   └── sympy_verifier.py       # Безопасный символьный аудит формул (SymPy Tools)
│
├── rag/                        # Векторная база знаний Qdrant (40+ теорем) и ретривер
│   ├── qdrant_store.py         # Векторное хранилище Qdrant (Local Embedded, 9500+ dims)
│   ├── retriever.py            # Поисковый слой (Multi-Query Qdrant + дедупликация)
│   └── corpus.py               # Академический мини-корпус (Зорич, Фихтенгольц, Кудрявцев)
│
├── agents/                     # Модульная Clean Architecture (все 5 ролей команды)
│   ├── orchestrator/           # 🎯 [ORCHESTRATOR] Рустем Галеев (Планировщик, Multi-Query RAG)
│   │   ├── agent.py            # Узел orchestrator_node, классификация задач и генерация гипотез
│   │   ├── prompts.py          # Промпты декомпозиции запросов
│   │   └── __init__.py         # Экспорт orchestrator_node
│   ├── prover/                 # 📐 [PROVER AGENT] Григорий Коценко (ТВОЙ АГЕНТ)
│   │   ├── agent.py            # Трехстадийный Prover Subgraph (Decompose -> SymPy -> Synthesize)
│   │   ├── prompts.py          # Академические промпты для GigaChat (LaTeX, Evidence Graph)
│   │   └── __init__.py         # Экспорт prover_subgraph и prover_node
│   ├── skeptic/                # 🕵️ [SKEPTIC AGENT] Степан Иванов (Red-Team аудит)
│   │   ├── agent.py            # Узел skeptic_node, аудит краевых условий
│   │   ├── catalog.py          # Реестр математических патологий и контрпримеров (|x|, sgn, 1/x...)
│   │   ├── prompts.py          # Промпты поиска брешей доказательства
│   │   └── __init__.py         # Экспорт skeptic_node
│   ├── judge/                  # ⚖️ [JUDGE AGENT] Сергей Галкин (Арбитраж и рефлексия)
│   │   ├── agent.py            # Узел judge_node, скоринг доверия и арбитраж
│   │   ├── prompts.py          # Промпты вердикта (ACCEPT/REVISE)
│   │   └── __init__.py         # Экспорт judge_node и judge_router
│   └── tester/                 # 🧪 [QA LEAD] Евгений Рудко (Evaluation Harness & бенчмарк)
│       ├── agent.py            # Класс TesterAgent для управления оценкой
│       ├── benchmark.py        # Сквозной раннер бенчмарков с замером Latency и SymPy Rate
│       ├── dataset.py          # Золотой набор академических тестов (BENCHMARK_CASES)
│       ├── metrics.py          # Расчет метрик качества и генерация академического отчета
│       └── __init__.py         # Экспорт run_benchmark_suite, BENCHMARK_CASES, TesterAgent
│
├── tests/                      # Полный набор модульных и интеграционных тестов (18 тестов)
│   ├── test_database.py        # Тесты векторной базы Qdrant и семантического поиска
│   ├── test_orchestrator.py    # Тесты планировщика и Multi-Query ретривера (Галеев)
│   ├── test_skeptic.py         # Тесты контрпримеров и поиска брешей (Иванов)
│   ├── test_judge.py           # Тесты арбитража и петли рефлексии (Галкин)
│   └── test_benchmark.py       # Тесты Evaluation Harness и расчет метрик (Рудко)
│
├── main.py                     # Оркестрация основного графа LangGraph и CLI запуск
└── app.py                      # Интерактивный Web UI (Доказательство + Стенд бенчмарков QA)
```

---

## ⭐️ Почему для Prover Agent нужен Подграф (Subgraph)?

В теоретической математике единый монолитный промпт неизбежно галлюцинирует и пропускает тонкие условия (например, разницу между непрерывностью на $[a, b]$ и дифференцируемостью на $(a, b)$).

Твой **Prover Subgraph** делит процесс доказательства на 3 строгие верифицируемые стадии:
1. **`decompose_conditions_node` (Декомпозиция условий)**: Выделяет необходимые математические предпосылки ($f \in C[a, b]$, $f(a) \cdot f(b) < 0$ и т.д.). При повторной итерации автоматически учитывает замечания Скептика.
2. **`sympy_verification_node` (SymPy Tools)**: Формально вычисляет символьные пределы, производные или корни модельных функций через `SymPy` с защитой от инъекций.
3. **`synthesize_proof_node` (Синтез доказательства)**: Модель GigaChat собирает пошаговое доказательство в формате LaTeX с привязкой к первоисточникам и отчетом SymPy, строя структуру `proof_graph`.

---

## 🚀 Быстрый старт

### 1. Настройка окружения
```bash
# Создание и активация виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Конфигурация ключей (`.env`)
Создайте файл `.env` на основе `.env.example`:
```env
GIGACHAT_CREDENTIALS=your_base64_credentials_here
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_MODEL=GigaChat
TAVILY_API_KEY=tvly-your_key_here
```

### 3. Запуск консольного графа
```bash
python main.py
```

### 4. Запуск веб-демонстрации (Streamlit)
```bash
streamlit run app.py
```
