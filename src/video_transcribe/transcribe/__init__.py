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
    ChunkingError,
)
from video_transcribe.transcribe.merger import merge_results

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
    "ChunkingError",
    # Merger
    "merge_results",
]
