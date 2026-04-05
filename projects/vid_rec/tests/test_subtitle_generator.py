import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.subtitle_generator import generate_subtitles_for_file, load_model

class TestSubtitleGenerator(unittest.TestCase):
    def setUp(self):
        self.video_path = Path("/test/video.mp4")
        self.output_dir = Path("/test/output_dir")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up created files/directories if any
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)

    @patch('src.subtitle_generator._model', new_callable=MagicMock)
    def test_load_model(self, mock_model):
        # Test that load_model sets the global _model
        load_model()
        self.assertIsNotNone(mock_model)

    @patch('src.subtitle_generator._model')
    def test_generate_subtitles_for_file_success(self, mock_whisper_model):
        # Mock the transcribe method of the faster_whisper model
        mock_whisper_model.transcribe.return_value = ([
            MagicMock(start=0, end=1, text="Hello"),
            MagicMock(start=2, end=3, text="World")
        ], MagicMock(duration=3))

        # Mock the global _model to be the mocked whisper model
        with patch('src.subtitle_generator._model', mock_whisper_model):
            output_path = generate_subtitles_for_file(str(self.video_path), str(self.output_dir))

            mock_whisper_model.transcribe.assert_called_once_with(
                str(self.video_path),
                language=None,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.name, "video.srt")

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("1
00:00:00,000 --> 00:00:01,000
Hello", content)
                self.assertIn("2
00:00:02,000 --> 00:00:03,000
World", content)

    @patch('src.subtitle_generator._model')
    def test_generate_subtitles_for_file_with_progress_callback(self, mock_whisper_model):
        mock_whisper_model.transcribe.return_value = ([
            MagicMock(start=0, end=1, text="Hello"),
            MagicMock(start=2, end=3, text="World")
        ], MagicMock(duration=3))

        mock_callback = MagicMock()

        with patch('src.subtitle_generator._model', mock_whisper_model):
            generate_subtitles_for_file(str(self.video_path), str(self.output_dir), progress_callback=mock_callback)

            # Check that the callback was called at least a few times
            self.assertTrue(mock_callback.called)
            # Example: check specific calls if needed
            mock_callback.assert_any_call(0, 3)
            mock_callback.assert_any_call(1, 3)
            mock_callback.assert_any_call(3, 3)

    @patch('src.subtitle_generator._model')
    def test_generate_subtitles_for_file_failure(self, mock_whisper_model):
        mock_whisper_model.transcribe.side_effect = Exception("Transcription failed")

        with patch('src.subtitle_generator._model', mock_whisper_model):
            with self.assertRaises(Exception):
                generate_subtitles_for_file(str(self.video_path), str(self.output_dir))


if __name__ == '__main__':
    unittest.main()
