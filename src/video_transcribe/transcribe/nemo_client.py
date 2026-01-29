"""NVIDIA NeMo speech recognition client for local transcription."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from video_transcribe.config import NEMO_MODEL_NAME, NEMO_DEVICE
from video_transcribe.transcribe.models import (
    ResponseFormat,
    TranscriptionResult,
    TranscriptionSegment,
)
from video_transcribe.transcribe.exceptions import (
    AudioFileNotFoundError,
    InvalidAudioFormatError,
    TranscriptionError,
)

# Supported audio formats for NeMo (via librosa/soundfile)
SUPPORTED_FORMATS = {".wav", ".mp3"}

# Default model
MODEL = "nvidia/parakeet-tdt-0.6b-v3"


class NeMoClient:
    """Local speech recognition via NVIDIA NeMo + Parakeet TDT.

    Uses NeMo's ASRModel.from_pretrained() with local inference.
    """

    SUPPORTED_FORMATS = SUPPORTED_FORMATS

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ) -> None:
        """Initialize NeMo client.

        Args:
            model_name: Model name (default: nvidia/parakeet-tdt-0.6b-v3).
            device: Device to use ("cuda" or "cpu", default: from NEMO_DEVICE env).

        Raises:
            ImportError: If NeMo dependencies are not installed.
        """
        self.model_name = model_name or NEMO_MODEL_NAME
        self.device = device or NEMO_DEVICE
        self._model = None  # Lazy loaded model

    def _get_model(self):
        """Lazy load NeMo ASR model.

        Returns:
            NeMo ASRModel instance.

        Raises:
            ImportError: If NeMo dependencies are not installed.
        """
        if self._model is None:
            try:
                import nemo.collections.asr as nemo_asr
            except ImportError as e:
                raise ImportError(
                    "NeMo dependencies not installed. "
                    "Install with: pip install -e '.[nemo]'"
                ) from e

            self._model = nemo_asr.models.ASRModel.from_pretrained(self.model_name)

        return self._model

    def transcribe(
        self,
        audio_path: str,
        prompt: str | None = None,  # noqa: ARG002  (not supported by NeMo)
        response_format: ResponseFormat = "json",
    ) -> TranscriptionResult:
        """Transcribe audio file using NeMo.

        Args:
            audio_path: Path to audio file.
            prompt: Ignored (NeMo doesn't support prompts).
            response_format: Output format (only "json" supported for NeMo).

        Returns:
            TranscriptionResult with transcribed text and segments.

        Raises:
            AudioFileNotFoundError: If audio file doesn't exist.
            InvalidAudioFormatError: If file format not supported.
            TranscriptionError: If transcription fails.
        """
        # Validate audio file exists
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise AudioFileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate format
        if audio_file.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise InvalidAudioFormatError(
                f"Unsupported format: {audio_file.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Get model and transcribe
        model = self._get_model()

        try:
            # NeMo transcribe returns a list of transcriptions (one per file)
            results = model.transcribe([audio_path])
        except Exception as e:
            raise TranscriptionError(f"NeMo transcription failed: {e}") from e

        # Parse result (first/only item in list)
        return self._parse_result(results[0] if results else "", audio_path)

    def _parse_result(self, result, audio_path: str) -> TranscriptionResult:
        """Parse NeMo transcription result.

        NeMo's transcribe() returns a list of Hypothesis objects. We extract
        the text from each hypothesis.

        Args:
            result: Hypothesis object or list of hypotheses.
            audio_path: Original audio file path (for duration).

        Returns:
            TranscriptionResult with text and segment.
        """
        # Extract text from Hypothesis object or handle string
        if hasattr(result, 'text'):
            text = result.text
        elif isinstance(result, str):
            text = result
        else:
            text = str(result)

        # Get duration from audio file
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            duration = len(audio) / 1000.0  # ms to seconds
        except Exception:
            duration = None

        # Create single segment
        segments = [
            TranscriptionSegment(
                speaker=None,
                start=0.0,
                end=duration,
                text=text,
            )
        ]

        return TranscriptionResult(
            text=text,
            duration=duration,
            segments=segments,
            model_used=self.model_name,
            response_format="json",
        )

    def transcribe_chunked(
        self,
        audio_path: str,
        model: str = MODEL,  # noqa: ARG002  (for compatibility)
        prompt: str | None = None,
        response_format: ResponseFormat = "json",
        language: str | None = None,  # noqa: ARG002  (not supported)
        temperature: float = 0,  # noqa: ARG002  (not supported)
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> TranscriptionResult:
        """Transcribe audio file with automatic chunking for large files.

        Uses size-based chunking (similar to OpenAI adapter).

        Args:
            audio_path: Path to audio file.
            model: Model to use (ignored, uses model_name from __init__).
            prompt: Ignored (NeMo doesn't support prompts).
            response_format: Output format.
            language: Ignored (NeMo auto-detects).
            temperature: Ignored (not supported by NeMo).
            progress_callback: Optional callback(current, total) for progress updates.

        Returns:
            TranscriptionResult with merged segments and adjusted timestamps.

        Raises:
            AudioFileNotFoundError: If audio file doesn't exist.
            InvalidAudioFormatError: If file format not supported.
            TranscriptionError: If transcription fails.
        """
        from video_transcribe.config import CHUNK_MAX_SIZE_MB
        from video_transcribe.audio import split_audio, cleanup_chunks, AudioChunk
        from video_transcribe.transcribe.merger import merge_results

        # Validate audio file exists and format
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise AudioFileNotFoundError(f"Audio file not found: {audio_path}")

        if audio_file.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise InvalidAudioFormatError(
                f"Unsupported format: {audio_file.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Check if chunking needed
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)

        if file_size_mb <= CHUNK_MAX_SIZE_MB:
            # No chunking needed - use standard transcription
            return self.transcribe(
                audio_path=audio_path,
                prompt=None,
                response_format=response_format,
            )

        # Chunking required
        try:
            chunks = split_audio(audio_path=audio_path)
        except Exception as e:
            raise TranscriptionError(f"Failed to split audio: {e}") from e

        try:
            # Process chunks sequentially
            results: list[TranscriptionResult] = []
            chunk_offsets: list[float] = []

            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress_callback(i + 1, len(chunks))

                result = self.transcribe(
                    audio_path=chunk.path,
                    prompt=None,
                    response_format=response_format,
                )
                results.append(result)
                chunk_offsets.append(chunk.start_sec)

            # Merge results (no diarization for NeMo)
            merged = merge_results(
                results=results,
                chunk_offsets=chunk_offsets,
                has_diarization=False,
            )

            return merged

        finally:
            # Always cleanup chunks
            cleanup_chunks(chunks)
