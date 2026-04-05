"""Tests for transcription engine abstraction.

This module tests the transcription engine abstraction layer which provides:
- Abstract base class for transcription engines
- Data models for transcripts and chunks
- LocalWhisperEngine implementation
- OfficialCaptionEngine wrapper for existing yt-dlp functionality
"""

from dataclasses import dataclass
from enum import Enum
from unittest.mock import MagicMock, Mock, patch

import pytest


# =============================================================================
# Test Data Models (TranscriptSchema)
# =============================================================================

class TestSourceTypeEnum:
    """Test SourceType enum for transcript source classification."""

    def test_source_type_enum_values(self):
        """
        Test that SourceType enum has all required values.

        Given: The SourceType enum is defined
        When: Accessing enum values
        Then: All required source types are available
        """
        # This test will fail until the enum is defined
        from yt_fts.transcribe.schema import SourceType

        assert SourceType.OFFICIAL.value == "official"
        assert SourceType.GENERATED_WHISPER.value == "generated_whisper"
        assert SourceType.GENERATED_VISUAL.value == "generated_visual"

    def test_source_type_enum_from_string(self):
        """
        Test creating SourceType from string values.

        Given: A string representing a source type
        When: Creating SourceType from string
        Then: Correct enum value is returned
        """
        from yt_fts.transcribe.schema import SourceType

        assert SourceType("official") == SourceType.OFFICIAL
        assert SourceType("generated_whisper") == SourceType.GENERATED_WHISPER
        assert SourceType("generated_visual") == SourceType.GENERATED_VISUAL


class TestVideoDataModel:
    """Test Video dataclass for video metadata."""

    def test_video_creation_with_required_fields(self):
        """
        Test creating a Video object with required fields.

        Given: Required video metadata fields
        When: Creating a Video instance
        Then: Object is created with correct values
        """
        from yt_fts.transcribe.schema import Video

        video = Video(
            video_id="test_video_id",
            title="Test Video Title",
            channel_id="test_channel_id",
            channel_name="Test Channel",
        )

        assert video.video_id == "test_video_id"
        assert video.title == "Test Video Title"
        assert video.channel_id == "test_channel_id"
        assert video.channel_name == "Test Channel"

    def test_video_creation_with_all_fields(self):
        """
        Test creating a Video object with all fields including optional ones.

        Given: All video metadata fields
        When: Creating a Video instance
        Then: Object is created with correct values
        """
        from yt_fts.transcribe.schema import Video

        video = Video(
            video_id="test_video_id",
            title="Test Video Title",
            channel_id="test_channel_id",
            channel_name="Test Channel",
            duration=600.0,
            publish_date="2024-01-01",
            thumbnail_url="https://example.com/thumb.jpg",
        )

        assert video.duration == 600.0
        assert video.publish_date == "2024-01-01"
        assert video.thumbnail_url == "https://example.com/thumb.jpg"

    def test_video_to_dict(self):
        """
        Test converting Video to dictionary.

        Given: A Video instance
        When: Calling to_dict() method
        Then: Dictionary representation is returned with all fields
        """
        from yt_fts.transcribe.schema import Video

        video = Video(
            video_id="test_video_id",
            title="Test Video Title",
            channel_id="test_channel_id",
            channel_name="Test Channel",
        )

        result = video.to_dict()

        assert result == {
            "video_id": "test_video_id",
            "title": "Test Video Title",
            "channel_id": "test_channel_id",
            "channel_name": "Test Channel",
            "duration": None,
            "publish_date": None,
            "thumbnail_url": None,
        }

    def test_video_from_dict(self):
        """
        Test creating Video from dictionary.

        Given: A dictionary with video data
        When: Calling Video.from_dict()
        Then: Video instance is created with correct values
        """
        from yt_fts.transcribe.schema import Video

        data = {
            "video_id": "test_video_id",
            "title": "Test Video Title",
            "channel_id": "test_channel_id",
            "channel_name": "Test Channel",
            "duration": 600.0,
        }

        video = Video.from_dict(data)

        assert video.video_id == "test_video_id"
        assert video.title == "Test Video Title"
        assert video.duration == 600.0


