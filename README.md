# Video Transcribe

Automated video transcription with speaker diarization and meeting summaries.

## Requirements

- Python >= 3.11
- ffmpeg — [install instructions](https://ffmpeg.org/download.html)

## Installation

```bash
# Create virtual environment
python3 -m venv .venv

# Install project in development mode
.venv/bin/pip install -e .
```

## Usage

### Convert video to audio

```bash
# Convert with default output (same directory, .mp3 extension)
.venv/bin/video-transcribe convert video.mp4

# Convert with custom output path
.venv/bin/video-transcribe convert video.mp4 -o output/audio.mp3
```

Output format: MP3, 16 kHz, mono (optimized for OpenAI API).

### Transcribe audio to text

```bash
# Basic transcription
.venv/bin/video-transcribe transcribe meeting.mp3

# With speaker diarization
.venv/bin/video-transcribe transcribe meeting.mp3 -m gpt-4o-transcribe-diarize

# With context prompt (for technical terms, acronyms)
.venv/bin/video-transcribe transcribe tutorial.mp3 -p "Technical terms: API, microservices, DevOps"

# Specify language
.venv/bin/video-transcribe transcribe meeting.mp3 -l ru

# Save to file
.venv/bin/video-transcribe transcribe meeting.mp3 -o transcript.txt

# Large files are automatically chunked (progress shown)
.venv/bin/video-transcribe transcribe large-meeting.mp3
# Output: Processing chunk 1/3...
#         Processing chunk 2/3...
#         Processing chunk 3/3...
```

**Available models:**

- `gpt-4o-transcribe` — OpenAI (supports prompt for context)
- `gpt-4o-transcribe-diarize` — OpenAI (speaker diarization, no prompt)
- `glm-asr-2512` — Z.AI (default, cheaper, no diarization)

**Large file support:** Files are automatically split into chunks with overlap:

- **OpenAI:** Size-based chunking (>20MB) with 2s overlap
- **Z.AI:** Duration-based chunking (>30s) with 2s overlap

Chunks are processed sequentially with progress indication, then merged with adjusted timestamps. Speaker labels are renumbered across chunks (A,B → A,B,C,D).

### Process video to text (one step)

```bash
# Basic - video directly to text
.venv/bin/video-transcribe process meeting.mp4

# With speaker diarization
.venv/bin/video-transcribe process meeting.mp4 -m gpt-4o-transcribe-diarize -f diarized_json

# With context prompt
.venv/bin/video-transcribe process tutorial.mp4 -p "Technical terms: API, microservices"

# Specify language
.venv/bin/video-transcribe process meeting.mp4 -l ru

# Keep audio for debugging
.venv/bin/video-transcribe process meeting.mp4 --keep-audio

# Custom output path
.venv/bin/video-transcribe process meeting.mp4 -o transcripts/meeting.txt
```

### Post-processing with LLM

```bash
# IT meeting summary (files saved next to video)
.venv/bin/video-transcribe process meeting.mp4 --postprocess
# Creates: meeting.mp4.txt + meeting.mp4.summary.md

# Screencast cleanup (tutorial format)
.venv/bin/video-transcribe process tutorial.mp4 --postprocess --preset screencast
# Creates: tutorial.mp4.txt + tutorial.mp4.screencast.md

# Save markdown files to separate directory
.venv/bin/video-transcribe process meeting.mp4 --postprocess --postprocess-dir ./summaries
# Creates: meeting.mp4.txt (next to video) + summaries/meeting.mp4.summary.md

# With OUTPUT_DIR environment variable
OUTPUT_DIR=./docs .venv/bin/video-transcribe process meeting.mp4 --postprocess
# Creates: meeting.mp4.txt (next to video) + docs/meeting.mp4.summary.md

# Full example with all options
.venv/bin/video-transcribe process standup.mp4 \
  -m gpt-4o-transcribe-diarize \
  -l ru \
  --postprocess \
  --preset meeting \
  --postprocess-dir ./summaries

# AI-suggested filenames (enabled by default)
.venv/bin/video-transcribe process meeting.mp4 --postprocess
# LLM may suggest: "Сводка встречи по Тест звука.md" instead of "meeting.mp4.summary.md"
# Use --no-smart-filename to disable
```

**Available presets:**

- `meeting` — structured meeting summary with action items
- `screencast` — convert screencast to structured tutorial

**AI-suggested filenames:**
When `--postprocess` is enabled, the LLM can suggest descriptive filenames (e.g., "Инструкция по удалению тикета.md" instead of "video.mp4.summary.md"). This is **enabled by default** — use `--no-smart-filename` to use standard naming.

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

### Speech-to-text provider selection

The tool supports multiple speech-to-text providers via `SPEECH_TO_TEXT_PROVIDER`:

| Provider           | Model                       | Limits             | Diarization | Price          |
| ------------------ | --------------------------- | ------------------ | ----------- | -------------- |
| **Z.AI** (default) | glm-asr-2512                | 30s duration, 25MB | ❌ No       | ~$0.0024/min   |
| **OpenAI**         | gpt-4o-transcribe           | 25MB file          | ❌ No       | Standard rate  |
| **OpenAI**         | gpt-4o-transcribe-diarize   | 25MB file          | ✅ Yes      | Premium rate   |
| **NeMo** (local)   | nvidia/parakeet-tdt-0.6b-v3 | None (local)       | ✅ Yes      | Free (offline) |

**Configuration:**

```bash
SPEECH_TO_TEXT_PROVIDER=zai  # or "openai" or "nemo"
SPEECH_TO_TEXT_API_KEY=your_api_key_here
SPEECH_TO_TEXT_BASE_URL=https://api.z.ai/api/paas/v4  # optional
SPEECH_TO_TEXT_MODEL=glm-asr-2512  # optional
```

### Optional settings

**Chunking (for fine-tuning large file handling):**

- `CHUNK_MAX_SIZE_MB=20` — Max chunk size for OpenAI (default: 20)
- `CHUNK_MAX_DURATION_SEC=30` — Max chunk duration for Z.AI (default: 30)
- `CHUNK_OVERLAP_SEC=2.0` — Overlap between chunks in seconds (default: 2.0)

**Post-processing:**

- `OUTPUT_DIR` — Directory for markdown files (default: same as video)
- `POSTPROCESS_API_KEY` — LLM API key (defaults to SPEECH_TO_TEXT_API_KEY)
- `POSTPROCESS_BASE_URL` — OpenAI-compatible API for post-processing
- `POSTPROCESS_MODEL` — Model name (default: gpt-5-mini)
  - Examples: gpt-5-mini, gpt-4o-mini, gpt-4o, glm-4.7, llama-3.1-70b
- `POSTPROCESS_TEMPERATURE` — Sampling temperature (default: 0.3)

**Legacy (deprecated, use SPEECH*TO_TEXT*\* above):**

- `OPENAI_API_KEY` — for OpenAI transcription
- `ZAI_API_KEY` — for ZAI transcription
