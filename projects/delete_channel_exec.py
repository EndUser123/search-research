import os
import sys

# Set up paths to import from src
project_root = r"p:\projects\yt-fts"
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Mocking get_db_path to return the correct local DB
from yt_fts.utils import config

config.get_db_path = lambda: os.path.join(project_root, "yt_fts.db")

from yt_fts.db.channels import delete_channel

channel_id = "UCX6OQ3DkcsbYNE6H8uQQuVA"
print(f"Deleting channel ID: {channel_id} (@PythonProgrammer)")

try:
    delete_channel(channel_id)
    print("Successfully deleted channel and associated data.")
except Exception as e:
    import traceback

    traceback.print_exc()
    print(f"Error during deletion: {e}")
