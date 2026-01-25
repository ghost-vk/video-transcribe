# Video Transcribe

Automated video transcription with speaker diarization and meeting summaries.

## Installation

```bash
# Create virtual environment
python3 -m venv .venv

# Install project in development mode
.venv/bin/pip install -e .
```

## Usage

```bash
# Run via module
.venv/bin/python -m video_transcribe

# Or via CLI command
.venv/bin/video-transcribe
```

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required API keys:
- `OPENAI_API_KEY` — for Whisper transcription
- `GLM_API_KEY` — for GLM 4.7 summarization
- `ZAI_API_KEY` — optional, for alternative transcription
