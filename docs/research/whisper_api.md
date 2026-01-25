# Research: OpenAI Whisper API

> Speech-to-Text от OpenAI: классический Whisper и новые GPT-4o модели

## Модели

| Модель                      | Описание                           |
| --------------------------- | ---------------------------------- |
| `whisper-1`                 | Классическая open-source модель    |
| `gpt-4o-mini-transcribe`    | Быстрая, дешёвая                   |
| `gpt-4o-transcribe`         | Высокое качество                   |
| `gpt-4o-transcribe-diarize` | **С диаризацией** (speaker labels) |

## Характеристики

| Параметр                     | Значение                             |
| ---------------------------- | ------------------------------------ |
| **Лимит файла**              | 25 MB                                |
| **Форматы**                  | mp3, mp4, mpeg, mpga, m4a, wav, webm |
| **Цена (whisper-1)**         | **$0.006/minute** ($0.36/hour)       |
| **Цена (gpt-4o-transcribe)** | $2.50 / 1M input tokens              |
| **Языки**                    | 98 языков (WER < 50%)                |

## API

```bash
POST https://api.openai.com/v1/audio/transcriptions
Headers:
  Authorization: Bearer $OPENAI_API_KEY
  Content-Type: multipart/form-data

Form data:
  model=gpt-4o-transcribe
  file=@audio.mp3
  response_format=json|text|verbose_json|vtt|srt
```

## Speaker Diarization

`gpt-4o-transcribe-diarize` поддерживает определение спикеров:

```python
transcript = client.audio.transcriptions.create(
    model="gpt-4o-transcribe-diarize",
    file=audio_file,
    response_format="diarized_json",
    chunking_strategy="auto",  # обязательно для >30 сек
)
# Returns: segments with speaker, start, end
```

### Known Speakers (опционально)

Можно указать до 4 эталонных аудио-клипа (2–10 сек) для маппинга спикеров:

```python
extra_body={
    "known_speaker_names": ["alice", "bob"],
    "known_speaker_references": ["data:audio/wav;base64,...", ...],
}
```

## Особенности

| Фича                      | whisper-1       | gpt-4o-transcribe\* | diarize |
| ------------------------- | --------------- | ------------------- | ------- |
| Timestamps (word/segment) | ✅              | ❌                  | ❌      |
| Prompt                    | ✅ (224 tokens) | ✅                  | ❌      |
| Streaming                 | ❌              | ✅                  | ✅      |
| Logprobs                  | ✅              | ✅                  | ✅      |
| Diarization               | ❌              | ❌                  | ✅      |

\*gpt-4o-mini-transcribe тоже поддерживает prompt и streaming

## Limitations

- **whisper-1**: не поддерживает streaming
- **diarize**: требует `chunking_strategy` для аудио >30 сек
- **diarize**: не поддерживает prompt, logprobs, timestamp_granularities

## Prompting для качества

```python
# Для исправления специфичных слов/акронимов
prompt="ZyntriQix, Digique Plus, CynapseFive, VortiQore V8..."
# whisper-1 учитывает только первые 224 токена
# gpt-4o-transcribe-diarize НЕ поддерживает prompt!
```

Или пост-процессинг через GPT-4 для коррекции терминологии.

## Longer Inputs (>25 MB)

Файлы больше 25 MB нужно разбить на чанки. OpenAI рекомендует **PyDub**:

```python
from pydub import AudioSegment

audio = AudioSegment.from_mp3("meeting.mp3")

# 10 минут в миллисекундах
ten_minutes = 10 * 60 * 1000

first_chunk = audio[:ten_minutes]
first_chunk.export("meeting_01.mp3", format="mp3")

# Лучше избегать разреза в середине предложения!
# Можно использовать VAD (Voice Activity Detection) для умной нарезки
```

**Советы**:

- Избегать разрыва посередине предложения (потеря контекста)
- Использовать сжатые форматы (mp3) для уменьшения размера
- Для `gpt-4o-transcribe-diarize` использовать `chunking_strategy="auto"`

## Языки (WER < 50%)

Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian,
Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian,
Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian,
Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean,
Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian,
Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian,
Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian,
Urdu, Vietnamese, Welsh.

## Вывод для проекта

| Параметр       | Whisper               | ZAI GLM-ASR        |
| -------------- | --------------------- | ------------------ |
| **Цена**       | $0.006/min            | $0.0024/min        |
| **Лимит**      | 25 MB                 | 30 сек + 25 MB     |
| **Диаризация** | ✅ (отдельная модель) | ❌                 |
| **Русский**    | ✅                    | ? (не указан явно) |

**ZAI дешевле в ~2.5 раза**, но **Whisper имеет диаризацию** — критично для meetings.

## Источники

- [Speech to text | OpenAI API](https://platform.openai.com/docs/guides/speech-to-text)
- [Whisper API Pricing (2026)](https://brasstranscripts.com/blog/openai-whisper-api-pricing-2025-self-hosted-vs-managed)
- [OpenAI Transcription Pricing Calculator](https://costgoat.com/pricing/openai-transcription)
