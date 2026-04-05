import os

files_to_check = [
    r"src\yt_fts\core\database.py",
    r"src\yt_fts\download\download_handler.py",
]


def inspect():
    for rel_path in files_to_check:
        path = os.path.abspath(rel_path)
        print(f"Checking {path}...")
        if not os.path.exists(path):
            print("File not found.")
            continue

        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            found = False
            for i, line in enumerate(lines):
                if (
                    line.startswith("<<<<<<<")
                    or line.startswith("=======")
                    or line.startswith(">>>>>>>")
                ):
                    found = True
                    print(f"Line {i+1}: {line.strip()}")

            if not found:
                print("No markers found.")
        except Exception as e:
            print(f"Error reading {path}: {e}")


if __name__ == "__main__":
    inspect()
