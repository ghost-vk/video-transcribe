"""Transcription-specific exceptions."""

class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass


class InvalidAudioFormatError(TranscriptionError):
    """Raised when audio format is not supported."""
    pass


class FileSizeLimitError(TranscriptionError):
    """Raised when audio file exceeds API size limit (25 MB)."""
    pass


class PromptNotSupportedError(TranscriptionError):
    """Raised when prompt provided with diarize model."""
    pass


class APIKeyMissingError(TranscriptionError):
    """Raised when OPENAI_API_KEY is not set."""
    pass


class AudioFileNotFoundError(TranscriptionError):
    """Raised when audio file doesn't exist."""
    pass


class ChunkingError(TranscriptionError):
    """Raised when audio chunking fails."""
    pass
