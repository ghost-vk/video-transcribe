"""CLI interface for video-transcribe."""

import json
import click
from pathlib import Path

from video_transcribe.audio import video_to_audio
from video_transcribe.transcribe import create_speech_to_text
from video_transcribe.pipeline import process_video
from video_transcribe.postprocess import list_presets


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
        client = create_speech_to_text()

        file_size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
        if file_size_mb > 20:
            click.echo(f"Transcribing {audio_path} using {model} (chunked)...")
        else:
            click.echo(f"Transcribing {audio_path} using {model}...")

        # Progress callback for chunked processing
        def progress_callback(current: int, total: int) -> None:
            if total > 1:
                click.echo(f"  Processing chunk {current}/{total}...", err=True)

        result = client.transcribe_chunked(
            audio_path=audio_path,
            model=model,  # type: ignore
            prompt=prompt,
            response_format=response_format,  # type: ignore
            language=language,
            temperature=temperature,
            progress_callback=progress_callback,
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
    "--output",
    "-o",
    type=click.Path(),
    help="Output text file path. Default: same as video with .txt extension.",
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
    "--temperature",
    type=click.FloatRange(0, 1),
    default=0,
    help="Sampling temperature (0-1). Lower = more deterministic.",
)
@click.option(
    "--keep-audio",
    is_flag=True,
    help="Keep intermediate audio file for debugging. Saved next to video file.",
)
@click.option(
    "--postprocess",
    is_flag=True,
    help="Enable LLM post-processing (summary, cleanup, etc.).",
)
@click.option(
    "--preset",
    "-P",
    "postprocess_preset",
    type=click.Choice(list_presets(), case_sensitive=False),
    default="meeting",
    help="Preset for post-processing. Ignored if --prompt-file is specified.",
)
@click.option(
    "--smart-filename/--no-smart-filename",
    default=True,
    help="Enable AI-suggested filenames for post-processing output (default: enabled).",
)
@click.option(
    "--postprocess-dir",
    type=click.Path(),
    help="Directory for post-processing markdown files. Overrides OUTPUT_DIR env.",
)
@click.option(
    "--prompt-file",
    type=click.Path(exists=True),
    help="Path to custom prompt file (markdown with YAML frontmatter). "
         "Takes priority over --preset if both are specified.",
)
def process(
    video_path: str,
    output: str | None,
    model: str,
    prompt: str | None,
    response_format: str,
    language: str | None,
    temperature: float,
    keep_audio: bool,
    postprocess: bool,
    postprocess_preset: str,
    smart_filename: bool,
    postprocess_dir: str | None,
    prompt_file: str | None,
) -> None:
    """Transcribe video file directly to text.

    This command combines video conversion and transcription in one step.

    Examples:
        video-transcribe process meeting.mp4
        video-transcribe process meeting.mp4 -o transcript.txt
        video-transcribe process meeting.mp4 -m gpt-4o-transcribe-diarize
        video-transcribe process meeting.mp4 --keep-audio
        video-transcribe process meeting.mp4 -l ru
        video-transcribe process tutorial.mp4 --postprocess --preset screencast
        video-transcribe process meeting.mp4 --postprocess --smart-filename
        video-transcribe process meeting.mp4 --postprocess --postprocess-dir ./summaries
        video-transcribe process meeting.mp4 --postprocess --prompt-file ./prompts/custom.md
    """
    try:
        click.echo(f"Processing {video_path}...")

        if keep_audio:
            click.echo("Audio will be saved for debugging.", err=True)

        # Progress callback for chunked processing
        def progress_callback(current: int, total: int) -> None:
            if total > 1:
                click.echo(f"  Processing chunk {current}/{total}...", err=True)

        result = process_video(
            video_path=video_path,
            output_path=output,
            model=model,  # type: ignore
            prompt=prompt,
            response_format=response_format,  # type: ignore
            language=language,
            temperature=temperature,
            keep_audio=keep_audio,
            progress_callback=progress_callback,
            postprocess=postprocess,
            postprocess_preset=postprocess_preset,
            smart_filename=smart_filename,
            postprocess_dir=postprocess_dir,
            prompt_file=prompt_file,
        )

        click.echo(f"Transcription saved: {Path(result.output_path).resolve()}")
        if result.audio_path:
            click.echo(f"Audio saved: {Path(result.audio_path).resolve()}")
        if result.postprocess:
            click.echo(f"Post-process saved: {Path(result.postprocess.output_path).resolve()}", err=True)

        click.echo(f"---", err=True)
        click.echo(f"Model: {result.transcript.model_used}", err=True)
        click.echo(f"Duration: {result.transcript.duration:.2f}s" if result.transcript.duration else "Duration: N/A", err=True)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
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
