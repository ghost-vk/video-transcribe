"""Factory for creating speech-to-text clients."""

import os
from typing import Union

from video_transcribe.config import (
    SPEECH_TO_TEXT_PROVIDER,
    SPEECH_TO_TEXT_API_KEY,
    SPEECH_TO_TEXT_BASE_URL,
)

from video_transcribe.transcribe.glm_asr_client import GLMASRClient
from video_transcribe.transcribe.adapter import OpenAIAdapter

SpeechToTextClient = Union[OpenAIAdapter, GLMASRClient]


def create_speech_to_text() -> SpeechToTextClient:
    """Create speech-to-text client based on SPEECH_TO_TEXT_PROVIDER.

    Returns:
        OpenAIAdapter or GLMASRClient instance.

    Raises:
        ValueError: If SPEECH_TO_TEXT_PROVIDER is invalid.
    """
    provider = SPEECH_TO_TEXT_PROVIDER.lower()

    if provider == "openai":
        # OpenAI-compatible API
        return OpenAIAdapter(api_key=SPEECH_TO_TEXT_API_KEY)
    elif provider == "zai":
        # Z.AI GLM-ASR-2512 API
        return GLMASRClient(
            api_key=SPEECH_TO_TEXT_API_KEY,
            base_url=SPEECH_TO_TEXT_BASE_URL,
        )
    else:
        raise ValueError(
            f"Invalid SPEECH_TO_TEXT_PROVIDER: {provider}. "
            f"Supported providers: openai, zai"
        )
