"""
CLI command for audio transcription.

Provides the 'yt-fts transcribe' command for transcribing audio from
YouTube videos or local files using various transcription engines.
"""

import json
from pathlib import Path

import click
from rich.console import Console

from yt_fts.transcribe import LocalWhisperEngine, OfficialCaptionEngine
from yt_fts.transcribe.schema import Transcript

# Create console instance to avoid circular import
console = Console()


@click.command(
    name="transcribe",
    help="""
    Transcribe audio from YouTube videos or local files.

    Transcription engines:
    * whisper: Local Whisper transcription (requires faster-whisper)
    * official: Download official YouTube captions (fastest, when available)

    Output formats:
    * json: Machine-readable JSON with timestamps
    * text: Plain text transcript
    * vtt: WebVTT subtitle format

    Examples:
      yt-fts transcribe --video-id dQw4w9WgXcQ --engine whisper
      yt-fts transcribe --audio-path ./audio.mp3 --engine whisper --model-size base
      yt-fts transcribe --video-id dQw4w9WgXcQ --engine official --output vtt
      yt-fts transcribe --video-id dQw4w9WgXcQ --engine whisper --language es
    """,
)
@click.option(
    "--video-id",
    "-v",
    default=None,
    help="YouTube video ID to transcribe (for official engine or to get audio)",
)
@click.option(
    "--audio-path",
    "-a",
    default=None,
    help="Path to local audio file for Whisper transcription",
)
@click.option(
    "--engine",
    "-e",
    type=click.Choice(["whisper", "official"], case_sensitive=False),
    default="official",
    show_default=True,
    help="Transcription engine to use",
)
@click.option(
    "--model-size",
    "-m",
    type=click.Choice(
        ["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"],
        case_sensitive=False,
    ),
    default="base",
    show_default=True,
    help="Whisper model size",
)
@click.option(
    "--language",
    "-l",
    default=None,
    help="Target language code (e.g., en, es). Auto-detect if not specified.",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "text", "vtt"], case_sensitive=False),
    default="json",
    show_default=True,
    help="Output format",
)
@click.option(
    "--device",
    "-d",
    type=click.Choice(["cpu", "cuda", "auto"], case_sensitive=False),
    default="cpu",
    show_default=True,
    help="Device for Whisper inference",
)
@click.option(
    "--translate",
    is_flag=True,
    help="Translate non-English audio to English (Whisper only)",
)
@click.option(
    "--save",
    "-s",
    default=None,
    help="Save transcript to file instead of stdout",
)
def transcribe(
    video_id: str | None,
    audio_path: str | None,
    engine: str,
    model_size: str,
    language: str | None,
    output: str,
    device: str,
    translate: bool,
    save: str | None,
) -> None:
    """
    Transcribe audio using the specified engine and output format.

    This command provides a unified interface for transcribing audio from
    various sources using different transcription backends.
    """
    # Validate inputs
    if engine == "official" and not video_id:
        console.print("[red]Error: --video-id is required for official engine[/red]")
        raise SystemExit(1)

    if engine == "whisper" and not audio_path and not video_id:
        console.print(
            "[red]Error: --audio-path or --video-id is required for whisper engine[/red]"
        )
        raise SystemExit(1)

    try:
        # Select and configure engine
        if engine == "whisper":
            transcriber = LocalWhisperEngine(
                model_size=model_size,
                device=device,
            )

            # Use provided audio path or download from YouTube
            source_path = audio_path
            if not source_path and video_id:
                # Download audio from YouTube
                console.print(f"[blue]Downloading audio for video {video_id}...[/blue]")
                source_path = _download_audio(video_id)
                if not source_path:
                    console.print("[red]Failed to download audio[/red]")
                    raise SystemExit(1)

            console.print(
                f"[blue]Transcribing with Whisper ({model_size} model, {device} device)...[/blue]"
            )
            if source_path is None:
                msg = "source_path is required for Whisper transcription"
                raise ValueError(msg)
            transcript = transcriber.transcribe(
                audio_path=source_path,
                video_id=video_id or "local_audio",
                language=language,
                translate=translate,
            )

        else:  # official
            official_transcriber = OfficialCaptionEngine()
            console.print(f"[blue]Fetching official captions for {video_id}...[/blue]")
            transcript = official_transcriber.transcribe(
                audio_path=source_path or video_id,
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                language=language or "en",
            )

        # Format output
        result = _format_transcript(transcript, output)

        # Save or print
        if save:
            Path(save).parent.mkdir(parents=True, exist_ok=True)
            Path(save).write_text(result, encoding="utf-8")
            console.print(f"[green]Transcript saved to: {save}[/green]")
        else:
            console.print(result)

        # Print summary
        console.print(
            f"\n[dim]Language: {transcript.language} | "
            f"Source: {transcript.source_type.value} | "
            f"Chunks: {len(transcript.chunks)}[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Transcription error: {e}[/red]")
        raise SystemExit(1)


def _download_audio(video_id: str) -> str | None:
    """
    Download audio from YouTube for transcription.

    Args:
        video_id: YouTube video ID

    Returns:
        Path to downloaded audio file, or None if failed
    """
    import tempfile

    import yt_dlp

    tmp_dir = tempfile.gettempdir()
    output_path = f"{tmp_dir}/{video_id}.m4a"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f"https://www.youtube.com/watch?v={video_id}"
            ydl.download([url])
        return output_path
    except Exception:
        return None


def _format_transcript(transcript: Transcript, output_format: str) -> str:
    """
    Format transcript for output.

    Args:
        transcript: Transcript object
        output_format: Desired output format (json, text, vtt)

    Returns:
        Formatted transcript string
    """
    if output_format == "json":
        return json.dumps(transcript.to_dict(), indent=2, ensure_ascii=False)

    if output_format == "text":
        lines = [f"# Transcript for {transcript.video_id}"]
        lines.append(f"# Language: {transcript.language}")
        lines.append(f"# Source: {transcript.source_type.value}")
        lines.append("")
        for chunk in transcript.chunks:
            timestamp = _format_timestamp(chunk.start_time)
            lines.append(f"[{timestamp}] {chunk.text}")
        return "\n".join(lines)

    if output_format == "vtt":
        lines = ["WEBVTT", ""]
        for i, chunk in enumerate(transcript.chunks, 1):
            start = _format_vtt_timestamp(chunk.start_time)
            end = _format_vtt_timestamp(chunk.end_time)
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(chunk.text)
            lines.append("")
        return "\n".join(lines)

    return ""


def _format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _format_vtt_timestamp(seconds: float) -> str:
    """Format seconds as VTT timestamp (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
