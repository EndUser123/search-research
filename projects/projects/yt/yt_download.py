"""
YouTube Download Script (Version 1.17 - Subtitles Only, Title Truncation)
-------------------------------------------------------
Downloads YouTube channel subtitles ONLY.

Uses yt-dlp's output template to TRUNCATE long titles, preventing path length errors.
"""

import argparse  # Import argparse
import io
import os
import subprocess
import sys
import threading
import time

from tqdm import tqdm

# Set UTF-8 encoding for stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def download_channel(url, channel_path):
    """This function is kept but does nothing."""
    print("Skipping channel download (as configured).")
    return 0


def get_playlist_id(channel_url):
    """Gets the playlist ID."""
    try:
        command = ["yt-dlp", "--flat-playlist", "--print", "playlist_id", channel_url]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        playlist_id = result.stdout.strip()
        print(f"DEBUG: Retrieved playlist ID: {playlist_id}")
        return playlist_id
    except subprocess.CalledProcessError as e:
        print(f"Error getting playlist ID: {e}")
        return None


def download_subtitles(url, channel_path):
    """Downloads subtitles only, with tqdm progress and pagination."""
    srt_folder = os.path.join(channel_path, "_SRT")
    os.makedirs(srt_folder, exist_ok=True)
    print(f"DEBUG: Starting download_subtitles. SRT folder: {srt_folder}")
    print(f"DEBUG: URL received in download_subtitles: {url}")
    print(f"DEBUG: channel_path received in download_subtitles: {channel_path}")

    playlist_id = get_playlist_id(url)
    if not playlist_id:
        print("ERROR: Could not retrieve playlist ID. Exiting.")
        return 1

    page_size = 100  # Adjust as needed
    playlist_index = 1

    while True:
        print(f"DEBUG: Processing starting at playlist index: {playlist_index}")
        process = None
        try:
            with tqdm(
                total=page_size,
                unit="subtitle",
                desc=f"Downloading Subtitles (Page {playlist_index // page_size + 1})",
            ) as pbar:
                command_subs = [
                    "yt-dlp",
                    "--verbose",
                    "--write-sub",
                    "--sub-lang",
                    "en",
                    "--sub-format",
                    "srt",
                    # TRUNCATE THE TITLE!  Use %(title).50s to limit to 50 characters.
                    "-o",
                    f"{srt_folder}/%(playlist_index)s-%(title).50s-%(id)s.%(ext)s",
                    "--skip-download",
                    "--playlist-start",
                    str(playlist_index),
                    "--playlist-end",
                    str(playlist_index + page_size - 1),
                    "--extractor-args",
                    "youtube:formats=missing_pot",
                    f"https://www.youtube.com/playlist?list={playlist_id}",
                ]
                print(f"DEBUG: Running command_subs: {command_subs}")

                process = subprocess.Popen(
                    command_subs,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                print(f"DEBUG: subprocess.Popen started. PID: {process.pid}")

                def monitor(process, timeout):
                    """Monitors the process and kills it if it exceeds the timeout."""
                    start_time = time.time()
                    while process.poll() is None:
                        if time.time() - start_time > timeout:
                            print("ERROR: yt-dlp timed out (thread monitor)!")
                            process.kill()
                            return
                        time.sleep(1)

                timeout_seconds = 300  # seconds.
                monitor_thread = threading.Thread(
                    target=monitor, args=(process, timeout_seconds)
                )
                monitor_thread.daemon = True
                monitor_thread.start()

                try:
                    for line in process.stdout:
                        line = line.strip()
                        print(f"DEBUG: yt-dlp output: {line}")
                        if "[download] Writing" in line:
                            pbar.update(1)
                        if "Finished downloading playlist" in line:
                            process.wait()
                            if process.returncode != 0:
                                raise subprocess.CalledProcessError(
                                    process.returncode, process.args
                                )
                            return 0  # Exit if finished

                    process.wait()
                    print(
                        f"DEBUG: subprocess.Popen completed. returncode: {process.returncode}"
                    )

                except Exception as e:
                    print(f"An exception occurred {e}")
                    if process:
                        process.kill()
                    return 1

                finally:
                    pass

                if process.returncode != 0:
                    raise subprocess.CalledProcessError(
                        process.returncode, process.args
                    )

            playlist_index += page_size

        except subprocess.CalledProcessError as e:
            print(f"\n\u2717 Download failed: Exit code {e.returncode}")
            print(
                f"yt-dlp stderr (subtitles):\n{e.stderr.encode('utf-8', errors='replace').decode('utf-8', errors='replace')}"
            )
            return 1
        except Exception as e:
            print(
                f"\n\u2717 Download failed: {str(e).encode('utf-8', errors='replace').decode('utf-8', errors='replace')}"
            )
            return 1


def main():
    parser = argparse.ArgumentParser(description="Download YouTube channel subtitles.")
    parser.add_argument("url", help="YouTube Channel URL")
    parser.add_argument("channel_path", help="Path to the channel folder")
    args = parser.parse_args()
    print(f"DEBUG: Parsed args in main: {args}")

    print(f"Downloading subtitles for channel: {args.url}")
    # download_channel is now a no-op.
    channel_exit_code = download_channel(args.url, args.channel_path)

    if channel_exit_code != 0:
        print("Skipping subtitle download due to channel download configuration.")
        return 1
    else:
        print("Proceeding to subtitles...")
        subtitle_exit_code = download_subtitles(args.url, args.channel_path)
        if subtitle_exit_code != 0:
            print(
                f"Subtitle download encountered errors. Exit code: {subtitle_exit_code}"
            )
            return 1
        else:
            print("Subtitle download completed successfully.")
            return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
