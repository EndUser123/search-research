#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import and run the main function from the download module
from dnld_telegram.download.__main__ import main as download_main  # noqa: E402

# Run the main async function
exit_code = asyncio.run(download_main())
sys.exit(exit_code or 0)
