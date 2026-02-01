"""Video to text pipeline orchestration."""

import json
import tempfile
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from video_transcribe.audio import video_to_audio
from video_transcribe.transcribe import create_speech_to_text
from video_transcribe.transcribe.models import (
    TranscriptionModel,
    ResponseFormat,
    TranscriptionResult,
)
from video_transcribe.postprocess import TextProcessor, save_postprocess_result, PromptPreset
from video_transcribe.postprocess.prompts import load_prompt_file, PromptTemplate
from video_transcribe.postprocess.models import PostprocessResult
from video_transcribe.postprocess.exceptions import PostprocessError
from video_transcribe.postprocess.filename import generate_safe_filename
from video_transcribe.config import OUTPUT_DIR

# Video file extensions to recognize
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


@dataclass
class ProcessResult:
    """Result of video processing pipeline."""

    video_path: str
    audio_path: str | None  # None if deleted
    transcript: TranscriptionResult
    postprocess: PostprocessResult | None = None  # NEW: post-processing result
    output_path: str | None = None


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
    progress_callback: Callable[[int, int], None] | None = None,
    postprocess: bool = True,
    postprocess_preset: str = "meeting",
    smart_filename: bool = False,
    postprocess_dir: str | None = None,
    prompt_file: str | None = None,
) -> ProcessResult:
    """Process video file to text transcript.

    Pipeline: video → audio → text → [postprocess] → file

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
        progress_callback: Optional callback(current, total) for progress updates.
        postprocess: Enable LLM post-processing (default: True).
        postprocess_preset: Preset name - "meeting" or "screencast".
        smart_filename: Enable AI-suggested filenames for post-processing output.
        postprocess_dir: Directory for post-processing markdown files (default: None).
                        Priority: 1) this param, 2) OUTPUT_DIR env var, 3) video dir.
        prompt_file: Path to custom prompt file (markdown with YAML frontmatter).
                     Takes priority over postprocess_preset if specified.

    Returns:
        ProcessResult with video path, audio path (None if deleted),
        transcript result, optional postprocess result, and output path.

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
        # Use system temp directory for temp file
        temp_dir = Path(tempfile.gettempdir()) / "video-transcribe"
        temp_dir.mkdir(parents=True, exist_ok=True)
        audio_path = str(temp_dir / f"{video_file.stem}-{id(video_path)}.mp3")

    # 3. Convert video to audio
    audio_path_result = video_to_audio(video_path, audio_path)

    # 4. Transcribe audio with automatic chunking
    client = create_speech_to_text()
    transcript = client.transcribe_chunked(
        audio_path=audio_path_result,
        model=model,
        prompt=prompt,
        response_format=response_format,
        language=language,
        temperature=temperature,
        progress_callback=progress_callback,
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

    # 6.5. Optional post-processing
    postprocess_result: PostprocessResult | None = None

    if postprocess:
        try:
            processor = TextProcessor()

            # Load template: custom prompt file or preset
            custom_template: PromptTemplate | None = None
            preset: PromptPreset | None = None

            if prompt_file:
                custom_template = load_prompt_file(prompt_file)
                # preset remains None (not used with custom template)
            else:
                preset = PromptPreset(postprocess_preset)

            postprocess_result = processor.process(
                transcript,
                preset,
                smart_filename=smart_filename,
                custom_template=custom_template,
            )

            # Determine output path for post-processed file
            # Priority: 1) postprocess_dir param, 2) OUTPUT_DIR env var, 3) video file's directory
            markdown_output_dir: Path
            if postprocess_dir is not None:
                # CLI option takes highest priority
                markdown_output_dir = Path(postprocess_dir)
            elif OUTPUT_DIR is not None:
                # Environment variable takes second priority
                markdown_output_dir = Path(OUTPUT_DIR)
            else:
                # Default: use video file's directory (current behavior)
                markdown_output_dir = Path(video_path).parent

            if smart_filename and postprocess_result.suggested_filename:
                # Use AI-suggested filename
                default_prefix = Path(video_path).stem
                postprocess_path = generate_safe_filename(
                    postprocess_result.suggested_filename,
                    markdown_output_dir,
                    default_prefix,
                )
            else:
                # Use default naming scheme with custom output directory
                # For custom prompts, preset is None - use default for naming
                preset_for_naming = preset or PromptPreset.MEETING
                postprocess_path = save_postprocess_result(
                    output_path,  # transcript path for naming
                    preset_for_naming,
                    output_dir=markdown_output_dir,
                )

            processor.save_to_file(postprocess_result, str(postprocess_path))

        except PostprocessError as e:
            # Do NOT interrupt pipeline - transcript is already saved
            warnings.warn(f"Post-processing failed: {e}. Transcript saved successfully.")
        except Exception as e:
            warnings.warn(f"Unexpected error in post-processing: {e}")

    # 7. Cleanup temp audio if not keeping
    final_audio_path: str | None = audio_path_result
    if not keep_audio:
        Path(audio_path_result).unlink(missing_ok=True)
        final_audio_path = None

    return ProcessResult(
        video_path=video_path,
        audio_path=final_audio_path,
        transcript=transcript,
        postprocess=postprocess_result,
        output_path=output_path,
    )
