"""Tests for intent_extractor.py migration to session-scoped state paths (TASK-005).

Tests verify that intent_extractor.py uses the new state_paths.py utilities
for session-scoped state management instead of flat directory structure.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parents[1]
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Import state_paths module directly for patching in tests
import importlib.util

spec = importlib.util.spec_from_file_location("state_paths", hooks_dir / "__lib" / "state_paths.py")
state_paths = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state_paths)

from UserPromptSubmit_modules.intent_extractor import (
    extract_problem,
    extract_target,
    intent_extractor_hook,
    parse_work_intent,
    save_intent_state,
)


class TestSessionScopedStatePaths:
    """Verify session-scoped state path usage (TASK-005 migration)."""

    def test_intent_state_file_uses_session_scoped_path(self, tmp_path):
        """Test that INTENT_STATE_FILE uses get_session_state_path utility."""
        # Import to check module-level constants
        from UserPromptSubmit_modules import intent_extractor

        # Verify module has imported state_paths utilities
        assert hasattr(intent_extractor, 'get_session_state_path'), \
            "intent_extractor must import get_session_state_path from state_paths"

    def test_save_intent_uses_session_scoped_path(self, tmp_path, monkeypatch):
        """Test that save_intent_state() uses session-scoped directory structure."""
        # Mock state directory to tmp_path
        from UserPromptSubmit_modules import intent_extractor

        # Create a mock HookContext with session_id
        class MockContext:
            def __init__(self):
                self.data = {
                    "session": {"id": "test_session_123"},
                    "session_id": "test_session_123"
                }
                self.prompt = "fix the bug in authentication"

        # Save intent state
        intent = {
            "work_type": "bugfix",
            "target": "authentication",
            "problem": "bug in authentication",
            "user_prompt": "fix the bug in authentication",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        context = MockContext()

        # Patch both HOOKS_DIR and STATE_DIR (including SESSIONS_DIR) to tmp_path for testing
        monkeypatch.setattr(intent_extractor, 'HOOKS_DIR', tmp_path)
        monkeypatch.setattr(state_paths, 'STATE_DIR', tmp_path / "state")
        monkeypatch.setattr(state_paths, 'SESSIONS_DIR', tmp_path / "state" / "sessions")
        monkeypatch.setattr(state_paths, 'TERMINALS_DIR', tmp_path / "state" / "terminals")
        monkeypatch.setattr(state_paths, 'SHARED_DIR', tmp_path / "state" / "shared")

        # Save should create session-scoped directory structure
        save_intent_state(intent, context)

        # Verify new session-scoped path was created
        session_state_path = tmp_path / "state" / "sessions" / "test_session_123" / "intent_state.json"
        assert session_state_path.exists(), \
            f"Session-scoped state file should exist at {session_state_path}"

        # Verify state file content
        with open(session_state_path) as f:
            state = json.load(f)

        assert "current_intent" in state
        assert state["current_intent"]["work_type"] == "bugfix"
        assert state["current_intent"]["target"] == "authentication"

    def test_legacy_file_cleanup_on_read(self, tmp_path, monkeypatch):
        """Test that legacy intent_state.json files are cleaned up after migration."""
        from UserPromptSubmit_modules import intent_extractor

        # Create legacy flat directory structure
        legacy_session_dir = tmp_path / "session_data"
        legacy_session_dir.mkdir(parents=True, exist_ok=True)

        # Create legacy state file
        legacy_file = legacy_session_dir / "intent_state.json"
        legacy_data = {
            "current_intent": {
                "work_type": "feature",
                "target": "test",
                "problem": "test feature",
                "user_prompt": "add test feature",
                "timestamp": datetime.now(UTC).isoformat(),
            },
            "last_updated": datetime.now(UTC).isoformat(),
        }

        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f)

        # Mock HookContext
        class MockContext:
            def __init__(self):
                self.data = {
                    "session": {"id": "test_session_456"},
                    "session_id": "test_session_456"
                }
                self.prompt = "add test feature"

        # Patch both HOOKS_DIR and STATE_DIR (including SESSIONS_DIR) to tmp_path for testing
        monkeypatch.setattr(intent_extractor, 'HOOKS_DIR', tmp_path)
        monkeypatch.setattr(state_paths, 'STATE_DIR', tmp_path / "state")
        monkeypatch.setattr(state_paths, 'SESSIONS_DIR', tmp_path / "state" / "sessions")
        monkeypatch.setattr(state_paths, 'TERMINALS_DIR', tmp_path / "state" / "terminals")
        monkeypatch.setattr(state_paths, 'SHARED_DIR', tmp_path / "state" / "shared")

        context = MockContext()

        # Trigger hook which should read from legacy file and migrate
        intent_extractor_hook(context)

        # Verify legacy file was cleaned up
        assert not legacy_file.exists(), \
            "Legacy intent_state.json should be cleaned up after migration"

        # Verify new session-scoped file exists
        new_file = tmp_path / "state" / "sessions" / "test_session_456" / "intent_state.json"
        assert new_file.exists(), \
            "New session-scoped state file should exist after migration"


class TestIntentExtractorFunctionality:
    """Verify intent extraction still works after migration."""

    def test_parse_work_intent_bugfix(self):
        """Test work type detection for bugfix patterns."""
        prompt = "fix the bug in authentication module"
        result = parse_work_intent(prompt)

        assert result["work_type"] == "bugfix"
        # Target extraction may vary - just check it extracted something
        assert result["target"] != "unspecified"
        assert "authentication" in result["problem"].lower() or "bug" in result["problem"].lower()

    def test_parse_work_intent_feature(self):
        """Test work type detection for feature patterns."""
        prompt = "add support for OAuth2 authentication"
        result = parse_work_intent(prompt)

        assert result["work_type"] == "feature"
        # Target extraction may vary - just check it extracted something
        assert result["target"] != "unspecified"
        assert "oauth2" in result["target"].lower() or "authentication" in result["target"].lower()

    def test_parse_work_intent_refactor(self):
        """Test work type detection for refactor patterns."""
        prompt = "refactor the authentication code for clarity"
        result = parse_work_intent(prompt)

        assert result["work_type"] == "refactor"
        # Target extraction may vary based on pattern matching
        assert result["target"] != "unspecified"

    def test_extract_target_from_quotes(self):
        """Test target extraction from quoted strings."""
        prompt = 'fix "auth.py" file'
        result = extract_target(prompt)

        assert result == "auth.py"

    def test_extract_target_from_backticks(self):
        """Test target extraction from backtick strings."""
        prompt = "fix `auth_module.py` bug"
        result = extract_target(prompt)

        assert result == "auth_module.py"

    def test_extract_problem(self):
        """Test problem extraction from prompt."""
        prompt = "fix the authentication bug that causes login failures"
        result = extract_problem(prompt)

        assert "authentication" in result.lower()
        assert result != "Not specified"

    def test_save_and_load_intent_state(self, tmp_path, monkeypatch):
        """Test round-trip save/load of intent state."""
        from UserPromptSubmit_modules import intent_extractor

        class MockContext:
            def __init__(self):
                self.data = {
                    "session": {"id": "test_session_789"},
                    "session_id": "test_session_789"
                }
                self.prompt = "test intent"

        # Patch both HOOKS_DIR and STATE_DIR (including SESSIONS_DIR) to tmp_path for testing
        monkeypatch.setattr(intent_extractor, 'HOOKS_DIR', tmp_path)
        monkeypatch.setattr(state_paths, 'STATE_DIR', tmp_path / "state")
        monkeypatch.setattr(state_paths, 'SESSIONS_DIR', tmp_path / "state" / "sessions")
        monkeypatch.setattr(state_paths, 'TERMINALS_DIR', tmp_path / "state" / "terminals")
        monkeypatch.setattr(state_paths, 'SHARED_DIR', tmp_path / "state" / "shared")

        intent = {
            "work_type": "test",
            "target": "test_module",
            "problem": "test problem",
            "user_prompt": "test intent",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Save
        save_intent_state(intent)

        # Load and verify
        session_file = tmp_path / "state" / "sessions" / "test_session_789" / "intent_state.json"
        assert session_file.exists()

        with open(session_file) as f:
            state = json.load(f)

        assert state["current_intent"]["work_type"] == "test"
        assert state["current_intent"]["target"] == "test_module"

    def test_hook_extracts_intent_from_substantive_prompt(self, tmp_path, monkeypatch):
        """Test that hook extracts intent from prompts > 15 chars."""
        from UserPromptSubmit_modules import intent_extractor

        class MockContext:
            def __init__(self):
                self.data = {
                    "session": {"id": "test_session_999"},
                    "session_id": "test_session_999"
                }
                self.prompt = "implement new authentication feature"

        # Patch both HOOKS_DIR and STATE_DIR (including SESSIONS_DIR) to tmp_path for testing
        monkeypatch.setattr(intent_extractor, 'HOOKS_DIR', tmp_path)
        monkeypatch.setattr(state_paths, 'STATE_DIR', tmp_path / "state")
        monkeypatch.setattr(state_paths, 'SESSIONS_DIR', tmp_path / "state" / "sessions")
        monkeypatch.setattr(state_paths, 'TERMINALS_DIR', tmp_path / "state" / "terminals")
        monkeypatch.setattr(state_paths, 'SHARED_DIR', tmp_path / "state" / "shared")

        context = MockContext()

        # Run hook
        result = intent_extractor_hook(context)

        # Hook returns None (doesn't inject context)
        assert result is None

        # Verify intent was saved
        session_file = tmp_path / "state" / "sessions" / "test_session_999" / "intent_state.json"
        assert session_file.exists()

        with open(session_file) as f:
            state = json.load(f)

        assert state["current_intent"]["work_type"] == "feature"

    def test_hook_skips_short_prompts(self, tmp_path, monkeypatch):
        """Test that hook skips prompts < 15 chars."""
        from UserPromptSubmit_modules import intent_extractor

        class MockContext:
            def __init__(self):
                self.data = {
                    "session": {"id": "test_session_short"},
                    "session_id": "test_session_short"
                }
                self.prompt = "test bug"

        # Patch HOOKS_DIR
        monkeypatch.setattr(intent_extractor, 'HOOKS_DIR', tmp_path)

        context = MockContext()

        # Run hook
        result = intent_extractor_hook(context)

        # Should not save state
        session_file = tmp_path / "state" / "sessions" / "test_session_short" / "intent_state.json"
        assert not session_file.exists()
