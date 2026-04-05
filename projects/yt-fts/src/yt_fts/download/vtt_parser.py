"""
VTT parsing and validation utilities for YouTube transcripts.

Provides VTT file operations including parsing, validation, and file discovery.
Extracted from utils/helpers.py and download_handler.py for better modularity.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import webvtt
    WEBVTT_AVAILABLE = True
except ImportError:
    WEBVTT_AVAILABLE = False

logger = logging.getLogger(__name__)


class VttParseError(Exception):
    """Exception raised when VTT parsing fails."""

    def __init__(self, message: str, vtt_path: str | None = None) -> None:
        super().__init__(message)
        self.vtt_path = vtt_path


def validate_vtt_file(vtt_path: Path | str) -> bool:
    """
    Check if a VTT file exists and is valid.
    
    Args:
        vtt_path: Path to the VTT file to validate
    
    Returns:
        True if VTT file exists and has content, False otherwise
    """
    path = Path(vtt_path)
    if not path.exists():
        return False
    return path.stat().st_size > 0


def find_vtt_file(
    video_id: str,
    tmp_dir: str | Path | None = None,
    language: str = "en",
) -> Path | None:
    """
    Find the actual VTT file among possible variants.
    
    VTT files may have different naming patterns depending on yt-dlp version
    and download options. This function searches for common variants.
    
    Args:
        video_id: YouTube video ID
        tmp_dir: Temporary directory to search (defaults to current directory)
        language: Language code for subtitles
    
    Returns:
        Path to the VTT file if found, None otherwise
    """
    base_dir = Path(tmp_dir) if tmp_dir else Path(".")
    
    # Common VTT file patterns to try
    patterns = [
        f"{video_id}.{language}.vtt",
        f"{video_id}.vtt",
        f"{video_id}.en.{language}.vtt",
    ]
    
    for pattern in patterns:
        vtt_path = base_dir / pattern
        if vtt_path.exists():
            return vtt_path
    
    return None


def get_vtt_variants(
    video_id: str,
    language: str = "en",
) -> list[str]:
    """
    Get list of possible VTT file paths for a video.
    
    Args:
        video_id: YouTube video ID
        language: Language code for subtitles
    
    Returns:
        List of possible VTT file names
    """
    return [
        f"{video_id}.{language}.vtt",
        f"{video_id}.vtt",
        f"{video_id}.en.{language}.vtt",
    ]


def extract_video_id_from_vtt_path(vtt_path: Path | str) -> str | None:
    """
    Extract video ID from a VTT file path.
    
    Args:
        vtt_path: Path to the VTT file
    
    Returns:
        Video ID if extracted successfully, None otherwise
    """
    path = Path(vtt_path)
    # Extract filename without extension
    stem = path.stem
    
    # Handle patterns like "abc123.en.vtt" -> "abc123"
    if "." in stem:
        stem = stem.split(".")[0]
    
    # YouTube video IDs are typically 11 characters
    if len(stem) == 11 and stem.isalnum():
        return stem
    
    return None


def get_vtt_files_from_tmpdir(tmp_dir: str | Path) -> list[Path]:
    """
    List all VTT files in a directory.
    
    Args:
        tmp_dir: Directory to search for VTT files
    
    Returns:
        List of Path objects for VTT files found
    """
    base_dir = Path(tmp_dir)
    if not base_dir.exists():
        return []
    
    return list(base_dir.glob("*.vtt"))
