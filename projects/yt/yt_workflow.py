r"""
YouTube Workflow Script (Version 3.1 - Corrected Base Path)
-------------------------------------------------------------
Uses C:\TEMP\_yt as the base path. Calls yt_download.py.
Uses the VIDEO ID for the channel folder to avoid path length issues.
"""

import os
import re
import subprocess
import sys
from unicodedata import normalize

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants for network retry behavior
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5
STATUS_FORCELIST = [500, 502, 503, 504]


def requests_retry_session():
    """Creates a session with retry strategy."""
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def extract_video_id_from_url(url):
    """Extracts the video ID from a YouTube URL."""
    patterns = [
        r"youtube\.com/watch\?v=([\w-]+)",
        r"youtube\.com/channel/([\w-]+)",
        r"youtube\.com/c/([\w-]+)",
        r"youtube\.com/@([\w-]+)",
        r"youtube\.com/user/([\w-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def sanitize_filename(filename):
    """Sanitizes a filename (not used)."""
    filename = normalize("NFKC", filename)
    sanitized = re.sub(r"[^\w\s-]", "_", filename).strip("_").rstrip(".")
    if re.match(r"(?i)^(con|prn|aux|nul|com[0-9]|lpt[0-9])$", sanitized):
        sanitized = f"invalid_{sanitized}"
    return sanitized


def check_youtube_channel_exists_head_request(channel_url):
    """Checks channel existence."""
    try:
        session = requests_retry_session()
        response = session.head(
            channel_url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        final_url = response.url
        valid_patterns = ["youtube.com/channel/", "youtube.com/@", "youtube.com/user/"]
        if any(p in final_url for p in valid_patterns):
            return True, final_url, None
        return False, final_url, "Invalid Final URL"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, None, "HTTP 404"
        else:
            return False, None, f"HTTP Other Error: {e.response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, None, f"Network Error: {type(e).__name__} - {str(e)}"


def check_channel_exists(youtube_url):
    """Checks overall channel existence."""
    print(f"Validating channel: {youtube_url}")
    exists, final_url, error_type = check_youtube_channel_exists_head_request(
        youtube_url
    )
    if exists and final_url:
        print(f"Resolved final URL: {final_url}")
        return True
    else:
        if error_type == "HTTP 404":
            print("Channel validation failed: YouTube Channel NOT found (HTTP 404).")
        elif error_type and "HTTP Other Error" in error_type:
            print(
                f"Channel validation failed: Potentially invalid YouTube Channel URL or temporary issue ({error_type})."
            )
            print(
                "It might help to double-check the URL. If the URL is correct, it could be a temporary YouTube issue."
            )
        elif error_type and "Network Error" in error_type:
            print(
                f"Channel validation failed: Network error during channel check ({error_type})."
            )
            print(
                "Please check your internet connection. If your connection is stable, it could be a temporary network issue reaching YouTube."
            )
        elif error_type == "Invalid Final URL":
            print(
                "Channel validation failed: URL redirected to an invalid YouTube channel page."
            )
            print("This suggests the provided URL is not a valid YouTube channel URL.")
        else:
            print("Channel validation failed for an unknown reason.")

        return False


def create_channel_folder(base_path, folder_name):
    """Creates the storage folder."""
    full_path = os.path.join(base_path, folder_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        print(f"Using storage folder: {full_path}")
        return full_path
    except OSError as e:
        print(f"Fatal error: Failed to create folder {full_path}")
        print(f"System message: {e.strerror}")
        sys.exit(1)


def run_workflow_script(script_name, *args):
    """Runs external scripts."""
    print(f"Calling script: {script_name} with args: {args}")
    try:
        cmd = [sys.executable, script_name] + list(args)
        result = subprocess.run(
            cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        print(f"{script_name} output:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Critical error in {script_name}:")
        print(f"Exit code: {e.returncode}")
        print(f"Output:\n{e.stdout}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Missing external script: {script_name}")
        sys.exit(1)


def main():
    try:
        if len(sys.argv) != 2:
            print(f"Usage: {os.path.basename(sys.argv[0])} [YouTube_Channel_URL]")
            sys.exit(1)

        youtube_url = sys.argv[1]
        base_folder = r"C:\TEMP\_yt"  # CORRECTED BASE FOLDER

        channel_id = extract_video_id_from_url(youtube_url)  # Still using video ID
        if not channel_id:
            print(
                "Error: Could not extract a valid channel/video identifier from the provided URL."
            )
            sys.exit(1)

        channel_folder = create_channel_folder(base_folder, channel_id)
        print(f"DEBUG: channel_folder in yt_workflow: {channel_folder}")

        if not check_channel_exists(youtube_url):
            print("Workflow stopped due to channel validation failure.")
            sys.exit(1)

        # Execute external workflow scripts in order
        scripts = [
            (
                "yt_download.py",
                youtube_url,
                channel_folder,
            ),  # Pass channel URL and ID-based folder
            # ("yt_converter.py", channel_folder), # Keep these commented out for initial testing
            # ("yt_cluster.py", channel_folder),
            # ("yt_combine.py", channel_folder)
        ]

        for script in scripts:
            run_workflow_script(*script)

        print("Workflow completed successfully")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__} - {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
