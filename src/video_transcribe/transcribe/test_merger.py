"""Tests for video_transcribe.transcribe.merger module."""

import pytest

from video_transcribe.transcribe.merger import merge_results
from video_transcribe.transcribe.models import (
    TranscriptionResult,
    TranscriptionSegment,
)


class TestSpeakerRenumberingTwoChunks:
    """Test suite for speaker renumbering across two chunks."""

    def test_speaker_renumbering_two_chunks(self) -> None:
        """Test speaker renumbering across two chunks.

        Given: Two chunks with speakers A,B each
        When: merge_results() is called with has_diarization=True
        Then: Second chunk's A,B are renumbered to C,D

        Chunk 1: A,B
        Chunk 2: A,B (new chunk, so A,B → C,D)
        Result:  A,B,C,D
        """
        # Arrange: Create two chunks with A,B pattern
        chunk1 = TranscriptionResult(
            text="Hello from chunk 1",
            duration=10.0,
            segments=[
                TranscriptionSegment(speaker='A', start=0.0, end=5.0, text='Hi A'),
                TranscriptionSegment(speaker='B', start=5.0, end=10.0, text='Hi B'),
            ],
            model_used='gpt-4o-transcribe-diarize',
            response_format='diarized_json',
        )
        chunk2 = TranscriptionResult(
            text="Hello from chunk 2",
            duration=10.0,
            segments=[
                TranscriptionSegment(speaker='A', start=0.0, end=5.0, text='Hello A'),
                TranscriptionSegment(speaker='B', start=5.0, end=10.0, text='Hello B'),
            ],
            model_used='gpt-4o-transcribe-diarize',
            response_format='diarized_json',
        )

        # Act
        result = merge_results([chunk1, chunk2], [0.0, 10.0], has_diarization=True)

        # Assert: First chunk A,B unchanged; second chunk A,B → C,D
        assert len(result.segments) == 4
        assert result.segments[0].speaker == 'A'
        assert result.segments[1].speaker == 'B'
        assert result.segments[2].speaker == 'C'
        assert result.segments[3].speaker == 'D'


class TestSpeakerRenumberingManyChunks:
    """Test suite for speaker renumbering across many chunks."""

    def test_speaker_renumbering_many_chunks(self) -> None:
        """Test speaker renumbering across many chunks.

        Given: Three chunks with A,B pattern repeating
        When: merge_results() is called with has_diarization=True
        Then: Speakers are renumbered sequentially across all chunks

        Chunk 1: A,B
        Chunk 2: A,B → C,D
        Chunk 3: A,B → E,F
        Result:  A,B,C,D,E,F
        """
        # Arrange: Create 3 chunks with A,B pattern
        chunks = []
        for i in range(3):
            chunks.append(
                TranscriptionResult(
                    text=f"Chunk {i}",
                    duration=10.0,
                    segments=[
                        TranscriptionSegment(
                            speaker='A', start=0.0, end=5.0, text=f'A{i}'
                        ),
                        TranscriptionSegment(
                            speaker='B', start=5.0, end=10.0, text=f'B{i}'
                        ),
                    ],
                    model_used='gpt-4o-transcribe-diarize',
                    response_format='diarized_json',
                )
            )

        # Act
        offsets = [0.0, 10.0, 20.0]
        result = merge_results(chunks, offsets, has_diarization=True)

        # Assert: Should be A,B,C,D,E,F
        speakers = [s.speaker for s in result.segments]
        assert speakers == ['A', 'B', 'C', 'D', 'E', 'F']


class TestSpeakerRenumberingBeyondZ:
    """Test suite for speaker renumbering beyond 26 speakers."""

    def test_speaker_renumbering_beyond_z(self) -> None:
        """Test speaker renumbering beyond 26 speakers.

        Given: 14 chunks with 2 speakers each (28 total speakers)
        When: merge_results() is called with has_diarization=True
        Then: Speakers go A-Z, then AA, AB, AC...

        First 26: A-Z
        Next:    AA, AB
        """
        # Arrange: Create 14 chunks × 2 speakers = 28 speakers
        chunks = []
        for i in range(14):
            chunks.append(
                TranscriptionResult(
                    text=f"Chunk {i}",
                    duration=10.0,
                    segments=[
                        TranscriptionSegment(
                            speaker='A', start=0.0, end=5.0, text=f'A{i}'
                        ),
                        TranscriptionSegment(
                            speaker='B', start=5.0, end=10.0, text=f'B{i}'
                        ),
                    ],
                    model_used='gpt-4o-transcribe-diarize',
                    response_format='diarized_json',
                )
            )

        # Act
        offsets = [i * 10.0 for i in range(14)]
        result = merge_results(chunks, offsets, has_diarization=True)

        # Assert: First 26 are A-Z, then AA, AB
        speakers = [s.speaker for s in result.segments]
        assert len(speakers) == 28

        # First 26 should be A-Z
        expected_first_26 = [chr(ord('A') + i) for i in range(26)]
        assert speakers[:26] == expected_first_26

        # Last two should be AA, AB
        assert speakers[26] == 'AA'
        assert speakers[27] == 'AB'


