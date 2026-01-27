"""Z.AI GLM-ASR-2512 client for audio transcription."""

import os
from collections.abc import Callable
from pathlib import Path
from typing import Literal

import requests

from video_transcribe.transcribe.models import (
    ResponseFormat,
    TranscriptionResult,
    TranscriptionSegment,
)
from video_transcribe.transcribe.exceptions import (
    APIKeyMissingError,
    FileSizeLimitError,
    AudioFileNotFoundError,
    InvalidAudioFormatError,
    TranscriptionError,
)

# Z.AI GLM-ASR-2512 model
MODEL = "glm-asr-2512"

# Supported audio formats per Z.AI docs
SUPPORTED_FORMATS = {".wav", ".mp3"}

# Z.AI API limits
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_DURATION = 30  # seconds (for future chunking)

# Default prompt to prevent Chinese translation
DEFAULT_PROMPT = "IMPORTANT! Target Language is RUSSIAN."


class GLMASRClient:
    """Z.AI GLM-ASR-2512 client for audio transcription.

    Uses direct HTTP requests to Z.AI API (not OpenAI-compatible).
    """

    BASE_URL = "https://api.z.ai/api/paas/v4"
    ENDPOINT = "/audio/transcriptions"
    SUPPORTED_FORMATS = SUPPORTED_FORMATS
    MAX_FILE_SIZE = MAX_FILE_SIZE
    MAX_DURATION = MAX_DURATION

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        """Initialize Z.AI GLM-ASR-2512 client.

        Args:
            api_key: Z.AI API key. If None, reads from SPEECH_TO_TEXT_API_KEY env var.
            base_url: Base URL for Z.AI API. Defaults to https://api.z.ai/api/paas/v4.

        Raises:
            APIKeyMissingError: If API key not provided and not in environment.
        """
        if api_key is None:
            api_key = os.getenv("SPEECH_TO_TEXT_API_KEY") or os.getenv("ZAI_API_KEY")

        if not api_key:
            raise APIKeyMissingError(
                "Z.AI API key not found. Set SPEECH_TO_TEXT_API_KEY or ZAI_API_KEY "
                "environment variable or pass api_key parameter."
            )

        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL

    def transcribe(
        self,
        audio_path: str,
        prompt: str | None = DEFAULT_PROMPT,
        response_format: ResponseFormat = "json",
    ) -> TranscriptionResult:
        """Transcribe audio file using Z.AI GLM-ASR-2512 API.

        Args:
            audio_path: Path to audio file (.wav or .mp3, ≤25 MB, ≤30 seconds).
            prompt: Optional prompt for context. Defaults to Russian language prompt
                to prevent Chinese translation.
            response_format: Output format (only "json" supported for Z.AI).

        Returns:
            TranscriptionResult with transcribed text and fake segments for compatibility.

        Raises:
            AudioFileNotFoundError: If audio file doesn't exist.
            InvalidAudioFormatError: If file format not supported (.wav or .mp3).
            FileSizeLimitError: If file exceeds 25 MB limit.
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

        # Validate file size
        file_size = audio_file.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise FileSizeLimitError(
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds limit "
                f"({self.MAX_FILE_SIZE / (1024 * 1024)} MB)."
            )

        # Build request
        url = f"{self.base_url}{self.ENDPOINT}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        payload = {
            "model": MODEL,
            "stream": "false",
        }

        # Add prompt if provided (default prevents Chinese translation)
        if prompt:
            payload["prompt"] = prompt

        # Make request
        try:
            with open(audio_path, "rb") as f:
                files = {"file": (audio_file.name, f, "audio/mpeg")}
                response = requests.post(url, data=payload, files=files, headers=headers)
        except Exception as e:
            raise TranscriptionError(f"Failed to read audio file: {e}") from e

        # Handle errors
        if response.status_code == 401:
            raise APIKeyMissingError(f"Z.AI API key is invalid: {response.text}")
        elif response.status_code == 413:
            raise FileSizeLimitError(f"File too large for Z.AI API: {response.text}")
        elif response.status_code == 400:
            raise InvalidAudioFormatError(f"Invalid audio format for Z.AI API: {response.text}")
        elif response.status_code != 200:
            raise TranscriptionError(f"Z.AI API error ({response.status_code}): {response.text}")

        # Parse response
        try:
            data = response.json()
        except Exception as e:
            raise TranscriptionError(f"Failed to parse Z.AI API response: {e}") from e

        return self._parse_response(data)

    def transcribe_chunked(
        self,
        audio_path: str,
        model: str = MODEL,  # noqa: ARG002  (for compatibility with OpenAIAdapter)
        prompt: str | None = None,
        response_format: ResponseFormat = "json",
        language: str | None = None,  # noqa: ARG002  (not supported by Z.AI)
        temperature: float = 0,  # noqa: ARG002  (not supported by Z.AI)
        progress_callback: Callable[[int, int], None] | None = None,  # noqa: ARG002
    ) -> TranscriptionResult:
        """Transcribe audio file (compatibility wrapper for OpenAIAdapter interface).

        Note: Z.AI doesn't support chunking in this MVP. This method calls transcribe()
        directly. Chunking will be implemented in a future version.

        Args:
            audio_path: Path to audio file.
            model: Model to use (ignored, always glm-asr-2512).
            prompt: Optional prompt for context. Defaults to Russian language prompt
                to prevent Chinese translation.
            response_format: Output format.
            language: Language code (ignored, Z.AI auto-detects).
            temperature: Sampling temperature (ignored, not supported by Z.AI).
            progress_callback: Progress callback (ignored, no chunking).

        Returns:
            TranscriptionResult with transcribed text.
        """
        # Use default prompt if None to prevent Chinese translation
        if prompt is None:
            prompt = DEFAULT_PROMPT

        return self.transcribe(
            audio_path=audio_path,
            prompt=prompt,
            response_format=response_format,
        )

    def _parse_response(self, response: dict) -> TranscriptionResult:
        """Parse Z.AI API response into TranscriptionResult.

        Z.AI response format:
        {
            "id": "task-id",
            "created": 1706232000,
            "request_id": "uuid",
            "model": "glm-asr-2512",
            "text": "transcribed text"
        }

        Note: Z.AI doesn't provide duration or segments, so we create fake segments
        for compatibility with merge_results() and post-processing.
        """
        text = response.get("text", "")

        # Create fake segment for compatibility
        segments = [
            TranscriptionSegment(
                speaker=None,
                start=0.0,
                end=None,  # Duration not available from Z.AI
                text=text,
            )
        ]

        return TranscriptionResult(
            text=text,
            duration=None,  # Not provided by Z.AI
            segments=segments,
            model_used=MODEL,
            response_format="json",
        )
