"""
Official YouTube caption transcription engine.

Bridges the new transcription abstraction with the existing yt-dlp
caption extraction used by yt-fts.
"""
import logging
import re
import tempfile
from pathlib import Path

from yt_fts.transcribe.base import TranscriptionEngine
from yt_fts.transcribe.schema import SourceType, Transcript, TranscriptChunk

logger = logging.getLogger(__name__)

def get_subtitles(video_id: str, url: str | None=None, language: str="en", tmp_dir: str | None=None) -> list[tuple[str, str, str]]:
    """
    Download and extract subtitles from YouTube.

    Args:
        video_id: YouTube video ID
        url: Optional full video URL (constructed from video_id if None)
        language: Language code for subtitles
        tmp_dir: Temporary directory for VTT files

    Returns:
        List of tuples (start_time, stop_time, text) in "HH:MM:SS.mmm" format
    """
    if url is None:
        url = f"https://www.youtube.com/watch?v={video_id}"
    if tmp_dir is None:
        tmp_dir = tempfile.gettempdir()
    import yt_dlp
    vtt_path = f"{tmp_dir}/{video_id}.{language}.vtt"
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "writesubtitles": True, "writeautomaticsub": True, "subtitleslangs": [language, "en-US", "en-GB", "en"], "subtitlesformat": "vtt", "outtmpl": f"{tmp_dir}/{video_id}"}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get("subtitles", {})
            auto_captions = info.get("automatic_captions", {})
            if not subtitles and (not auto_captions):
                return []
            ydl.download([url])
            for lang in [language, "en-US", "en-GB", "en"]:
                candidate = f"{tmp_dir}/{video_id}.{lang}.vtt"
                if Path(candidate).exists():
                    vtt_path = candidate
                    break
                candidate = f"{tmp_dir}/{video_id}.{lang.replace('-', '_')}.vtt"
                if Path(candidate).exists():
                    vtt_path = candidate
                    break
            return _parse_vtt_to_tuples(vtt_path)
    except Exception as e:
        logger.warning("Failed to download captions for %s: %s", video_id, e)
    return []

def _parse_vtt_to_tuples(vtt_path: str) -> list[tuple[str, str, str]]:
    """
    Parse VTT file into list of (start_time, stop_time, text) tuples.

    Args:
        vtt_path: Path to VTT file

    Returns:
        List of tuples with timestamp strings and text
    """
    if not Path(vtt_path).exists():
        return []
    result: list[tuple[str, str, str]] = []
    try:
        import webvtt
        for caption in webvtt.read(vtt_path):
            result.append((str(caption.start), str(caption.end), caption.text))
    except Exception:
        result = _word_level_vtt_parser(vtt_path)
    return result

def _word_level_vtt_parser(vtt_path: str) -> list[tuple[str, str, str]]:
    """
    Parse VTT file using regex for word-level captions.

    Args:
        vtt_path: Path to VTT file

    Returns:
        List of tuples with timestamp strings and text
    """
    result: list[tuple[str, str, str]] = []
    time_pattern = "^(.*) align:start position:0%"
    with Path(vtt_path).open("r") as f:
        lines = f.readlines()
    for count, line in enumerate(lines):
        time_match = re.match(time_pattern, line)
        if time_match:
            start = re.search("^(.*) -->", time_match.group(1))
            start_time = start.group(1) if start else "00:00:00.000"
            stop = re.search("--> (.*)", time_match.group(1))
            stop_time = stop.group(1) if stop else "00:00:00.000"
            if count + 1 < len(lines):
                sub_titles = lines[count + 1].strip()
                if result and result[-1][2] == sub_titles:
                    result[-1] = (start_time, stop_time, sub_titles)
                else:
                    result.append((start_time, stop_time, sub_titles))
    return result

class OfficialCaptionEngine(TranscriptionEngine):
    """
    Engine that extracts official YouTube captions.

    Uses yt-dlp to download existing captions from YouTube.
    This is the fastest method when captions are available.
    """

    def __init__(self, tmp_dir: str | None=None):
        """
        Initialize the official caption engine.

        Args:
            tmp_dir: Directory for temporary VTT files (uses system temp if None)
        """
        self.tmp_dir = tmp_dir

    def transcribe(self, audio_path: str | None=None, video_id: str | None=None, url: str | None=None, language: str="en") -> Transcript:
        """
        Extract official captions from YouTube.

        Args:
            audio_path: YouTube video ID (alias for base class compatibility)
            video_id: YouTube video ID (preferred parameter name)
            url: Optional full video URL
            language: Preferred language code

        Returns:
            Transcript object with caption data
        """
        if video_id is None:
            video_id = audio_path
        if video_id is None:
            msg = "Either video_id or audio_path must be provided"
            raise ValueError(msg)
        subtitle_tuples = get_subtitles(video_id=video_id, url=url, language=language, tmp_dir=self.tmp_dir)
        chunks = []
        for start_str, stop_str, text in subtitle_tuples:
            start_time = _parse_timestamp_to_seconds(start_str)
            stop_time = _parse_timestamp_to_seconds(stop_str)
            duration = stop_time - start_time
            chunks.append(TranscriptChunk(text=text, start_time=start_time, duration=duration))
        return Transcript(video_id=video_id, language=language, source_type=SourceType.OFFICIAL, chunks=chunks)

def _parse_timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert VTT timestamp to seconds.

    Args:
        timestamp: Time string in format "HH:MM:SS.mmm" or "MM:SS.mmm"

    Returns:
        Time in seconds as float
    """
    try:
        if hasattr(timestamp, "seconds"):
            return float(timestamp.seconds)
        parts = str(timestamp).split(":")
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        if len(parts) == 2:
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        return float(parts[0]) if parts else 0.0
    except (ValueError, AttributeError):
        return 0.0
