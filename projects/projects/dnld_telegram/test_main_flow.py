import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables first (find .env in project root)
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Add the src directory to the path
import sys

sys.path.insert(0, os.path.join(project_root, "src"))

from dnld_telegram.download.__main__ import main as download_main


async def run_with_better_error_handling():
    """Run the main function with better error handling"""
    try:
        print("Starting download_main with better error handling...")
        exit_code = await download_main()
        print(f"Application exited with code: {exit_code}")
        return exit_code
    except KeyboardInterrupt:
        print("Application interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Set a timeout for the script
    try:
        # Run with a 30-second timeout
        result = asyncio.run(
            asyncio.wait_for(run_with_better_error_handling(), timeout=30.0)
        )
        print(f"Script completed with result: {result}")
    except TimeoutError:
        print("Script timed out after 30 seconds")
    except Exception as e:
        print(f"Script failed with error: {e}")
