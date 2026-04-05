#!/usr/bin/env python3
"""Unit tests for evidence verification gate."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(hooks_dir.resolve()))

# Add skills/code to path for EvidenceManager import
skills_code_path = hooks_dir.parent.parent / "skills" / "code"
sys.path.insert(0, str(skills_code_path.resolve()))

from stop.evidence_verification_gate import EvidenceVerificationGate


@pytest.fixture
def temp_ledger_dir():
    """Create temporary state directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    old_cwd = Path.cwd()

    # Create state directory
    state_dir = temp_dir / ".claude" / "state"
    state_dir.mkdir(parents=True)

    yield state_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_evidence_manager():
    """Create a mock EvidenceManager with test data in the actual state directory."""
    # Import here after path setup
    from pathlib import Path

    from utils.evidence import EvidenceManager

    # Use a unique terminal_id for testing
    terminal_id = "test_verification_gate"
    mgr = EvidenceManager(terminal_id)

    # Get the ledger file path for cleanup later
    state_dir = Path("P:/.claude/state")
    test_ledger = state_dir / f"code_evidence_{terminal_id}.json"

    # EvidenceManager.__init__ already created the ledger via _ensure_ledger_exists()
    # We can optionally clean up and recreate if needed, but normally we just use it as-is

    # Record some evidence - uses the existing ledger created in __init__
    mgr.record_red("TASK-001", ["tests/test_feature.py"], "pytest tests/test_feature.py", 1)
    mgr.record_green("TASK-001", ["src/feature.py"], "pytest tests/test_feature.py", 1)
    mgr.record_refactor("TASK-001", [], "pytest tests/test_feature.py", 1)
    mgr.record_verify("TASK-001", 0, 0, "PASS")

    # Create implementation files to make them exist
    # Use the current working directory (tests directory)
    test_file = Path("tests/test_feature.py")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# test")

    impl_file = Path("src/feature.py")
    impl_file.parent.mkdir(parents=True, exist_ok=True)
    impl_file.write_text("# impl")

    try:
        yield mgr
    finally:
        # Clean up test ledger
        if test_ledger.exists():
            test_ledger.unlink()
        # Clean up test files
        if test_file.exists():
            test_file.unlink()
        if impl_file.exists():
            impl_file.unlink()


class TestTaskIDExtraction:
    """Test task_id extraction from conversation."""

    def test_extract_from_env_var(self, monkeypatch):
        """Extract task_id from environment variable."""
        gate = EvidenceVerificationGate()

        # Set env var
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-123")
        conversation = {}

        result = gate._extract_task_id(conversation)

        assert result == "TASK-123"

    def test_extract_from_conversation_metadata(self, monkeypatch):
        """Extract task_id from conversation metadata."""
        gate = EvidenceVerificationGate()

        # No env var
        monkeypatch.delenv("EVIDENCE_TASK_ID", raising=False)
        conversation = {"task_id": "TASK-456"}

        result = gate._extract_task_id(conversation)

        assert result == "TASK-456"

    def test_extract_priority_env_var_wins(self, monkeypatch):
        """Environment variable takes priority over conversation metadata."""
        gate = EvidenceVerificationGate()

        # Set both - env var should win
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-ENV")
        conversation = {"task_id": "TASK-CONV"}

        result = gate._extract_task_id(conversation)

        assert result == "TASK-ENV"

    def test_extract_returns_none_when_no_task_id(self, monkeypatch):
        """Return None when no task_id available."""
        gate = EvidenceVerificationGate()

        # No env var, no conversation metadata
        monkeypatch.delenv("EVIDENCE_TASK_ID", raising=False)
        conversation = {}

        result = gate._extract_task_id(conversation)

        assert result is None


