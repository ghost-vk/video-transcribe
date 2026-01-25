"""LLM client for post-processing.

OpenAI-compatible client that supports any provider (OpenAI, GLM, etc.)
based on configuration.
"""

from openai import OpenAI, APIConnectionError, RateLimitError, APIError

from video_transcribe.config import (
    POSTPROCESS_API_KEY,
    POSTPROCESS_BASE_URL,
    DEFAULT_POSTPROCESS_MODEL,
    DEFAULT_POSTPROCESS_TEMPERATURE,
)
from video_transcribe.postprocess.exceptions import GLMClientError


class LLMClient:
    """OpenAI-compatible LLM client for post-processing.

    Supports any OpenAI-compatible API provider (OpenAI, GLM, etc.)
    based on configuration settings.

    Example:
        Using GLM-4.7:
            POSTPROCESS_API_KEY=...
            POSTPROCESS_BASE_URL=https://api.z.ai/api/coding/paas/v4
            POSTPROCESS_MODEL=glm-4.7

        Using OpenAI gpt-4o-mini:
            POSTPROCESS_API_KEY=...
            POSTPROCESS_BASE_URL=  # None uses OpenAI default
            POSTPROCESS_MODEL=gpt-4o-mini
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        """Initialize LLM client.

        Args:
            api_key: API key. Defaults to POSTPROCESS_API_KEY from config.
            base_url: Base URL for API. Defaults to POSTPROCESS_BASE_URL from config.
                      If None, uses OpenAI's default URL.
            model: Model name. Defaults to POSTPROCESS_MODEL from config.
            temperature: Sampling temperature. Defaults to POSTPROCESS_TEMPERATURE from config.

        Raises:
            GLMClientError: If API key is not set.
        """
        # Use provided values or fall back to config
        api_key = api_key or POSTPROCESS_API_KEY
        if not api_key or not api_key.strip():
            raise GLMClientError(
                "POSTPROCESS_API_KEY not set. "
                "Set POSTPROCESS_API_KEY or OPENAI_API_KEY in your .env file."
            )

        base_url = base_url if base_url is not None else POSTPROCESS_BASE_URL
        self.model = model if model is not None else DEFAULT_POSTPROCESS_MODEL
        self.temperature = temperature if temperature is not None else DEFAULT_POSTPROCESS_TEMPERATURE

        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Execute chat completion.

        Args:
            prompt: User prompt.
            system_prompt: Optional system prompt.

        Returns:
            Generated text response.

        Raises:
            GLMClientError: If API call fails.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            return response.choices[0].message.content or ""

        except APIConnectionError as e:
            raise GLMClientError(f"Failed to connect to API: {e}")
        except RateLimitError as e:
            raise GLMClientError(f"API rate limit exceeded: {e}")
        except APIError as e:
            raise GLMClientError(f"API error: {e}")
        except Exception as e:
            raise GLMClientError(f"Unexpected error: {e}")


# Backward compatibility alias
GLMClient = LLMClient
