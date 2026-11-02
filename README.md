# 🧮 Agentic Truth — Помощник по теоретическому матанализу

> **Проект Команды № 14 (КП1 / КП2)**  
> Мультиагентная верификация доказательств, Citation-First RAG и формальный символьный аудит логики на базе **LangGraph**, **GigaChat** и **SymPy**.

---

## 🏛 Новая архитектура проекта (Clean Architecture)

Вместо монолитного файла проект разбит на четкие модули с разделением ответственности по ролям команды:

```
agentic-truth/
├── .gitignore                  # Игнорирование .venv, .env, __pycache__, архивов
├── .env.example                # Шаблон конфигурации для GigaChat и Tavily
├── requirements.txt            # Фиксированные зависимости (GigaChat, LangGraph, SymPy)
├── README.md                   # Документация архитектуры и руководство запуска
│
├── config/                     # Настройки проекта
│   └── settings.py             # Централизованная конфигурация и чтение .env
│
├── core/                       # Ядро системы
│   ├── state.py                # Общий контракт состояния графа (State TypedDict)
│   ├── llm.py                  # Фабрика моделей: СТРОГО GigaChat (Сбер)
│   └── config.py               # Конфигурационные параметры
│
├── tools/                      # Инструменты агентов
│   └── sympy_verifier.py       # Безопасный символьный аудит формул (SymPy Tools)
│
├── rag/                        # База знаний и поиск
│   ├── corpus.py               # Академический мини-корпус (Зорич, Фихтенгольц, Кудрявцев)
│   └── retriever.py            # Поисковый слой (Локальный корпус + Tavily Search)
│
├── agents/                     # Модули агентов (5 ролей команды)
│   ├── prover/                 # ⭐️ [PROVER AGENT] Григорий Коценко (ТВОЙ АГЕНТ)
│   │   ├── agent.py            # Трехстадийный Prover Subgraph (Decompose -> SymPy -> Synthesize)
│   │   ├── prompts.py          # Академические промпты для GigaChat (LaTeX, цитаты)
│   │   └── __init__.py         # Экспорт prover_subgraph и prover_node
│   ├── orchestrator.py         # Интерфейс/заглушка для Рустема Галеева (Orchestrator)
│   ├── skeptic.py              # Интерфейс/заглушка для Степана Иванова (Skeptic)
│   ├── judge.py                # Интерфейс/заглушка для Сергея Галкина (Judge)
│   └── test_agent.py           # Интерфейс/заглушка для Евгения Рудко (Test Agent / QA)
│
├── main.py                     # Оркестрация основного графа LangGraph и CLI запуск
└── app.py                      # Интерактивный Web UI на Streamlit
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
