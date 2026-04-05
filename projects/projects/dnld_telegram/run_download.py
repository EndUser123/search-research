#!/usr/bin/env python3
"""
Wrapper script to run the download module with proper path setup.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run the download module
if __name__ == "__main__":
    try:
        import asyncio

        from download.__main__ import main

        exit_code = asyncio.run(main())
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"Error running download module: {e}")
        sys.exit(1)
