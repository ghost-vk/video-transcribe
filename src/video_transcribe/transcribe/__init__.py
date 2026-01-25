"""Speech-to-text transcription module."""

from video_transcribe.transcribe.adapter import OpenAIAdapter
from video_transcribe.transcribe.models import (
    TranscriptionModel,
    ResponseFormat,
    TranscriptionResult,
    TranscriptionSegment,
)
from video_transcribe.transcribe.exceptions import (
    TranscriptionError,
    InvalidAudioFormatError,
    FileSizeLimitError,
    PromptNotSupportedError,
    APIKeyMissingError,
    AudioFileNotFoundError,
)

__all__ = [
    # Adapters
    "OpenAIAdapter",
    # Models
    "TranscriptionModel",
    "ResponseFormat",
    "TranscriptionResult",
    "TranscriptionSegment",
    # Exceptions
    "TranscriptionError",
    "InvalidAudioFormatError",
    "FileSizeLimitError",
    "PromptNotSupportedError",
    "APIKeyMissingError",
    "AudioFileNotFoundError",
]
