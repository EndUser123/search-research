import os
import sys
import traceback


def test():
    try:
        sys.path.append(os.path.abspath("src"))
        print(f"sys.path: {sys.path}")

        print("Importing yt_fts.db.maintenance...")
        print("Successfully imported yt_fts.db.maintenance")

        print("Successfully imported make_db")

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    test()
