import os


def fix_tests_imports():
    tests_dir = os.path.join(os.getcwd(), "tests")
    print(f"Scanning {tests_dir}...")

    count = 0
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()

                    # Replace both import statements and string references (for patch)
                    new_content = content.replace("from src.yt_fts", "from yt_fts")
                    new_content = new_content.replace(
                        "import src.yt_fts", "import yt_fts"
                    )
                    new_content = new_content.replace('"src.yt_fts', '"yt_fts')
                    new_content = new_content.replace("'src.yt_fts", "'yt_fts")

                    if content != new_content:
                        print(f"Fixing {path}")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1
                except Exception as e:
                    print(f"Error processing {path}: {e}")

    print(f"Fixed imports in {count} test files.")


if __name__ == "__main__":
    fix_tests_imports()
