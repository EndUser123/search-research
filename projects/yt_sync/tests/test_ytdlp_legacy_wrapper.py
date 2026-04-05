import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure the parent directory is in the path so we can import from yt_sync
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from yt_sync.ytdlp_legacy_wrapper import (
    SPOOFED_USER_AGENT,
    YTDLP_EXECUTABLE,
    build_command,
    find_ytdlp_executable,
    run_ytdlp_subprocess,
)


class TestYtdlpLegacyWrapper(unittest.TestCase):
    def setUp(self):
        self.args = MagicMock()
        self.args.yt_verbose = False
        self.args.auth_config = {}
        self.args.cookies_from_browser = None
        self.args.profile = None
        self.args.throttling_config = {}

    @patch("yt_sync.ytdlp_legacy_wrapper.Path")
    @patch("shutil.which")
    def test_find_ytdlp_executable_local(self, mock_which, mock_path):
        # Setup mock for local executable
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent = MagicMock()
        mock_local_path = MagicMock()
        mock_local_path.is_file.return_value = True
        mock_path_instance.parent.parent.__truediv__.return_value = mock_local_path
        mock_path.return_value = mock_path_instance

        result = find_ytdlp_executable()
        self.assertEqual(result, str(mock_local_path))
        mock_which.assert_not_called()

    @patch("yt_sync.ytdlp_legacy_wrapper.Path")
    @patch("shutil.which")
    def test_find_ytdlp_executable_system(self, mock_which, mock_path):
        # Setup mock for system executable
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent = MagicMock()
        mock_local_path = MagicMock()
        mock_local_path.is_file.return_value = False
        mock_path_instance.parent.parent.__truediv__.return_value = mock_local_path
        mock_path.return_value = mock_path_instance
        mock_which.return_value = "/usr/bin/yt-dlp"

        result = find_ytdlp_executable()
        self.assertEqual(result, "/usr/bin/yt-dlp")
        mock_which.assert_called_once_with("yt-dlp")

    @patch("yt_sync.ytdlp_legacy_wrapper.Path")
    @patch("shutil.which")
    def test_find_ytdlp_executable_not_found(self, mock_which, mock_path):
        # Setup mock for no executable found
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent = MagicMock()
        mock_local_path = MagicMock()
        mock_local_path.is_file.return_value = False
        mock_path_instance.parent.parent.__truediv__.return_value = mock_local_path
        mock_path.return_value = mock_path_instance
        mock_which.return_value = None

        result = find_ytdlp_executable()
        self.assertIsNone(result)
        mock_which.assert_called_once_with("yt-dlp")

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_executable_not_found(self, mock_find):
        mock_find.return_value = None
        result = build_command(self.args, [])
        self.assertIsNone(result)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_basic(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_verbose(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        self.args.yt_verbose = True
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--verbose",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_with_cookies_file(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        self.args.auth_config = {
            "cookies_file": "cookies.txt",
            "http_headers": {"Cookie": "test=cookie"},
        }
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--cookies",
            "cookies.txt",
            "--add-header",
            "Cookie: test=cookie",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_with_cookies_browser(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        self.args.cookies_from_browser = "firefox"
        self.args.profile = "default"
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--cookies-from-browser",
            "firefox:default",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_with_throttling(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        self.args.throttling_config = {
            "ratelimit": "100K",
            "sleep_interval_requests": 1,
            "sleep_interval": 2,
        }
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
            "--limit-rate",
            "100K",
            "--sleep-requests",
            "1",
            "--sleep-interval",
            "2",
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_with_url_and_extra_args(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        extra_args = ["--format", "best"]
        url = "https://www.youtube.com/watch?v=test"
        result = build_command(self.args, extra_args, url)
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
            "--format",
            "best",
            "https://www.youtube.com/watch?v=test",
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_per_call_config_disable_sleep(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        self.args.throttling_config = {"sleep_interval": 2}
        per_call_config = {"disable_sleep_interval": True}
        result = build_command(self.args, [], per_call_config=per_call_config)
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("subprocess.run")
    def test_run_ytdlp_subprocess_success(self, mock_run):
        command = ["yt-dlp", "--version"]
        mock_run.return_value = subprocess.CompletedProcess(
            args=command, returncode=0, stdout="2023.03.04", stderr=""
        )
        result = run_ytdlp_subprocess(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "2023.03.04")
        mock_run.assert_called_once_with(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )

    @patch("subprocess.run")
    def test_run_ytdlp_subprocess_timeout(self, mock_run):
        command = ["yt-dlp", "some_url"]
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=command, timeout=1800)
        result = run_ytdlp_subprocess(command)
        self.assertEqual(result.returncode, 124)
        self.assertEqual(result.stderr, "Process timed out")
        mock_run.assert_called_once_with(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )

    @patch("subprocess.run")
    def test_run_ytdlp_subprocess_unexpected_error(self, mock_run):
        command = ["yt-dlp", "some_url"]
        mock_run.side_effect = Exception("Unexpected error")
        result = run_ytdlp_subprocess(command)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unexpected error", result.stderr)
        mock_run.assert_called_once_with(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800,
        )

    @patch("yt_sync.ytdlp_legacy_wrapper.logger.error")
    @patch("subprocess.run")
    def test_run_ytdlp_subprocess_logs_errors(self, mock_run, mock_log_error):
        command = ["yt-dlp", "some_url"]
        mock_run.side_effect = Exception("Test error")
        run_ytdlp_subprocess(command)
        mock_log_error.assert_called_once_with(
            "Unexpected error running yt-dlp subprocess: Test error"
        )

    @patch("yt_sync.ytdlp_legacy_wrapper.logger.debug")
    @patch("subprocess.run")
    def test_run_ytdlp_subprocess_logs_debug(self, mock_run, mock_log_debug):
        command = ["yt-dlp", "--version"]
        mock_run.return_value = subprocess.CompletedProcess(
            args=command, returncode=0, stdout="2023.03.04", stderr=""
        )
        run_ytdlp_subprocess(command)
        self.assertTrue(mock_log_debug.called)

    def test_module_constants(self):
        from yt_sync.ytdlp_legacy_wrapper import SPOOFED_USER_AGENT

        self.assertEqual(YTDLP_EXECUTABLE, "yt-dlp.exe")
        self.assertIn("Mozilla/5.0", SPOOFED_USER_AGENT)

    @patch("yt_sync.ytdlp_legacy_wrapper.logger.error")
    @patch("yt_sync.ytdlp_legacy_wrapper.Path")
    @patch("shutil.which")
    def test_find_ytdlp_executable_logs_error(
        self, mock_which, mock_path, mock_log_error
    ):
        mock_path_instance = MagicMock()
        mock_path_instance.parent.parent = MagicMock()
        mock_local_path = MagicMock()
        mock_local_path.is_file.return_value = False
        mock_path_instance.parent.parent.__truediv__.return_value = mock_local_path
        mock_path.return_value = mock_path_instance
        mock_which.return_value = None

        find_ytdlp_executable()
        mock_log_error.assert_called_once_with("Could not find 'yt-dlp.exe'.")

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_empty_extra_args(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        result = build_command(self.args, [])
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
        ]
        self.assertEqual(result, expected)

    @patch("yt_sync.ytdlp_legacy_wrapper.find_ytdlp_executable")
    def test_build_command_invalid_url(self, mock_find):
        mock_find.return_value = "/usr/bin/yt-dlp"
        result = build_command(self.args, [], url="invalid_url")
        expected = [
            "/usr/bin/yt-dlp",
            "--ignore-config",
            "--no-warnings",
            "--user-agent",
            SPOOFED_USER_AGENT,
            "invalid_url",
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
