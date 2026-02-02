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
.venv/bin/video-transcribe process meeting.mp4

# Testing
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -v
.venv/bin/pytest src/video_transcribe/test_config.py -v

# Entry point: src/video_transcribe/__main__.py:main
```

## Architecture

The project follows a modular pipeline architecture:

```
Video → Audio → Chunking → Transcription (with diarization) →
Merge → [Post-processing] → Markdown output
```

**Module structure:**
- `src/video_transcribe/audio/` — Audio extraction and chunking (FFmpeg/PyDub)
- `src/video_transcribe/transcribe/` — Adapter pattern for multiple ASR services
- `src/video_transcribe/postprocess/` — LLM-based text transformation (GLM-4.7 / gpt-5-mini)
- `src/video_transcribe/pipeline.py` — Pipeline orchestration (video → text)
- `src/video_transcribe/cli.py` — Click-based CLI interface

## Key Technical Decisions

**Audio Format:** MP3, 16kHz mono — optimized for OpenAI API ingestion (defined in `config.py`)

**Chunking Strategy:**
- **OpenAI:** Size-based chunking (>20MB) with 2s overlap
- **Z.AI:** Duration-based chunking (>30s) with 2s overlap
- Overlap is WITHIN the limit, not added on top (e.g., Z.AI: [0-30s], [28-58s], [56-86s]...)
- Speaker renumbering across chunks (A,B → A,B,C,D for new speakers in each chunk)
- Supports >26 speakers (A-Z, then AA, AB, AC...)
- Uses `tempfile.gettempdir()` for cross-platform compatibility

**ASR Services:**
- Primary: OpenAI `gpt-4o-transcribe` (with prompt support, 25MB limit)
- Diarization: OpenAI `gpt-4o-transcribe-diarize` (speaker labels, no prompt)
- Alternative: ZAI GLM-ASR-2512 (cheaper, no diarization, 30s duration limit, implemented)
- Local: NVIDIA NeMo Parakeet TDT 0.6B V3 (offline, diarization support)

**Post-processing:**
- OpenAI-compatible LLM client (configurable provider)
- Default: gpt-5-mini via OpenAI API
- Can use any OpenAI-compatible provider (GLM-4.7, etc.)
- Two presets: `meeting` and `screencast`
- Markdown files can be saved to separate directory via `OUTPUT_DIR` or `--postprocess-dir`

**CLI Framework:** Click (chosen over Typer/rich-cli)

**Testing:** pytest + pytest-mock, co-located tests

## Testing

**Framework:** pytest 8.0+ with pytest-mock 3.12+

**Structure:** Co-located tests (`test_*.py` next to source files)

**Key pattern:** For modules with env vars at import time (like `config.py`), use `importlib.reload()` after `monkeypatch.setenv()` to pick up new environment values.

```python
def test_config_validation(monkeypatch):
    monkeypatch.setenv("CHUNK_MAX_SIZE_MB", "30")
    import video_transcribe.config
    config = importlib.reload(video_transcribe.config)
    assert config.CHUNK_MAX_SIZE_MB == 30
```

**See:** `docs/TESTING.md` for complete testing guide.

## Configuration

Environment variables (`.env`):
- `SPEECH_TO_TEXT_PROVIDER` — Provider: "openai", "zai", or "nemo" (default: "zai")
- `SPEECH_TO_TEXT_API_KEY` — API key for speech-to-text (defaults to OPENAI_API_KEY or ZAI_API_KEY)
- `SPEECH_TO_TEXT_BASE_URL` — Base URL for speech-to-text API
- `SPEECH_TO_TEXT_MODEL` — Model name (default: glm-asr-2512)
- `OPENAI_API_KEY` — OpenAI API key (legacy, use SPEECH_TO_TEXT_API_KEY)
- `OUTPUT_DIR` — Directory for post-processing markdown files (default: None = video dir)
- `POSTPROCESS_API_KEY` — Post-processing LLM (defaults to OPENAI_API_KEY)
- `POSTPROCESS_BASE_URL` — Optional, for OpenAI-compatible post-processing API
- `POSTPROCESS_MODEL` — Model name (default: gpt-5-mini)
- `POSTPROCESS_TEMPERATURE` — Sampling temperature (default: 0.3)
- `CHUNK_MAX_SIZE_MB` — Max chunk size in MB (default: 20)
- `CHUNK_MAX_DURATION_SEC` — Max chunk duration in seconds (default: 30.0)
- `CHUNK_OVERLAP_SEC` — Overlap between chunks in seconds (default: 2.0)
- `NEMO_MODEL_NAME` — NeMo model name (default: nvidia/parakeet-tdt-0.6b-v3)
- `NEMO_DEVICE` — Device for NeMo: "cpu" or "cuda" (default: "cpu")

## Current Status (Phase 3: MVP)

**Implemented:**
- Video to audio conversion (`audio/converter.py`)
- Audio chunking (`audio/chunker.py`)
  - `split_audio()` — size-based chunking for OpenAI (>20MB)
  - `split_audio_by_duration()` — duration-based chunking for Z.AI (>30s)
- Transcription adapter with provider factory (`transcribe/factory.py`)
  - `create_speech_to_text()` — creates OpenAI, Z.AI, or NeMo client based on config
  - OpenAI adapter (`transcribe/adapter.py`)
  - Z.AI GLM-ASR client (`transcribe/glm_asr_client.py`)
    - `transcribe_chunked()` — automatic duration-based chunking
    - Russian language prompt to prevent Chinese translation
  - NeMo adapter (`transcribe/nemo_client.py`) — local ASR with diarization
- Result merger (`transcribe/merger.py`) — combine chunks with speaker renumbering
- Post-processing module (`postprocess/`)
  - OpenAI-compatible LLM client (configurable provider/model)
  - `meeting` preset — structured meeting summaries
  - `screencast` preset — screencast → tutorial conversion
- Pipeline orchestration (`pipeline.py`) — video → text → [postprocess]
- CLI with `convert`, `transcribe`, and `process` commands
- `.env` support via `python-dotenv`
- Test infrastructure with pytest (config.py tests implemented)

**Pending:**
- Additional tests (chunker, merger, filename per TEST_PLAN.md)

## System Dependencies

**FFmpeg** must be installed on the system. The converter will raise `RuntimeError` if FFmpeg is not found.

## Code Conventions

- Python 3.11+ with type annotations
- Functions raise descriptive exceptions (`FileNotFoundError`, `RuntimeError`)
- Type hints use `|` union syntax (e.g., `str | None`)
- Docstrings follow Google style
