"""
Execution path functions for batch download operations.

Split from batch_download into separate functions for better modularity.
"""
from __future__ import annotations

from yt_fts.utils.rich_console import get_console

console = get_console()
def execute_tui_path(
    channels: list[str],
    fail_fast: bool,
) -> bool:
    """Execute the TUI (Textual UI) execution path.

    Args:
        channels: List of channel URLs
        fail_fast: If True, abort on TUI errors

    Returns:
        True if TUI executed successfully, False if it fell through to batch
    """
    try:
        from .ui.dashboard import (
            MIN_TEXTUAL_VERSION,
            GoogleStitchUI,
            is_textual_compatible,
        )

        compatible, installed = is_textual_compatible()

        if installed is None:
            console.print(
                "WARNING:  [yellow]Textual not installed or not importable.[/yellow]"
            )
            console.print(
                f'💡 Install Textual to use the interactive dashboard, e.g., `pip install "textual>={MIN_TEXTUAL_VERSION}"`'
            )
            if fail_fast:
                console.print(
                    "🛑 [red]Fail-fast enabled: aborting due to missing Textual.[/red]"
                )
                msg = "Missing required dependency: textual"
                raise RuntimeError(msg)
            console.print(
                "WARNING:  Proceeding without dashboard because degraded mode is enabled"
            )
            return False

        if not compatible:
            console.print(
                f"WARNING:  [yellow]Textual version {installed} is older than the required {MIN_TEXTUAL_VERSION}.[/yellow]"
            )
            console.print(
                f'💡 Upgrade by running: pip install "textual>={MIN_TEXTUAL_VERSION}"'
            )
            if fail_fast:
                console.print(
                    "🛑 [red]Fail-fast enabled: aborting due to incompatible Textual version.[/red]"
                )
                msg = "Incompatible Textual version"
                raise RuntimeError(msg)
            console.print(
                "WARNING:  Proceeding without dashboard because degraded mode is enabled"
            )
            return False

        console.print(f"🧭 Textual version detected: {installed}")
        console.print("🔷 Launching interactive dashboard (Textual TUI)...")
        GoogleStitchUI(channels=channels).run()
        console.print("🔷 Dashboard exited, bye!")
        return True

    except Exception as e:
        console.print(f"❌ [red]Failed to launch dashboard:[/red] {e!s}")
        if not fail_fast:
            console.print(
                "WARNING:  Proceeding with batch download due to non-fail-fast configuration"
            )
            return False
        raise


def execute_parallel_path(
    channels: list[str],
    quota_strategy,
    language: str,
    cookies_from_browser: str,
    delay: float,
    max_retries: int,
    continue_on_error: bool,
    time_per_channel: float,
    time_per_video: float,
    time_per_batch: float,
    videos_download_per_channel: int,
    videos_download_per_batch: int,
    display_plugin: str,
    auto_backfill: bool,
    freshness_hours: int,
    rich_progress: bool,
    rich_display: str,
    use_phase2: bool,
    phase2_batch_size: int,
    fzf: bool,
    parallel_workers: int,
    fail_fast: bool,
    simple: bool,
    output_format: str,
) -> bool:
    """Execute the parallel batch processing path.

    Args:
        channels: List of channel URLs
        quota_strategy: QuotaStrategy instance
        language: Language for transcription
        cookies_from_browser: Browser to use for cookies
        delay: Delay between channels
        max_retries: Maximum retry attempts
        continue_on_error: Continue on individual download errors
        time_per_channel: Timeout per channel
        time_per_video: Timeout per video
        time_per_batch: Timeout for entire batch
        videos_download_per_channel: Min videos to save per channel
        videos_download_per_batch: Max videos across all channels
        display_plugin: Display plugin to use
        auto_backfill: Enable auto backfill
        freshness_hours: Freshness threshold for backfill
        rich_progress: Use Rich progress bars
        rich_display: Rich display mode
        use_phase2: Enable phase 2 backfill
        phase2_batch_size: Batch size for phase 2
        fzf: Use fzf output
        parallel_workers: Number of parallel workers
        fail_fast: If True, abort on errors
        simple: Simple output mode
        output_format: Output format

    Returns:
        True if parallel execution succeeded, False if fallback needed
    """
    from yt_fts.core.batch_display import should_auto_enable_rich
    from yt_fts.download.parallel_processor import ParallelBatchProcessor

    if (
        not rich_progress
        and output_format != "json"
        and should_auto_enable_rich(simple, fzf)
    ):
        rich_progress = True

    processor = ParallelBatchProcessor(
        quota_strategy=quota_strategy,
        language=language,
        cookies_from_browser=cookies_from_browser,
        delay_between_channels=delay,
        max_retries=max_retries,
        continue_on_error=continue_on_error,
        time_per_channel=time_per_channel,
        time_per_video=time_per_video,
        time_per_batch=time_per_batch,
        min_saved=videos_download_per_channel,
        videos_download_per_batch=videos_download_per_batch,
        display_plugin=display_plugin,
        auto_backfill=auto_backfill,
        freshness_hours=freshness_hours,
        use_rich_progress=rich_progress,
        rich_display_mode=rich_display,
        use_phase2=use_phase2,
        phase2_batch_size=phase2_batch_size,
        use_fzf=fzf,
        use_json=output_format == "json",
    )

    console.print(f"Ready to process {len(channels)} channels in parallel\n")

    try:
        results = processor.process_channels(
            channels=channels,
            num_workers=parallel_workers
        )

        from yt_fts.download.summary import print_summary
        print_summary(console, results, channels)
        return True

    except Exception as e:
        console.print(f"\n[red]❌ Parallel processing failed: {e}[/red]")
        if fail_fast:
            msg = f"Parallel processing failed: {e}"
            raise RuntimeError(msg)
        console.print("[yellow]Falling back to sequential processing...[/yellow]\n")
        return False