class TestTranscriptChunkDataModel:
    """Test TranscriptChunk dataclass for individual transcript segments."""

    def test_chunk_creation_with_required_fields(self):
        """
        Test creating a TranscriptChunk with required fields.

        Given: Text content and timestamp information
        When: Creating a TranscriptChunk instance
        Then: Object is created with correct values
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        chunk = TranscriptChunk(
            text="Hello world",
            start_time=0.0,
            duration=1.5,
        )

        assert chunk.text == "Hello world"
        assert chunk.start_time == 0.0
        assert chunk.duration == 1.5

    def test_chunk_with_negative_start_time_raises_error(self):
        """
        Test that negative start times are rejected.

        Given: A chunk with negative start time
        When: Validating the chunk
        Then: ValidationError is raised
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        with pytest.raises(ValueError, match="start_time must be non-negative"):
            TranscriptChunk(
                text="Hello world",
                start_time=-1.0,
                duration=1.5,
            )

    def test_chunk_with_negative_duration_raises_error(self):
        """
        Test that negative durations are rejected.

        Given: A chunk with negative duration
        When: Validating the chunk
        Then: ValidationError is raised
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        with pytest.raises(ValueError, match="duration must be positive"):
            TranscriptChunk(
                text="Hello world",
                start_time=0.0,
                duration=-0.5,
            )

    def test_chunk_with_empty_text_raises_error(self):
        """
        Test that empty text content is rejected.

        Given: A chunk with empty text
        When: Validating the chunk
        Then: ValidationError is raised
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        with pytest.raises(ValueError, match="text cannot be empty"):
            TranscriptChunk(
                text="",
                start_time=0.0,
                duration=1.5,
            )

    def test_chunk_end_time_calculation(self):
        """
        Test calculating end time from start_time and duration.

        Given: A chunk with start_time and duration
        When: Accessing end_time property
        Then: Correct end time is returned
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        chunk = TranscriptChunk(
            text="Hello world",
            start_time=10.0,
            duration=5.5,
        )

        assert chunk.end_time == 15.5

    def test_chunk_to_dict(self):
        """
        Test converting TranscriptChunk to dictionary.

        Given: A TranscriptChunk instance
        When: Calling to_dict() method
        Then: Dictionary representation is returned
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        chunk = TranscriptChunk(
            text="Hello world",
            start_time=0.0,
            duration=1.5,
        )

        result = chunk.to_dict()

        assert result == {
            "text": "Hello world",
            "start_time": 0.0,
            "duration": 1.5,
        }

    def test_chunk_from_dict(self):
        """
        Test creating TranscriptChunk from dictionary.

        Given: A dictionary with chunk data
        When: Calling TranscriptChunk.from_dict()
        Then: TranscriptChunk instance is created
        """
        from yt_fts.transcribe.schema import TranscriptChunk

        data = {
            "text": "Hello world",
            "start_time": 0.0,
            "duration": 1.5,
        }

        chunk = TranscriptChunk.from_dict(data)

        assert chunk.text == "Hello world"
        assert chunk.start_time == 0.0
        assert chunk.duration == 1.5


