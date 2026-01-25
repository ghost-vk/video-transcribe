# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Video Transcribe is a Python CLI tool for automated video transcription with speaker diarization and meeting summaries. It's designed for processing IT meeting recordings (Google Meet/Zoom → OBS) and generating structured follow-ups in Russian with IT context.

## Development Commands

```bash
# Setup
python3 -m venv .venv
.venv/bin/pip install -e .

# Run CLI
.venv/bin/video-transcribe convert video.mp4
.venv/bin/video-transcribe convert video.mp4 -o output/audio.mp3
.venv/bin/video-transcribe transcribe meeting.mp3
.venv/bin/video-transcribe transcribe meeting.mp3 -m gpt-4o-transcribe-diarize -l ru

# Entry point: src/video_transcribe/__main__.py:main
```

## Architecture

The project follows a modular pipeline architecture:

```
Video → Audio → Chunking → Transcription (with diarization) →
Merge → Context Injection → Markdown output
```

**Planned module structure:**
- `src/video_transcribe/audio/` — Audio extraction and chunking (FFmpeg/PyDub)
- `src/video_transcribe/transcribe/` — Adapter pattern for multiple ASR services
- `src/video_transcribe/summary/` — LLM-based meeting summarization
- `src/video_transcribe/cli.py` — Click-based CLI interface

## Key Technical Decisions

**Audio Format:** MP3, 16kHz mono — optimized for OpenAI API ingestion (defined in `config.py`)

**ASR Services:**
- Primary: OpenAI `gpt-4o-transcribe` (with prompt support, 25MB limit)
- Diarization: OpenAI `gpt-4o-transcribe-diarize` (speaker labels, no prompt)
- Alternative (planned): ZAI GLM-ASR-2512 (cheaper, no diarization, 30-sec chunks)

**Summarization:** GLM 4.7 via OpenAI-compatible API

**CLI Framework:** Click (chosen over Typer/rich-cli)

## Configuration

Environment variables (`.env`):
- `OPENAI_API_KEY` — Whisper transcription
- `ZAI_API_KEY` — Alternative ASR
- `GLM_API_KEY` — GLM 4.7 summarization
- `GLM_BASE_URL` — Default: `https://open.bigmodel.cn/api/paas/v4`

## Current Status (Phase 3: MVP)

**Implemented:**
- Video to audio conversion (`audio/converter.py`)
- Transcription adapter with OpenAI (`transcribe/adapter.py`)
  - `gpt-4o-transcribe` — supports prompt for context
  - `gpt-4o-transcribe-diarize` — speaker diarization
- CLI with `convert` and `transcribe` commands
- `.env` support via `python-dotenv`

**Pending:**
- Audio chunking for API limits (25MB)
- Summary module (GLM 4.7)
- ZAI alternative implementation
- Tests

## System Dependencies

**FFmpeg** must be installed on the system. The converter will raise `RuntimeError` if FFmpeg is not found.

## Code Conventions

- Python 3.11+ with type annotations
- Functions raise descriptive exceptions (`FileNotFoundError`, `RuntimeError`)
- Type hints use `|` union syntax (e.g., `str | None`)
- Docstrings follow Google style
