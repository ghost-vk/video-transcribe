"""Transcription adapter using OpenAI API."""

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from video_transcribe.transcribe.models import (
    TranscriptionModel,
    ResponseFormat,
    TranscriptionResult,
    TranscriptionSegment,
)
from video_transcribe.transcribe.exceptions import (
    APIKeyMissingError,
    FileSizeLimitError,
    PromptNotSupportedError,
    AudioFileNotFoundError,
    InvalidAudioFormatError,
    TranscriptionError,
)

# Supported audio formats per OpenAI docs
SUPPORTED_FORMATS = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}

# File size limit: 25 MB per OpenAI API
MAX_FILE_SIZE_MB = 25

# Models
DIARIZE_MODEL = "gpt-4o-transcribe-diarize"


class OpenAIAdapter:
    """OpenAI transcription adapter using gpt-4o-transcribe models."""

    SUPPORTED_FORMATS = SUPPORTED_FORMATS
    MAX_FILE_SIZE_MB = MAX_FILE_SIZE_MB
    DIARIZE_MODEL = DIARIZE_MODEL

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.

        Raises:
            APIKeyMissingError: If API key not provided and not in environment.
        """
        load_dotenv()
        if api_key is None:
            import os
            api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise APIKeyMissingError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=api_key)

    def transcribe(
        self,
        audio_path: str,
        model: TranscriptionModel = "gpt-4o-transcribe",
        prompt: str | None = None,
        response_format: ResponseFormat = "json",
        language: str | None = None,
        temperature: float = 0,
    ) -> TranscriptionResult:
        """Transcribe audio file using OpenAI API.

        Args:
            audio_path: Path to audio file.
            model: Model to use ("gpt-4o-transcribe" or "gpt-4o-transcribe-diarize").
            prompt: Optional context prompt. NOT supported with diarize model.
            response_format: Output format ("text", "json", "verbose_json", "diarized_json").
            language: Optional language code (e.g., "ru", "en").
            temperature: Sampling temperature (0-1). Lower = more deterministic.

        Returns:
            TranscriptionResult with transcribed text and metadata.

        Raises:
            AudioFileNotFoundError: If audio file doesn't exist.
            InvalidAudioFormatError: If file format not supported.
            FileSizeLimitError: If file exceeds 25 MB limit.
            PromptNotSupportedError: If prompt provided with diarize model.
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

        # Validate file size
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise FileSizeLimitError(
                f"File size ({file_size_mb:.2f} MB) exceeds limit "
                f"({self.MAX_FILE_SIZE_MB} MB). Use chunking for larger files."
            )

        # Validate prompt compatibility
        if model == self.DIARIZE_MODEL and prompt:
            raise PromptNotSupportedError(
                f"Prompt parameter is not supported by {self.DIARIZE_MODEL}. "
                f"Use 'gpt-4o-transcribe' for prompt-based transcription."
            )

        # Validate response_format compatibility
        if response_format == "diarized_json" and model != self.DIARIZE_MODEL:
            raise InvalidAudioFormatError(
                f"response_format='diarized_json' only works with {self.DIARIZE_MODEL}"
            )

        # Open file for upload
        with open(audio_path, "rb") as audio:
            # Build API request parameters
            request_params: dict = {
                "model": model,
                "file": audio,
                "response_format": response_format,
            }

            # Add optional parameters
            if prompt and model != self.DIARIZE_MODEL:
                request_params["prompt"] = prompt

            if language:
                request_params["language"] = language

            if temperature != 0:
                request_params["temperature"] = temperature

            # Add chunking strategy for diarize
            if model == self.DIARIZE_MODEL:
                request_params["chunking_strategy"] = "auto"

            # Call API
            try:
                response = self.client.audio.transcriptions.create(**request_params)
            except Exception as e:
                raise TranscriptionError(f"OpenAI API error: {e}") from e

        # Parse response
        return self._parse_response(response, model, response_format)

    def _parse_response(
        self,
        response,
        model: TranscriptionModel,
        response_format: ResponseFormat,
    ) -> TranscriptionResult:
        """Parse OpenAI API response into TranscriptionResult."""
        if response_format == "text":
            return TranscriptionResult(
                text=str(response),
                duration=0.0,
                segments=[],
                model_used=model,
                response_format=response_format,
            )

        if response_format == "json":
            return TranscriptionResult(
                text=response.text,
                duration=getattr(response, 'duration', 0.0),
                segments=[],
                model_used=model,
                response_format=response_format,
            )

        # verbose_json and diarized_json have segments
        segments = []
        if response_format == "verbose_json":
            for seg in response.segments:
                segments.append(TranscriptionSegment(
                    speaker=None,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                ))

        elif response_format == "diarized_json":
            for seg in response.segments:
                segments.append(TranscriptionSegment(
                    speaker=seg.speaker,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                ))

        return TranscriptionResult(
            text=response.text if hasattr(response, 'text') else
                   ''.join(s.text for s in segments),
            duration=response.duration if hasattr(response, 'duration') else
                      (segments[-1].end if segments else 0.0),
            segments=segments,
            model_used=model,
            response_format=response_format,
        )
