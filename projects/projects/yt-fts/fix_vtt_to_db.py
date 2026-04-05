# Fix vtt_to_db with error handling

# Read the file
with open("src/yt_fts/download/download_handler.py", encoding="utf-8") as f:
    content = f.read()

# Find and replace vtt_to_db with better error handling
# This is a simpler approach - just add logging at key points

# Add logging before the file loop
old_loop_start = "            for vtt in file_paths:"
new_loop_start = """            saved_count = 0
            failed_count = 0

            for vtt in file_paths:"""
content = content.replace(old_loop_start, new_loop_start)

# Add commit logging
old_commit = """            con.commit()

        con.close()"""
new_commit = """            con.commit()

            self.console.print(f"[green]✓ Saved {saved_count} transcripts[/green]")
            if failed_count > 0:
                self.console.print(f"[yellow]⚠ {failed_count} files failed to save[/yellow]")

        con.close()"""
content = content.replace(old_commit, new_commit)

# Add error handling around individual file processing
old_file_processing = """                base_name = os.path.basename(vtt)
                vid_id = base_name.split(".")[0]"""
new_file_processing = """                try:
                    base_name = os.path.basename(vtt)
                    vid_id = base_name.split(".")[0]"""
content = content.replace(old_file_processing, new_file_processing)

# Add the success tracking and error handling at the end of the file processing
old_progress = """                # Update progress for this file
                progress.advance(task)"""
new_progress = """                    # Track success
                    saved_count += 1

                except Exception as e:
                    # Track failure
                    failed_count += 1
                    log_technical_error(e, {
                        "operation": "vtt_to_db",
                        "vtt_file": vtt,
                        "video_id": vid_id if 'vid_id' in locals() else 'unknown'
                    })
                    # Continue with next file instead of failing entire batch

                # Update progress for this file
                progress.advance(task)"""
content = content.replace(old_progress, new_progress)

# Write back
with open("src/yt_fts/download/download_handler.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Added error handling and tracking to vtt_to_db")
