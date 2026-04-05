"""
Subtitle Converter (Version 1.2 - UTF-8 Handling, Corrected Import Order)
------------------
Converts SRT/VTT files to cleaned TXT format in _TXT subfolder.
Ensures UTF-8 encoding for proper handling of all characters.
"""

import argparse
import io
import os
import re
import sys  # Import sys *before* using it

# Set UTF-8 encoding for stdout and stderr at the VERY BEGINNING of the script
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def remove_consecutive_duplicates(text: str) -> str:
    """Remove repeated consecutive words using regex"""
    return re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", text, flags=re.IGNORECASE)


def convert_srt_to_txt(srt_path: str, txt_path: str) -> None:
    """Convert SRT file to cleaned TXT format"""
    try:
        with open(srt_path, encoding="utf-8") as srt_file:
            content = srt_file.read()

        # Remove SRT metadata and join text lines
        cleaned = " ".join(
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.strip().isdigit() and "-->" not in line
        )

        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(remove_consecutive_duplicates(cleaned))

    except Exception as e:
        print(f"Error converting {srt_path}: {str(e)}")


def process_channel(channel_folder: str) -> None:
    """Main conversion workflow for a channel folder"""
    srt_folder = os.path.join(channel_folder, "_SRT")
    txt_folder = os.path.join(channel_folder, "_TXT")

    # Validate folder structure
    if not os.path.exists(srt_folder):
        print(f"Missing _SRT folder: {srt_folder}")
        exit(1)

    os.makedirs(txt_folder, exist_ok=True)

    # Process all subtitle files
    for filename in os.listdir(srt_folder):
        if filename.lower().endswith((".srt", ".vtt")):
            srt_path = os.path.join(srt_folder, filename)
            txt_filename = f"{os.path.splitext(filename)[0]}.txt"
            txt_path = os.path.join(txt_folder, txt_filename)

            convert_srt_to_txt(srt_path, txt_path)
            print(f"Converted: {filename} \u2192 {txt_filename}")  # Use Unicode arrow


def main():
    parser = argparse.ArgumentParser(
        description="Convert subtitle files to TXT format",
        epilog="Example: python yt_converter.py C:\\TEMP\\_yt\\ChannelName",
    )
    parser.add_argument(
        "channel_folder", help="Channel directory created by workflow.bat"
    )

    args = parser.parse_args()
    channel_path = os.path.abspath(args.channel_folder.strip('"'))

    if not os.path.exists(channel_path):
        print(f"Invalid channel folder: {channel_path}")
        exit(1)

    print(f"Processing channel: {channel_path}")
    process_channel(channel_path)
    print("\nConversion complete!")


if __name__ == "__main__":
    main()
