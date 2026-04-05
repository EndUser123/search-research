#!/usr/bin/env python3
# Final Version: June 28, 2025 v82.0 - Main entry point for the yt_sync package.

import sys
from pathlib import Path

# This is the crucial part: It adds the project directory to Python's path,
# allowing it to find the 'yt_sync' package.
sys.path.insert(0, str(Path(__file__).resolve().parent))


if __name__ == "__main__":
    # This is the new, correct way to start the application.
    # We configure logging BEFORE importing the main logic. This prevents
    # any other module from creating an unconfigured logger instance.
    from yt_sync.logging_config import setup_logging

    setup_logging()

    from yt_sync import main_logic

    main_logic.start()
