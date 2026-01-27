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

# OpenAI API for transcription
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")  # Optional, uses default if None

# Speech-to-text settings (provider-agnostic)
SPEECH_TO_TEXT_PROVIDER: str = os.getenv("SPEECH_TO_TEXT_PROVIDER", "zai")  # openai | zai
SPEECH_TO_TEXT_API_KEY: str = (
    os.getenv("SPEECH_TO_TEXT_API_KEY", "")
    or os.getenv("OPENAI_API_KEY", "")
    or os.getenv("ZAI_API_KEY", "")
)
SPEECH_TO_TEXT_BASE_URL: str = os.getenv(
    "SPEECH_TO_TEXT_BASE_URL", "https://api.z.ai/api/paas/v4"
)
SPEECH_TO_TEXT_MODEL: str = os.getenv("SPEECH_TO_TEXT_MODEL", "glm-asr-2512")

# API limits
OPENAI_MAX_FILE_SIZE_MB: int = 25
OPENAI_SUPPORTED_AUDIO_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

# Chunking settings
CHUNK_MAX_SIZE_MB: int = int(os.getenv("CHUNK_MAX_SIZE_MB", "20"))
CHUNK_OVERLAP_SEC: float = float(os.getenv("CHUNK_OVERLAP_SEC", "2.0"))
CHUNK_MAX_DURATION_SEC: float = float(os.getenv("CHUNK_MAX_DURATION_SEC", "30.0"))

# Post-processing settings
POSTPROCESS_API_KEY: str = os.getenv("POSTPROCESS_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
POSTPROCESS_BASE_URL: str | None = os.getenv("POSTPROCESS_BASE_URL")  # Optional, uses default if None
DEFAULT_POSTPROCESS_MODEL: str = os.getenv("POSTPROCESS_MODEL", "gpt-5-mini")
DEFAULT_POSTPROCESS_TEMPERATURE: float = float(os.getenv("POSTPROCESS_TEMPERATURE", "0.3"))

# Legacy aliases (for backward compatibility)
GLM_API_KEY: str = POSTPROCESS_API_KEY
GLM_BASE_URL: str | None = POSTPROCESS_BASE_URL


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
    if CHUNK_MAX_DURATION_SEC <= 0:
        raise ValueError(f"CHUNK_MAX_DURATION_SEC must be positive, got {CHUNK_MAX_DURATION_SEC}")
    if CHUNK_OVERLAP_SEC >= CHUNK_MAX_DURATION_SEC:
        raise ValueError(
            f"CHUNK_OVERLAP_SEC ({CHUNK_OVERLAP_SEC}) must be less than "
            f"CHUNK_MAX_DURATION_SEC ({CHUNK_MAX_DURATION_SEC})"
        )

    # Post-process API key warning (not error - post-processing is optional)
    if not POSTPROCESS_API_KEY:
        import warnings
        warnings.warn(
            "POSTPROCESS_API_KEY not set in .env - post-processing will not be available. "
            "Set POSTPROCESS_API_KEY or OPENAI_API_KEY to enable post-processing."
        )
