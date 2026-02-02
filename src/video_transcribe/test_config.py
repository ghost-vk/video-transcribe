"""Tests for video_transcribe.config module."""

import importlib

import pytest
from _pytest.monkeypatch import MonkeyPatch


class TestValidateConfig:
    """Test suite for config.validate_config() function."""

    def test_validate_chunk_overlap_negative_raises(self, monkeypatch: MonkeyPatch) -> None:
        """Test that CHUNK_OVERLAP_SEC < 0 raises ValueError.

        Given: CHUNK_OVERLAP_SEC is set to -1.0
        When: validate_config() is called
        Then: ValueError is raised with appropriate message
        """
        # Arrange: Set invalid env var
        monkeypatch.setenv("CHUNK_OVERLAP_SEC", "-1.0")

        # Act: Reload config to pick up env change
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert: Should raise ValueError
        with pytest.raises(ValueError, match="CHUNK_OVERLAP_SEC must be non-negative"):
            config.validate_config()

    def test_validate_chunk_duration_positive(self, monkeypatch: MonkeyPatch) -> None:
        """Test that CHUNK_MAX_DURATION_SEC <= 0 raises ValueError.

        Given: CHUNK_MAX_DURATION_SEC is set to 0 (invalid)
        When: validate_config() is called
        Then: ValueError is raised with appropriate message
        """
        # Arrange: Set invalid env var
        monkeypatch.setenv("CHUNK_MAX_DURATION_SEC", "0")

        # Act: Reload config
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert: Should raise ValueError
        with pytest.raises(ValueError, match="CHUNK_MAX_DURATION_SEC must be positive"):
            config.validate_config()

    def test_validate_chunk_duration_negative_also_raises(self, monkeypatch: MonkeyPatch) -> None:
        """Test that negative CHUNK_MAX_DURATION_SEC also raises ValueError.

        This is an edge case for the <= 0 check.
        """
        # Arrange
        monkeypatch.setenv("CHUNK_MAX_DURATION_SEC", "-10")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        with pytest.raises(ValueError, match="CHUNK_MAX_DURATION_SEC must be positive"):
            config.validate_config()

    def test_validate_overlap_less_than_duration(self, monkeypatch: MonkeyPatch) -> None:
        """Test that overlap >= duration raises ValueError.

        Given: CHUNK_OVERLAP_SEC (2) >= CHUNK_MAX_DURATION_SEC (2)
        When: validate_config() is called
        Then: ValueError is raised
        """
        # Arrange: Set overlap equal to duration (invalid)
        monkeypatch.setenv("CHUNK_OVERLAP_SEC", "2.0")
        monkeypatch.setenv("CHUNK_MAX_DURATION_SEC", "2.0")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        with pytest.raises(ValueError, match="CHUNK_OVERLAP_SEC .* must be less than CHUNK_MAX_DURATION_SEC"):
            config.validate_config()

    def test_validate_overlap_greater_than_duration_raises(self, monkeypatch: MonkeyPatch) -> None:
        """Test that overlap > duration also raises ValueError."""
        # Arrange: overlap greater than duration
        monkeypatch.setenv("CHUNK_OVERLAP_SEC", "5.0")
        monkeypatch.setenv("CHUNK_MAX_DURATION_SEC", "3.0")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        with pytest.raises(ValueError, match="CHUNK_OVERLAP_SEC .* must be less than CHUNK_MAX_DURATION_SEC"):
            config.validate_config()

    def test_validate_max_size_less_than_openai_limit(self, monkeypatch: MonkeyPatch) -> None:
        """Test that CHUNK_MAX_SIZE_MB >= 25 raises ValueError.

        Given: CHUNK_MAX_SIZE_MB is set to 25 (equal to OPENAI_MAX_FILE_SIZE_MB)
        When: validate_config() is called
        Then: ValueError is raised
        """
        # Arrange: Set size equal to OpenAI limit (invalid, must be LESS)
        monkeypatch.setenv("CHUNK_MAX_SIZE_MB", "25")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        with pytest.raises(ValueError, match="CHUNK_MAX_SIZE_MB .* must be less than OPENAI_MAX_FILE_SIZE_MB"):
            config.validate_config()

    def test_validate_max_size_greater_than_limit_raises(self, monkeypatch: MonkeyPatch) -> None:
        """Test that CHUNK_MAX_SIZE_MB > 25 also raises ValueError."""
        # Arrange
        monkeypatch.setenv("CHUNK_MAX_SIZE_MB", "30")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        with pytest.raises(ValueError, match="CHUNK_MAX_SIZE_MB .* must be less than OPENAI_MAX_FILE_SIZE_MB"):
            config.validate_config()

    def test_validate_config_passes_with_valid_defaults(self, monkeypatch: MonkeyPatch) -> None:
        """Test that validate_config() passes with default valid values.

        This is a positive test case to ensure valid config doesn't raise.
        """
        # Arrange: Use valid values (or clear env to use defaults)
        monkeypatch.delenv("CHUNK_OVERLAP_SEC", raising=False)
        monkeypatch.delenv("CHUNK_MAX_DURATION_SEC", raising=False)
        monkeypatch.delenv("CHUNK_MAX_SIZE_MB", raising=False)

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert: Should not raise
        config.validate_config()  # No exception expected

    def test_validate_config_passes_with_custom_valid_values(self, monkeypatch: MonkeyPatch) -> None:
        """Test that validate_config() passes with custom valid values."""
        # Arrange: Set valid custom values
        monkeypatch.setenv("CHUNK_OVERLAP_SEC", "1.5")
        monkeypatch.setenv("CHUNK_MAX_DURATION_SEC", "60.0")
        monkeypatch.setenv("CHUNK_MAX_SIZE_MB", "20")

        # Act
        import video_transcribe.config
        config = importlib.reload(video_transcribe.config)

        # Assert
        config.validate_config()  # No exception
        assert config.CHUNK_OVERLAP_SEC == 1.5
        assert config.CHUNK_MAX_DURATION_SEC == 60.0
        assert config.CHUNK_MAX_SIZE_MB == 20
