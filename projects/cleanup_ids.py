import os
import sys

# Set up paths to import from src
project_root = r"p:\projects\yt-fts"
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Set environment variable to target the correct database
os.environ["YT_FTS_DB_PATH"] = r"p:\projects\yt-fts\data\subtitles.db"

from yt_fts.db.channels import delete_channel

# Both potential IDs just in case
ids_to_delete = ["UC2sekS462J7_QCtcuy0uGxw", "UCX6OQ3DkcsbYNE6H8uQQuVA"]

for channel_id in ids_to_delete:
    print(f"Checking/Deleting channel: {channel_id}")
    try:
        delete_channel(channel_id)
        print(f"Successfully processed deletion for {channel_id}")
    except Exception as e:
        print(f"Note for {channel_id}: {e}")

print("Cleanup complete.")
