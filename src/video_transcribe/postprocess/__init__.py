"""Post-processing module for transforming transcripts.

This module provides LLM-based transformation of transcription results
into structured summaries, tutorials, and other formats.

Example:
    >>> from video_transcribe.postprocess import TextProcessor, PromptPreset
    >>> processor = TextProcessor()
    >>> result = processor.process(transcript, PromptPreset.IT_MEETING_SUMMARY)
    >>> print(result.raw_output)
"""

from video_transcribe.postprocess.client import LLMClient, GLMClient  # GLMClient is alias
from video_transcribe.postprocess.processor import (
    TextProcessor,
    save_postprocess_result,
)
from video_transcribe.postprocess.prompts import PromptPreset, list_presets
from video_transcribe.postprocess.models import PostprocessResult
from video_transcribe.postprocess.exceptions import (
    PostprocessError,
    GLMClientError,
    PromptTemplateError,
    FilenameError,
)
from video_transcribe.postprocess import filename

__all__ = [
    "LLMClient",
    "GLMClient",  # Backward compatibility alias
    "TextProcessor",
    "PromptPreset",
    "PostprocessResult",
    "save_postprocess_result",
    "list_presets",
    "PostprocessError",
    "GLMClientError",
    "PromptTemplateError",
    "FilenameError",
    "extract_filename_from_response",
    "strip_filename_marker",
    "sanitize_filename",
    "validate_filename",
    "generate_safe_filename",
]
