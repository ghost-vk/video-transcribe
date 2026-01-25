"""Video to text pipeline orchestration."""

import json
import time
from dataclasses import dataclass
from pathlib import Path

from video_transcribe.audio import video_to_audio
from video_transcribe.transcribe import OpenAIAdapter
from video_transcribe.transcribe.models import (
    TranscriptionModel,
    ResponseFormat,
    TranscriptionResult,
)

# Video file extensions to recognize
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# Scratchpad directory for temp files
SCRATCHPAD_DIR = "/tmp/claude/-home-v-gitlab-com-video-transcribe/049a38f0-fa96-4db3-9ec8-00c6724c77d9/scratchpad"


@dataclass
class ProcessResult:
    """Result of video processing pipeline."""

    video_path: str
    audio_path: str | None  # None if deleted
    transcript: TranscriptionResult
    output_path: str | None


def is_video_file(path: str) -> bool:
    """Check if file is a video by extension.

    Args:
        path: File path to check.

    Returns:
        True if file has a video extension, False otherwise.
    """
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def process_video(
    video_path: str,
    output_path: str | None = None,
    model: TranscriptionModel = "gpt-4o-transcribe",
    prompt: str | None = None,
    response_format: ResponseFormat = "json",
    language: str | None = None,
    temperature: float = 0,
    keep_audio: bool = False,
) -> ProcessResult:
    """Process video file to text transcript.

    Pipeline: video → audio → text → file

    Args:
        video_path: Path to video file.
        output_path: Path to save transcript. If None, uses video name with .txt extension.
        model: Transcription model to use.
        prompt: Optional context prompt (not supported with diarize model).
        response_format: Output format ("text", "json", "verbose_json", "diarized_json").
        language: Optional language code (e.g., "ru", "en").
        temperature: Sampling temperature (0-1).
        keep_audio: If True, keep intermediate audio file next to video.
                   If False, use temp file and delete after transcription.

    Returns:
        ProcessResult with video path, audio path (None if deleted),
        transcript result, and output path.

    Raises:
        FileNotFoundError: If video file doesn't exist.
        RuntimeError: If FFmpeg conversion fails.
        TranscriptionError: If OpenAI API call fails.
    """
    video_file = Path(video_path)

    # 1. Validate video exists
    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # 2. Determine audio output path
    if keep_audio:
        audio_path = str(video_file.with_suffix(".mp3"))
    else:
        # Use scratchpad for temp file
        timestamp = int(time.time())
        audio_path = f"{SCRATCHPAD_DIR}/video-transcribe-{timestamp}.mp3"
        Path(SCRATCHPAD_DIR).mkdir(parents=True, exist_ok=True)

    # 3. Convert video to audio
    audio_path_result = video_to_audio(video_path, audio_path)

    # 4. Transcribe audio
    adapter = OpenAIAdapter()
    transcript = adapter.transcribe(
        audio_path=audio_path_result,
        model=model,
        prompt=prompt,
        response_format=response_format,
        language=language,
        temperature=temperature,
    )

    # 5. Determine output path
    if output_path is None:
        output_path = str(video_file.with_suffix(".txt"))
    else:
        output_path = str(Path(output_path))

    # 6. Save transcript to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if response_format == "text":
        output_file.write_text(transcript.text, encoding="utf-8")
    else:
        output_file.write_text(
            json.dumps({
                "text": transcript.text,
                "duration": transcript.duration,
                "model": transcript.model_used,
                "segments": [
                    {
                        "speaker": s.speaker,
                        "start": s.start,
                        "end": s.end,
                        "text": s.text,
                    }
                    for s in transcript.segments
                ],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # 7. Cleanup temp audio if not keeping
    final_audio_path: str | None = audio_path_result
    if not keep_audio:
        Path(audio_path_result).unlink(missing_ok=True)
        final_audio_path = None

    return ProcessResult(
        video_path=video_path,
        audio_path=final_audio_path,
        transcript=transcript,
        output_path=output_path,
    )
