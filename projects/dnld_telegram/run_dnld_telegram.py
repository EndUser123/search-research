#!/usr/bin/env python3
import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def main():
    try:
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
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
