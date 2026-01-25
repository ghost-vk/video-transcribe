"""Data models for post-processing results."""

from dataclasses import dataclass, field


@dataclass
class PostprocessResult:
    """Result of text transformation via LLM.

    Attributes:
        preset_name: Name of the preset that was used.
        raw_output: Raw markdown output from LLM.
        model_used: Model name that generated the output.
        input_tokens: Input tokens used (if available from API).
        output_tokens: Output tokens used (if available from API).
    """
    preset_name: str
    raw_output: str
    model_used: str
    input_tokens: int | None
    output_tokens: int | None
    _output_path: str | None = field(default=None, repr=False)

    @property
    def output_path(self) -> str | None:
        """Path where output was saved (set by caller)."""
        return self._output_path

    def set_output_path(self, path: str) -> None:
        """Set the output file path.

        Args:
            path: Path to the output file.
        """
        self._output_path = path