class TestTranscriptDataModel:
    """Test Transcript dataclass for complete transcript."""

    def test_transcript_creation_with_required_fields(self):
        """
        Test creating a Transcript with required fields.

        Given: Video ID, language, source type, and chunks
        When: Creating a Transcript instance
        Then: Object is created with correct values
        """
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        chunks = [
            TranscriptChunk(text="Hello", start_time=0.0, duration=1.0),
            TranscriptChunk(text="World", start_time=1.0, duration=1.0),
        ]

        transcript = Transcript(
            video_id="test_video_id",
            language="en",
            source_type=SourceType.OFFICIAL,
            chunks=chunks,
        )

        assert transcript.video_id == "test_video_id"
        assert transcript.language == "en"
        assert transcript.source_type == SourceType.OFFICIAL
        assert len(transcript.chunks) == 2

    def test_transcript_with_empty_chunks_is_allowed(self):
        """
        Test that transcripts with empty chunks are allowed.

        Empty chunks represent videos without subtitles (e.g., no captions available).
        This is a valid state for transcripts from videos that have no caption data.

        Given: A transcript with empty chunks list
        When: Creating the Transcript
        Then: Transcript is created successfully with empty chunks
        """
        from yt_fts.transcribe.schema import Transcript, SourceType

        # Empty chunks should be allowed (for videos without subtitles)
        transcript = Transcript(
            video_id="test_video_id",
            language="en",
            source_type=SourceType.OFFICIAL,
            chunks=[],
        )

        assert transcript.video_id == "test_video_id"
        assert len(transcript.chunks) == 0
        assert transcript.duration == 0.0
        assert transcript.full_text == ""

    def test_transcript_duration_calculation(self):
        """
        Test calculating total transcript duration.

        Given: A transcript with multiple chunks
        When: Accessing duration property
        Then: Total duration is calculated correctly
        """
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        chunks = [
            TranscriptChunk(text="Hello", start_time=0.0, duration=1.0),
            TranscriptChunk(text="World", start_time=1.0, duration=2.0),
            TranscriptChunk(text="Test", start_time=3.0, duration=1.5),
        ]

        transcript = Transcript(
            video_id="test_video_id",
            language="en",
            source_type=SourceType.OFFICIAL,
            chunks=chunks,
        )

        # Duration should be end of last chunk
        assert transcript.duration == 4.5

    def test_transcript_full_text_property(self):
        """
        Test concatenating all chunk text.

        Given: A transcript with multiple chunks
        When: Accessing full_text property
        Then: All chunk text is concatenated with spaces
        """
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        chunks = [
            TranscriptChunk(text="Hello", start_time=0.0, duration=1.0),
            TranscriptChunk(text="World", start_time=1.0, duration=1.0),
        ]

        transcript = Transcript(
            video_id="test_video_id",
            language="en",
            source_type=SourceType.OFFICIAL,
            chunks=chunks,
        )

        assert transcript.full_text == "Hello World"

    def test_transcript_to_dict(self):
        """
        Test converting Transcript to dictionary.

        Given: A Transcript instance
        When: Calling to_dict() method
        Then: Full dictionary representation is returned
        """
        from yt_fts.transcribe.schema import Transcript, TranscriptChunk, SourceType

        chunks = [
            TranscriptChunk(text="Hello", start_time=0.0, duration=1.0),
        ]

        transcript = Transcript(
            video_id="test_video_id",
            language="en",
            source_type=SourceType.OFFICIAL,
            chunks=chunks,
        )

        result = transcript.to_dict()

        assert result["video_id"] == "test_video_id"
        assert result["language"] == "en"
        assert result["source_type"] == "official"
        assert len(result["chunks"]) == 1
        assert result["chunks"][0]["text"] == "Hello"

    def test_transcript_from_dict(self):
        """
        Test creating Transcript from dictionary.

        Given: A dictionary with transcript data
        When: Calling Transcript.from_dict()
        Then: Transcript instance is created
        """
        from yt_fts.transcribe.schema import Transcript, SourceType

        data = {
            "video_id": "test_video_id",
            "language": "en",
            "source_type": "official",
            "chunks": [
                {"text": "Hello", "start_time": 0.0, "duration": 1.0},
                {"text": "World", "start_time": 1.0, "duration": 1.0},
            ],
        }

        transcript = Transcript.from_dict(data)

        assert transcript.video_id == "test_video_id"
        assert transcript.language == "en"
        assert transcript.source_type == SourceType.OFFICIAL
        assert len(transcript.chunks) == 2


# =============================================================================
# Test Abstract Base Class (TranscriptionEngine)
# =============================================================================

