import os
import shutil
import sqlite3
import sys
import tempfile
from zipfile import ZipFile

import requests

# Use the same config directory logic as the production code
# to ensure tests and app use the same database location
if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "yt-fts")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/yt-fts")

def fetch_and_unzip_test_db():
    # This database doesn't work with Gemini implementation because the ChromaDB dimension is set to 1536 when the Gemini implementation expects 768
    url = "https://yt-fts-testdb-server.notjoemartinez.workers.dev/yt-fts/test_dbs/2024-07-04.zip"

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the zip file
        response = requests.get(url)
        zip_path = os.path.join(temp_dir, "downloaded.zip")

        with open(zip_path, "wb") as zip_file:
            zip_file.write(response.content)

        # Unzip the file
        extract_dir = os.path.join(temp_dir, "extracted")
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Move the yt-fts directory to ~/.config/
        source_dir = os.path.join(extract_dir, "yt-fts")
        dest_dir = CONFIG_DIR

        # Try to remove existing directory, but handle locked files gracefully
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
            except (PermissionError, OSError):
                # Database is locked by another process, try to just replace the db file
                db_file = os.path.join(dest_dir, "subtitles.db")
                if os.path.exists(db_file):
                    try:
                        os.remove(db_file)
                    except (PermissionError, OSError):
                        # Can't remove locked file, skip this setup
                        return

        # Copy the new database (create parent dirs if needed)
        os.makedirs(dest_dir, exist_ok=True)
        for item in os.listdir(source_dir):
            src = os.path.join(source_dir, item)
            dst = os.path.join(dest_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True, symlinks=True)
            else:
                shutil.copy2(src, dst)

    # print(f"The 'yt-fts' directory has been copied to {dest_dir}")
    # print("Contents of the copied directory:")
    # for root, dirs, files in os.walk(dest_dir):
    #     level = root.replace(dest_dir, '').count(os.sep)
    #     indent = ' ' * 4 * level
    #     print(f"{indent}{os.path.basename(root)}/")
    #     sub_indent = ' ' * 4 * (level + 1)
    #     for f in files:
    #         print(f"{sub_indent}{f}")



def get_test_db():
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()
    return curr
