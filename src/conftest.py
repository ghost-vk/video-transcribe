"""Shared fixtures for tests in src/ directory.

These fixtures are specifically for tests co-located with source code.
The tests/conftest.py contains fixtures for tests in the tests/ directory.
"""

from pathlib import Path

import pytest


@pytest.fixture
def small_audio_file(tmp_path: Path) -> Path:
    """Create a small audio file for testing (no chunking needed).

    Creates a 5 second silent MP3 file (~50-100KB) that is small enough
    to not require chunking with default 20MB limit.

    Returns:
        Path: Path to the small audio file.
    """
    from pydub import AudioSegment

    audio = AudioSegment.silent(duration=5000)  # 5 seconds in ms
    audio_path = tmp_path / "small_audio.mp3"
    audio.export(str(audio_path), format="mp3")
    return audio_path


@pytest.fixture
def large_audio_file(tmp_path: Path) -> Path:
    """Create a large audio file for testing (chunking required).

    Creates a 90 second silent MP3 file (~1-2MB) that will require
    chunking with default 30 second duration limit.

    Returns:
        Path: Path to the large audio file.
    """
    from pydub import AudioSegment

    audio = AudioSegment.silent(duration=90000)  # 90 seconds in ms
    audio_path = tmp_path / "large_audio.mp3"
    audio.export(str(audio_path), format="mp3")
    return audio_path
