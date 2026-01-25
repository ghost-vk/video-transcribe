"""CLI interface for video-transcribe."""

import json
import click
from pathlib import Path

from video_transcribe.audio import video_to_audio
from video_transcribe.transcribe import OpenAIAdapter


@click.group()
def cli() -> None:
    """Video Transcribe - Automated video transcription with speaker diarization."""
    pass


@cli.command()
@click.argument(
    "audio_path",
    type=click.Path(exists=True),
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["gpt-4o-transcribe", "gpt-4o-transcribe-diarize"], case_sensitive=False),
    default="gpt-4o-transcribe",
    help="Transcription model to use.",
)
@click.option(
    "--prompt",
    "-p",
    help="Optional context prompt (NOT supported with diarize model). "
         "Useful for technical terms, acronyms, or topic context.",
)
@click.option(
    "--format",
    "-f",
    "response_format",
    type=click.Choice(["text", "json", "verbose_json", "diarized_json"], case_sensitive=False),
    default="json",
    help="Response format. 'diarized_json' requires diarize model.",
)
@click.option(
    "--language",
    "-l",
    help="Language code (e.g., 'ru', 'en'). Auto-detect if not specified.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path. If not specified, prints to stdout.",
)
@click.option(
    "--temperature",
    type=click.FloatRange(0, 1),
    default=0,
    help="Sampling temperature (0-1). Lower = more deterministic.",
)
def transcribe(
    audio_path: str,
    model: str,
    prompt: str | None,
    response_format: str,
    language: str | None,
    output: str | None,
    temperature: float,
) -> None:
    """Transcribe audio file to text using OpenAI.

    Examples:
        video-transcribe transcribe meeting.mp3
        video-transcribe transcribe meeting.mp3 -m gpt-4o-transcribe-diarize
        video-transcribe transcribe tutorial.mp3 -p "ZyntriQix, Digique Plus"
        video-transcribe transcribe meeting.mp3 -l ru -o transcript.txt
    """
    try:
        adapter = OpenAIAdapter()

        click.echo(f"Transcribing {audio_path} using {model}...")
        result = adapter.transcribe(
            audio_path=audio_path,
            model=model,  # type: ignore
            prompt=prompt,
            response_format=response_format,  # type: ignore
            language=language,
            temperature=temperature,
        )

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if response_format == "text":
                output_path.write_text(result.text, encoding="utf-8")
            else:
                output_path.write_text(
                    json.dumps({
                        "text": result.text,
                        "duration": result.duration,
                        "model": result.model_used,
                        "segments": [
                            {
                                "speaker": s.speaker,
                                "start": s.start,
                                "end": s.end,
                                "text": s.text,
                            }
                            for s in result.segments
                        ],
                    }, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

            click.echo(f"Transcription saved: {output}")
        else:
            if result.segments:
                for segment in result.segments:
                    speaker = f"[{segment.speaker}] " if segment.speaker else ""
                    click.echo(f"{speaker}{segment.text}")
            else:
                click.echo(result.text)

            click.echo(f"\n---", err=True)
            click.echo(f"Model: {result.model_used}", err=True)
            click.echo(f"Duration: {result.duration:.2f}s" if result.duration else "Duration: N/A", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


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
