"""Post-processing exceptions."""

class PostprocessError(Exception):
    """Base exception for post-processing errors."""
    pass


class GLMClientError(PostprocessError):
    """Error from GLM API call."""
    pass


class PromptTemplateError(PostprocessError):
    """Error in prompt template formatting."""
    pass


class FilenameError(PostprocessError):
    """Error in filename generation or validation."""
    pass
