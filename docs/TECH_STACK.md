# Tech Stack

## Основные технологии

| Компонент           | Выбор                                             |
| ------------------- | ------------------------------------------------- |
| **Python**          | 3.11+ (типизация)                                 |
| **Окружение**       | venv                                              |
| **FFmpeg**          | Через subprocess                                  |
| **Транскрибация**   | OpenAI gpt-4o-transcribe (основной), gpt-4o-transcribe-diarize (спикеры) + ZAI GLM-ASR-2512 (альтернатива, реализован) |
| **LLM для summary** | GLM 4.7 (OpenAI-совместимая)                      |
| **CLI**             | Click 8.1+                                         |
| **Конфигурация**    | .env (без YAML пока)                              |

## Параметры пайплайна

| Параметр          | Значение                             |
| ----------------- | ------------------------------------ |
| Нарезка аудио     | По размеру (>20MB, OpenAI) или по времени (>30s, Z.AI) |
| Размер чанка      | 20MB (OpenAI) или 30s (Z.AI)         |
| Перекрытие кусков | 2 сек (CHUNK_OVERLAP_SEC, из env)    |
| Отправка в API    | Последовательно                      |
| Обработка ошибок  | Минимум, без retry в MVP             |

## Архитектура

```
src/
├── audio/          # извлечение/нарезка аудио
│   ├── converter.py    # FFmpeg video → audio
│   └── chunker.py      # Split large files (size-based or duration-based)
├── transcribe/     # адаптер + реализации
│   ├── factory.py      # Provider factory (OpenAI/Z.AI)
│   ├── adapter.py      # OpenAI API wrapper
│   ├── glm_asr_client.py  # Z.AI GLM-ASR wrapper
│   ├── models.py       # Data models
│   ├── merger.py       # Merge chunked results
│   └── exceptions.py   # Custom exceptions
├── postprocess/     # LLM вызовы
└── cli.py          # точка входа
```
