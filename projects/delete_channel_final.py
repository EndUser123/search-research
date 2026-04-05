import os
import sys

# Set up paths to import from src
project_root = r"p:\projects\yt-fts"
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Set environment variable to target the correct database
os.environ["YT_FTS_DB_PATH"] = r"p:\projects\yt-fts\data\subtitles.db"

from yt_fts.db.channels import delete_channel

channel_id = "UC2sekS462J7_QCtcuy0uGxw"
print(f"Deleting channel: {channel_id} (pythonprogrammer)")

try:
    delete_channel(channel_id)
    print("Successfully deleted channel and associated data.")
except Exception as e:
    import traceback

    traceback.print_exc()
    print(f"Error during deletion: {e}")
