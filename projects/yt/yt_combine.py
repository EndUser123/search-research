"""
Transcript Combiner
-------------------
Combines clustered transcripts into chunked files
"""

import argparse
from pathlib import Path

# -------------------- CONFIG --------------------
WORD_LIMIT = 450000
INPUT_CLUSTER = "_CLUSTER"
INPUT_TEXT = "_TEXT"
OUTPUT_COMBINED = "_COMBINED"
# ------------------------------------------------


def validate_folder(path: Path, name: str) -> None:
    """Ensure required folder exists"""
    if not path.exists():
        print(f"Error: Missing {name} folder\n{path}")
        exit(1)


def process_cluster_file(
    cluster_file: Path, text_folder: Path, output_folder: Path
) -> None:
    """Process individual cluster file and create combined chunks"""
    with open(cluster_file, encoding="utf-8") as f:
        file_names = [line.strip() for line in f if line.strip()]

    combined_content = []
    for fname in file_names:
        text_path = text_folder / fname
        if text_path.exists():
            try:
                content = text_path.read_text(encoding="utf-8").strip()
                combined_content.append(f"----- {fname} -----\n{content}")
            except Exception as e:
                print(f"Error reading {text_path}: {e}")
        else:
            print(f"Missing transcript: {text_path}")

    if not combined_content:
        print(f"No content found for {cluster_file.name}")
        return

    # Generate output filename
    base_name = f"{cluster_file.stem.replace('_sil_', '_')}_combined"
    output_path = output_folder / f"{base_name}_part{{}}.txt"

    # Split and save content
    full_text = "\n\n".join(combined_content)
    words = full_text.split()

    chunk_num = 1
    for i in range(0, len(words), WORD_LIMIT):
        chunk_path = output_path.format(chunk_num)
        chunk_text = " ".join(words[i : i + WORD_LIMIT])
        chunk_path.write_text(chunk_text, encoding="utf-8")
        print(f"Saved {chunk_path.name} ({len(words[i : i + WORD_LIMIT]):,} words)")
        chunk_num += 1


def main():
    parser = argparse.ArgumentParser(
        description="Combine clustered transcripts into chunked files",
        epilog="Example: python yt_combine.py C:\\TEMP\\_yt\\ChannelName",
    )
    parser.add_argument(
        "channel_folder", type=Path, help="Channel directory from workflow.bat"
    )

    args = parser.parse_args()
    channel_path = args.channel_folder.resolve()

    # Validate folder structure
    validate_folder(channel_path, "channel")
    validate_folder(channel_path / INPUT_CLUSTER, INPUT_CLUSTER)
    validate_folder(channel_path / INPUT_TEXT, INPUT_TEXT)

    # Setup output folder
    output_path = channel_path / OUTPUT_COMBINED
    output_path.mkdir(exist_ok=True)

    # Process all cluster files
    print(f"\nProcessing clusters in {channel_path.name}")
    for cluster_file in (channel_path / INPUT_CLUSTER).glob("*.txt"):
        print(f"\nCombining {cluster_file.name}")
        process_cluster_file(cluster_file, channel_path / INPUT_TEXT, output_path)

    print("\nCombining complete!")


if __name__ == "__main__":
    main()
