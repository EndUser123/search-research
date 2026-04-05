"""
Transcription worker loop - processes videos from task queue.

Single-threaded worker that:
1. Checks out videos from the task queue
2. Downloads audio
3. Transcribes with Whisper
4. Saves transcript to database
5. Checks in as done or failed

Multiple instances can run in parallel - each independently checks out work.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from yt_fts.utils.config import get_db_path

from .transcription_worker import (
    checkin_video_done,
    checkin_video_failed,
    checkout_video,
    get_pending_count,
)

logger = logging.getLogger(__name__)


class TranscriptionWorker:
    """Single-threaded transcription worker using task queue pattern."""

    def __init__(
        self,
        channel_id: str,
        whisper_model: str = "base",
        keep_audio: bool = False,
        tmp_dir: str | None = None,
    ):
        """Initialize the transcription worker.

        Args:
            channel_id: Channel ID to process videos from
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            keep_audio: Keep audio files after transcription
            tmp_dir: Temporary directory for audio downloads
        """
        self.channel_id = channel_id
        self.whisper_model = whisper_model
        self.keep_audio = keep_audio
        self.tmp_dir = tmp_dir or tempfile.gettempdir()
        self.worker_id = f"worker-{os.getpid()}"
        self._whisper_engine = None

    def _get_whisper_engine(self):
        """Lazy-load the Whisper engine for transcription."""
        if self._whisper_engine is None:
            try:
                from yt_fts.transcribe import LocalWhisperEngine
                self._whisper_engine = LocalWhisperEngine(model_size=self.whisper_model)
                logger.info("Loaded Whisper model: %s", self.whisper_model)
            except ImportError as e:
                logger.exception("Failed to import Whisper: %s", e)
                self._whisper_engine = None
        return self._whisper_engine

    def _download_audio(self, video_id: str) -> str | None:
        """Download audio file for transcription using yt-dlp.

        Args:
            video_id: YouTube video ID

        Returns:
            Path to downloaded audio file, or None if download failed
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        audio_base = Path(self.tmp_dir) / f"{video_id}_audio"
        ydl_opts = {
            "format": "m4a/bestaudio/best",
            "outtmpl": str(audio_base),
            "quiet": True,
            "no_warnings": True,
            "overwrite": True,
        }

        try:
            import yt_dlp

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Find the downloaded file - try with extension first, then without
            audio_path = list(Path(self.tmp_dir).glob(f"{video_id}_audio.*"))
            if not audio_path:
                # Try without extension (yt-dlp may not add extension)
                audio_path = list(Path(self.tmp_dir).glob(f"{video_id}_audio"))
            if audio_path:
                return str(audio_path[0])
            return None
        except Exception as e:
            logger.exception("Failed to download audio for %s: %s", video_id, e)
            return None

    def _transcribe(self, audio_path: str, video_id: str) -> bool:
        """Transcribe audio file and save to database.

        Args:
            audio_path: Path to audio file
            video_id: YouTube video ID

        Returns:
            True if transcription succeeded, False otherwise
        """
        engine = self._get_whisper_engine()
        if engine is None:
            logger.error("Whisper engine not available")
            return False

        try:
            transcript = engine.transcribe(audio_path, video_id, language="en")
            self._save_transcript_to_db(transcript)
            return True
        except Exception as e:
            logger.exception("Transcription failed for %s: %s", video_id, e)
            return False

    def _save_transcript_to_db(self, transcript) -> None:
        """Save transcribed transcript to database.

        Args:
            transcript: Transcript object from Whisper engine
        """
        from sqlite_utils import Database

        db = Database(get_db_path())
        for chunk in transcript.chunks:
            start = int(chunk.start_time)
            duration = getattr(chunk, "duration", None)
            stop = int(start + duration) if duration else int(start + 5)
            db["Subtitles"].insert({
                "video_id": transcript.video_id,
                "start_time": str(start),
                "stop_time": str(stop),
                "text": chunk.text,
                "source_type": "whisper",
                "language_code": "en",
            })
        logger.info("Saved %d subtitle segments for %s", len(transcript.chunks), transcript.video_id)

    def process_video(self, video_id: str) -> bool:
        """Process a single video: download → transcribe → save.

        Args:
            video_id: YouTube video ID

        Returns:
            True if successful, False otherwise
        """
        logger.info("[%s] Processing: %s", self.worker_id, video_id)

        # Download audio
        audio_path = self._download_audio(video_id)
        if not audio_path:
            logger.error("[%s] Failed to download audio for %s", self.worker_id, video_id)
            return False

        logger.debug("[%s] Downloaded audio to: %s", self.worker_id, audio_path)

        # Transcribe
        success = self._transcribe(audio_path, video_id)

        # Cleanup
        if not self.keep_audio:
            Path(audio_path).unlink(missing_ok=True)

        if success:
            logger.info("[%s] ✓ Completed: %s", self.worker_id, video_id)
        else:
            logger.error("[%s] ✗ Failed: %s", self.worker_id, video_id)

        return success

    def run(self, limit: int | None = None) -> dict:
        """Run the worker loop until no more videos or limit reached.

        Args:
            limit: Maximum number of videos to process (None for unlimited)

        Returns:
            Dict with success_count, failed_count, total_count
        """
        success_count = 0
        failed_count = 0
        total_count = 0

        logger.info("[%s] Starting worker for channel: %s", self.worker_id, self.channel_id)
        pending = get_pending_count(self.channel_id)
        logger.info("[%s] Pending videos: %d", self.worker_id, pending)

        if limit:
            logger.info("[%s] Will process max %d videos", self.worker_id, limit)

        while True:
            # Check limit
            if limit is not None and total_count >= limit:
                logger.info("[%s] Reached limit of %d videos", self.worker_id, limit)
                break

            # Checkout a video
            video = checkout_video(self.channel_id, self.worker_id)
            if video is None:
                logger.info("[%s] No more videos to process", self.worker_id)
                break

            video_id = video["video_id"]
            total_count += 1

            # Process the video
            try:
                success = self.process_video(video_id)
                if success:
                    checkin_video_done(video_id)
                    success_count += 1
                else:
                    checkin_video_failed(video_id, "Transcription failed")
                    failed_count += 1
            except Exception as e:
                logger.exception("[%s] Error processing %s: %s", self.worker_id, video_id, e)
                checkin_video_failed(video_id, str(e))
                failed_count += 1

        logger.info(
            "[%s] Worker complete: %d success, %d failed, %d total",
            self.worker_id,
            success_count,
            failed_count,
            total_count,
        )

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total_count": total_count,
        }


def run_worker(
    channel_id: str,
    limit: int | None = None,
    whisper_model: str = "base",
    keep_audio: bool = False,
) -> dict:
    """Convenience function to run a transcription worker.

    Args:
        channel_id: Channel ID to process
        limit: Max videos to process (None for all pending)
        whisper_model: Whisper model size
        keep_audio: Keep audio files

    Returns:
        Dict with success_count, failed_count, total_count
    """
    worker = TranscriptionWorker(
        channel_id=channel_id,
        whisper_model=whisper_model,
        keep_audio=keep_audio,
    )
    return worker.run(limit=limit)
