"""
yt-fts utilities package
"""
import datetime
import re
from pathlib import Path
from typing import TypedDict

import requests
import webvtt


class Model(TypedDict):
    name: str
    api_key: str
    base_url: str
    embedding_model: str
    chat_model: str


# Export TypedDict contracts for cross-module interfaces
# These provide type safety for data passed between modules
from yt_fts.utils.types import (
    ChannelDisplayInfo,
    DownloadResultInfo,
    ImportProgressInfo,
    ImportResultInfo,
    RssInfo,
    SearchResults,
)

__all__ = [
    "ChannelDisplayInfo",
    "DownloadResultInfo",
    "ImportProgressInfo",
    "ImportResultInfo",
    "Model",
    "RssInfo",
    "SearchResults",
]

def show_message(code: str) -> None:
    """Display error messages for common yt-fts issues."""
    error_dict = {"search_too_long": "Error: Search text must be less than 40 characters", "no_matches_found": "No matches found.\n- Try shortening the search text or use wildcards to match partial words.", "channel_not_found": "channel not found.\n- Try using channel id", "multiple_channels_found": "Multiple channels found.\n- Try using id", "channel_url_not_correct": "The given channel URL is not correct, expected pattern : https://www.youtube.com/@TimDillonShow/videos"}
    import logging
    logging.getLogger(__name__).error(error_dict[code])

def time_to_secs(time_str: str) -> int:
    """
    Convert timestamp to seconds for YouTube URLs. Subtracts 3 seconds to give a buffer.
    """
    time_rex = re.search("^(\\d\\d):(\\d\\d):(\\d\\d)", time_str)
    if not time_rex:
        return 0
    hours = int(time_rex.group(1)) * 3600
    mins = int(time_rex.group(2)) * 60
    secs = int(time_rex.group(3))
    total_secs = hours + mins + secs
    return total_secs - 3

def get_time_delta(timestamp1: str, timestamp2: str) -> str:
    """Calculate time difference between two timestamps."""
    from datetime import datetime
    format_string = "%H:%M:%S.%f"
    dt1 = datetime.strptime(timestamp1, format_string)
    dt2 = datetime.strptime(timestamp2, format_string)
    diff = dt2 - dt1
    return str(diff).split(".")[0]

def get_model_config(api_key: str | None=None) -> Model:
    """Get model configuration for API keys and endpoints."""
    import os
    models: list[Model] = [{"name": "OPENAI", "embedding_model": "text-embedding-ada-002", "chat_model": "gpt-4o", "api_key": "", "base_url": "https://api.openai.com/v1"}, {"name": "GEMINI", "embedding_model": "text-embedding-004", "chat_model": "gemini-2.5-flash", "api_key": "", "base_url": "https://generativelanguage.googleapis.com/v1beta"}]
    if api_key is not None:
        if api_key.startswith("sk-"):
            models[0]["api_key"] = api_key
            return models[0]
        if api_key.startswith("AIza"):
            models[1]["api_key"] = api_key
            return models[1]
    else:
        for model in models:
            api_key = os.environ.get(f"{model['name']}_API_KEY")
            if api_key is not None:
                model["api_key"] = api_key
                return model
    msg = "No model configuration found. Please set the environment variable for the model API key."
    raise ValueError(msg)

def get_date(date_string: str) -> datetime.date:
    """Parse date string in YYYYMMDD or YYYY-MM-DD format."""
    if "-" in date_string:
        return datetime.date.fromisoformat(date_string)
    return datetime.datetime.strptime(date_string, "%Y%m%d").date()

