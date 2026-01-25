# Research: ZAI GLM-ASR-2512

> Автоматическая распознавание речи (ASR) от Z.AI

## Характеристики

| Параметр        | Значение                       |
| --------------- | ------------------------------ |
| **CER**         | 0.0717 (мирового уровня)       |
| **Лимит аудио** | ≤ 30 секунд                    |
| **Лимит файла** | ≤ 25 MB                        |
| **Цена**        | $0.03 / MTok (~$0.0024/minute) |

## API

```bash
POST https://api.z.ai/api/paas/v4/audio/transcriptions
Headers:
  Authorization: Bearer API_Key
  Content-Type: multipart/form-data

Form data:
  model=glm-asr-2512
  stream=false|true
  file=@audio-file
```

## Особенности

- **Custom Dictionary**: можно добавлять свою терминологию (кодовые названия проектов, имена)
- **Complex Scenarios**: хорошо работает с китайско-английским миксом, IT-терминологией

## Вывод для проекта

**Критично**: лимит **30 секунд** требует нарезки аудио — это подтверждает архитектурное решение:

```
Видео → Аудио → Нарезка (30 сек) → Транскрибация → Склейка
```

## Кейсы применения

- Real-time Meeting Minutes
- Customer Service QA
- Live Video Captioning
- Office Document Input (голосовой ввод документов)
- Medical Record Entry

## Источники

- [Overview](https://docs.z.ai/guides/audio/glm-asr-2512)
- [Pricing](https://docs.z.ai/guides/overview/pricing)
