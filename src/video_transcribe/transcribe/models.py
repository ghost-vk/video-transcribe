"""Data models for transcription responses."""

from dataclasses import dataclass
from typing import Literal

# Model identifiers
TranscriptionModel = Literal[
    "gpt-4o-transcribe",
    "gpt-4o-transcribe-diarize",
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
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str
    duration: float
    segments: list[TranscriptionSegment]
    model_used: TranscriptionModel
    response_format: ResponseFormat