def summarize_error(error_msg: str) -> str:
    """
    Summarize error message for display in Rich UI and error handling.
    """
    if not error_msg:
        return "Unknown error"
    if error_msg.startswith("KeyError:") and ("<_io." in error_msg or "mode=" in error_msg):
        return "KeyError: Missing required data in YouTube response"
    if "<_io.TextIOWrapper" in error_msg or "<_io.BufferedWriter" in error_msg:
        return "I/O error - file or stream operation failed"
    if "mode=" in error_msg and "encoding=" in error_msg and ("_io" in error_msg):
        return "I/O error - unable to access required file or stream"
    if error_msg.startswith("KeyError:") and len(error_msg) < 50:
        return f"Missing data: {error_msg}"
    if "403" in error_msg or "Forbidden" in error_msg:
        return "Access forbidden (403 error) - video may be private or geo-restricted"
    if "429" in error_msg or "Too Many Requests" in error_msg:
        return "Rate limited (429 error) - YouTube is throttling requests"
    if "404" in error_msg or "Not Found" in error_msg:
        return "Video not found (404 error) - may have been deleted"
    if "network" in error_msg.lower() or "connection" in error_msg.lower():
        return "Network connection error - check internet connection"
    if "timeout" in error_msg.lower():
        return "Request timeout - YouTube servers taking too long to respond"
    if "cannot import" in error_msg.lower():
        return "Import error - missing function or module dependency"
    if "no such table" in error_msg.lower():
        return "Database error - required table doesn't exist"
    if "permission" in error_msg.lower() or "denied" in error_msg.lower():
        return "Permission denied - insufficient access rights"
    return error_msg[:100] + "..." if len(error_msg) > 100 else error_msg

def bold_query_matches(text: str, query: str) -> str:
    """
    Bold the query in the text, keeping the case the same
    """
    query_words = query.lower().split()
    result_words = []
    for word in text.split():
        if word.lower() in query_words:
            result_words.append(f"[bold][bright_magenta]{word}[/bright_magenta][/bold]")
        else:
            result_words.append(word)
    return " ".join(result_words)

def handle_reject_consent_cookie(channel_url: str, s: requests.Session, timeout: int=10) -> None:
    """
    Auto rejects the consent cookie if request is redirected to the consent page.

    Args:
        channel_url: The channel URL to check
        s: requests session
        timeout: Request timeout in seconds (default 10) - prevents hanging on slow/blocked requests
    """
    r = s.get(channel_url, timeout=timeout)
    if "https://consent.youtube.com" in r.url:
        m = re.search('<input type=\\"hidden\\" name=\\"bl\\" value=\\"([^\\"]*)\\"', r.text)
        if m:
            data: dict[str, str] = {"gl": "DE", "pc": "yt", "continue": channel_url, "x": "6", "bl": m.group(1), "hl": "de", "set_eom": "true"}
            s.post("https://consent.youtube.com/save", data=data, timeout=timeout)

def parse_vtt(vtt_path: str) -> list[dict[str, str]]:
    """Parse VTT subtitle file and return list of subtitle segments."""
    result = word_level_vtt_parser(vtt_path)
    if len(result) == 0:
        result = normal_vtt_parser(vtt_path)
    if len(result) == 0:
        import logging
        logging.getLogger(__name__).error("Error: Failed to parse subtitles for: %s", vtt_path)
    return result

def normal_vtt_parser(vtt_path: str) -> list[dict[str, str]]:
    """Parse standard VTT format subtitles."""
    result: list[dict[str, str]] = []
    for caption in webvtt.read(vtt_path):
        start_time = caption.start
        stop_time = caption.end
        text = caption.text
        result.append({"start_time": start_time, "stop_time": stop_time, "text": text})
    return result

def word_level_vtt_parser(vtt_path: str) -> list[dict[str, str]]:
    """
    Extract start time and text from VTT file with word-level timing.
    """
    result: list[dict[str, str]] = []
    time_pattern = "^(.*) align:start position:0%"
    with Path(vtt_path).open("r") as f:
        lines = f.readlines()
    for count, line in enumerate(lines):
        time_match = re.match(time_pattern, line)
        if time_match:
            start = re.search("^(.*) -->", time_match.group(1))
            if start is None:
                continue
            start_time = start.group(1)
            stop = re.search("--> (.*)", time_match.group(1))
            if stop is None:
                continue
            stop_time = stop.group(1)
            sub_titles = lines[count + 1]
            if result and result[-1]["text"] == sub_titles.strip("\n"):
                result[-1] = {"start_time": start_time, "stop_time": stop_time, "text": sub_titles.strip("\n")}
            else:
                result.append({"start_time": start_time, "stop_time": stop_time, "text": sub_titles.strip("\n")})
    return result
