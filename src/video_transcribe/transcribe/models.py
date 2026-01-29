"""Data models for transcription responses."""

from dataclasses import dataclass
from typing import Literal

# Model identifiers
TranscriptionModel = Literal[
    "gpt-4o-transcribe",
    "gpt-4o-transcribe-diarize",
    "nvidia/parakeet-tdt-0.6b-v3",
]

ResponseFormat = Literal[
    "text",
    "json",
    "verbose_json",
    "diarized_json",
]


@dataclass
class TranscriptionSegment:
    """Single segment of transcribed text with speaker info."""
    speaker: str | None
    start: float | None
    end: float | None
    text: str


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str
    duration: float | None
    segments: list[TranscriptionSegment]
    model_used: TranscriptionModel
    response_format: ResponseFormat
