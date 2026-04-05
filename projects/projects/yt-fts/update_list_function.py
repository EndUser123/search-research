#!/usr/bin/env python3
"""
Script to update the list function in cli.py to support JSON output.
"""

# Read the file
with open("src/yt_fts/core/cli.py", encoding="utf-8") as f:
    lines = f.readlines()

# Find the list function
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if "def list(transcript: str | None, channel: str | None, library: bool, json: bool = False) -> None:" in line:
        start_idx = i
    if start_idx is not None and i > start_idx:
        if line.strip().startswith("@cli.command("):
            end_idx = i
            break
        if line.strip().startswith("def ") and "command" not in line:
            end_idx = i
            break

if start_idx is None:
    print("Could not find list function!")
    exit(1)

if end_idx is None:
    # Find the next function definition
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip().startswith("@cli.command("):
            end_idx = i
            break
        if lines[i].strip().startswith("def ") and "cli" not in lines[i]:
            end_idx = i
            break

print(f"Found list function from line {start_idx + 1} to {end_idx}")

# Create the new function body
new_function = """def list(transcript: str | None, channel: str | None, library: bool, json: bool = False) -> None:
    from ..ui.list_formatter import show_video_list, show_video_transcript
    from .database import get_channels
    import sqlite3
    from ..utils.config import get_db_path
    from ..utils.helpers import get_time_delta
    from .database import get_title_from_db

    if json:
        # JSON output mode
        if transcript:
            # Show transcript as JSON
            con = sqlite3.connect(get_db_path())
            cur = con.cursor()
            cur.execute("SELECT * FROM subtitles WHERE video_id=?", (transcript,))
            rows = cur.fetchall()

            if not rows:
                output_json(format_error_json(f"No transcript found for video ID: {transcript}", "not_found"))
                con.close()
                return

            word_count = 0
            for row in rows:
                word_count += len(row[4].split())

            video_length = get_time_delta(rows[0][2], rows[-1][2])
            video_title = get_title_from_db(transcript)

            con.close()

            output_json(format_transcript_json(transcript, rows, video_title, video_length, word_count))

        elif channel:
            # Show channel videos as JSON
            channel_id = get_channel_id_from_input(channel)
            con = sqlite3.connect(get_db_path())
            cur = con.cursor()
            cur.execute("SELECT * FROM videos WHERE channel_id=?", (channel_id,))
            rows = cur.fetchall()
            con.close()

            output_json(format_video_list_json(rows, channel_id))

        elif library or True:
            # Show all channels as JSON
            raw_channels = get_channels()
            output_json(format_channel_list_json(raw_channels))
    else:
        # Normal Rich output mode
        if transcript:
            show_video_transcript(transcript)
        elif channel:
            channel_id = get_channel_id_from_input(channel)
            show_video_list(channel_id)
        elif library:
            list_channels()
        else:
            list_channels()

    # Success - let Click handle naturally


"""

# Replace the old function with the new one
new_lines = lines[:start_idx] + [new_function] + lines[end_idx:]

# Write the file
with open("src/yt_fts/core/cli.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Successfully updated list function!")