class TestPythonTests:
    """Test Python test execution."""

    def test_no_pytest_config_skips_gracefully(self, monkeypatch):
        """Skip gracefully when no pytest configuration detected."""
        gate = EvidenceVerificationGate()

        with tempfile.TemporaryDirectory() as temp_dir:
            # No pytest config files
            passed, error = gate._run_python_tests(temp_dir)

            assert passed is True
            assert error == ""

    def test_pytest_not_installed_skips_gracefully(self, monkeypatch):
        """Skip gracefully when pytest not installed."""
        gate = EvidenceVerificationGate()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml to trigger pytest attempt
            (Path(temp_dir) / "pyproject.toml").write_text("[tool.pytest]")

            # Mock subprocess.run to simulate FileNotFoundError
            import subprocess

            original_run = subprocess.run

            def mock_run(*args, **kwargs):
                raise FileNotFoundError("pytest")

            monkeypatch.setattr(subprocess, "run", mock_run)

            passed, error = gate._run_python_tests(temp_dir)

            assert passed is True  # Should skip gracefully
            assert "" == error

    def test_pytest_failure_returns_error(self, monkeypatch):
        """Detect pytest failure and return error message."""
        gate = EvidenceVerificationGate()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml
            (Path(temp_dir) / "pyproject.toml").write_text("[tool.pytest]")

            # Mock subprocess.run to simulate test failure
            import subprocess

            original_run = subprocess.run

            def mock_run(*args, **kwargs):
                # Simulate pytest failure
                result = subprocess.CompletedProcess(
                    args=args[0] if args else [],
                    returncode=1,
                    stdout="FAILED - test_foo",
                    stderr="",
                )
                return result

            monkeypatch.setattr(subprocess, "run", mock_run)

            passed, error = gate._run_python_tests(temp_dir)

            assert passed is False
            assert "pytest failed" in error

    def test_pytest_timeout_returns_error(self, monkeypatch):
        """Detect pytest timeout and return error message."""
        gate = EvidenceVerificationGate()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml
            (Path(temp_dir) / "pyproject.toml").write_text("[tool.pytest]")

            # Mock subprocess.run to simulate timeout
            import subprocess

            original_run = subprocess.run

            def mock_run(*args, **kwargs):
                raise subprocess.TimeoutExpired("cmd", 60)

            monkeypatch.setattr(subprocess, "run", mock_run)

            passed, error = gate._run_python_tests(temp_dir)

            assert passed is False
            assert "timed out" in error

    def test_pytest_success_returns_true(self, monkeypatch):
        """Detect pytest success and return True."""
        gate = EvidenceVerificationGate()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml
            (Path(temp_dir) / "pyproject.toml").write_text("[tool.pytest]")

            # Mock subprocess.run to simulate success
            import subprocess

            original_run = subprocess.run

            def mock_run(*args, **kwargs):
                # Simulate pytest success
                result = subprocess.CompletedProcess(
                    args=args[0] if args else [],
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                return result

            monkeypatch.setattr(subprocess, "run", mock_run)

            passed, error = gate._run_python_tests(temp_dir)

            assert passed is True
            assert error == ""


class TestGateProcess:
    """Test gate process method."""

    def test_no_task_id_passes_through(self, monkeypatch, mock_evidence_manager):
        """Gate passes through when no task_id is available."""
        gate = EvidenceVerificationGate()

        # No task_id
        monkeypatch.delenv("EVIDENCE_TASK_ID", raising=False)
        conversation = {}
        final_response = "test response"

        result = gate.process(conversation, final_response)

        assert result == {"passed": True}

    def test_all_checks_pass_returns_passed(self, monkeypatch, mock_evidence_manager):
        """Gate returns passed when all verification checks pass."""
        gate = EvidenceVerificationGate()

        # Set task_id
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-001")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_verification_gate")
        conversation = {}
        final_response = "test response"

        result = gate.process(conversation, final_response)

        assert result == {"passed": True}

    def test_missing_impl_files_blocks(self, monkeypatch):
        """Gate blocks when implementation files are missing."""
        gate = EvidenceVerificationGate()

        # Use the same terminal_id for both evidence and gate
        terminal_id = "test_verification_gate_missing"

        # Set task_id and terminal_id to match
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-002")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", terminal_id)
        conversation = {}
        final_response = "test response"

        # Create evidence manager with missing impl files using absolute path
        from pathlib import Path

        from utils.evidence import EvidenceManager

        mgr = EvidenceManager(terminal_id)

        # Use absolute state path to match gate's expected path
        state_dir = Path("P:/.claude/state")
        state_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any existing test ledger
        test_ledger = state_dir / f"code_evidence_{terminal_id}.json"
        if test_ledger.exists():
            test_ledger.unlink()

        # Override ledger file path to use absolute path
        mgr.ledger_file = test_ledger
        mgr._ensure_ledger_exists()

        # Record evidence with missing impl file
        mgr.record_red("TASK-002", ["tests/test_missing.py"], "pytest", 1)
        mgr.record_green("TASK-002", ["src/missing.py"], "pytest", 1)
        mgr.record_refactor("TASK-002", [], "pytest", 1)
        mgr.record_verify("TASK-002", 0, 0, "PASS")

        # Note: src/missing.py does NOT exist on disk

        result = gate.process(conversation, final_response)

        # Clean up test ledger
        if test_ledger.exists():
            test_ledger.unlink()

        assert result["passed"] is False
        assert "File verification failed" in result["reason"]
        assert "Implementation files missing" in result["reason"]

    def test_incomplete_evidence_blocks(self, monkeypatch):
        """Gate blocks when evidence is incomplete."""
        gate = EvidenceVerificationGate()

        # Set task_id
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-003")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_verification_gate")
        conversation = {}
        final_response = "test response"

        # Create evidence manager with incomplete evidence using absolute path
        from pathlib import Path

        from utils.evidence import EvidenceManager

        terminal_id = "test_verification_gate_incomplete"
        mgr = EvidenceManager(terminal_id)

        # Use absolute state path to match gate's expected path
        state_dir = Path("P:/.claude/state")
        state_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any existing test ledger
        test_ledger = state_dir / f"code_evidence_{terminal_id}.json"
        if test_ledger.exists():
            test_ledger.unlink()

        # Override ledger file path to use absolute path
        mgr.ledger_file = test_ledger
        mgr._ensure_ledger_exists()

        # Record only RED evidence (incomplete)
        mgr.record_red("TASK-003", [], "pytest", 1)

        # Update terminal_id to match our test
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", terminal_id)
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-003")

        result = gate.process(conversation, final_response)

        # Clean up test ledger
        if test_ledger.exists():
            test_ledger.unlink()

        assert result["passed"] is False
        assert "Evidence verification failed" in result["reason"]

    def test_pytest_failure_is_advisory(self, monkeypatch, mock_evidence_manager):
        """Pytest failures are advisory (logged but don't block)."""
        gate = EvidenceVerificationGate()

        # Set task_id
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-001")
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test_verification_gate")
        conversation = {}
        final_response = "test response"

        # Mock _run_python_tests to return failure
        def mock_run_tests(working_dir):
            return False, "pytest failed: some test failed"

        gate._run_python_tests = mock_run_tests

        result = gate.process(conversation, final_response)

        # Should still pass because pytest is advisory
        assert result["passed"] is True

    def test_terminal_id_default(self, monkeypatch):
        """Uses 'verification_gate' as default terminal_id."""
        gate = EvidenceVerificationGate()

        # Set task_id but no terminal_id - gate will use default "verification_gate"
        monkeypatch.setenv("EVIDENCE_TASK_ID", "TASK-001")
        monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)
        conversation = {}
        final_response = "test response"

        # Create evidence for the default terminal_id that the gate will use
        from pathlib import Path

        from utils.evidence import EvidenceManager

        # Gate uses "verification_gate" as default terminal_id
        terminal_id = "verification_gate"
        mgr = EvidenceManager(terminal_id)

        # Get the ledger file path for cleanup later
        state_dir = Path("P:/.claude/state")
        state_dir.mkdir(parents=True, exist_ok=True)
        test_ledger = state_dir / f"code_evidence_{terminal_id}.json"

        # EvidenceManager.__init__ already created the ledger via _ensure_ledger_exists()
        # We'll use it directly

        # Create complete evidence
        mgr.record_red("TASK-001", ["tests/test_feature.py"], "pytest tests/test_feature.py", 1)
        mgr.record_green("TASK-001", ["src/feature.py"], "pytest tests/test_feature.py", 1)
        mgr.record_refactor("TASK-001", [], "pytest tests/test_feature.py", 1)
        mgr.record_verify("TASK-001", 0, 0, "PASS")

        # Create implementation files
        test_file = Path("tests/test_feature.py")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")

        impl_file = Path("src/feature.py")
        impl_file.parent.mkdir(parents=True, exist_ok=True)
        impl_file.write_text("# impl")

        try:
            result = gate.process(conversation, final_response)
            assert result == {"passed": True}  # All evidence complete
        finally:
            # Clean up test ledger
            if test_ledger.exists():
                test_ledger.unlink()
            # Clean up test files
            if test_file.exists():
                test_file.unlink()
            if impl_file.exists():
                impl_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
