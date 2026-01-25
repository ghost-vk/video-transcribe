"""Main entry point for video-transcribe CLI."""

from video_transcribe.cli import cli
from video_transcribe.config import validate_config


def main() -> None:
    """Entry point for the CLI."""
    # Validate configuration before running
    validate_config()
    cli()


if __name__ == "__main__":
    main()
