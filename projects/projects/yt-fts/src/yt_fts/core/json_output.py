"""
JSON output utilities for yt-fts CLI commands.

This module provides helper functions for generating JSON output
from various CLI commands while maintaining compatibility with
existing Rich-formatted output.
"""

import json
from datetime import datetime, timezone
from typing import Any

import click


def output_json(data: dict[str, Any]) -> None:
    """
    Output data as JSON to stdout.

    Args:
        data: Dictionary containing the data to serialize as JSON
    """
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def format_search_results_json(
    query: str,
    scope: str,
    results: list[Any],
    use_fts: bool = True,
    use_vector: bool = False,
) -> dict[str, Any]:
    """
    Format search results as JSON structure.

    Args:
        query: The search query string
        scope: Search scope ('all', 'channel', 'video')
        results: List of search results (dict or object format)
        use_fts: Whether full-text search was used
        use_vector: Whether vector search was used

    Returns:
        Dictionary with structured search results
    """
    # Group results by video
    videos_dict: dict[str, dict[str, Any]] = {}
    channel_names = set()

    for result in results:
        # Handle both dict and object formats
        if isinstance(result, dict):
            video_id = result.get("video_id", "")
            video_title = result.get("video_title", result.get("title", "Unknown"))
            video_date = result.get("video_date", "")
            channel_name = result.get("channel_name", result.get("channel", "Unknown"))
            timestamp = result.get("timestamp", result.get("start_time", "00:00:00"))
            text = result.get("text", "")
            link = result.get("link", "")
            relevance_score = result.get("relevance_score", result.get("similarity", None))
            result_type = result.get("result_type", "fts")
        else:
            video_id = getattr(result, "video_id", "")
            video_title = getattr(result, "video_title", "Unknown")
            video_date = getattr(result, "video_date", "")
            channel_name = getattr(result, "channel_name", getattr(result, "channel", "Unknown"))
            timestamp = getattr(result, "timestamp", getattr(result, "start_time", "00:00:00"))
            text = getattr(result, "text", "")
            link = getattr(result, "link", "")
            relevance_score = getattr(result, "relevance_score", getattr(result, "similarity", None))
            result_type = getattr(result, "result_type", "fts")

        channel_names.add(channel_name)

        # Initialize video entry if not exists
        if video_id not in videos_dict:
            videos_dict[video_id] = {
                "channel_name": channel_name,
                "video_id": video_id,
                "video_title": video_title,
                "video_date": video_date,
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "quotes": []
            }

        # Add quote to video
        quote_entry = {
            "timestamp": timestamp,
            "text": text,
            "url": link
        }

        # Add relevance score if available (for vector search)
        if relevance_score is not None:
            quote_entry["relevance_score"] = round(float(relevance_score), 3)

        # Add result type
        quote_entry["search_type"] = result_type

        videos_dict[video_id]["quotes"].append(quote_entry)

    # Convert to list
    videos_list = list(videos_dict.values())

    # Build output structure
    return {
        "query": query,
        "scope": scope,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "matches": sum(len(v["quotes"]) for v in videos_list),
        "videos": len(videos_list),
        "channels": len(channel_names),
        "search_types": {
            "full_text": use_fts,
            "vector": use_vector
        },
        "results": videos_list
    }



def format_channel_list_json(channels: list[tuple]) -> dict[str, Any]:
    """
    Format channel list as JSON structure.

    Args:
        channels: List of channel tuples from database

    Returns:
        Dictionary with structured channel list
    """
    channel_list = []

    for channel in channels:
        row_id = channel[0]
        channel_id = channel[1]
        channel_name = channel[2]
        channel_url = f"https://www.youtube.com/channel/{channel_id}"

        # Get video count
        from .database import get_num_vids
        video_count = get_num_vids(channel_id)

        channel_entry = {
            "id": row_id,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "channel_url": channel_url,
            "video_count": video_count
        }

        # Check if semantic search is enabled
        try:
            from yt_fts.ui.list_formatter import check_ss_enabled
            if check_ss_enabled(channel_id):
                channel_entry["semantic_search_enabled"] = True
        except Exception:
            pass

        channel_list.append(channel_entry)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_channels": len(channel_list),
        "channels": channel_list
    }


def format_video_list_json(videos: list[tuple], channel_id: str) -> dict[str, Any]:
    """
    Format video list for a channel as JSON structure.

    Args:
        videos: List of video tuples from database
        channel_id: Channel ID for the videos

    Returns:
        Dictionary with structured video list
    """
    from .database import get_channel_name_from_id, get_title_from_db

    channel_name = get_channel_name_from_id(channel_id)
    video_list = []

    for video in videos:
        video_id = video[0]
        video_title = get_title_from_db(video_id)
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        video_list.append({
            "video_id": video_id,
            "video_title": video_title,
            "video_url": video_url
        })

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_url": f"https://www.youtube.com/channel/{channel_id}",
        "video_count": len(video_list),
        "videos": video_list
    }


def format_transcript_json(video_id: str, rows: list[tuple], video_title: str, video_length: str, word_count: int) -> dict[str, Any]:
    """
    Format video transcript as JSON structure.

    Args:
        video_id: Video ID
        rows: Subtitle rows from database
        video_title: Video title
        video_length: Video length string
        word_count: Total word count

    Returns:
        Dictionary with structured transcript
    """
    from yt_fts.utils.helpers import time_to_secs

    quotes = []

    for row in rows:
        timestamp = row[2]
        time = time_to_secs(timestamp)
        url = f"https://www.youtube.com/watch?v={video_id}&t={time}s"
        text = row[4]

        quotes.append({
            "timestamp": timestamp,
            "url": url,
            "text": text
        })

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "video_id": video_id,
        "video_title": video_title,
        "video_url": video_url,
        "video_length": video_length,
        "word_count": word_count,
        "quote_count": len(quotes),
        "quotes": quotes
    }


def format_error_json(message: str, error_type: str = "error") -> dict[str, Any]:
    """
    Format error message as JSON structure.

    Args:
        message: Error message
        error_type: Type of error ('error', 'warning', etc.)

    Returns:
        Dictionary with error information
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": error_type,
        "message": message
    }
