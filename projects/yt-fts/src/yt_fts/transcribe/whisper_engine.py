"""
Local Whisper transcription engine.

Uses faster-whisper (optional dependency) for local transcription.
Gracefully degrades if the package is not installed.
"""
from __future__ import annotations

import logging
from typing import Any

from yt_fts.transcribe.base import TranscriptionEngine
from yt_fts.transcribe.schema import SourceType, Transcript, TranscriptChunk

logger = logging.getLogger(__name__)
try:
    from faster_whisper import WhisperModel

    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None  # type: ignore[import-untyped]


class TranscriptionError(Exception):
    """Raised when transcription fails."""


class CaptionNotFoundError(Exception):
    """Raised when no captions are available for a video."""


VALID_MODEL_SIZES = [
    "tiny",
    "base",
    "small",
    "medium",
    "large",
    "large-v1",
    "large-v2",
    "large-v3",
]
VALID_DEVICES = ["cpu", "cuda", "auto"]


class LocalWhisperEngine(TranscriptionEngine):
    """
    Local Whisper transcription using faster-whisper.

    This engine processes audio files locally using Whisper.
    Requires faster-whisper to be installed.

    Device selection:
    - CUDA if available (GPU)
    - Falls back to CPU
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str | None = None,
        compute_type: str | None = None,
    ):
        """
        Initialize the Whisper engine.

        Args:
            model_size: Model size ("tiny", "base", "small", "medium", "large")
            device: Force device ("cuda", "cpu", or None for auto-detect)
            compute_type: Compute type ("float16", "int8", etc.)

        Raises:
            ValueError: If invalid model_size or device is provided
        """
        if model_size not in VALID_MODEL_SIZES:
            message = (
                f"Invalid model_size: {model_size}. Must be one of {VALID_MODEL_SIZES}"
            )
            raise ValueError(message)
        self.model_size = model_size
        if device is None:
            self.device = "cpu"
        elif device not in VALID_DEVICES:
            message = f"Invalid device: {device}. Must be one of {VALID_DEVICES}"
            raise ValueError(message)
        else:
            self.device = device
        if compute_type is None:
            compute_type = "float16" if self.device == "cuda" else "int8"
        self.compute_type = compute_type
        self._model: Any = None

    def _get_model(self) -> Any:
        """Lazy-load the Whisper model."""
        if self._model is None:
            if WhisperModel is None:
                return None
            logger.info(
                "Loading Whisper model (size=%s, device=%s, compute_type=%s)",
                self.model_size,
                self.device,
                self.compute_type,
            )
            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio_path: str, **kwargs: Any) -> Transcript:
        """
        Transcribe an audio file using local Whisper.

        Args:
            audio_path: Path to audio file
            **kwargs: Additional parameters including:
                - video_id: YouTube video ID
                - language: Optional language code (auto-detected if None)
                - translate: Whether to translate to English

        Returns:
            Transcript object with transcription results

        Raises:
            TranscriptionError: If transcription fails
        """
        video_id = kwargs.get('video_id', '')
        language = kwargs.get('language')
        translate = kwargs.get('translate', False)
        model = self._get_model()
        if model is None:
            message = "faster-whisper is not installed"
            raise TranscriptionError(message)
        try:
            transcribe_kwargs: dict[str, Any] = {}
            if language:
                transcribe_kwargs["language"] = language
            if translate:
                transcribe_kwargs["task"] = "translate"
            transcribe_kwargs.update(kwargs)
            segments, info = model.transcribe(audio_path, **transcribe_kwargs)
            chunks = []
            for segment in segments:
                duration = segment.end - segment.start
                chunks.append(
                    TranscriptChunk(
                        text=segment.text.strip(),
                        start_time=segment.start,
                        duration=duration,
                    )
                )
            detected_language = getattr(info, "language", language or "en")
            return Transcript(
                video_id=video_id,
                language=detected_language,
                source_type=SourceType.GENERATED_WHISPER,
                chunks=chunks,
            )
        except Exception as e:
            message = f"Whisper transcription failed: {e}"
            raise TranscriptionError(message) from e
