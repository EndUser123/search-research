"""
Transcription worker CLI commands.
"""
from __future__ import annotations

import os

import click

from yt_fts.workers.transcription_worker import get_pending_count
from yt_fts.workers.transcription_worker_loop import TranscriptionWorker
from yt_fts.utils.rich_console import get_console

from .database import get_channel_id_from_input


@click.command(
    name="transcribe-no-subs",
    help="""
            Transcribe videos marked [No Subtitles] using Whisper.

            Uses a task queue pattern - multiple workers can run in parallel.
            Each worker independently checks out videos, processes them, and checks them back in.
            Failed videos are returned to the queue for retry.
        """,
)
@click.option(
    "-c",
    "--channel",
    required=True,
    help="The name or ID of the channel to process",
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=None,
    help="Maximum number of videos to process (default: process all pending)",
)
@click.option(
    "-m",
    "--whisper-model",
    type=click.Choice(["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]),
    default="base",
    help="Whisper model size (default: base). Larger models are more accurate but slower.",
)
@click.option(
    "--keep-audio",
    is_flag=True,
    default=False,
    help="Keep audio files after transcription (for debugging)",
)
def transcribe_no_subs(
    channel: str,
    limit: int | None,
    whisper_model: str,
    keep_audio: bool,
) -> None:
    """Transcribe videos marked [No Subtitles] using Whisper task queue."""
    console = get_console()

    # Resolve channel ID
    try:
        channel_id = get_channel_id_from_input(channel)
    except ValueError as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        return 1

    # Check pending count
    pending = get_pending_count(channel_id)
    if pending == 0:
        console.print(f"[yellow]No videos pending transcription for channel: {channel}[/yellow]")
        return 0

    console.print("\n[bold]Transcription Worker[/bold]")
    console.print(f"Channel: {channel} ({channel_id})")
    console.print(f"Pending videos: {pending}")
    console.print(f"Whisper model: {whisper_model}")
    console.print(f"Worker ID: worker-{os.getpid()}")
    if limit:
        console.print(f"Limit: {limit} videos")
    console.print()

    # Run worker
    try:
        worker = TranscriptionWorker(
            channel_id=channel_id,
            whisper_model=whisper_model,
            keep_audio=keep_audio,
        )
        results = worker.run(limit=limit)

        # Report results
        console.print("\n[bold]Results:[/bold]")
        console.print(f"✓ Success: {results['success_count']}")
        console.print(f"✗ Failed: {results['failed_count']}")
        console.print(f"Total processed: {results['total_count']}")

        # Check remaining
        remaining = get_pending_count(channel_id)
        if remaining > 0:
            console.print(f"\n[yellow]Remaining pending: {remaining}[/yellow]")
            console.print("[dim]Run another worker to continue processing.[/dim]")

        return 0 if results["failed_count"] == 0 else 1

    except KeyboardInterrupt:
        console.print("\n[yellow]Transcription interrupted by user[/yellow]")
        return 130
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}")
        return 1
