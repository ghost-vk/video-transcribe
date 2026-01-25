"""CLI interface for video-transcribe."""

import click

from video_transcribe.audio import video_to_audio


@click.group()
def cli() -> None:
    """Video Transcribe - Automated video transcription with speaker diarization."""
    pass


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--output-audio",
    "-o",
    help="Path to save the audio file. Default: same as video with .mp3 extension.",
)
def convert(video_path: str, output_audio: str | None) -> None:
    """Convert video file to audio.

    Example:
        video-transcribe convert meeting.mp4
        video-transcribe convert meeting.mp4 -o audio/meeting.mp3
    """
    try:
        result_path = video_to_audio(video_path, output_audio)
        click.echo(f"Audio saved: {result_path}")
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
