#!/usr/bin/env python3
"""
Check why downloads are being skipped
"""

import json
import os


def check_download_status() -> None:
    """Check the download tracking status"""

    # Check downloaded files
    downloaded_path = "channels/koreannarchive/downloaded_files.json"
    enumerated_path = "channels/koreannarchive/enumerated_files.json"

    print("=== Download Status Analysis ===")

    if os.path.exists(downloaded_path):
        with open(downloaded_path) as f:
            downloaded_data = json.load(f)
        print(f"Downloaded files tracked: {len(downloaded_data)}")

        # Show first few entries
        print("\nFirst 5 downloaded file entries:")
        for i, (key, value) in enumerate(list(downloaded_data.items())[:5]):
            print(f"  {i + 1}. {key}: {value}")
    else:
        print("No downloaded_files.json found")

    if os.path.exists(enumerated_path):
        with open(enumerated_path) as f:
            enumerated_data = json.load(f)
        print(f"\nEnumerated files: {len(enumerated_data)}")

        # Show first few entries
        print("\nFirst 5 enumerated file entries:")
        for i, (key, value) in enumerate(list(enumerated_data.items())[:5]):
            print(f"  {i + 1}. {key}: {value}")
    else:
        print("No enumerated_files.json found")

    # Check _media directory
    media_path = "channels/koreannarchive/_media"
    if os.path.exists(media_path):
        media_files = [
            f
            for f in os.listdir(media_path)
            if os.path.isfile(os.path.join(media_path, f))
        ]
        print(f"\nActual files in _media: {len(media_files)}")

        # Show first few files
        print("\nFirst 5 files in _media:")
        for i, filename in enumerate(media_files[:5]):
            file_path = os.path.join(media_path, filename)
            file_size = os.path.getsize(file_path)
            print(f"  {i + 1}. {filename} ({file_size:,} bytes)")
    else:
        print("No _media directory found")


if __name__ == "__main__":
    check_download_status()
