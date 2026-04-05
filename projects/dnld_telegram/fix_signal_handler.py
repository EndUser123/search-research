"""
Fix for signal handler issues in dnld_telegram
"""

# Fix 2: Modify the signal handler to be less aggressive with database operations
# File: src/dnld_telegram/download/__main__.py


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    global termination_event, shutdown_in_progress

    def signal_handler(_signum, _frame):
        """Handle termination signals with graceful cleanup."""
        global shutdown_in_progress

        from loguru import logger

        # Use loguru logger for proper timestamp formatting
        logger.info("🛑 Ctrl+C received. Initiating graceful cleanup...")

        # Set termination event to signal all operations to stop
        if termination_event:
            termination_event.set()

        # Set shutdown flag to indicate we're in shutdown mode
        shutdown_in_progress = True
        logger.info(
            "✅ Graceful shutdown initiated - waiting for current operations to complete..."
        )

        # Don't raise KeyboardInterrupt - let asyncio loop handle shutdown naturally

    # Setup signal handlers (Windows and Unix compatible)
    import signal

    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)
