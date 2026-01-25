"""Text processing logic for post-processing transcripts."""

import re
from datetime import datetime
from pathlib import Path

from video_transcribe.postprocess.client import GLMClient
from video_transcribe.postprocess.prompts import get_preset, PromptPreset
from video_transcribe.postprocess.models import PostprocessResult
from video_transcribe.transcribe.models import TranscriptionResult, TranscriptionSegment
from video_transcribe.postprocess.exceptions import PromptTemplateError


class TextProcessor:
    """Transform transcription result using LLM."""

    def __init__(self, client: GLMClient | None = None) -> None:
        """Initialize processor.

        Args:
            client: GLM client. If None, creates default instance.
        """
        self.client = client or GLMClient()

    def process(
        self,
        transcript: TranscriptionResult,
        preset: PromptPreset = PromptPreset.IT_MEETING_SUMMARY,
    ) -> PostprocessResult:
        """Transform transcript using preset.

        Args:
            transcript: Transcription result to transform.
            preset: Prompt preset to use.

        Returns:
            PostprocessResult with generated text.

        Raises:
            PromptTemplateError: If template formatting fails.
            GLMClientError: If LLM call fails.
        """
        # 1. Get prompt template
        template = get_preset(preset)

        # 2. Format with transcript data
        try:
            user_prompt = self._format_prompt(template.user, transcript, preset)
        except KeyError as e:
            raise PromptTemplateError(f"Missing placeholder in template: {e}")

        # 3. Call LLM
        raw_output = self.client.complete(
            prompt=user_prompt,
            system_prompt=template.system,
        )

        # 4. Extract token usage (if available)
        input_tokens = None
        output_tokens = None

        # 5. Return result
        return PostprocessResult(
            preset_name=preset.value,
            raw_output=raw_output,
            model_used=self.client.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    def _format_prompt(
        self,
        template: str,
        transcript: TranscriptionResult,
        preset: PromptPreset,
    ) -> str:
        """Format template with transcript data.

        Supported placeholders:
        - {transcript} - full text
        - {segments} - formatted segments with speakers
        - {duration} - duration in seconds
        - {duration_minutes} - duration in minutes
        - {duration_formatted} - HH:MM:SS formatted
        - {model} - model used for transcription
        - {date} - current date

        Args:
            template: Prompt template with placeholders.
            transcript: Transcription result.
            preset: Preset being used (for context).

        Returns:
            Formatted prompt string.

        Raises:
            KeyError: If placeholder is missing from transcript data.
        """
        duration_min = transcript.duration / 60 if transcript.duration else 0

        # Format duration as HH:MM:SS
        duration_formatted = self._format_duration(transcript.duration)

        return template.format(
            transcript=transcript.text,
            segments=self._format_segments(transcript.segments),
            duration=transcript.duration,
            duration_minutes=duration_min,
            duration_formatted=duration_formatted,
            model=transcript.model_used,
            date=datetime.now().strftime("%Y-%m-%d"),
        )

    def _format_duration(self, seconds: float | None) -> str:
        """Format duration as HH:MM:SS.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string or "N/A" if seconds is None.
        """
        if seconds is None:
            return "N/A"
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _format_segments(self, segments: list[TranscriptionSegment]) -> str:
        """Format segments as readable text with timestamps and speakers.

        Args:
            segments: List of transcription segments.

        Returns:
            Formatted string with one segment per line.
        """
        lines = []
        for seg in segments:
            speaker = f"[{seg.speaker}] " if seg.speaker else ""
            timestamp = f"({seg.start:.1f}-{seg.end:.1f}) "
            lines.append(f"{timestamp}{speaker}{seg.text}")
        return "\n".join(lines)

    def save_to_file(
        self,
        result: PostprocessResult,
        output_path: str,
    ) -> None:
        """Save post-process result to markdown file.

        Args:
            result: Post-process result to save.
            output_path: Path to save file.
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(result.raw_output, encoding="utf-8")
        result.set_output_path(str(output_file))


def save_postprocess_result(
    transcript_path: str,
    preset: PromptPreset,
) -> str:
    """Generate output path for post-process result.

    Args:
        transcript_path: Original transcript file path.
        preset: Preset that was used.

    Returns:
        Output path for post-process result.

    Examples:
        >>> save_postprocess_result("meeting.mp4.txt", PromptPreset.IT_MEETING_SUMMARY)
        "meeting.mp4.summary.md"
        >>> save_postprocess_result("tutorial.mp4.txt", PromptPreset.SCREENCAST_CLEANUP)
        "tutorial.mp4.screencast.md"
    """
    path = Path(transcript_path)

    # Determine suffix based on preset
    if preset == PromptPreset.IT_MEETING_SUMMARY:
        suffix = ".summary.md"
    elif preset == PromptPreset.SCREENCAST_CLEANUP:
        suffix = ".screencast.md"
    else:
        suffix = ".processed.md"

    # Remove .txt if present, add new suffix
    if path.suffix == ".txt":
        return str(path.with_suffix(suffix))
    return str(path.with_suffix(path.suffix + suffix))
