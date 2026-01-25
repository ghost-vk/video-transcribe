"""Video to audio converter."""

from pathlib import Path

import ffmpeg

from video_transcribe.config import DEFAULT_AUDIO_FORMAT, DEFAULT_AUDIO_SAMPLE_RATE


def video_to_audio(video_path: str, output_path: str | None = None) -> str:
    """Convert video file to audio.

    Args:
        video_path: Path to the video file.
        output_path: Path to save the audio file. If None, saves next to the video
            with the same name and .mp3 extension.

    Returns:
        Path to the created audio file.

    Raises:
        FileNotFoundError: If video file doesn't exist.
        RuntimeError: If ffmpeg is not installed or conversion fails.
    """
    video_file = Path(video_path)

    if not video_file.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if output_path is None:
        output_path = str(video_file.with_suffix(f".{DEFAULT_AUDIO_FORMAT}"))

    try:
        (
            ffmpeg.input(video_path)
            .output(
                output_path,
                acodec="libmp3lame",
                ar=DEFAULT_AUDIO_SAMPLE_RATE,
                ac=1,  # mono
            )
            .run(overwrite_output=True, quiet=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg is not installed. Please install ffmpeg: "
            "https://ffmpeg.org/download.html"
        ) from None

    return output_path
