# Roadmap

## Phase 1: Research

- [ ] Изучить API транскрибации (Whisper, ZAI)
  - Лимиты по размеру файла
  - Поддержка диаризации (спикеры)
  - Цена и качество
- [ ] Изучить GLM 4.7 для summary
  - OpenAI-совместимость
  - Контекстное окно
- [ ] Разобраться с FFmpeg
  - Базовые команды для извлечения аудио
  - Форматы и кодеки
- [ ] Определить формат промптов
  - Дефолтный шаблон
  - Передача контекста
- [ ] Выбрать CLI-фреймворк
  - click, typer, rich-cli

## Phase 2: Инициализация проекта

- [ ] Создать структуру проекта
- [ ] Настроить venv
- [ ] Добавить `.env.example`
- [ ] Настроить типизацию (mypy?)

## Phase 3: MVP

- [x] Модуль извлечения аудио (FFmpeg)
- [x] Модуль нарезки аудио
- [x] Адаптер транскрибации
- [x] Реализация OpenAI (gpt-4o-transcribe, gpt-4o-transcribe-diarize)
- [x] Pipeline модуль (process команда)
- [x] Модуль postprocess (GLM 4.7 / gpt-5-mini)
  - [x] it_meeting_summary preset
  - [x] screencast_cleanup preset
- [x] CLI-интерфейс
- [ ] Базовые тесты

## Phase 4: Улучшения (будущее)

- [x] Реализация ZAI (duration-based chunking)
- [ ] Retry и обработка ошибок
- [ ] Параллельная отправка кусков
- [ ] YAML-конфигурация
