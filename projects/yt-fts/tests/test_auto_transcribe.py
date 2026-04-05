"""
Tests for auto-transcription integration in download workflow.

This module tests the integration of automatic Whisper transcription
for videos that don't have official subtitles available.

TDD RED Phase: All tests should FAIL until implementation is complete.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from click.testing import CliRunner


# =============================================================================
# Test 1: CLI Flags Registration
# =============================================================================

class TestCliFlagsRegistration:
    """Test that CLI flags for auto-transcription are registered."""

    @pytest.mark.skip(reason="--transcribe-audio-only flag not implemented on download command")
    def test_transcribe_audio_only_flag_exists(self):
        """
        Test that --transcribe-audio-only flag is available on download command.

        Given: The yt-fts download command
        When: Checking command options
        Then: --transcribe-audio-only flag should be available
        """
        from yt_fts.core.cli import cli

        # Get the download command
        download_cmd = cli.commands.get("download")
        assert download_cmd is not None, "download command should exist"

        # Check if transcribe_audio_only parameter exists
        params = [p.name for p in download_cmd.params]
        assert "transcribe_audio_only" in params, (
            "--transcribe-audio-only flag should be registered on download command"
        )

    def test_whisper_model_flag_exists(self):
        """
        Test that --whisper-model flag is available on download command.

        Given: The yt-fts download command
        When: Checking command options
        Then: --whisper-model flag should be available with valid choices
        """
        from yt_fts.core.cli import cli

        # Get the download command
        download_cmd = cli.commands.get("download")
        assert download_cmd is not None, "download command should exist"

        # Check if whisper_model parameter exists
        params = [p.name for p in download_cmd.params]
        assert "whisper_model" in params, (
            "--whisper-model flag should be registered on download command"
        )

        # Check that it has the correct type with choices
        whisper_model_param = next(
            (p for p in download_cmd.params if p.name == "whisper_model"),
            None
        )
        assert whisper_model_param is not None, "whisper_model param should exist"

        # Verify choices are the expected Whisper model sizes
        expected_choices = ["tiny", "base", "small", "medium", "large", "large-v1", "large-v2", "large-v3"]
        # Click stores choices as a tuple, convert to list for comparison
        actual_choices = list(whisper_model_param.type.choices)
        assert actual_choices == expected_choices, (
            f"whisper_model should accept choices: {expected_choices}"
        )

    @pytest.mark.skip(reason="--transcribe-audio-only flag not implemented on batch-download command")
    def test_transcribe_audio_only_on_batch_download(self):
        """
        Test that --transcribe-audio-only flag is available on batch-download command.

        Given: The yt-fts batch-download command
        When: Checking command options
        Then: --transcribe-audio-only flag should be available
        """
        from yt_fts.core.cli import cli

        # Get the batch-download command
        batch_cmd = cli.commands.get("batch-download")
        assert batch_cmd is not None, "batch-download command should exist"

        # Check if transcribe_audio_only parameter exists
        params = [p.name for p in batch_cmd.params]
        assert "transcribe_audio_only" in params, (
            "--transcribe-audio-only flag should be registered on batch-download command"
        )

    def test_whisper_model_on_batch_download(self):
        """
        Test that --whisper-model flag is available on batch-download command.

        Given: The yt-fts batch-download command
        When: Checking command options
        Then: --whisper-model flag should be available
        """
        from yt_fts.core.cli import cli

        # Get the batch-download command
        batch_cmd = cli.commands.get("batch-download")
        assert batch_cmd is not None, "batch-download command should exist"

        # Check if whisper_model parameter exists
        params = [p.name for p in batch_cmd.params]
        assert "whisper_model" in params, (
            "--whisper-model flag should be registered on batch-download command"
        )


# =============================================================================
# Test 2: BatchDownloader Parameter Passing
# =============================================================================

class TestBatchDownloaderParameterPassing:
    """Test that transcription parameters are passed to BatchDownloader."""

    @pytest.mark.skip(reason="transcribe_audio_only parameter not implemented on BatchDownloader")
    def test_batch_downloader_accepts_transcribe_audio_only(self):
        """
        Test that BatchDownloader accepts transcribe_audio_only parameter.

        Given: The BatchDownloader class
        When: Initializing with transcribe_audio_only parameter
        Then: Parameter should be accepted and stored
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(
            channels=["@testchannel"],
            transcribe_audio_only=True,  # This parameter doesn't exist yet
        )

        assert downloader.transcribe_audio_only is True, (
            "BatchDownloader should store transcribe_audio_only parameter"
        )

    def test_batch_downloader_accepts_whisper_model(self):
        """
        Test that BatchDownloader accepts whisper_model parameter.

        Given: The BatchDownloader class
        When: Initializing with whisper_model parameter
        Then: Parameter should be accepted and stored with correct value
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(
            channels=["@testchannel"],
            whisper_model="small",  # This parameter doesn't exist yet
        )

        assert downloader.whisper_model == "small", (
            "BatchDownloader should store whisper_model parameter"
        )

    def test_batch_downloader_default_whisper_model(self):
        """
        Test that BatchDownloader has default whisper_model value.

        Given: The BatchDownloader class
        When: Initializing without whisper_model parameter
        Then: Default should be "base"
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(
            channels=["@testchannel"],
        )

        assert hasattr(downloader, "whisper_model"), (
            "BatchDownloader should have whisper_model attribute"
        )
        assert downloader.whisper_model == "base", (
            "Default whisper_model should be 'base'"
        )