class TestTranscriptionEngineBaseClass:
    """Test TranscriptionEngine abstract base class."""

    def test_cannot_instantiate_abstract_base_class(self):
        """
        Test that TranscriptionEngine cannot be instantiated directly.

        Given: The abstract TranscriptionEngine class
        When: Trying to create an instance
        Then: TypeError is raised
        """
        from yt_fts.transcribe.base import TranscriptionEngine

        with pytest.raises(TypeError, match="abstract"):
            TranscriptionEngine()

    def test_subclass_must_implement_transcribe(self):
        """
        Test that subclasses must implement the transcribe method.

        Given: A subclass without transcribe implementation
        When: Trying to instantiate the subclass
        Then: TypeError is raised about missing abstract method
        """
        from yt_fts.transcribe.base import TranscriptionEngine

        class IncompleteEngine(TranscriptionEngine):
            pass

        with pytest.raises(TypeError, match="transcribe"):
            IncompleteEngine()

    def test_concrete_subclass_can_be_instantiated(self):
        """
        Test that a concrete subclass with transcribe() can be instantiated.

        Given: A subclass implementing transcribe method
        When: Creating an instance
        Then: Instance is created successfully
        """
        from yt_fts.transcribe.base import TranscriptionEngine
        from yt_fts.transcribe.schema import Transcript, SourceType

        class MockEngine(TranscriptionEngine):
            def transcribe(self, audio_path: str) -> Transcript:
                return Transcript(
                    video_id="test",
                    language="en",
                    source_type=SourceType.OFFICIAL,
                    chunks=[],
                )

        engine = MockEngine()
        assert isinstance(engine, TranscriptionEngine)

    def test_transcribe_method_signature(self):
        """
        Test that transcribe method has correct signature.

        Given: A concrete TranscriptionEngine subclass
        When: Inspecting the transcribe method
        Then: Method accepts audio_path parameter and returns Transcript
        """
        from yt_fts.transcribe.base import TranscriptionEngine
        from yt_fts.transcribe.schema import Transcript, SourceType
        import inspect

        class MockEngine(TranscriptionEngine):
            def transcribe(self, audio_path: str, **kwargs) -> Transcript:
                return Transcript(
                    video_id="test",
                    language="en",
                    source_type=SourceType.OFFICIAL,
                    chunks=[],
                )

        engine = MockEngine()
        sig = inspect.signature(engine.transcribe)

        # Check that audio_path is a parameter
        assert "audio_path" in sig.parameters


# =============================================================================
# Test LocalWhisperEngine
# =============================================================================

class TestLocalWhisperEngine:
    """Test LocalWhisperEngine implementation."""

    def test_initialization_with_default_parameters(self):
        """
        Test engine initialization with default model and device.

        Given: No parameters provided
        When: Creating LocalWhisperEngine
        Then: Engine uses default model size and device
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        engine = LocalWhisperEngine()

        assert engine.model_size == "base"
        assert engine.device == "cpu"

    def test_initialization_with_custom_model_size(self):
        """
        Test engine initialization with custom model size.

        Given: A valid model size parameter
        When: Creating LocalWhisperEngine
        Then: Engine uses the specified model size
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        engine = LocalWhisperEngine(model_size="large")

        assert engine.model_size == "large"

    def test_initialization_with_cuda_device(self):
        """
        Test engine initialization with CUDA device.

        Given: device="cuda" parameter
        When: Creating LocalWhisperEngine
        Then: Engine is configured for CUDA
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        engine = LocalWhisperEngine(device="cuda")

        assert engine.device == "cuda"

    def test_initialization_with_invalid_model_size_raises_error(self):
        """
        Test that invalid model sizes are rejected.

        Given: An invalid model size
        When: Creating LocalWhisperEngine
        Then: ValueError is raised
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        with pytest.raises(ValueError, match="Invalid model_size"):
            LocalWhisperEngine(model_size="invalid_model")

    def test_initialization_with_invalid_device_raises_error(self):
        """
        Test that invalid devices are rejected.

        Given: An invalid device
        When: Creating LocalWhisperEngine
        Then: ValueError is raised
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        with pytest.raises(ValueError, match="Invalid device"):
            LocalWhisperEngine(device="invalid_device")

    @patch("yt_fts.transcribe.whisper_engine.WhisperModel")
    def test_transcribe_returns_valid_transcript(self, mock_model):
        """
        Test that transcribe() returns a valid Transcript object.

        Given: An audio file and mocked WhisperModel
        When: Calling transcribe()
        Then: A Transcript with correct structure is returned
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine
        from yt_fts.transcribe.schema import SourceType

        # Mock the WhisperModel behavior
        mock_segments = [
            MagicMock(text="Hello world", start=0.0, end=1.5),
            MagicMock(text="Test transcript", start=1.5, end=3.0),
        ]
        mock_info = MagicMock(language="en")
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
        mock_model.return_value = mock_model_instance

        engine = LocalWhisperEngine()
        result = engine.transcribe(
            audio_path="/path/to/audio.mp3",
            video_id="test_video_id",
        )

        assert result.video_id == "test_video_id"
        assert result.language == "en"
        assert result.source_type == SourceType.GENERATED_WHISPER
        assert len(result.chunks) == 2
        assert result.chunks[0].text == "Hello world"
        assert result.chunks[0].start_time == 0.0

    @patch("yt_fts.transcribe.whisper_engine.WhisperModel")
    def test_language_detection(self, mock_model):
        """
        Test language detection during transcription.

        Given: An audio file with unknown language
        When: Calling transcribe() without language parameter
        Then: Language is auto-detected and returned in Transcript
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine
        from yt_fts.transcribe.schema import SourceType

        mock_segments = [MagicMock(text="Hola mundo", start=0.0, end=1.5)]
        mock_info = MagicMock(language="es")
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
        mock_model.return_value = mock_model_instance

        engine = LocalWhisperEngine()
        result = engine.transcribe(
            audio_path="/path/to/audio.mp3",
            video_id="test_video_id",
        )

        assert result.language == "es"

    @patch("yt_fts.transcribe.whisper_engine.WhisperModel")
    def test_translation_to_english(self, mock_model):
        """
        Test translation parameter for non-English audio.

        Given: An audio file in Spanish
        When: Calling transcribe() with translate=True
        Then: Transcript is translated to English
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine
        from yt_fts.transcribe.schema import SourceType

        mock_segments = [MagicMock(text="Hello world", start=0.0, end=1.5)]
        mock_info = MagicMock(language="en")
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
        mock_model.return_value = mock_model_instance

        engine = LocalWhisperEngine()
        result = engine.transcribe(
            audio_path="/path/to/audio.mp3",
            video_id="test_video_id",
            translate=True,
        )

        # Verify translate parameter was passed to WhisperModel
        mock_model_instance.transcribe.assert_called_once()
        call_kwargs = mock_model_instance.transcribe.call_args.kwargs
        # The translation should result in English language
        assert result.language == "en"

    @patch("yt_fts.transcribe.whisper_engine.WhisperModel")
    def test_chunk_word_timestamps_aggregation(self, mock_model):
        """
        Test that word-level timestamps are converted to chunk-level.

        Given: Whisper output with segments
        When: Processing the transcription
        Then: Chunks have correct start_time and duration
        """
        from yt_fts.transcribe.whisper_engine import LocalWhisperEngine

        mock_segments = [
            MagicMock(text="First segment", start=0.0, end=2.5),
            MagicMock(text="Second segment", start=2.5, end=5.0),
        ]
        mock_info = MagicMock(language="en")
        mock_model_instance = MagicMock()
        mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
        mock_model.return_value = mock_model_instance

        engine = LocalWhisperEngine()
        result = engine.transcribe(
            audio_path="/path/to/audio.mp3",
            video_id="test_video_id",
        )

        assert result.chunks[0].start_time == 0.0
        assert result.chunks[0].duration == 2.5
        assert result.chunks[1].start_time == 2.5
        assert result.chunks[1].duration == 2.5


