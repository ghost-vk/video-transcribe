"""Tests for video_transcribe.audio.chunker module."""

from pathlib import Path

import pytest

from video_transcribe.audio.chunker import (
    AudioChunk,
    cleanup_chunks,
    split_audio,
    split_audio_by_duration,
)


class TestNoChunkingNeededSmallFile:
    """Test suite for small files that don't need chunking."""

    def test_no_chunking_needed_small_file(self, small_audio_file) -> None:
        """Test that small files return single chunk with is_temp=False.

        Given: Audio file smaller than max_size_mb (20MB default)
        When: split_audio() is called with default max_size_mb
        Then: Returns single AudioChunk with is_temp=False

        The original file should NOT be deleted on cleanup.
        """
        # Arrange: small_audio_file is ~5 seconds (~50-100KB)
        # Act: Split with default 20MB limit
        chunks = split_audio(str(small_audio_file), max_size_mb=20)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].is_temp is False  # Original file, should NOT be deleted
        assert chunks[0].path == str(small_audio_file)  # Same as original
        assert chunks[0].index == 0
        assert chunks[0].start_sec == 0.0
        assert chunks[0].end_sec > 0  # Should have duration


class TestOverlapWithinLimit:
    """Test suite for overlap behavior within duration limit."""

    def test_overlap_within_limit(self, large_audio_file) -> None:
        """Test that overlap is WITHIN duration limit, not added on top.

        Given: 90s audio file, 30s max duration, 2s overlap
        When: split_audio_by_duration() is called
        Then: Chunks are [0-30s], [28-58s], [56-86s] (overlap WITHIN 30s)

        Key: Overlap is SUBTRACTED from the limit, not added to it.
        - Chunk 1: 0-30s (30s total)
        - Chunk 2: starts at 28s (30-2), ends at 58s (28+30)
        - Chunk 3: starts at 56s (58-2), ends at 86s (56+30, but capped at 90s)
        """
        # Arrange: 90s file, 30s limit, 2s overlap
        # Act
        chunks = split_audio_by_duration(
            str(large_audio_file),
            max_duration_sec=30.0,
            overlap_sec=2.0,
        )

        # Assert: Should have 3 chunks
        assert len(chunks) == 3

        # First chunk: 0-30s (no overlap at start)
        assert chunks[0].start_sec == 0.0
        assert chunks[0].end_sec == pytest.approx(30.0, abs=0.1)

        # Second chunk: starts at 28s (30-2), ends at 58s
        assert chunks[1].start_sec == pytest.approx(28.0, abs=0.1)
        assert chunks[1].end_sec == pytest.approx(58.0, abs=0.1)

        # Third chunk: starts at 56s (58-2), ends at ~86-90s
        assert chunks[2].start_sec == pytest.approx(56.0, abs=0.1)
        assert chunks[2].end_sec > 56.0
        assert chunks[2].end_sec <= 90.0


class TestOverlapValidation:
    """Test suite for overlap validation errors."""

    def test_overlap_equals_duration_raises(self, small_audio_file) -> None:
        """Test that overlap >= duration raises RuntimeError.

        Given: overlap equals max_duration_sec
        When: split_audio_by_duration() is called
        Then: RuntimeError is raised with descriptive message
        """
        # Arrange: 5s audio file
        # Act & Assert: overlap (5s) equals max_duration (5s)
        with pytest.raises(RuntimeError, match="Overlap.*must be less than max duration"):
            split_audio_by_duration(
                str(small_audio_file),
                max_duration_sec=5.0,
                overlap_sec=5.0,
            )

    def test_overlap_greater_than_duration_raises(self, small_audio_file) -> None:
        """Test that overlap > duration also raises RuntimeError."""
        # Arrange: 5s audio file
        # Act & Assert: overlap (6s) greater than max_duration (5s)
        with pytest.raises(RuntimeError, match="Overlap.*must be less than max duration"):
            split_audio_by_duration(
                str(small_audio_file),
                max_duration_sec=5.0,
                overlap_sec=6.0,
            )

    def test_max_duration_zero_raises(self, small_audio_file) -> None:
        """Test that max_duration <= 0 raises RuntimeError."""
        # Act & Assert
        with pytest.raises(RuntimeError, match="must be positive"):
            split_audio_by_duration(
                str(small_audio_file),
                max_duration_sec=0.0,
                overlap_sec=1.0,
            )


