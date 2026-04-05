"""
Tests for Ralph Loop Hard Stop v7 features.

TDD RED phase: These tests are written BEFORE the implementation.
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, Mock

import sys
from pathlib import Path as _Path

# Add hooks directory to path
_hooks_path = str(_Path(__file__).parent.parent / "hooks")
if _hooks_path not in sys.path:
    sys.path.insert(0, _hooks_path)

# Load stop-hook module directly (hyphen not valid in Python import names)
import importlib.util
spec = importlib.util.spec_from_file_location("stop_hook", _Path(__file__).parent.parent / "hooks" / "stop-hook.py")
stop_hook = importlib.util.module_from_spec(spec)
sys.modules['stop_hook'] = stop_hook  # Register before loading
spec.loader.exec_module(stop_hook)

RalphConfig = stop_hook.RalphConfig
TestResultSchema = stop_hook.TestResultSchema
TestResultVerifier = stop_hook.TestResultVerifier

# Restore original Path import
from pathlib import Path


class TestRalphConfig:
    """Tests for RalphConfig configuration class."""

    def test_get_test_command_default(self):
        """Default test command should be pytest -q."""
        with patch.dict("os.environ", {}, clear=True):
            assert RalphConfig.get_test_command() == "pytest -q"

    def test_get_test_command_from_env(self):
        """Test command can be overridden via RALPH_TEST_COMMAND."""
        with patch.dict("os.environ", {"RALPH_TEST_COMMAND": "pytest -v"}):
            assert RalphConfig.get_test_command() == "pytest -v"

    def test_get_test_timeout_default(self):
        """Default timeout should be 60 seconds."""
        with patch.dict("os.environ", {}, clear=True):
            assert RalphConfig.get_test_timeout() == 60

    def test_get_test_timeout_from_env(self):
        """Timeout can be overridden via RALPH_TEST_TIMEOUT."""
        with patch.dict("os.environ", {"RALPH_TEST_TIMEOUT": "120"}):
            assert RalphConfig.get_test_timeout() == 120

    def test_get_coverage_threshold_default(self):
        """Default coverage threshold should be 80%."""
        with patch.dict("os.environ", {}, clear=True):
            assert RalphConfig.get_coverage_threshold() == 80.0

    def test_get_coverage_threshold_from_env(self):
        """Coverage threshold can be overridden via RALPH_COVERAGE_THRESHOLD."""
        with patch.dict("os.environ", {"RALPH_COVERAGE_THRESHOLD": "90"}):
            assert RalphConfig.get_coverage_threshold() == 90.0

    def test_get_clock_skew_grace_default(self):
        """Default clock skew grace should be 30 seconds."""
        with patch.dict("os.environ", {}, clear=True):
            assert RalphConfig.get_clock_skew_grace() == 30

    def test_get_tdd_guard_output_dir_default(self):
        """Default TDD Guard output dir should be .claude/tdd-guard/data."""
        with patch.dict("os.environ", {}, clear=True):
            result = RalphConfig.get_tdd_guard_output_dir()
            assert result == Path(".claude/tdd-guard/data")

    def test_get_tdd_guard_output_dir_from_env(self):
        """TDD Guard output dir can be overridden via TDD_GUARD_OUTPUT_DIR."""
        with patch.dict("os.environ", {"TDD_GUARD_OUTPUT_DIR": "custom/path"}):
            result = RalphConfig.get_tdd_guard_output_dir()
            assert result == Path("custom/path")

    def test_get_test_json_path(self):
        """Test JSON path should be project_root/.claude/tdd-guard/data/test.json."""
        with patch.dict("os.environ", {}, clear=True):
            result = RalphConfig.get_test_json_path(Path("/my/project"))
            assert result == Path("/my/project/.claude/tdd-guard/data/test.json")

    def test_get_htmlcov_path(self):
        """HTML coverage path should be project_root/htmlcov/index.html."""
        with patch.dict("os.environ", {}, clear=True):
            result = RalphConfig.get_htmlcov_path(Path("/my/project"))
            assert result == Path("/my/project/htmlcov/index.html")


class TestTestResultSchema:
    """Tests for TestResultSchema validation."""

    def test_validate_valid_complete_data(self):
        """Valid complete test data should pass validation."""
        valid_data = {
            "total": 10,
            "passed": 8,
            "failed": 2,
            "skipped": 0,
            "hasFailures": True,
            "hasTests": True,
        }
        is_valid, error = TestResultSchema.validate(valid_data)
        assert is_valid
        assert error is None

    def test_validate_missing_required_field(self):
        """Missing required field should fail validation."""
        incomplete_data = {
            "total": 10,
            "passed": 8,
            # missing "failed"
            "skipped": 0,
            "hasFailures": True,
            "hasTests": True,
        }
        is_valid, error = TestResultSchema.validate(incomplete_data)
        assert not is_valid
        assert "missing" in error.lower()

    def test_validate_wrong_field_type(self):
        """Wrong field type should fail validation."""
        wrong_type_data = {
            "total": "not_a_number",  # should be int
            "passed": 8,
            "failed": 2,
            "skipped": 0,
            "hasFailures": True,
            "hasTests": True,
        }
        is_valid, error = TestResultSchema.validate(wrong_type_data)
        assert not is_valid
        assert "wrong type" in error.lower()

    def test_validate_with_tests_array(self):
        """Valid data with tests array should pass validation."""
        data_with_tests = {
            "total": 2,
            "passed": 1,
            "failed": 1,
            "skipped": 0,
            "hasFailures": True,
            "hasTests": True,
            "tests": [
                {"name": "test_foo", "outcome": "passed"},
                {"name": "test_bar", "outcome": "failed", "failure": "AssertionError"},
            ]
        }
        is_valid, error = TestResultSchema.validate(data_with_tests)
        assert is_valid
        assert error is None

    def test_validate_invalid_test_outcome(self):
        """Invalid test outcome should fail validation."""
        data_with_invalid_outcome = {
            "total": 1,
            "passed": 0,
            "failed": 1,
            "skipped": 0,
            "hasFailures": True,
            "hasTests": True,
            "tests": [
                {"name": "test_foo", "outcome": "invalid_outcome"},
            ]
        }
        is_valid, error = TestResultSchema.validate(data_with_invalid_outcome)
        assert not is_valid
        assert "invalid outcome" in error.lower()


class TestTestResultVerifier:
    """Tests for TestResultVerifier."""

    def test_read_fresh_tdd_guard_results_no_file(self):
        """Should return None when test.json doesn't exist."""
        session_start = datetime.now()
        project_root = Path("/fake/project")

        result = TestResultVerifier.read_fresh_tdd_guard_results(
            session_start, project_root, grace_seconds=30
        )
        assert result is None

    @patch("stop_hook.Path.exists")
    @patch("stop_hook.Path.read_text")
    def test_read_fresh_tdd_guard_results_stale_file(self, mock_read, mock_exists):
        """Should return None when test.json is stale (older than session_start)."""
        # Setup - Use a real file timestamp from the past
        from unittest.mock import MagicMock, patch
        import time
        
        mock_exists.return_value = True
        mock_read.return_value = '{"total": 10, "passed": 10, "failed": 0, "skipped": 0, "hasFailures": False, "hasTests": True}'

        # Create a timestamp 1 hour in the past
        stale_timestamp = time.time() - 3600  # 1 hour ago
        mock_stat = MagicMock()
        mock_stat.st_mtime = stale_timestamp
        
        with patch("stop_hook.Path") as mock_path_class:
            # Setup mock_path_class to return our mocks
            mock_path_class.return_value.exists.return_value = True
            mock_path_class.return_value.read_text.return_value = '{"total": 10, "passed": 10, "failed": 0, "skipped": 0, "hasFailures": False, "hasTests": True}'
            mock_path_class.return_value.stat.return_value = mock_stat
            
            session_start = datetime.now()
            project_root = Path("/fake/project")

            result = TestResultVerifier.read_fresh_tdd_guard_results(
                session_start, project_root, grace_seconds=30
            )

        # Verify
        assert result is None

    def test_read_fresh_tdd_guard_results_fresh_file(self):
        """Should return test summary when test.json is fresh."""
        from unittest.mock import MagicMock, patch
        import time
        
        # Create a timestamp from now (fresh)
        fresh_timestamp = time.time()
        
        # Session start 1 hour ago, so the file is fresh
        session_start = datetime.now() - timedelta(hours=1)
        project_root = Path("/fake/project")
        
        # We need to patch get_test_json_path to return a mock path object
        mock_test_json_path = MagicMock()
        mock_test_json_path.exists.return_value = True
        mock_test_json_path.read_text.return_value = '''{
            "total": 5,
            "passed": 5,
            "failed": 0,
            "skipped": 0,
            "hasFailures": false,
            "hasTests": true
        }'''
        mock_stat = MagicMock()
        mock_stat.st_mtime = fresh_timestamp
        mock_test_json_path.stat.return_value = mock_stat
        
        with patch.object(RalphConfig, 'get_test_json_path', return_value=mock_test_json_path):
            result = TestResultVerifier.read_fresh_tdd_guard_results(
                session_start, project_root, grace_seconds=30
            )

        # Verify
        assert result is not None
        assert result["source"] == "tdd_guard"
        assert result["summary"]["total"] == 5
        assert result["summary"]["passed"] == 5
        assert result["passed"] is True

    def test_read_fresh_tdd_guard_results_invalid_schema(self):
        """Should return None when test.json has invalid schema."""
        from unittest.mock import MagicMock, patch
        import time
        
        # Fresh timestamp but invalid schema
        fresh_timestamp = time.time()
        mock_stat = MagicMock()
        mock_stat.st_mtime = fresh_timestamp
        
        with patch("stop_hook.Path") as mock_path_class:
            mock_path_class.return_value.exists.return_value = True
            # Malformed JSON missing required fields
            mock_path_class.return_value.read_text.return_value = '{"incomplete": "data"}'
            mock_path_class.return_value.stat.return_value = mock_stat
            
            session_start = datetime.now() - timedelta(hours=1)
            project_root = Path("/fake/project")

            result = TestResultVerifier.read_fresh_tdd_guard_results(
                session_start, project_root, grace_seconds=30
            )

        # Verify - should return None (triggers subprocess fallback)
        assert result is None

    @patch("stop_hook.subprocess.run")
    def test_run_tests_via_subprocess_success(self, mock_run):
        """Subprocess test runner should return success when tests pass."""
        # Setup
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "tests passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute
        result = TestResultVerifier.run_tests_via_subprocess(
            workdir="/fake/project",
            timeout=60
        )

        # Verify
        assert result["source"] == "subprocess"
        assert result["passed"] is True
        assert result["exit_code"] == 0

    @patch("stop_hook.subprocess.run")
    def test_run_tests_via_subprocess_failure(self, mock_run):
        """Subprocess test runner should return failure when tests fail."""
        # Setup
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "tests failed"
        mock_result.stderr = "AssertionError"
        mock_run.return_value = mock_result

        # Execute
        result = TestResultVerifier.run_tests_via_subprocess(
            workdir="/fake/project",
            timeout=60
        )

        # Verify
        assert result["source"] == "subprocess"
        assert result["passed"] is False
        assert result["exit_code"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
