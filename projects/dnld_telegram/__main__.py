#!/usr/bin/env python3
"""
Entry point for dnld_telegram application.
Allows running the application from the project root with:
    uv run dnld_telegram --help
    uv run dnld_telegram --dry-run
    uv run dnld_telegram
"""

import sys
from pathlib import Path

# Add the src directory to the Python path so we can import modules
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def main():
    """Main entry point for the dnld_telegram application."""
    try:
        # Import and run the download module
        from dnld_telegram.download.__main__ import main as download_main

        return download_main()
    except ImportError as e:
        print(f"Error importing download module: {e}")
        print("Make sure you're running this from the dnld_telegram directory")
        return 1
    except Exception as e:
        print(f"Error running dnld_telegram: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
