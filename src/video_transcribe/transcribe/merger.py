"""Merge transcription results from multiple audio chunks."""

from video_transcribe.transcribe.models import (
    TranscriptionResult,
    TranscriptionSegment,
)


def merge_results(
    results: list[TranscriptionResult],
    chunk_offsets: list[float],  # Start time of each chunk in original audio
    has_diarization: bool = False,
) -> TranscriptionResult:
    """Merge multiple transcription results into one.

    Handles timestamp adjustment and speaker renumbering for diarization.

    Args:
        results: List of TranscriptionResult objects from each chunk.
        chunk_offsets: Start time in seconds for each chunk (same order as results).
        has_diarization: True if results contain speaker diarization.

    Returns:
        Merged TranscriptionResult with adjusted timestamps and speakers.

    Raises:
        ValueError: If results and chunk_offsets length mismatch.
    """
    if len(results) != len(chunk_offsets):
        raise ValueError(
            f"Results count ({len(results)}) must match offsets count ({len(chunk_offsets)})"
        )

    if not results:
        raise ValueError("At least one result required for merging")

    # Merge all segments
    all_segments: list[TranscriptionSegment] = []
    for result, offset in zip(results, chunk_offsets):
        for segment in result.segments:
            # Adjust timestamps (handle None values)
            adjusted_start = segment.start + offset if segment.start is not None else None
            adjusted_end = segment.end + offset if segment.end is not None else None
            adjusted_segment = TranscriptionSegment(
                speaker=segment.speaker,
                start=adjusted_start,
                end=adjusted_end,
                text=segment.text,
            )
            all_segments.append(adjusted_segment)

    # Sort by timestamp
    all_segments.sort(key=lambda s: s.start)

    # Renumber speakers if diarization enabled
    if has_diarization:
        all_segments = _renumber_speakers(all_segments)

    # Combine text
    combined_text = " ".join(seg.text for seg in all_segments)

    # Calculate total duration
    last_duration = results[-1].duration if results[-1].duration is not None else 0.0
    total_duration = chunk_offsets[-1] + last_duration

    # Use model from first result
    model_used = results[0].model_used
    response_format = results[0].response_format

    return TranscriptionResult(
        text=combined_text,
        duration=total_duration,
        segments=all_segments,
        model_used=model_used,
        response_format=response_format,
    )


def _renumber_speakers(segments: list[TranscriptionSegment]) -> list[TranscriptionSegment]:
    """Renumber speakers to maintain global consistency across chunks.

    Problem: Each chunk has "Speaker A", "Speaker B", etc.
    Solution: Detect when a new chunk starts and renumber subsequent speakers.

    Algorithm:
    1. Track speakers seen so far (set of speaker IDs)
    2. When encountering "Speaker A" after "Speaker B/C": likely new chunk boundary
    3. Assign new IDs (Speaker C, D, E, ...) for speakers in new chunk
    4. Update all segments with renumbered speakers

    Args:
        segments: Segments sorted by timestamp with chunk overlaps.

    Returns:
        Segments with renumbered speaker labels.
    """
    if not segments:
        return segments

    # Map from original speaker ID to renumbered ID
    speaker_map: dict[str, str] = {}
    next_speaker_num = ord('A')  # Start with 'A'

    # Track last speaker to detect chunk boundaries
    last_speaker: str | None = None

    for segment in segments:
        original_speaker = segment.speaker
        if original_speaker is None:
            continue

        # Check if this is a chunk boundary (speaker reset to A after B/C)
        # When we see "A" again after seeing other speakers, it's a new chunk
        if last_speaker and last_speaker != 'A' and original_speaker == 'A':
            # New chunk detected - clear the speaker map to start renumbering
            # The next speaker will get the next available letter
            speaker_map.clear()

        # Renumber speaker if not already mapped
        if original_speaker not in speaker_map:
            # Generate speaker ID (A, B, ..., Z, AA, AB, ...)
            if next_speaker_num <= ord('Z'):
                new_id = chr(next_speaker_num)
                next_speaker_num += 1
            else:
                # After Z, use AA, AB, AC, ...
                idx = next_speaker_num - ord('A')
                new_id = chr(ord('A') + idx // 26 - 1) + chr(ord('A') + idx % 26)
                next_speaker_num += 1
            speaker_map[original_speaker] = new_id

        # Update segment with renumbered speaker
        segment.speaker = speaker_map[original_speaker]
        last_speaker = original_speaker

    return segments
