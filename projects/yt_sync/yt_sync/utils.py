# yt_sync/utils.py

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MAX_FILENAME_LENGTH = 200
HANGUL_JUNGSEONG_FILLER, HANGUL_FILLER, HALFWIDTH_HANGUL_FILLER = 0x1160, 0x3164, 0xFFA0
IDEOGRAPHIC_SPACE, ZERO_WIDTH_NO_BREAK_SPACE = 0x3000, 0xFEFF
VIDEO_EXTENSIONS = [
    ".mp4",
    ".mkv",
    ".webm",
    ".mov",
    ".avi",
    ".flv",
    ".mpg",
    ".mpeg",
    ".wmv",
    ".ts",
]


def _sanitize_numeric_field(
    value: Any, default: int | float = 0
) -> int | float:
    """Safely convert a field to a numeric type, handling strings and edge cases."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.]", "", value)
        if not cleaned:
            return default
        try:
            return float(cleaned) if "." in cleaned else int(cleaned)
        except (ValueError, TypeError):
            return default
    try:
        return float(value)
    except (ValueError, TypeError, AttributeError):
        return default


def _sanitize_format_entry(fmt: dict[str, Any]) -> dict[str, Any] | None:
    """Sanitizes a single format entry, returning a clean dict or None if critically malformed."""
    try:
        if not fmt.get("format_id"):
            logger.debug("Discarding format entry: missing format_id")
            return None

        sanitized = fmt.copy()
        sanitized["height"] = _sanitize_numeric_field(fmt.get("height"))
        sanitized["width"] = _sanitize_numeric_field(fmt.get("width"))
        sanitized["fps"] = _sanitize_numeric_field(fmt.get("fps"))
        sanitized["tbr"] = _sanitize_numeric_field(fmt.get("tbr"))
        sanitized["abr"] = _sanitize_numeric_field(fmt.get("abr"))
        sanitized["vbr"] = _sanitize_numeric_field(fmt.get("vbr"))

        if sanitized.get("vcodec") and sanitized["vcodec"] != "none":
            if sanitized["height"] <= 0 and sanitized["width"] <= 0:
                logger.debug(
                    f"Discarding video format {fmt.get('format_id')}: invalid dimensions"
                )
                return None

        return sanitized
    except Exception as e:
        logger.warning(
            f"Failed to sanitize format {fmt.get('format_id', 'unknown')}: {e}"
        )
        return None


def _calculate_video_quality_score(fmt: dict[str, Any]) -> float:
    """Calculates a quality score for a video format."""
    resolution_score = fmt.get("height", 0) * fmt.get("width", 0)
    bitrate_score = fmt.get("vbr", 0) if fmt.get("vbr", 0) > 0 else fmt.get("tbr", 0)
    fps_multiplier = min(fmt.get("fps", 30) / 30.0, 2.0)
    return (resolution_score * 1000) + (bitrate_score * 10) + (fps_multiplier * 100)


def _calculate_audio_quality_score(fmt: dict[str, Any]) -> float:
    """Calculates a quality score for an audio format."""
    return fmt.get("abr", 0) if fmt.get("abr", 0) > 0 else fmt.get("tbr", 0)


def select_best_formats_programmatically(formats: list[dict[str, Any]]) -> str:
    """
    Defensively selects the best video and audio formats from yt-dlp's list.
    This function implements a multi-layer sanitization and fallback strategy.
    """
    if not formats:
        raise ValueError("Format list is empty.")

    sanitized_formats = [
        f for f in (_sanitize_format_entry(fmt) for fmt in formats) if f
    ]
    if not sanitized_formats:
        raise ValueError("No usable formats found after sanitization.")

    video_only = [
        f
        for f in sanitized_formats
        if f.get("vcodec") not in (None, "none") and f.get("acodec") in (None, "none")
    ]
    audio_only = [
        f
        for f in sanitized_formats
        if f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")
    ]
    combined = [
        f
        for f in sanitized_formats
        if f.get("vcodec") not in (None, "none")
        and f.get("acodec") not in (None, "none")
    ]

    if video_only and audio_only:
        best_video = max(video_only, key=_calculate_video_quality_score)
        best_audio = max(audio_only, key=_calculate_audio_quality_score)
        logger.debug(
            f"Selected video format {best_video['format_id']} + audio format {best_audio['format_id']}"
        )
        return f"{best_video['format_id']}+{best_audio['format_id']}"

    if combined:
        best_combined = max(
            combined,
            key=lambda f: _calculate_video_quality_score(f)
            + _calculate_audio_quality_score(f),
        )
        logger.debug(
            f"Selected combined format {best_combined['format_id']} as fallback."
        )
        return best_combined["format_id"]

    logger.error(
        "No separate or combined formats could be selected, returning default selector."
    )
    return "bestvideo+bestaudio/best[height<=?2160]/best"


def extract_handle_from_url(url: str) -> str | None:
    """Extract the channel handle from a YouTube URL."""
    handle_match = re.search(r"@([^/]+)", url)
    if handle_match:
        return handle_match.group(1)

    channel_match = re.search(r"/channel/([^/]+)", url)
    if channel_match:
        return channel_match.group(1)

    logger.warning(f"Could not extract handle from URL: {url}")
    return None


def get_id_from_filename(filename: str) -> str | None:
    """Extract video ID from filename. Assumes format: 'title [ID].ext'"""
    match = re.search(r"\[([a-zA-Z0-9_-]{11})\]", filename)
    return match.group(1) if match else None


def sanitize_filename(name: str) -> str:
    """Enhanced sanitization with Unicode normalization and word-aware length limiting."""
    if name == "None":
        return "untitled"
    if not name:
        return "untitled"
    name = unicodedata.normalize("NFKC", name)
    cleaned_chars = []
    for char in name:
        category = unicodedata.category(char)
        code_point = ord(char)
        if (
            category.startswith(("Z", "C"))
            or code_point
            in [
                HANGUL_JUNGSEONG_FILLER,
                HANGUL_FILLER,
                HALFWIDTH_HANGUL_FILLER,
                IDEOGRAPHIC_SPACE,
                ZERO_WIDTH_NO_BREAK_SPACE,
            ]
            or (0x2000 <= code_point <= 0x200F)
            or (0x2028 <= code_point <= 0x202F)
            or (0x205F <= code_point <= 0x206F)
        ):
            if cleaned_chars and cleaned_chars[-1] != " ":
                cleaned_chars.append(" ")
        else:
            cleaned_chars.append(char)
    name = "".join(cleaned_chars)
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        return "untitled"
    if len(name) > MAX_FILENAME_LENGTH:
        name = name[:MAX_FILENAME_LENGTH]
    return name


def get_optimal_format_selector(args: Any) -> str:
    """Returns optimized format selector string for the legacy downloader."""
    if hasattr(args, "format") and args.format:
        return args.format
    return "bestvideo[height>=?720][height<=?2160]+bestaudio/best[height<=?2160]/best"


def extract_channel_info_with_ytdlp(url: str) -> dict[str, Any]:
    """Extracts basic channel info using yt-dlp as a fallback."""
    try:
        import yt_dlp
    except ImportError:
        raise ImportError("yt-dlp library is required for this function.")

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": True,
        "dump_single_json": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError("yt-dlp could not extract channel info.")

        handle = info.get("channel_handle") or info.get("uploader_id")
        if not handle:
            raise ValueError("yt-dlp could not extract a unique channel handle or ID.")

        channel_id = info.get("channel_id")
        if not channel_id or not channel_id.startswith("UC"):
            raise ValueError(f"yt-dlp did not return a valid channel ID for {handle}")

        uploads_playlist_id = "UU" + channel_id[2:]

        return {
            "handle": handle,
            "title": info.get("channel") or info.get("uploader"),
            "uploads_playlist_id": uploads_playlist_id,
        }


def get_video_files_in_dir(directory: Path) -> list[Path]:
    """Returns a list of all video files in a given directory."""
    return [
        f
        for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]
