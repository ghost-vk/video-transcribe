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
```

**Available models:**
- `gpt-4o-transcribe` — supports prompt parameter for context
- `gpt-4o-transcribe-diarize` — speaker diarization (no prompt support)

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required API keys:
- `OPENAI_API_KEY` — for Whisper transcription
- `GLM_API_KEY` — for GLM 4.7 summarization
- `ZAI_API_KEY` — optional, for alternative transcription