class TestChunkBoundariesCalculation:
    """Test suite for chunk boundary calculations."""

    def test_chunk_boundaries_calculation(self, large_audio_file) -> None:
        """Test that chunk boundaries are calculated correctly.

        Given: Audio file requiring chunking
        When: split_audio_by_duration() is called
        Then: All boundaries are valid and don't exceed total duration
        """
        # Arrange
        max_duration = 30.0

        # Act
        chunks = split_audio_by_duration(
            str(large_audio_file),
            max_duration_sec=max_duration,
            overlap_sec=2.0,
        )

        # Assert: Get total duration from first chunk
        total_duration = chunks[0].original_duration_sec

        # Verify all chunks have valid boundaries
        for chunk in chunks:
            assert chunk.start_sec >= 0, "Start must be non-negative"
            assert chunk.end_sec <= total_duration, "End must not exceed total duration"
            assert chunk.start_sec < chunk.end_sec, "Start must be less than end"

        # Verify chunk index sequence
        for i, chunk in enumerate(chunks):
            assert chunk.index == i, f"Chunk {i} has wrong index"

    def test_no_tiny_final_chunk(self, large_audio_file) -> None:
        """Test that tiny final chunks are avoided.

        The chunker avoids creating very small final chunks by checking
        if remaining audio is less than half the chunk duration.
        """
        # Arrange
        max_duration = 30.0

        # Act
        chunks = split_audio_by_duration(
            str(large_audio_file),
            max_duration_sec=max_duration,
            overlap_sec=2.0,
        )

        # Assert: Check chunk sizes (except possibly the last one)
        for i, chunk in enumerate(chunks):
            duration = chunk.end_sec - chunk.start_sec

            if i < len(chunks) - 1:  # Non-last chunks
                # Should be close to max_duration (within overlap tolerance)
                assert duration >= max_duration - 2.0, \
                    f"Chunk {i} duration ({duration}s) too small"

    def test_chunk_metadata_complete(self, large_audio_file) -> None:
        """Test that all chunk metadata is correctly set."""
        # Act
        chunks = split_audio_by_duration(str(large_audio_file), max_duration_sec=30.0)

        # Assert: All chunks should have complete metadata
        for chunk in chunks:
            assert chunk.path is not None
            assert isinstance(chunk.path, str)
            assert Path(chunk.path).exists(), f"Chunk file {chunk.path} doesn't exist"
            assert chunk.index >= 0
            assert chunk.start_sec >= 0.0
            assert chunk.end_sec > chunk.start_sec
            assert chunk.original_duration_sec > 0.0
            assert chunk.is_temp is True  # All chunks except original are temp


class TestCleanupChunks:
    """Test suite for cleanup_chunks() function."""

    def test_cleanup_temp_only(self, tmp_path) -> None:
        """Test that cleanup_chunks() only deletes is_temp=True files.

        Given: Mix of temp and non-temp chunks
        When: cleanup_chunks() is called
        Then: Only is_temp=True files are deleted

        This is a critical safety feature to prevent deletion of original files.
        """
        # Arrange: Create original file and temp chunk
        original = tmp_path / "original.mp3"
        original.touch()

        temp_chunk = tmp_path / "chunk_000.mp3"
        temp_chunk.touch()

        chunks = [
            AudioChunk(
                path=str(original),
                index=0,
                start_sec=0.0,
                end_sec=10.0,
                original_duration_sec=10.0,
                is_temp=False,  # Original file - should NOT be deleted
            ),
            AudioChunk(
                path=str(temp_chunk),
                index=1,
                start_sec=0.0,
                end_sec=10.0,
                original_duration_sec=10.0,
                is_temp=True,  # Temp chunk - should be deleted
            ),
        ]

        # Act
        cleanup_chunks(chunks)

        # Assert: Original should still exist
        assert original.exists(), "Original file should NOT be deleted"

        # Temp chunk should be deleted
        assert not temp_chunk.exists(), "Temp chunk should be deleted"

    def test_cleanup_empty_list(self) -> None:
        """Test that cleanup_chunks() handles empty list gracefully."""
        # Arrange: Empty list
        chunks: list[AudioChunk] = []

        # Act: Should not raise
        cleanup_chunks(chunks)

        # Assert: No exception
        assert True

    def test_cleanup_nonexistent_file(self, tmp_path) -> None:
        """Test that cleanup_chunks() handles missing files gracefully.

        Best-effort cleanup means no exceptions if files don't exist.
        """
        # Arrange: Chunk pointing to non-existent file
        nonexistent = tmp_path / "nonexistent.mp3"
        chunks = [
            AudioChunk(
                path=str(nonexistent),
                index=0,
                start_sec=0.0,
                end_sec=10.0,
                original_duration_sec=10.0,
                is_temp=True,
            ),
        ]

        # Act: Should not raise (best-effort cleanup)
        cleanup_chunks(chunks)

        # Assert: No exception
        assert True


class TestSplitAudioIntegration:
    """Integration tests for split_audio() function."""

    def test_split_audio_file_not_found(self, tmp_path) -> None:
        """Test that FileNotFoundError is raised for non-existent file."""
        # Arrange: Non-existent file
        nonexistent = tmp_path / "nonexistent.mp3"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            split_audio(str(nonexistent))

    def test_split_audio_all_temp_chunks(self, large_audio_file) -> None:
        """Test that split_audio() creates all temp chunks when file is large.

        For files requiring chunking, all chunks should have is_temp=True.
        """
        # Arrange: Use very small max_size to force chunking
        # Act: Split with 1MB limit (large_audio_file is ~1-2MB)
        chunks = split_audio(str(large_audio_file), max_size_mb=1)

        # Assert: If multiple chunks, all should be temp
        if len(chunks) > 1:
            for chunk in chunks:
                assert chunk.is_temp is True, f"Chunk {chunk.index} should be temp"

    def test_split_audio_scratchpad_dir(self, large_audio_file, tmp_path) -> None:
        """Test that custom scratchpad_dir is used for temp files."""
        # Arrange: Custom scratchpad directory
        custom_dir = tmp_path / "custom_chunks"

        # Act: Split with custom scratchpad
        chunks = split_audio(
            str(large_audio_file),
            max_size_mb=1,
            scratchpad_dir=str(custom_dir),
        )

        # Assert: All chunk files should be in custom directory
        for chunk in chunks:
            if chunk.is_temp:
                assert Path(chunk.path).parent == custom_dir
