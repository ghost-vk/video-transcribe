"""Shared fixtures for video-transcribe tests."""

import importlib
from unittest.mock import MagicMock

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def clean_config(monkeypatch: MonkeyPatch):
    """Reset config module with clean environment (no env vars set).

    This fixture clears all relevant environment variables and reloads
    the config module to ensure tests start with a known state.

    Usage:
        def test_something(clean_config):
            # Now config has default values (no env vars set)
            from video_transcribe import config
            assert config.CHUNK_MAX_SIZE_MB == 20  # Default value
    """
    # Environment variables that config.py reads
    env_vars_to_clear = [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "SPEECH_TO_TEXT_PROVIDER",
        "SPEECH_TO_TEXT_API_KEY",
        "SPEECH_TO_TEXT_BASE_URL",
        "SPEECH_TO_TEXT_MODEL",
        "CHUNK_MAX_SIZE_MB",
        "CHUNK_OVERLAP_SEC",
        "CHUNK_MAX_DURATION_SEC",
        "POSTPROCESS_API_KEY",
        "POSTPROCESS_BASE_URL",
        "POSTPROCESS_MODEL",
        "POSTPROCESS_TEMPERATURE",
        "OUTPUT_DIR",
        "ZAI_API_KEY",
        "NEMO_MODEL_NAME",
        "NEMO_DEVICE",
    ]

    # Clear all env vars to get default config values
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Import and reload config module to pick up defaults
    import video_transcribe.config
    importlib.reload(video_transcribe.config)

    return video_transcribe.config


@pytest.fixture
def mock_env(monkeypatch: MonkeyPatch):
    """Fixture to set custom environment variables before loading config.

    Usage:
        def test_with_custom_env(mock_env):
            mock_env.setenv("CHUNK_MAX_SIZE_MB", "30")
            config = mock_env.reload_config()

            assert config.CHUNK_MAX_SIZE_MB == 30

    Returns an object with setenv(), delenv(), and reload_config() methods.
    """
    class MockEnvManager:
        def __init__(self, monkeypatch_ref: MonkeyPatch):
            self.monkeypatch = monkeypatch_ref

        def setenv(self, key: str, value: str) -> None:
            """Set an environment variable."""
            self.monkeypatch.setenv(key, value)

        def delenv(self, key: str) -> None:
            """Delete an environment variable."""
            self.monkeypatch.delenv(key, raising=False)

        def reload_config(self):
            """Reload config module to pick up env changes."""
            import video_transcribe.config
            return importlib.reload(video_transcribe.config)

    return MockEnvManager(monkeypatch)


@pytest.fixture
def mock_dotenv(monkeypatch: MonkeyPatch) -> MagicMock:
    """Mock load_dotenv to prevent loading actual .env file during tests.

    This prevents tests from reading the real .env file in the project root.

    Usage:
        def test_with_mocked_dotenv(mock_dotenv):
            # load_dotenv is now mocked
            from video_transcribe import config
            # Config won't load from .env file
    """
    import sys
    mock = MagicMock()
    monkeypatch.setattr("dotenv.load_dotenv", mock)
    return mock
