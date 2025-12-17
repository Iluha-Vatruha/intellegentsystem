# ES Clothing Recommender (CLIPS + Flask + clipspy)

Простой проект: экспертная система подбора одежды по погоде.
CLIPS knowledge base: `knowledge.clp` (40 правил).
Flask UI — веб-форма.

## Требования
- Python 3.8–3.12 (рекомендуется 3.9+)
- pip

## Установка
1. Создайте виртуальное окружение:
   python -m venv .venv
   .venv\Scripts\activate     (Windows)
   source .venv/bin/activate  (Linux/Mac)

2. Установите зависимости:
   pip install -r requirements.txt

   Если возникнут проблемы с clipspy на Windows — попробуйте установить готовый wheel с PyPI (pip сам подберёт).

## Запуск
python app.py

Откройте http://127.0.0.1:5000

## Файлы
- knowledge.clp — CLIPS rules
- app.py — Flask приложение
- templates/index.html — UI
