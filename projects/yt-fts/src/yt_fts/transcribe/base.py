"""
Abstract base class for transcription engines.

All transcription engines must implement the TranscriptionEngine interface
to provide a consistent API for transcript extraction.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from yt_fts.transcribe.schema import Transcript


class TranscriptionEngine(ABC):
    """
    Abstract base class for transcription engines.

    All transcription implementations must inherit from this class
    and implement the transcribe() method.
    """

    @abstractmethod
    def transcribe(self, audio_path: str, **kwargs: Any) -> Transcript:
        """
        Transcribe audio and return its transcript.

        Args:
            audio_path: Path to audio file or video identifier
            **kwargs: Additional engine-specific parameters

        Returns:
            Transcript object containing the transcription results

        Raises:
            TranscriptionError: If transcription fails
            CaptionNotFoundError: If no captions are available
        """
