"""
Interrupt handling for batch download operations.

Provides a context manager for graceful shutdown during downloads.
"""
from collections.abc import Generator
from contextlib import contextmanager

from yt_fts.utils.rich_console import get_console

console = get_console()
@contextmanager
def graceful_interrupt_handler(
    downloader,
    fail_fast: bool = False,
    export_report: str = "",
) -> Generator[None, None, None]:
    """Context manager for handling graceful interruption of downloads.

    Args:
        downloader: The BatchDownloader instance
        fail_fast: If True, reraise exceptions immediately
        export_report: Path to export report after interruption

    Yields:
        None

    Handles:
        KeyboardInterrupt: Graceful shutdown with progress saving
    """
    interrupt_handler = None

    try:
        from yt_fts.utils.interrupt_handler import GracefulInterruptHandler

        interrupt_handler = GracefulInterruptHandler()

        # Register any existing thread pools if the downloader has them
        if hasattr(downloader, "executor") and downloader.executor:
            from yt_fts.utils.interrupt_handler import register_executor
            register_executor(downloader.executor)

    except ImportError:
        console.print("[yellow]WARNING: Graceful interruption handler not available[/yellow]")

    try:
        if interrupt_handler:
            with interrupt_handler:
                console.print()
                console.print("[dim]Press Ctrl+C to safely interrupt downloads[/dim]\n")
                downloader.download_all()
        else:
            downloader.download_all()

        # Export report if requested
        if export_report:
            try:
                downloader.export_report(export_report)
            except AttributeError:
                console.print(
                    "[yellow]WARNING: Export report functionality not available[/yellow]"
                )
        # Yield to allow the with block to execute (typically empty)
        yield

    except KeyboardInterrupt:
        console.print("\n\n🛑 [bold yellow]Download interrupted by user[/bold yellow]")

        # Enhanced interruption handling
        if interrupt_handler:
            console.print("[green]Graceful shutdown in progress...[/green]")

            # Show progress if available
            if hasattr(downloader, "get_progress"):
                progress = downloader.get_progress()
                console.print(f" Progress: {progress}")

            # Save partial progress
            if hasattr(downloader, "save_progress"):
                try:
                    downloader.save_progress()
                    console.print("💾 [green]Progress saved successfully[/green]")
                except Exception as e:
                    console.print(
                        f"[yellow]WARNING: Could not save progress: {e}[/yellow]"
                    )

            # Display summary if available
            try:
                downloader.display_summary()
            except (AttributeError, Exception) as e:
                console.print(
                    f"[yellow]WARNING: Summary display functionality not available: {e}[/yellow]"
                )

            console.print("[green]Graceful shutdown complete[/green]")
        else:
            console.print("[yellow]Interrupt received (no graceful handler available)[/yellow]")

        if fail_fast:
            raise

    except Exception as e:
        console.print(f"\n[red]❌ Download failed: {e}[/red]")
        if fail_fast:
            raise
        console.print("[yellow]Continuing after error...[/yellow]")


def setup_interrupt_handler(downloader) -> object | None:
    """Set up and return an interrupt handler for the downloader.

    Args:
        downloader: The BatchDownloader instance

    Returns:
        GracefulInterruptHandler instance or None
    """
    try:
        from yt_fts.utils.interrupt_handler import GracefulInterruptHandler

        interrupt_handler = GracefulInterruptHandler()

        # Register any existing thread pools if the downloader has them
        if hasattr(downloader, "executor") and downloader.executor:
            from yt_fts.utils.interrupt_handler import register_executor
            register_executor(downloader.executor)

        return interrupt_handler

    except ImportError:
        console.print("[yellow]WARNING: Graceful interruption handler not available[/yellow]")
        return None
