import os
import re
import sys

import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter


def sanitize_filename(name):
    """Remove invalid filename characters."""
    return re.sub(r'[<>:"/\\|?*]', "", name)


def get_video_urls(channel_url):
    """Scrape video URLs from the channel's /videos page."""
    try:
        if not channel_url.endswith("/videos"):
            channel_url += "/videos"
        response = requests.get(channel_url)
        response.raise_for_status()
        html_content = response.text
        video_ids = re.findall(r"/watch\?v=([A-Za-z0-9_-]{11})", html_content)
        unique_urls = list(
            set(f"https://www.youtube.com/watch?v={vid}" for vid in video_ids)
        )
        return unique_urls
    except Exception as e:
        print(f"Error fetching video URLs: {e}")
        return []


def get_channel_transcripts(channel_url, root_path="C:\\TEMP\\_yt"):
    """Download all transcripts from a channel into organized folders."""
    try:
        # Extract channel name from URL
        channel_name = sanitize_filename(
            channel_url.split("@")[-1] if "@" in channel_url else "UnknownChannel"
        )
        print(f"Processing channel: {channel_name}")

        # Set up folder structure
        if os.path.abspath(os.getcwd()) == os.path.abspath(root_path):
            channel_dir = channel_name
        else:
            channel_dir = os.path.join(root_path, channel_name)
        srt_dir = os.path.join(channel_dir, "_SRT")
        os.makedirs(srt_dir, exist_ok=True)

        # Get video URLs
        video_urls = get_video_urls(channel_url)
        if not video_urls:
            print("No video URLs found. Exiting.")
            return

        # Formatter for SRT
        formatter = SRTFormatter()

        # Process each video
        for video_url in video_urls:
            try:
                video_id = video_url.split("v=")[1].split("&")[0]
                # Try to get title via a lightweight request (no pytube)
                try:
                    response = requests.get(video_url)
                    title_match = re.search(r"<title>(.*?)</title>", response.text)
                    video_title = (
                        sanitize_filename(
                            title_match.group(1).replace(" - YouTube", "")
                        )
                        if title_match
                        else video_id
                    )
                except Exception:
                    video_title = video_id  # Fallback to video ID if title fetch fails

                # Get transcript (no Shorts filter since pytube is out)
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                srt_transcript = formatter.format_transcript(transcript)

                # Save SRT file
                output_file = os.path.join(srt_dir, f"{video_title}.srt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(srt_transcript)
                print(f"Saved: {output_file}")

            except Exception as e:
                print(f"Failed for {video_url}: {e}")
                continue

    except Exception as e:
        print(f"Error with channel {channel_url}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python yt_grok_get_srt.py <Channel_URL>")
        sys.exit(1)

    channel_url = sys.argv[1]
    get_channel_transcripts(channel_url)
