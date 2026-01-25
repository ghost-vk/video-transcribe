"""Configuration constants for video-transcribe."""

import os
from dotenv import load_dotenv

load_dotenv()

# Audio settings
DEFAULT_AUDIO_FORMAT: str = "mp3"
DEFAULT_AUDIO_SAMPLE_RATE: int = 16000  # kHz, recommended for Whisper API

# Transcription settings
DEFAULT_TRANSCRIPTION_MODEL: str = "gpt-4o-transcribe"
DEFAULT_TRANSCRIPTION_LANGUAGE: str | None = None  # Auto-detect
DEFAULT_TRANSCRIPTION_TEMPERATURE: float = 0  # Deterministic

# API limits
OPENAI_MAX_FILE_SIZE_MB: int = 25
OPENAI_SUPPORTED_AUDIO_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

# Chunking settings
CHUNK_MAX_SIZE_MB: int = int(os.getenv("CHUNK_MAX_SIZE_MB", "20"))
CHUNK_OVERLAP_SEC: float = float(os.getenv("CHUNK_OVERLAP_SEC", "2.0"))


def validate_config() -> None:
    """Validate configuration values.

    Call this at application startup to check config validity.

    Raises:
        ValueError: If configuration values are invalid.
    """
    if CHUNK_MAX_SIZE_MB >= OPENAI_MAX_FILE_SIZE_MB:
        raise ValueError(
            f"CHUNK_MAX_SIZE_MB ({CHUNK_MAX_SIZE_MB}) must be less than "
            f"OPENAI_MAX_FILE_SIZE_MB ({OPENAI_MAX_FILE_SIZE_MB})"
        )
    if CHUNK_OVERLAP_SEC < 0:
        raise ValueError(f"CHUNK_OVERLAP_SEC must be non-negative, got {CHUNK_OVERLAP_SEC}")