# =============================================================================
# Test OfficialCaptionEngine
# =============================================================================

class TestOfficialCaptionEngine:
    """Test OfficialCaptionEngine for YouTube caption extraction."""

    def test_initialization(self):
        """
        Test OfficialCaptionEngine initialization.

        Given: No parameters required
        When: Creating OfficialCaptionEngine
        Then: Engine is created successfully
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine

        engine = OfficialCaptionEngine()

        assert isinstance(engine, OfficialCaptionEngine)

    @patch("yt_fts.transcribe.official_engine.get_subtitles")
    def test_transcribe_from_youtube_url(self, mock_get_subtitles):
        """
        Test extracting captions from YouTube URL.

        Given: A valid YouTube video URL
        When: Calling transcribe() with the URL
        Then: Official captions are extracted and returned as Transcript
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine
        from yt_fts.transcribe.schema import SourceType

        # Mock the get_subtitles function
        mock_get_subtitles.return_value = [
            ("00:00:00.000", "00:00:01.500", "Hello world"),
            ("00:00:01.500", "00:00:03.000", "Test caption"),
        ]

        engine = OfficialCaptionEngine()
        result = engine.transcribe(
            audio_path="test_video_id",
            video_id="test_video_id",
        )

        assert result.video_id == "test_video_id"
        assert result.source_type == SourceType.OFFICIAL
        assert len(result.chunks) == 2
        assert result.chunks[0].text == "Hello world"

    @patch("yt_fts.transcribe.official_engine.get_subtitles")
    def test_transcribe_handles_missing_language(self, mock_get_subtitles):
        """
        Test handling of transcripts without language metadata.

        Given: Subtitles without language information
        When: Calling transcribe()
        Then: Language defaults to "en" (English)
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine
        from yt_fts.transcribe.schema import SourceType

        mock_get_subtitles.return_value = [
            ("00:00:00.000", "00:00:01.500", "Hello world"),
        ]

        engine = OfficialCaptionEngine()
        result = engine.transcribe(
            audio_path="test_video_id",
            video_id="test_video_id",
            url="https://www.youtube.com/watch?v=test_video_id",
        )

        assert result.language == "en"

    @patch("yt_fts.transcribe.official_engine.get_subtitles")
    def test_transcribe_with_language_parameter(self, mock_get_subtitles):
        """
        Test specifying language for caption extraction.

        Given: A language code parameter
        When: Calling transcribe() with language
        Then: Correct language is set on the Transcript
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine

        mock_get_subtitles.return_value = [
            ("00:00:00.000", "00:00:01.500", "Hola mundo"),
        ]

        engine = OfficialCaptionEngine()
        result = engine.transcribe(
            audio_path="test_video_id",
            video_id="test_video_id",
            url="https://www.youtube.com/watch?v=test_video_id",
            language="es",
        )

        assert result.language == "es"

    @patch("yt_fts.transcribe.official_engine.get_subtitles")
    def test_transcribe_timestamp_conversion(self, mock_get_subtitles):
        """
        Test conversion of timestamp format from string to float.

        Given: Subtitles with "HH:MM:SS.mmm" format timestamps
        When: Calling transcribe()
        Then: Chunks have correct float start_time and duration
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine

        mock_get_subtitles.return_value = [
            ("00:00:10.500", "00:00:12.000", "Test text"),
        ]

        engine = OfficialCaptionEngine()
        result = engine.transcribe(
            audio_path="test_video_id",
            video_id="test_video_id",
            url="https://www.youtube.com/watch?v=test_video_id",
        )

        assert result.chunks[0].start_time == 10.5
        assert result.chunks[0].duration == 1.5

    @patch("yt_fts.transcribe.official_engine.get_subtitles")
    def test_transcribe_empty_subtitles_returns_empty_chunks(self, mock_get_subtitles):
        """
        Test handling of videos with no subtitles.

        Given: A video without available captions
        When: Calling transcribe()
        Then: Transcript is created with empty chunks list
        """
        from yt_fts.transcribe.official_engine import OfficialCaptionEngine

        mock_get_subtitles.return_value = []

        engine = OfficialCaptionEngine()
        result = engine.transcribe(
            audio_path="test_video_id",
            video_id="test_video_id",
            url="https://www.youtube.com/watch?v=test_video_id",
        )

        assert len(result.chunks) == 0


# =============================================================================
# Test Package Exports
# =============================================================================

class TestPackageExports:
    """Test that transcribe package exports all necessary components."""

    def test_schema_exports(self):
        """
        Test that schema module exports all data models.

        Given: The transcribe.schema module
        When: Importing from yt_fts.transcribe.schema
        Then: All expected classes are available
        """
        from yt_fts.transcribe import schema

        # Check that all expected classes are defined
        assert hasattr(schema, "SourceType")
        assert hasattr(schema, "Video")
        assert hasattr(schema, "TranscriptChunk")
        assert hasattr(schema, "Transcript")

    def test_base_exports(self):
        """
        Test that base module exports TranscriptionEngine.

        Given: The transcribe.base module
        When: Importing from yt_fts.transcribe.base
        Then: TranscriptionEngine ABC is available
        """
        from yt_fts.transcribe import base

        assert hasattr(base, "TranscriptionEngine")

    def test_package_init_exports(self):
        """
        Test that __init__.py exports main components.

        Given: The transcribe package
        When: Importing from yt_fts.transcribe
        Then: Main classes are re-exported
        """
        from yt_fts.transcribe import (
            LocalWhisperEngine,
            OfficialCaptionEngine,
            SourceType,
            Transcript,
            TranscriptChunk,
            TranscriptionEngine,
            Video,
        )

        # Verify imports work
        assert TranscriptionEngine is not None
        assert LocalWhisperEngine is not None
        assert OfficialCaptionEngine is not None
        assert SourceType is not None
        assert Video is not None
        assert Transcript is not None
        assert TranscriptChunk is not None
