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
from pathlib import Path

# Add the project root to the Python path so we can import the download module
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def main():
    """Main entry point for dnld_telegram."""
    try:
        # Import and run the main function from the download module
        from dnld_telegram.download.__main__ import main as download_main

        # Run the main async function
        exit_code = asyncio.run(download_main())
        return exit_code or 0

    except ImportError as e:
        print(f"Error importing download module: {e}")
        print("Make sure you're running this from the project directory")
        return 1
    except Exception as e:
        print(f"Error running dnld_telegram: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
