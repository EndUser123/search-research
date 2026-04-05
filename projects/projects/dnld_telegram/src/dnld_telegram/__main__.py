#!/usr/bin/env python3
"""dnld_telegram - Enhanced Telegram Media Downloader

A sophisticated async Telegram media downloader with production-ready features:
- Advanced concurrency management with backpressure handling
- Intelligent error handling and recovery patterns
- Comprehensive observability and monitoring
- Resilience patterns for unreliable networks
- Structured logging with rich progress displays
"""

import asyncio
import sys


def main():
    """Main entry point for dnld_telegram."""
    try:
        # Import and run the main function from the download module
        from .download.__main__ import main as download_main

        # Run the main async function
        exit_code = asyncio.run(download_main())
        return exit_code or 0

    except ImportError as e:
        print(f"Error importing download module: {e}")
        print("Make sure you're running this from the project directory")
        return 1
    except KeyboardInterrupt:
        print("\nProcess terminated by user (Ctrl+C).")
        return 1
    except Exception as e:
        print(f"Error running dnld_telegram: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
