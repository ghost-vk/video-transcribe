"""Video Transcribe - Automated video transcription with speaker diarization."""

__version__ = "0.1.0"

from video_transcribe.pipeline import process_video, is_video_file

__all__ = ["process_video", "is_video_file"]
