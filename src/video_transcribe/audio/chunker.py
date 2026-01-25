"""Audio chunking for large files exceeding API limits."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

import ffmpeg
from pydub import AudioSegment

from video_transcribe.config import (
    CHUNK_MAX_SIZE_MB,
    CHUNK_OVERLAP_SEC,
)


@dataclass
class AudioChunk:
    """Single audio chunk with metadata for transcription."""

    path: str
    """Path to chunk file."""

    index: int
    """Zero-based chunk index (0, 1, 2, ...)."""

    start_sec: float
    """Start time in original audio (seconds)."""

    end_sec: float
    """End time in original audio (seconds)."""

    original_duration_sec: float
    """Total duration of original audio (seconds)."""

    is_temp: bool = True
    """If True, this is a temporary chunk file that should be cleaned up.
    If False, this is the original file and should NOT be deleted."""


def split_audio(
    audio_path: str,
    max_size_mb: int = CHUNK_MAX_SIZE_MB,
    overlap_sec: float = CHUNK_OVERLAP_SEC,
    scratchpad_dir: str | None = None,
) -> list[AudioChunk]:
    """Split audio file into chunks for API processing.

    Args:
        audio_path: Path to audio file to split.
        max_size_mb: Maximum size per chunk in MB (default from CHUNK_MAX_SIZE_MB).
        overlap_sec: Overlap between chunks in seconds (default from CHUNK_OVERLAP_SEC).
        scratchpad_dir: Directory for temporary chunk files.
            If None, uses system temp directory.

    Returns:
        List of AudioChunk objects ordered by index.

    Raises:
        FileNotFoundError: If audio file doesn't exist.
        RuntimeError: If audio splitting fails.
    """
    audio_file = Path(audio_path)

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Check if chunking is needed
    file_size_mb = audio_file.stat().st_size / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        # No chunking needed - return single chunk with is_temp=False
        duration = _get_audio_duration(audio_path)
        return [AudioChunk(
            path=str(audio_file),
            index=0,
            start_sec=0.0,
            end_sec=duration,
            original_duration_sec=duration,
            is_temp=False,  # Original file, should NOT be deleted
        )]

    # Load audio for splitting
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load audio file: {e}") from e

    duration_ms = len(audio)
    duration_sec = duration_ms / 1000.0

    # Calculate chunks based on time strategy
    chunks_boundaries = _split_by_time(
        audio, audio_path, duration_sec, file_size_mb, max_size_mb, overlap_sec
    )

    # Use system temp dir if not specified
    if scratchpad_dir is None:
        scratchpad = Path(tempfile.gettempdir()) / "video-transcribe-chunks"
    else:
        scratchpad = Path(scratchpad_dir)
    scratchpad.mkdir(parents=True, exist_ok=True)

    # Export chunks to files
    chunk_results: list[AudioChunk] = []
    for i, (start_ms, end_ms) in enumerate(chunks_boundaries):
        chunk_path = scratchpad / f"{audio_file.stem}_chunk_{i:03d}{audio_file.suffix}"
        chunk_audio = audio[start_ms:end_ms]

        try:
            chunk_audio.export(str(chunk_path), format="mp3")
        except Exception as e:
            # Cleanup on failure
            for existing in chunk_results:
                Path(existing.path).unlink(missing_ok=True)
            raise RuntimeError(f"Failed to export chunk {i}: {e}") from e

        chunk_results.append(AudioChunk(
            path=str(chunk_path),
            index=i,
            start_sec=start_ms / 1000.0,
            end_sec=end_ms / 1000.0,
            original_duration_sec=duration_sec,
        ))

    return chunk_results


def _split_by_time(
    audio: AudioSegment,
    audio_path: str,
    duration_sec: float,
    file_size_mb: float,
    max_size_mb: int,
    overlap_sec: float,
) -> list[tuple[int, int]]:
    """Split audio by calculating chunk duration from file size and bitrate.

    Returns list of (start_ms, end_ms) tuples.
    """
    # Calculate chunk duration based on size ratio
    chunk_duration_sec = (max_size_mb / file_size_mb) * duration_sec

    # Adjust for overlap
    chunk_duration_ms = int((chunk_duration_sec - overlap_sec) * 1000)
    overlap_ms = int(overlap_sec * 1000)

    if chunk_duration_ms <= 0:
        raise RuntimeError(
            f"Overlap ({overlap_sec}s) exceeds calculated chunk duration "
            f"({chunk_duration_sec:.2f}s). Use smaller overlap or larger max_size."
        )

    chunks: list[tuple[int, int]] = []
    start_ms = 0

    while start_ms < len(audio):
        end_ms = min(start_ms + chunk_duration_ms + overlap_ms, len(audio))
        chunks.append((start_ms, end_ms))

        # Move start forward (accounting for overlap)
        start_ms = start_ms + chunk_duration_ms

        # Avoid tiny final chunks
        if len(audio) - start_ms < chunk_duration_ms // 2:
            break

    return chunks


def _get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        probe = ffmpeg.probe(audio_path)
        return float(probe['format']['duration'])
    except Exception as e:
        raise RuntimeError(f"Failed to get audio duration: {e}") from e


def cleanup_chunks(chunks: list[AudioChunk]) -> None:
    """Delete temporary chunk files.

    Only deletes chunks where is_temp=True to avoid deleting the original file.

    Args:
        chunks: List of AudioChunk objects to clean up.
    """
    for chunk in chunks:
        if not chunk.is_temp:
            # Skip original file
            continue
        try:
            Path(chunk.path).unlink(missing_ok=True)
        except Exception:
            # Best effort cleanup
            pass
