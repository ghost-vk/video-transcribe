"""Audio processing module."""

from video_transcribe.audio.converter import video_to_audio
from video_transcribe.audio.chunker import (
    split_audio,
    split_audio_by_duration,
    cleanup_chunks,
    AudioChunk,
)

__all__ = [
    "video_to_audio",
    "split_audio",
    "split_audio_by_duration",
    "cleanup_chunks",
    "AudioChunk",
]
