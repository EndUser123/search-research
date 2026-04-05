import os
import sys
import traceback


def verify_functionality():
    try:
        sys.path.append(os.path.abspath("src"))
        print(f"sys.path: {sys.path}")

        print("Importing database module...")
        print("Import success.")

        from yt_fts.core.database import get_channels

        print("Calling get_channels()...")
        channels = get_channels()
        print(f"Result: {len(channels)}")

    except Exception:
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()


if __name__ == "__main__":
    verify_functionality()