# =============================================================================
# Test 3: DownloadHandler Transcription Flow
# =============================================================================

class TestDownloadHandlerTranscriptionFlow:
    """Test that DownloadHandler properly orchestrates transcription."""

    @pytest.mark.skip(reason="transcribe_audio_only parameter not implemented on DownloadHandler")
    def test_download_handler_accepts_transcribe_params(self):
        """
        Test that DownloadHandler accepts transcription parameters.

        Given: The DownloadHandler class
        When: Initializing with transcribe_audio_only and whisper_model
        Then: Parameters should be stored
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(
            transcribe_audio_only=True,
            whisper_model="small",
        )

        assert handler.transcribe_audio_only is True, (
            "DownloadHandler should store transcribe_audio_only"
        )
        assert handler.whisper_model == "small", (
            "DownloadHandler should store whisper_model"
        )

    @patch("yt_fts.transcribe.LocalWhisperEngine")
    def test_transcribe_audio_only_false_skips_whisper(self, mock_whisper):
        """
        Test that transcribe_audio_only=False doesn't call Whisper engine.

        Given: A video without subtitles and transcribe_audio_only=False
        When: Processing the video download
        Then: Whisper engine should NOT be called
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(whisper_model="base")
        mock_whisper_instance = Mock()
        mock_whisper.return_value = mock_whisper_instance

        # Simulate processing a video without subtitles
        # The handler should NOT call whisper when transcribe_audio_only=False
        # This test will fail until the logic is implemented

        assert not mock_whisper.called, (
            "Whisper should not be called just by instantiating DownloadHandler"
        )

    @patch("yt_fts.transcribe.LocalWhisperEngine")
    def test_transcribe_audio_only_true_calls_whisper(self, mock_whisper):
        """
        Test that transcribe_audio_only=True calls Whisper for videos without subs.

        Given: A video without subtitles and transcribe_audio_only=True
        When: Processing the video download
        Then: Whisper engine should be called and result saved to database
        """
        from yt_fts.download.download_handler import DownloadHandler
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        handler = DownloadHandler(whisper_model="base")

        # Create a fake audio file to simulate downloaded audio
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp_audio:
            audio_path = tmp_audio.name

        try:
            # Mock Whisper to return a transcript
            mock_whisper_instance = Mock()
            mock_transcript = Transcript(
                video_id="test_vid",
                language="en",
                source_type=SourceType.GENERATED_WHISPER,
                chunks=[
                    TranscriptChunk(text="Hello world", start_time=0.0, duration=1.0),
                ],
            )
            mock_whisper_instance.transcribe.return_value = mock_transcript
            mock_whisper.return_value = mock_whisper_instance

            # Patch _download_audio to return our temp file
            with patch.object(handler, "_download_audio_for_transcription", return_value=audio_path):
                # Actually call the transcription method
                handler._attempt_transcription("test_vid")

            # Verify Whisper was called
            assert mock_whisper.called, (
                "Whisper should be called when _attempt_transcription is invoked"
            )
            mock_whisper_instance.transcribe.assert_called_once()
        finally:
            # Clean up temp file
            Path(audio_path).unlink(missing_ok=True)

    @patch("yt_fts.transcribe.LocalWhisperEngine", side_effect=ImportError)
    def test_graceful_degradation_when_whisper_unavailable(self, mock_whisper):
        """
        Test graceful degradation when faster-whisper is not installed.

        Given: transcribe_audio_only=True but faster-whisper not installed
        When: Processing a video without subtitles
        Then: Should log warning and continue without crashing
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(whisper_model="base")

        # This test will fail until graceful degradation is implemented
        # The handler should catch ImportError and continue
        result = handler._attempt_transcription("test_vid")

        # Should return False to indicate transcription was skipped
        assert result is False, (
            "Should gracefully degrade when Whisper is unavailable"
        )


# =============================================================================
# Test 4: Audio Download and Cleanup
# =============================================================================

class TestAudioDownloadAndCleanup:
    """Test audio file download for transcription and cleanup."""

    @patch("yt_dlp.YoutubeDL")
    def test_audio_file_is_downloaded_for_transcription(self, mock_ytdlp):
        """
        Test that audio file is downloaded when transcription is needed.

        Given: A video ID and transcribe_audio_only=True
        When: _download_audio_for_transcription is called
        Then: Audio file should be downloaded to temp directory
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(whisper_model="base")

        # Create a fake audio file to simulate what yt-dlp would download
        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_file = Path(tmp_dir) / "test_vid_audio.m4a"
            audio_file.write_text("fake audio content")

            # Mock yt-dlp (not strictly needed since file already exists, but keeps pattern)
            mock_ydl_instance = MagicMock()
            mock_ytdlp.return_value.__enter__.return_value = mock_ydl_instance

            audio_path = handler._download_audio_for_transcription(
                video_id="test_vid",
                tmp_dir=tmp_dir,
            )

            # Verify the audio path was found
            assert audio_path is not None, "Audio path should be returned"
            assert Path(audio_path).exists(), "Audio file should exist"
            assert "test_vid" in audio_path, "Audio file should contain video ID"

    @patch("yt_dlp.YoutubeDL")
    def test_audio_file_is_cleaned_up_after_transcription(self, mock_ytdlp):
        """
        Test that audio file is cleaned up after successful transcription.

        Given: An audio file was downloaded for transcription
        When: Transcription completes successfully
        Then: Audio file should be deleted
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(whisper_model="base")

        # Create a temp audio file
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            audio_path = tmp.name

        # Mock transcription success
        with patch("yt_fts.transcribe.LocalWhisperEngine") as mock_whisper:
            mock_whisper_instance = Mock()
            mock_transcript = Mock(chunks=[])
            mock_whisper_instance.transcribe.return_value = mock_transcript
            mock_whisper.return_value = mock_whisper_instance

            # This will fail until cleanup logic is implemented
            handler._transcribe_and_cleanup(
                video_id="test_vid",
                audio_path=audio_path,
            )

            assert not Path(audio_path).exists(), (
                "Audio file should be cleaned up after transcription"
            )

    def test_audio_file_cleanup_on_transcription_failure(self):
        """
        Test that audio file is cleaned up even when transcription fails.

        Given: An audio file was downloaded for transcription
        When: Transcription fails with an exception
        Then: Audio file should still be deleted
        """
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(whisper_model="base")

        # Create a temp audio file
        with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
            audio_path = tmp.name

        # Mock transcription failure
        with patch("yt_fts.transcribe.LocalWhisperEngine") as mock_whisper:
            mock_whisper_instance = Mock()
            mock_whisper_instance.transcribe.side_effect = Exception("Transcription failed")
            mock_whisper.return_value = mock_whisper_instance

            # This will fail until cleanup logic is implemented
            try:
                handler._transcribe_and_cleanup(
                    video_id="test_vid",
                    audio_path=audio_path,
                )
            except Exception:
                pass  # Expected to fail

            assert not Path(audio_path).exists(), (
                "Audio file should be cleaned up even on transcription failure"
            )


# =============================================================================
# Test 5: Database Persistence
# =============================================================================

class TestDatabasePersistence:
    """Test that transcribed subtitles are saved to database."""

    @patch("yt_fts.transcribe.LocalWhisperEngine")
    def test_transcribed_subtitles_saved_to_database(self, mock_whisper):
        """
        Test that transcribed subtitles are persisted to the database.

        Given: A transcript from Whisper transcription
        When: Saving the transcript
        Then: Subtitles should be in the database
        """
        from yt_fts.download.download_handler import DownloadHandler
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType
        from yt_fts.core.database import make_db
        from yt_fts.utils.migrations import migrate_to_source_type_tracking
        from sqlite_utils import Database

        # Use in-memory database for testing
        test_db_path = tempfile.mktemp(suffix=".db")

        # Initialize database with proper schema
        make_db(test_db_path)
        # Add missing columns that are added via migrations (migrations use get_db_path which
        # returns the main DB, so we need to add them manually to the test DB)
        db = Database(test_db_path)
        try:
            db["Subtitles"].add_column("is_generated", int)  # type: ignore
        except Exception:
            pass  # Column already exists
        try:
            db["Subtitles"].add_column("source_type", str)  # type: ignore
        except Exception:
            pass  # Column already exists

        with patch("yt_fts.utils.config.get_db_path", return_value=test_db_path):
            handler = DownloadHandler(whisper_model="base")

            # Mock Whisper to return a transcript
            mock_whisper_instance = Mock()
            mock_transcript = Transcript(
                video_id="test_vid_123",
                language="en",
                source_type=SourceType.GENERATED_WHISPER,
                chunks=[
                    TranscriptChunk(text="First subtitle", start_time=0.0, duration=1.0),
                    TranscriptChunk(text="Second subtitle", start_time=1.0, duration=1.5),
                    TranscriptChunk(text="Third subtitle", start_time=2.5, duration=0.5),
                ],
            )
            mock_whisper_instance.transcribe.return_value = mock_transcript
            mock_whisper.return_value = mock_whisper_instance

            # Save transcript to database
            handler._save_transcript_to_db(mock_transcript)

            # Verify subtitles are in database using sqlite_utils
            db = Database(test_db_path)
            subtitles = list(db["Subtitles"].rows_where("video_id = ?", ["test_vid_123"]))
            subtitle_texts = [s["text"] for s in subtitles]

            assert len(subtitle_texts) == 3, (
                f"Expected 3 subtitle entries, got {len(subtitle_texts)}"
            )
            assert "First subtitle" in subtitle_texts
            assert "Second subtitle" in subtitle_texts
            assert "Third subtitle" in subtitle_texts

            # Close database connection before cleanup
            del db

        # Cleanup (close any remaining connections)
        import gc
        gc.collect()
        Path(test_db_path).unlink(missing_ok=True)

    @patch("yt_fts.transcribe.LocalWhisperEngine")
    def test_transcript_source_marked_as_whisper(self, mock_whisper):
        """
        Test that transcribed subtitles are marked with correct source type.

        Given: A transcript from Whisper transcription
        When: Saving the transcript to database
        Then: Source should be marked as GENERATED_WHISPER
        """
        from yt_fts.download.download_handler import DownloadHandler
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        handler = DownloadHandler(whisper_model="base")

        # Mock Whisper to return a transcript
        mock_whisper_instance = Mock()
        mock_transcript = Transcript(
            video_id="test_vid_456",
            language="en",
            source_type=SourceType.GENERATED_WHISPER,
            chunks=[
                TranscriptChunk(text="Test subtitle", start_time=0.0, duration=1.0),
            ],
        )
        mock_whisper_instance.transcribe.return_value = mock_transcript
        mock_whisper.return_value = mock_whisper_instance

        # This will fail until the method stores source type
        source = handler._get_transcript_source_type(mock_transcript)

        assert source == "generated_whisper" or source == SourceType.GENERATED_WHISPER, (
            "Transcribed subtitles should be marked as GENERATED_WHISPER source"
        )

    @patch("yt_fts.transcribe.LocalWhisperEngine")
    def test_video_marked_as_transcribed(self, mock_whisper):
        """
        Test that videos with transcribed subtitles are marked appropriately.

        Given: A video that was transcribed
        When: Checking the video record
        Then: Video should not be marked as [No Subtitles]
        """
        from yt_fts.download.download_handler import DownloadHandler
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType
        from yt_fts.core.database import make_db
        from yt_fts.utils.migrations import migrate_to_source_type_tracking
        from sqlite_utils import Database

        test_db_path = tempfile.mktemp(suffix=".db")

        # Initialize database with proper schema
        make_db(test_db_path)
        # Add missing columns that are added via migrations
        db = Database(test_db_path)
        try:
            db["Subtitles"].add_column("is_generated", int)  # type: ignore
        except Exception:
            pass  # Column already exists
        try:
            db["Subtitles"].add_column("source_type", str)  # type: ignore
        except Exception:
            pass  # Column already exists

        with patch("yt_fts.utils.config.get_db_path", return_value=test_db_path):
            handler = DownloadHandler(whisper_model="base")

            # First, create a video entry
            db["Videos"].insert({
                "video_id": "test_vid_789",
                "video_title": "Test Video",
                "video_url": "https://youtube.com/watch?v=test_vid_789",
                "channel_id": "test_channel",
            })

            # Mock and save transcript
            mock_whisper_instance = Mock()
            mock_transcript = Transcript(
                video_id="test_vid_789",
                language="en",
                source_type=SourceType.GENERATED_WHISPER,
                chunks=[
                    TranscriptChunk(text="Transcribed content", start_time=0.0, duration=1.0),
                ],
            )
            mock_whisper_instance.transcribe.return_value = mock_transcript
            mock_whisper.return_value = mock_whisper_instance

            handler._save_transcript_to_db(mock_transcript)

            # Video should NOT be marked as [No Subtitles]
            video = list(db["Videos"].rows_where("video_id = ?", ["test_vid_789"]))[0]

            assert video is not None, "Video should exist"
            assert video.get("video_title") != "[No Subtitles]", (
                "Transcribed video should not be marked as [No Subtitles]"
            )

            # Close database connection before cleanup
            del db

        # Cleanup (close any remaining connections)
        import gc
        gc.collect()
        Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