class TestTimestampAdjustment:
    """Test suite for timestamp adjustment with chunk offsets."""

    def test_timestamp_adjustment_with_offset(self) -> None:
        """Test that timestamps are adjusted with chunk offsets.

        Given: Two chunks with known timestamps
        When: merge_results() is called with offsets
        Then: Each segment's timestamps are adjusted by its chunk offset
        """
        # Arrange: Create two chunks with 10s duration each
        chunk1 = TranscriptionResult(
            text="First",
            duration=10.0,
            segments=[
                TranscriptionSegment(
                    speaker='A', start=0.0, end=5.0, text='First segment'
                ),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )
        chunk2 = TranscriptionResult(
            text="Second",
            duration=10.0,
            segments=[
                TranscriptionSegment(
                    speaker='A', start=0.0, end=5.0, text='Second segment'
                ),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )

        # Act: Chunk 2 starts at 10s
        result = merge_results([chunk1, chunk2], [0.0, 10.0], has_diarization=False)

        # Assert: First segment unchanged, second segment +10s offset
        assert result.segments[0].start == 0.0
        assert result.segments[0].end == 5.0
        assert result.segments[1].start == 10.0
        assert result.segments[1].end == 15.0

    def test_timestamp_adjustment_with_none_values(self) -> None:
        """Test that None timestamps are handled gracefully.

        Given: Segments with None start/end times
        When: merge_results() is called
        Then: None values are preserved
        """
        # Arrange
        chunk = TranscriptionResult(
            text="Test",
            duration=10.0,
            segments=[
                TranscriptionSegment(speaker=None, start=None, end=None, text='No time'),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )

        # Act
        result = merge_results([chunk], [0.0], has_diarization=False)

        # Assert: None values preserved
        assert result.segments[0].start is None
        assert result.segments[0].end is None


class TestMergeResultsValidation:
    """Test suite for merge_results() input validation."""

    def test_merge_results_length_mismatch_raises(self) -> None:
        """Test that mismatched results/offsets lengths raise ValueError.

        Given: results and offsets with different lengths
        When: merge_results() is called
        Then: ValueError is raised with descriptive message
        """
        # Arrange
        chunk = TranscriptionResult(
            text="Test",
            duration=10.0,
            segments=[],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )

        # Act & Assert: Mismatched lengths
        with pytest.raises(ValueError, match="Results count.*must match offsets count"):
            merge_results([chunk], [0.0, 10.0], has_diarization=False)

    def test_merge_results_empty_raises(self) -> None:
        """Test that empty results list raises ValueError.

        Given: Empty results list
        When: merge_results() is called
        Then: ValueError is raised
        """
        # Arrange: Empty lists
        results: list[TranscriptionResult] = []
        offsets: list[float] = []

        # Act & Assert
        with pytest.raises(ValueError, match="At least one result required"):
            merge_results(results, offsets, has_diarization=False)


class TestMergeResultsMetadata:
    """Test suite for merged result metadata."""

    def test_merge_results_total_duration(self) -> None:
        """Test that total duration is calculated correctly.

        Given: Multiple chunks with known durations
        When: merge_results() is called
        Then: Total duration = last_offset + last_chunk_duration
        """
        # Arrange: 3 chunks, each 10s
        chunks = []
        for i in range(3):
            chunks.append(
                TranscriptionResult(
                    text=f"Chunk {i}",
                    duration=10.0,
                    segments=[
                        TranscriptionSegment(speaker='A', start=0.0, end=5.0, text='Test'),
                    ],
                    model_used='gpt-4o-transcribe',
                    response_format='json',
                )
            )

        # Act: Offsets are 0, 10, 20
        result = merge_results(chunks, [0.0, 10.0, 20.0], has_diarization=False)

        # Assert: Total duration = 20 + 10 = 30
        assert result.duration == 30.0

    def test_merge_results_text_concatenation(self) -> None:
        """Test that text from all segments is concatenated.

        Note: merge_results() combines text from segments, not from result.text.
        The segments' text is joined with spaces.
        """
        # Arrange: Results with segments containing text
        chunk1 = TranscriptionResult(
            text="Ignored",  # This is not used for merged text
            duration=5.0,
            segments=[
                TranscriptionSegment(speaker=None, start=0.0, end=2.5, text='Hello'),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )
        chunk2 = TranscriptionResult(
            text="Ignored",  # This is not used for merged text
            duration=5.0,
            segments=[
                TranscriptionSegment(speaker=None, start=5.0, end=7.5, text='World'),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )

        # Act
        result = merge_results([chunk1, chunk2], [0.0, 5.0], has_diarization=False)

        # Assert: Text from segments is concatenated with spaces
        assert result.text == "Hello World"

    def test_merge_results_without_diarization(self) -> None:
        """Test merge without speaker diarization.

        Given: Results without speaker labels
        When: merge_results() is called with has_diarization=False
        Then: No speaker renumbering occurs
        """
        # Arrange: Results without speaker info
        chunk1 = TranscriptionResult(
            text="First",
            duration=10.0,
            segments=[
                TranscriptionSegment(speaker=None, start=0.0, end=5.0, text='First'),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )
        chunk2 = TranscriptionResult(
            text="Second",
            duration=10.0,
            segments=[
                TranscriptionSegment(speaker=None, start=0.0, end=5.0, text='Second'),
            ],
            model_used='gpt-4o-transcribe',
            response_format='json',
        )

        # Act
        result = merge_results([chunk1, chunk2], [0.0, 10.0], has_diarization=False)

        # Assert: No speaker renumbering
        assert result.segments[0].speaker is None
        assert result.segments[1].speaker is None