def execute_sequential_path(
    channels: list[str],
    jobs: int,
    language: str,
    cookies_from_browser: str,
    delay: float,
    max_retries: int,
    continue_on_error: bool,
    rich_formatter,
    rich_mode: str,
    time_per_channel: float,
    time_per_video: float,
    time_per_batch: float,
    videos_download_per_channel: int,
    channels_download_per_batch: int,
    videos_download_per_batch: int,
    quota_strategy,
    display_plugin: str,
    auto_backfill: bool,
    freshness_hours: int,
    transcribe_audio_only: bool,
    whisper_model: str,
    fail_fast: bool,
    export_report: str,
) -> None:
    """Execute the sequential batch processing path.

    Args:
        channels: List of channel URLs
        jobs: Number of concurrent download jobs per channel
        language: Language for transcription
        cookies_from_browser: Browser to use for cookies
        delay: Delay between channels
        max_retries: Maximum retry attempts
        continue_on_error: Continue on individual download errors
        rich_formatter: Rich formatter instance
        rich_mode: Rich mode ('new', 'old', or None)
        time_per_channel: Timeout per channel
        time_per_video: Timeout per video
        time_per_batch: Timeout for entire batch
        videos_download_per_channel: Min videos to save per channel
        channels_download_per_batch: Target channels to download
        videos_download_per_batch: Max videos across all channels
        quota_strategy: QuotaStrategy instance
        display_plugin: Display plugin to use
        auto_backfill: Enable auto backfill
        freshness_hours: Freshness threshold for backfill
        transcribe_audio_only: Enable Whisper transcription
        whisper_model: Whisper model size
        fail_fast: If True, abort on errors
        export_report: Path to export report
    """
    from yt_fts.download.batch_downloader import BatchDownloader
    from yt_fts.download.batch_config import (
        ContentConfig,
        ExecutionConfig,
        LimitsConfig,
        TranscriptConfig,
        UIConfig,
    )

    # Layer 3: Migrate to config-based constructor
    execution_config = ExecutionConfig(
        jobs=jobs,
        language=language,
        cookies_from_browser=cookies_from_browser,
        delay_between_channels=delay,
        max_retries=max_retries,
        continue_on_error=continue_on_error,
    )
    limits_config = LimitsConfig(
        time_per_channel=time_per_channel,
        time_per_video=time_per_video,
        time_per_batch=time_per_batch,
        min_saved=videos_download_per_channel,
        target_downloads=channels_download_per_batch,
        videos_download_per_batch=videos_download_per_batch,
    )
    content_config = ContentConfig(
        auto_backfill=auto_backfill,
        freshness_hours=freshness_hours,
        quota_strategy=quota_strategy,
    )
    ui_config = UIConfig(
        rich_mode=rich_mode,
        display_plugin=display_plugin,
    )
    transcript_config = TranscriptConfig(
        whisper_model=whisper_model,
    )

    downloader = BatchDownloader(
        channels=channels,
        rich_formatter=rich_formatter,
        transcribe_audio_only=transcribe_audio_only,
        execution_config=execution_config,
        limits_config=limits_config,
        content_config=content_config,
        ui_config=ui_config,
        transcript_config=transcript_config,
    )

    console.print(f"  Max retries: {max_retries}")
    console.print(f"  Continue on error: {'Yes' if continue_on_error else 'No'}")
    console.print("  Skip initial wait on startup: Yes")
    console.print(f"Ready to process {len(channels)} channels")

    # Execute with graceful interrupt handling
    from .batch_interrupt import graceful_interrupt_handler

    with graceful_interrupt_handler(downloader, fail_fast, export_report):
        pass  # Handler does the work
