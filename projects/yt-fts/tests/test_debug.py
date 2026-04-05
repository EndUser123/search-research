import os
import sys


def test_imports():
    src_path = os.path.abspath("src")
    sys.path.append(src_path)
    print(f"sys.path: {sys.path}")

    try:
        print("Imported core.database")
        print("Imported batch_downloader")
        print("Imports successful!")
    except Exception as e:
        print(f"Import failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_imports()
