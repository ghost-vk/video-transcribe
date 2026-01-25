"""Configuration constants for video-transcribe."""

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
