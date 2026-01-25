# Tech Stack

## Основные технологии

| Компонент           | Выбор                                             |
| ------------------- | ------------------------------------------------- |
| **Python**          | 3.11+ (типизация)                                 |
| **Окружение**       | venv                                              |
| **FFmpeg**          | Через subprocess                                  |
| **Транскрибация**   | OpenAI gpt-4o-transcribe (основной), gpt-4o-transcribe-diarize (спикеры) + ZAI (альтернатива, в планах) |
| **LLM для summary** | GLM 4.7 (OpenAI-совместимая)                      |
| **CLI**             | Click 8.1+                                         |
| **Конфигурация**    | .env (без YAML пока)                              |

## Параметры пайплайна

| Параметр          | Значение                             |
| ----------------- | ------------------------------------ |
| Нарезка аудио     | По размеру файла (>20MB)             |
| Размер чанка      | 20MB (CHUNK_MAX_SIZE_MB, из env)     |
| Перекрытие кусков | 2 сек (CHUNK_OVERLAP_SEC, из env)    |
| Отправка в API    | Последовательно                      |
| Обработка ошибок  | Минимум, без retry в MVP             |

## Архитектура

```
src/
├── audio/          # извлечение/нарезка аудио
│   ├── converter.py    # FFmpeg video → audio
│   └── chunker.py      # Split large files with overlap
├── transcribe/     # адаптер + реализации
│   ├── adapter.py      # OpenAI API wrapper
│   ├── models.py       # Data models
│   ├── merger.py       # Merge chunked results
│   └── exceptions.py   # Custom exceptions
├── summary/        # LLM вызовы
└── cli.py          # точка входа
```
