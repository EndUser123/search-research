"""
Shared fixtures for skill-first enforcement system tests.

This module provides reusable fixtures for testing the three-layer enforcement pipeline:
- Intent file lifecycle
- TTL enforcement
- TOCTOU retry logic
- Help flag detection
- Prose bypass detection
- Pattern 2 exemption
- Multi-terminal isolation
- Three-tier path lookup
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Base hooks directory for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory for intent files.

    This fixture provides a clean temporary directory for each test,
    preventing cross-test pollution. The directory is automatically
    cleaned up after each test.

    Returns:
        Path: Temporary directory path
    """
    state_dir = tmp_path / "state" / "terminals"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


@pytest.fixture
def mock_terminal_id():
    """Provide a consistent mock terminal ID for testing.

    Returns:
        str: Mock terminal UUID
    """
    return "test-console-abc123-def456"


@pytest.fixture
def sample_intent_file(temp_state_dir, mock_terminal_id):
    """Create a sample intent file for testing.

    This fixture creates a valid intent file with all required fields
    in the correct location within the temporary state directory.

    Args:
        temp_state_dir: Temporary state directory fixture
        mock_terminal_id: Mock terminal ID fixture

    Returns:
        Path: Path to the created intent file
    """
    intent_dir = temp_state_dir / mock_terminal_id
    intent_dir.mkdir(parents=True, exist_ok=True)

    intent_file = intent_dir / "pending_command_intent.json"

    # Create sample intent data
    intent_data = {
        "skill": "test-skill",
        "prompt": "/test-command with args",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "test-session-123",
        "terminal_id": mock_terminal_id,
        "created_at": int(datetime.now(timezone.utc).timestamp())
    }

    intent_file.write_text(json.dumps(intent_data, indent=2))

    return intent_file


@pytest.fixture
def stale_intent_file(temp_state_dir, mock_terminal_id):
    """Create a stale intent file for TTL testing.

    This fixture creates an intent file that is older than the default
    90-second TTL window, useful for testing expiration logic.

    Args:
        temp_state_dir: Temporary state directory fixture
        mock_terminal_id: Mock terminal ID fixture

    Returns:
        Path: Path to the created stale intent file
    """
    intent_dir = temp_state_dir / mock_terminal_id
    intent_dir.mkdir(parents=True, exist_ok=True)

    intent_file = intent_dir / "pending_command_intent.json"

    # Create intent data with old timestamp (> 90 seconds ago)
    old_timestamp = int(datetime.now(timezone.utc).timestamp()) - 120  # 2 minutes ago

    intent_data = {
        "skill": "test-skill",
        "prompt": "/test-command",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "test-session-123",
        "terminal_id": mock_terminal_id,
        "created_at": old_timestamp
    }

    intent_file.write_text(json.dumps(intent_data, indent=2))

    return intent_file


@pytest.fixture
def mock_skill_enforcer():
    """Create a mock skill_enforcer module for testing.

    This fixture provides a MagicMock object that simulates the
    skill_enforcer module, allowing tests to verify function calls
    without importing the actual module.

    Returns:
        MagicMock: Mock skill_enforcer module
    """
    mock_enforcer = MagicMock()
    mock_enforcer._is_help_request = MagicMock(return_value=False)
    mock_enforcer._write_intent_file = MagicMock(return_value=None)
    return mock_enforcer


@pytest.fixture
def sample_hook_input():
    """Create sample hook input data for testing.

    This fixture provides realistic hook input data that matches
    the actual PreToolUse hook format.

    Returns:
        dict: Sample hook input with tool_name, tool_input, etc.
    """
    return {
        "tool_name": "Read",
        "tool_input": {
            "file_path": "P:/test/file.py"
        },
        "tool_response": "file content here",
        "session_id": "test-session-123",
        "terminal_id": "test-console-abc123"
    }


@pytest.fixture
def multi_terminal_state_dirs(temp_state_dir):
    """Create multiple terminal state directories for isolation testing.

    This fixture creates several terminal directories to test
    concurrent operations and isolation between terminals.

    Args:
        temp_state_dir: Temporary state directory fixture

    Returns:
        list: List of (terminal_id, intent_dir) tuples
    """
    terminals = []
    for i in range(3):
        terminal_id = f"test-terminal-{i}"
        intent_dir = temp_state_dir / terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)
        terminals.append((terminal_id, intent_dir))

    return terminals


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing.

    This fixture configures common environment variables used
    by the skill-first enforcement system.

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        dict: Dictionary of configured env vars
    """
    env_vars = {
        "SKILL_FIRST_INTENT_TTL_SECONDS": "90",
        "SKILL_BYPASS_DETECTION_ENABLED": "true",
        "SKILL_BYPASS_DETECTION_MODE": "warn"
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars
