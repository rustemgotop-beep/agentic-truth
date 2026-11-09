#!/usr/bin/env bash
# Скрипт гарантированного запуска Streamlit в изолированном виртуальном окружении проекта

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    echo "🚀 Запуск Agentic Truth Web UI в окружении .venv..."
    .venv/bin/streamlit run app.py
else
    echo "⚠️ Окружение .venv не найдено, пробую глобальный streamlit..."
    streamlit run app.py
fi
