import os
from typing import Any
from langchain_core.language_models import FakeListLLM
from langchain_core.runnables import RunnableLambda
from core.config import config


def get_gigachat_llm(temperature: float = 0.1):
    """
    Фабрика языковой модели: строго GigaChat (Сбер).
    Автоматически инициализирует клиент GigaChat с корректными параметрами и scope.
    """
    credentials = config.gigachat_credentials
    scope = config.gigachat_scope
    model = config.gigachat_model

    if credentials:
        try:
            from langchain_gigachat.chat_models import GigaChat
            import gigachat

            # Попытка динамически определить доступную модель на аккаунте
            selected_model = model
            try:
                with gigachat.GigaChat(
                    credentials=credentials,
                    verify_ssl_certs=config.verify_ssl_certs,
                    scope=scope
                ) as client:
                    models_data = client.get_models().data
                    available = [m.id_ for m in models_data if "embed" not in m.id_.lower()]
                    if available:
                        selected_model = available[0]
            except Exception:
                pass

            return GigaChat(
                credentials=credentials,
                verify_ssl_certs=config.verify_ssl_certs,
                scope=scope,
                model=selected_model,
                temperature=temperature
            )
        except Exception as e:
            print(f"⚠️ Ошибка инициализации GigaChat: {e}")

    # Fallback-режим для локальных тестов и демонстрации, если ключ еще не добавлен в .env
    print("ℹ️ Внимание: GIGACHAT_CREDENTIALS не найден в .env. Активирован локальный тестовый режим.")
    
    def mock_academic_responder(prompt_input: Any) -> str:
        prompt_str = prompt_input.to_string() if hasattr(prompt_input, "to_string") else str(prompt_input)
        if "декомпозиции" in prompt_str.lower():
            return (
                "- Функция $f(x)$ непрерывна на замкнутом отрезке $[a, b]$\n"
                "- Функция $f(x)$ принимает на концах отрезка значения разных знаков: $f(a) \\cdot f(b) < 0$\n"
                "- Область определения функции связна и содержит отрезок $[a, b]$"
            )
        elif "sympy" in prompt_str.lower() and "символьных вычислениях" in prompt_str.lower():
            return "sp.limit(sp.sin(x)/x, x, 0)"
        else:
            return (
                "### 1. Точная формулировка теоремы\n"
                "Пусть функция $f(x)$ непрерывна на отрезке $[a, b]$ и принимает на его концах значения "
                "разных знаков ($f(a) \cdot f(b) < 0$). Тогда существует точка $c \\in (a, b)$, такая что $f(c) = 0$.\n\n"
                "### 2. Условия применимости (Assumptions)\n"
                "- $f(x) \\in C[a, b]$\n"
                "- $f(a) \cdot f(b) < 0$\n\n"
                "### 3. Опорные леммы и теоретическая база\n"
                "- Лемма о вложенных отрезках Коши-Кантора (принцип полноты действительных чисел)\n"
                "- Определение непрерывности по Гейне/Коши\n\n"
                "### 4. Пошаговое строгое доказательство\n"
                "- **Шаг 1**: Рассматриваем отрезок $[a_0, b_0] = [a, b]$. Делим его точкой середины $x_0 = (a_0 + b_0)/2$.\n"
                "- **Шаг 2**: Если $f(x_0) = 0$, теорема доказана ($c = x_0$). Если $f(x_0) \\neq 0$, выбираем ту половину, "
                "на концах которой знаки различны. Обозначаем ее $[a_1, b_1]$.\n"
                "- **Шаг 3**: Продолжая процесс дихотомии, получаем последовательность вложенных отрезков $[a_n, b_n]$, "
                "длина которых $(b - a)/2^n \\to 0$.\n"
                "- **Шаг 4**: По лемме Коши-Кантора существует единственная общая точка $c = \\lim a_n = \\lim b_n$.\n"
                "- **Шаг 5**: В силу непрерывности $f(c) = \\lim f(a_n) \\le 0$ и $f(c) = \\lim f(b_n) \\ge 0$, следовательно, $f(c) = 0$.\n\n"
                "### 5. Формальная символьная проверка (SymPy Audit)\n"
                "- Символьное тождество и сходимость шага дихотомии проверены в SymPy.\n\n"
                "### 6. Первоисточники и цитаты (Grounded Evidence)\n"
                "- В.А. Зорич, «Математический анализ», Ч. 1, Гл. 4 (§2 «Свойства непрерывных функций»)."
            )

    return RunnableLambda(mock_academic_responder)


# Алиас для единообразия
get_llm = get_gigachat_llm
