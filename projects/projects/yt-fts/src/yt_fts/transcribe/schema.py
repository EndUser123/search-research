"""
Data structures for transcription results.

Defines the core data models used across all transcription engines.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SourceType(Enum):
    """Enumeration of transcript source types."""

    OFFICIAL = "official"
    GENERATED_WHISPER = "generated_whisper"
    GENERATED_VISUAL = "generated_visual"


@dataclass
class Video:
    """
    Video metadata.

    Attributes:
        video_id: YouTube video ID
        title: Video title
        channel_id: Channel ID
        channel_name: Channel name
        duration: Video duration in seconds (optional)
        publish_date: Publication date string (optional)
        thumbnail_url: URL to thumbnail image (optional)
    """

    video_id: str
    title: str
    channel_id: str
    channel_name: str
    duration: float | None = None
    publish_date: str | None = None
    thumbnail_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert Video to dictionary representation."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "channel_id": self.channel_id,
            "channel_name": self.channel_name,
            "duration": self.duration,
            "publish_date": self.publish_date,
            "thumbnail_url": self.thumbnail_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Video":
        """Create Video from dictionary representation."""
        return cls(
            video_id=data["video_id"],
            title=data["title"],
            channel_id=data["channel_id"],
            channel_name=data["channel_name"],
            duration=data.get("duration"),
            publish_date=data.get("publish_date"),
            thumbnail_url=data.get("thumbnail_url"),
        )


@dataclass
class TranscriptChunk:
    """
    A single chunk of transcript text with timing information.

    Attributes:
        text: The transcript text for this chunk
        start_time: Start time in seconds (e.g., 1.5)
        duration: Duration of the chunk in seconds (e.g., 3.5)
    """

    text: str
    start_time: float
    duration: float

    def __post_init__(self) -> None:
        """Validate the chunk data after initialization."""
        if self.start_time < 0:
            msg = f"start_time must be non-negative, got {self.start_time}"
            raise ValueError(msg)
        if self.duration <= 0:
            msg = f"duration must be positive, got {self.duration}"
            raise ValueError(msg)
        if not self.text or not self.text.strip():
            msg = "text cannot be empty"
            raise ValueError(msg)

    @property
    def end_time(self) -> float:
        """Calculate end time from start_time and duration."""
        return self.start_time + self.duration

    def to_dict(self) -> dict[str, Any]:
        """Convert TranscriptChunk to dictionary representation."""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranscriptChunk":
        """Create TranscriptChunk from dictionary representation."""
        return cls(
            text=data["text"],
            start_time=data["start_time"],
            duration=data["duration"],
        )


@dataclass
class Transcript:
    """
    A complete video transcript with metadata.

    Attributes:
        video_id: YouTube video ID
        language: Language code (e.g., "en", "es")
        source_type: Type of transcript source (SourceType enum)
        chunks: List of transcript chunks in chronological order
    """

    video_id: str
    language: str
    source_type: SourceType
    chunks: list[TranscriptChunk]

    def __post_init__(self) -> None:
        """Validate the transcript after initialization."""
        if not self.video_id:
            msg = "video_id cannot be empty"
            raise ValueError(msg)
        if not self.language:
            msg = "language cannot be empty"
            raise ValueError(msg)

    @property
    def duration(self) -> float:
        """Calculate total duration from the last chunk's end time."""
        if not self.chunks:
            return 0.0
        return self.chunks[-1].end_time

    @property
    def full_text(self) -> str:
        """Concatenate all chunk text with spaces."""
        return " ".join(chunk.text for chunk in self.chunks)

    def to_dict(self) -> dict[str, Any]:
        """Convert Transcript to dictionary representation."""
        return {
            "video_id": self.video_id,
            "language": self.language,
            "source_type": self.source_type.value,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transcript":
        """Create Transcript from dictionary representation."""
        source_type = (
            SourceType(data["source_type"])
            if isinstance(data["source_type"], str)
            else data["source_type"]
        )
        return cls(
            video_id=data["video_id"],
            language=data["language"],
            source_type=source_type,
            chunks=[
                TranscriptChunk.from_dict(chunk_data) for chunk_data in data["chunks"]
            ],
        )
