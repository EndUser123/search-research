import os


def fix_imports():
    src_dir = os.path.join(os.getcwd(), "src")
    print(f"Scanning {src_dir}...")

    count = 0
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()

                    if "from src.yt_fts" in content:
                        print(f"Fixing {path}")
                        new_content = content.replace("from src.yt_fts", "from yt_fts")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1
                except Exception as e:
                    print(f"Error processing {path}: {e}")

    print(f"Fixed imports in {count} files.")


if __name__ == "__main__":
    fix_imports()
