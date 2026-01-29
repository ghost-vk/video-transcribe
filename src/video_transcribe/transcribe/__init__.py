"""Speech-to-text transcription module."""

from video_transcribe.transcribe.adapter import OpenAIAdapter
from video_transcribe.transcribe.glm_asr_client import GLMASRClient
from video_transcribe.transcribe.nemo_client import NeMoClient
from video_transcribe.transcribe.factory import create_speech_to_text, SpeechToTextClient
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
    "GLMASRClient",
    "NeMoClient",
    # Factory
    "create_speech_to_text",
    "SpeechToTextClient",
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
