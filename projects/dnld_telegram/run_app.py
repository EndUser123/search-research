import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import asyncio

from dnld_telegram.download.__main__ import main as download_main

# Call the main function with the arguments
args = sys.argv[1:]
print(f"Running with args: {args}")

# We need to modify sys.argv to simulate the command line arguments
sys.argv = ["dnld_telegram"] + args

try:
    exit_code = asyncio.run(download_main())
    print(f"Application exited with code: {exit_code}")
except KeyboardInterrupt:
    print("Process terminated by user (Ctrl+C).")
    os._exit(1)
except Exception as e:
    print(f"Error running application: {e}")
    import traceback

    traceback.print_exc()
