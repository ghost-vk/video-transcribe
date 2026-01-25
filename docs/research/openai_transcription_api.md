# OpenAI Transcription API

## Models

| Model | Features | Response Formats |
|-------|----------|------------------|
| `gpt-4o-transcribe` | Prompt support | `text`, `json` |
| `gpt-4o-transcribe-diarize` | Speaker diarization | `text`, `json`, `diarized_json` |

## API Limits

- **Max file size:** 25 MB
- **Supported formats:** mp3, mp4, mpeg, mpga, m4a, wav, webm
- **chunking_strategy:** Required for diarize when audio > 30 sec

## Diarization

```python
from openai import OpenAI

client = OpenAI()

with open("meeting.wav", "rb") as audio_file:
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-transcribe-diarize",
        file=audio_file,
        response_format="diarized_json",
        chunking_strategy="auto",
    )

for segment in transcript.segments:
    print(f"{segment.speaker}: {segment.text}")
```

**Response format:**
```json
{
  "segments": [
    {"speaker": "SPEAKER_1", "text": "...", "start": 0.0, "end": 5.2},
    {"speaker": "SPEAKER_2", "text": "...", "start": 5.5, "end": 10.1}
  ]
}
```

## Known Speakers (Optional)

```python
import base64

def to_data_url(path: str) -> str:
    with open(path, "rb") as fh:
        return "data:audio/wav;base64," + base64.b64encode(fh.read()).decode("utf-8")

transcript = client.audio.transcriptions.create(
    model="gpt-4o-transcribe-diarize",
    file=audio_file,
    response_format="diarized_json",
    chunking_strategy="auto",
    extra_body={
        "known_speaker_names": ["agent", "customer"],
        "known_speaker_references": [
            to_data_url("agent.wav"),
            to_data_url("customer.wav")
        ],
    },
)
```

## Constraints

| Feature | gpt-4o-transcribe | gpt-4o-transcribe-diarize |
|---------|-------------------|---------------------------|
| Prompt | ✅ | ❌ |
| Diarization | ❌ | ✅ |
| Logprobs | ✅ | ❌ |
| `timestamp_granularities[]` | ❌ | ❌ |

## Languages

50+ languages including Russian. Full list:
Afrikaans, Arabic, Armenian, Azerbaijani, Belarusian, Bosnian, Bulgarian, Catalan, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, Galician, German, Greek, Hebrew, Hindi, Hungarian, Icelandic, Indonesian, Italian, Japanese, Kannada, Kazakh, Korean, Latvian, Lithuanian, Macedonian, Malay, Marathi, Maori, Nepali, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swahili, Swedish, Tagalog, Tamil, Thai, Turkish, Ukrainian, Urdu, Vietnamese, Welsh.

## Pricing

Check [OpenAI Pricing](https://openai.com/api/pricing) for current rates.

## References

- [Official Documentation](https://platform.openai.com/docs/guides/speech-to-text)
