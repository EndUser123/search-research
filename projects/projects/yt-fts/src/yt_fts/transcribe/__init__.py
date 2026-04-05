"""
Transcription engine abstraction for yt-fts.

This module provides a unified interface for different transcription sources:
- OfficialCaptionEngine: Uses YouTube's built-in captions (via yt-dlp)
- LocalWhisperEngine: Uses local Whisper/faster-whisper for transcription

Exports:
    TranscriptionEngine: Abstract base class for all transcription engines
    Transcript: Dataclass representing a complete transcript
    TranscriptChunk: Dataclass representing a single subtitle chunk
    Video: Dataclass representing video metadata
    SourceType: Enum for transcript source types
    LocalWhisperEngine: Local Whisper transcription implementation
    OfficialCaptionEngine: Official YouTube caption wrapper
"""

from yt_fts.transcribe.base import TranscriptionEngine
from yt_fts.transcribe.official_engine import OfficialCaptionEngine
from yt_fts.transcribe.schema import (
    SourceType,
    Transcript,
    TranscriptChunk,
    Video,
)
from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

__all__ = [
    "LocalWhisperEngine",
    "OfficialCaptionEngine",
    "SourceType",
    "Transcript",
    "TranscriptChunk",
    "TranscriptionEngine",
    "Video",
]
