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
- `gpt-4o-transcribe` — supports prompt parameter for context
- `gpt-4o-transcribe-diarize` — speaker diarization (no prompt support)

**Large file support:** Files exceeding 20MB are automatically split into chunks with overlap, processed sequentially, and merged with adjusted timestamps. Speaker labels are renumbered across chunks (A,B → A,B,C,D).

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

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Required API keys:
- `OPENAI_API_KEY` — for Whisper transcription
- `GLM_API_KEY` — for GLM 4.7 summarization
- `ZAI_API_KEY` — optional, for alternative transcription

Optional chunking settings (for fine-tuning large file handling):
- `CHUNK_MAX_SIZE_MB=20` — Safe margin from 25MB API limit (default: 20)
- `CHUNK_OVERLAP_SEC=2.0` — Overlap between chunks in seconds (default: 2.0)
