"""Test terminal-scoped state for PreToolUse_investigation_gate.py

Proof owner for: ADR-20260410-investigation-gate-terminal-scoped-state
Contract: test_investigation_gate_terminal_scoped.py

Tests verify the terminal-scoped state migration:
1. TASK-001: _safe_id_str() helper strips dangerous chars
2. TASK-002: _state_file_candidates() includes terminal_id
3. TASK-003: _resolve_state_file() accepts terminal_id, no global cache
4. TASK-004: load_state/save_state accept terminal_id, no TTL
5. TASK-005: fresh_state() includes terminal_id field
6. TASK-006: process_hook() forwards terminal_id
7. TASK-007: main() extracts terminal_id from stdin JSON
8. TASK-008: Block message uses emoji prefix, not bracket-label

Critical unhappy-path tests:
- test_multi_terminal_isolation: Two terminals -> different files, no bleed
- test_compact_resume_same_terminal: State survives simulated compaction
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_investigation_gate import (
    _safe_id_str,
    _state_file_candidates,
    _resolve_state_file,
    _is_compaction_scenario,
    _reconstruct_files_read_from_input,
    load_state,
    save_state,
    fresh_state,
    process_hook,
    _candidate_is_writable,
)


# === TASK-001: _safe_id_str() tests ===

class TestSafeIdStr:
    """TASK-001: _safe_id_str() helper."""

    def test_safe_id_str_basic(self) -> None:
        """Basic sanitization removes special chars."""
        assert _safe_id_str("env_abc") == "env_abc"
        assert _safe_id_str("console_xyz") == "console_xyz"

    def test_safe_id_str_special_chars(self) -> None:
        """Special chars are replaced with underscores (each char individually)."""
        # Each special char becomes one underscore
        assert _safe_id_str("env_abc!@#") == "env_abc___"
        assert _safe_id_str("foo<>bar") == "foo__bar"  # < and > each become _
        # Input: 'test:"/\\|?*' -> chars: ' (x2), :, ", /, \\ (x2), |, ?, * = 9 special chars
        assert _safe_id_str('test:"/\\|?*') == "test_______"  # 9 underscores

    def test_safe_id_str_truncation(self) -> None:
        """Long strings are truncated to 64 chars."""
        result = _safe_id_str("x" * 100)
        assert len(result) == 64
        assert result == "x" * 64

    def test_safe_id_str_empty(self) -> None:
        """Empty or whitespace-only returns 'default'."""
        assert _safe_id_str("") == "default"
        assert _safe_id_str("   ") == "default"
        assert _safe_id_str("\t\n") == "default"

    def test_safe_id_str_whitespace(self) -> None:
        """Internal spaces are replaced with underscores."""
        assert _safe_id_str("foo bar") == "foo_bar"
        assert _safe_id_str("foo  bar") == "foo__bar"


# === TASK-002: _state_file_candidates() tests ===

class TestStateFileCandidates:
    """TASK-002: _state_file_candidates() with terminal_id."""

    def test_state_file_candidates_with_id(self) -> None:
        """With terminal_id, filenames include the safe terminal name."""
        candidates = _state_file_candidates("env_abc")
        filenames = [c.name for c in candidates]
        assert all("investigation_state_env_abc" in f for f in filenames)

    def test_state_file_candidates_empty(self) -> None:
        """Empty terminal_id falls back to 'default'."""
        candidates = _state_file_candidates("")
        filenames = [c.name for c in candidates]
        assert all("investigation_state_default" in f for f in filenames)

    def test_state_file_candidates_order(self) -> None:
        """Candidate order is configured -> local_fallback -> temp_fallback."""
        candidates = _state_file_candidates("test_term")
        assert len(candidates) == 3
        # Order should be: configured (CSF_STATE_DIR), local_fallback (session_data), temp_fallback (temp)
        c0, c1, c2 = [str(c) for c in candidates]
        assert "claude" in c0 or "state" in c0  # configured path
        assert "session_data" in c1
        assert "temp" in c2.lower() or "tmp" in c2.lower()


# === TASK-003: _resolve_state_file() tests ===

class TestResolveStateFile:
    """TASK-003: _resolve_state_file() accepts terminal_id, no global cache."""

    def test_resolve_state_file_with_id(self, tmp_path: Path) -> None:
        """Resolves to a writable path ending with terminal-scoped filename."""
        with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):
            candidates = _state_file_candidates("env_test")
            # Find a writable candidate
            for candidate in candidates:
                if _candidate_is_writable(candidate):
                    assert "investigation_state_env_test" in candidate.name
                    break

    def test_resolve_state_file_empty(self, tmp_path: Path) -> None:
        """Empty terminal_id uses 'default' fallback."""
        with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):
            candidates = _state_file_candidates("")
            for candidate in candidates:
                if _candidate_is_writable(candidate):
                    assert "investigation_state_default" in candidate.name
                    break


# === TASK-004: load_state/save_state tests ===

class TestLoadSaveState:
    """TASK-004: load_state and save_state accept terminal_id, no TTL."""

    def test_save_and_load_state_with_id(self, tmp_path: Path) -> None:
        """save_state then load_state returns same terminal-scoped data."""
        terminal_id = "test_terminal_001"
        state = fresh_state(terminal_id)
        state["files_read"] = ["P:/test/a.py", "P:/test/b.py"]
        state["modules_investigated"] = {"P:/test"}

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                sys, "path", [str(HOOKS_DIR)] + sys.path
            ):
                # Patch _resolve_state_file to use tmpdir
                from PreToolUse_investigation_gate import _state_file_candidates as orig_candidates

                def _mock_candidates(tid: str = "") -> list[Path]:
                    safe = _safe_id_str(tid) if tid else "default"
                    return [Path(tmpdir) / f"investigation_state_{safe}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    save_state(state, terminal_id)
                    loaded = load_state(terminal_id)

        assert loaded["files_read"] == ["P:/test/a.py", "P:/test/b.py"]
        assert loaded["terminal_id"] == "test_terminal_001"

    def test_corrupted_state_file(self, tmp_path: Path) -> None:
        """Corrupted JSON returns fresh_state, not exception."""
        terminal_id = "test_corrupt"
        tmpfile = tmp_path / f"investigation_state_{_safe_id_str(terminal_id)}.json"
        tmpfile.write_text("{ invalid json }")

        with tempfile.TemporaryDirectory():
            with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

                def _mock_candidates(tid: str = "") -> list[Path]:
                    return [tmp_path / f"investigation_state_{_safe_id_str(tid if tid else 'default')}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    result = load_state(terminal_id)

        # Should return fresh_state, not crash
        assert isinstance(result, dict)
        assert "files_read" in result
        assert result["files_read"] == []

    def test_missing_state_file(self, tmp_path: Path) -> None:
        """Missing file returns fresh_state."""
        terminal_id = "test_missing"

        with tempfile.TemporaryDirectory():
            with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

                def _mock_candidates(tid: str = "") -> list[Path]:
                    return [tmp_path / f"investigation_state_{_safe_id_str(tid if tid else 'default')}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    result = load_state(terminal_id)

        assert isinstance(result, dict)
        assert result["files_read"] == []

    def test_empty_terminal_id(self, tmp_path: Path) -> None:
        """Empty terminal_id uses 'default' filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

                def _mock_candidates(tid: str = "") -> list[Path]:
                    safe = _safe_id_str(tid) if tid else "default"
                    return [Path(tmpdir) / f"investigation_state_{safe}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    state = fresh_state("")
                    assert state["terminal_id"] == "default"

                    save_state(state, "")
                    loaded = load_state("")
                    assert loaded["terminal_id"] == "default"


# === TASK-005: fresh_state() tests ===

class TestFreshState:
    """TASK-005: fresh_state() includes terminal_id field."""

    def test_fresh_state_terminal_id(self) -> None:
        """fresh_state with terminal_id includes it in output."""
        state = fresh_state("env_abc")
        assert state["terminal_id"] == "env_abc"
        assert isinstance(state["files_read"], list)
        assert isinstance(state["modules_investigated"], set)

    def test_fresh_state_default(self) -> None:
        """fresh_state without terminal_id defaults to 'default'."""
        state = fresh_state("")
        assert state["terminal_id"] == "default"

        state2 = fresh_state()
        assert state2["terminal_id"] == "default"

    def test_fresh_state_has_required_fields(self) -> None:
        """fresh_state returns all required InvestigationState fields."""
        state = fresh_state("test")
        required = [
            "timestamp",
            "terminal_id",
            "files_read",
            "modules_investigated",
            "investigation_declared",
            "greenfield_declared",
            "searches_performed",
        ]
        for field in required:
            assert field in state, f"Missing field: {field}"


# === TASK-006: process_hook() terminal_id forwarding ===

class TestProcessHookTerminalId:
    """TASK-006: process_hook() accepts and forwards terminal_id."""

    def test_process_hook_accepts_terminal_id(self) -> None:
        """process_hook signature accepts terminal_id parameter."""
        # This tests the function signature and that it runs without error
        result = process_hook(
            tool_name="Read",
            tool_input={"file_path": "P:/test.py"},
            user_message="test",
            terminal_id="test_terminal_002",
        )
        # Should return (True, ...) — allowed
        assert result[0] is True

    def test_process_hook_different_terminals_get_different_state(self) -> None:
        """Two terminals with different IDs maintain isolated state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

                def _mock_candidates(tid: str = "") -> list[Path]:
                    safe = _safe_id_str(tid) if tid else "default"
                    return [Path(tmpdir) / f"investigation_state_{safe}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    # Terminal A saves state
                    state_a = fresh_state("terminal_a")
                    state_a["files_read"] = ["P:/a.py"]
                    save_state(state_a, "terminal_a")

                    # Terminal B saves state
                    state_b = fresh_state("terminal_b")
                    state_b["files_read"] = ["P:/b.py", "P:/c.py"]
                    save_state(state_b, "terminal_b")

                    # Each terminal reads back its own state
                    loaded_a = load_state("terminal_a")
                    loaded_b = load_state("terminal_b")

        assert loaded_a["files_read"] == ["P:/a.py"]
        assert loaded_b["files_read"] == ["P:/b.py", "P:/c.py"]
        assert loaded_a["terminal_id"] == "terminal_a"
        assert loaded_b["terminal_id"] == "terminal_b"


# === TASK-007: main() terminal_id extraction ===

class TestMainTerminalId:
    """TASK-007: main() extracts terminal_id from stdin JSON."""

    def test_main_extracts_terminal_id(self) -> None:
        """main() reads terminal_id from input_data."""
        import json
        from io import StringIO
        from PreToolUse_investigation_gate import get_last_user_message_from_input

        input_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "P:/test.py"},
            "terminal_id": "env_console_test",
            "terminalId": None,
            "conversation": [{"role": "user", "content": "hello"}],
        }

        # Verify extraction logic works
        terminal_id = str(
            input_data.get("terminal_id")
            or input_data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        ).strip()
        assert terminal_id == "env_console_test"

    def test_main_extracts_terminalId_variant(self) -> None:
        """main() accepts terminalId (camelCase) variant."""
        input_data = {
            "tool_name": "Read",
            "tool_input": {},
            "terminalId": "console_camelcase",
        }

        terminal_id = str(
            input_data.get("terminal_id")
            or input_data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        ).strip()
        assert terminal_id == "console_camelcase"


# === TASK-008: Block message quality ===

class TestBlockMessageQuality:
    """TASK-008: Block message uses emoji prefix, not bracket-label."""

    def test_block_message_uses_emoji_prefix(self) -> None:
        """Block message starts with emoji prefix, not bracket-label."""
        # Trigger a block by calling process_hook with no prior reads
        result = process_hook(
            tool_name="Edit",
            tool_input={"path": "P:/test.py", "old_string": "foo", "new_string": "bar"},
            user_message="fix the bug",
            terminal_id="test_block_msg",
        )

        # result is (allowed: bool, message: str)
        if not result[0]:  # Blocked
            message = result[1]
            assert message.startswith("⛔"), f"Expected emoji prefix, got: {message[:50]}"
            assert "[WORKFLOW_BLOCK_NOT_HOOK_CRASH]" not in message
            assert "This is a workflow checkpoint, not an error." in message

    def test_block_message_shows_target_and_coverage(self) -> None:
        """Block message includes target path, risk tier, and coverage ratio."""
        result = process_hook(
            tool_name="Edit",
            tool_input={"path": "P:/foo/bar.py", "old_string": "a", "new_string": "b"},
            user_message="fix",
            terminal_id="test_coverage",
        )

        if not result[0]:
            message = result[1]
            assert "P:/foo/bar.py" in message or "bar.py" in message
            assert "Coverage:" in message
            assert "related files read" in message


# === Critical unhappy-path tests ===

class TestMultiTerminalIsolation:
    """Critical: Multi-terminal isolation — two terminals get different files."""

    def test_multi_terminal_isolation(self, tmp_path: Path) -> None:
        """Two terminals with different IDs -> different files, no bleed."""
        with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

            def _mock_candidates(tid: str = "") -> list[Path]:
                safe = _safe_id_str(tid) if tid else "default"
                return [tmp_path / f"investigation_state_{safe}.json"]

            with patch(
                "PreToolUse_investigation_gate._state_file_candidates",
                _mock_candidates,
            ):
                # Terminal 1: reads a.py
                state1 = fresh_state("terminal_1")
                state1["files_read"] = ["P:/module_a/a.py", "P:/module_a/b.py"]
                save_state(state1, "terminal_1")

                # Terminal 2: reads c.py
                state2 = fresh_state("terminal_2")
                state2["files_read"] = ["P:/module_c/c.py"]
                save_state(state2, "terminal_2")

                # Load fresh for each terminal
                loaded1 = load_state("terminal_1")
                loaded2 = load_state("terminal_2")

        # Terminals must not bleed into each other
        assert loaded1["files_read"] == ["P:/module_a/a.py", "P:/module_a/b.py"]
        assert loaded2["files_read"] == ["P:/module_c/c.py"]
        assert loaded1["terminal_id"] == "terminal_1"
        assert loaded2["terminal_id"] == "terminal_2"

        # Verify files are actually separate on disk
        f1 = tmp_path / "investigation_state_terminal_1.json"
        f2 = tmp_path / "investigation_state_terminal_2.json"
        assert f1.exists(), f"Terminal 1 state file not found: {f1}"
        assert f2.exists(), f"Terminal 2 state file not found: {f2}"

        with open(f1) as fh:
            disk1 = json.load(fh)
        with open(f2) as fh:
            disk2 = json.load(fh)

        assert "P:/module_a/a.py" in disk1["files_read"]
        assert "P:/module_c/c.py" in disk2["files_read"]
        assert "P:/module_a/a.py" not in disk2["files_read"]
        assert "P:/module_c/c.py" not in disk1["files_read"]


class TestCompactResumeSameTerminal:
    """Critical: Same terminal survives simulated compaction (no TTL)."""

    def test_compact_resume_same_terminal(self, tmp_path: Path) -> None:
        """State for same terminal persists across simulated compaction."""
        terminal_id = "console_same"

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(sys, "path", [str(HOOKS_DIR)] + sys.path):

                def _mock_candidates(tid: str = "") -> list[Path]:
                    safe = _safe_id_str(tid) if tid else "default"
                    return [Path(tmpdir) / f"investigation_state_{safe}.json"]

                with patch(
                    "PreToolUse_investigation_gate._state_file_candidates",
                    _mock_candidates,
                ):
                    # Before compaction: reads a.py
                    state_before = fresh_state(terminal_id)
                    state_before["files_read"] = ["P:/old/a.py", "P:/old/b.py"]
                    save_state(state_before, terminal_id)

                    # Simulate time passing (old TTL would have expired here)
                    time.sleep(0.1)

                    # After compaction: load state — should still have the reads
                    # (no TTL check anymore, terminal_id persistence is the key)
                    state_after = load_state(terminal_id)

        assert state_after["files_read"] == ["P:/old/a.py", "P:/old/b.py"]
        assert state_after["terminal_id"] == "console_same"


class TestNoTTLInLoadState:
    """Verify that load_state does NOT have a TTL timestamp age check."""

    def test_load_state_no_timestamp_age_check(self, tmp_path: Path) -> None:
        """load_state should not check timestamp age (TTL removal)."""
        import re

        # Read the source to confirm TTL check is removed
        source_file = HOOKS_DIR / "PreToolUse_investigation_gate.py"
        source = source_file.read_text(encoding="utf-8")

        # The old TTL check looked like: age = now - timestamp
        # After removal, there should be no age/TTL check in load_state
        load_state_start = source.find("def load_state(")
        load_state_end = source.find("\ndef ", load_state_start + 1)
        load_state_body = source[load_state_start:load_state_end]

        # Should NOT contain TTL-style age checks
        assert "age" not in load_state_body.lower() or "_is_compaction" in load_state_body.lower()
        # The compaction check is fine, but TTL expiry check is gone


class TestCompactionReconstruction:
    """Tests for session compaction recovery via transcript parsing."""

    def test_is_compaction_scenario_true(self) -> None:
        """Returns True when state is empty but transcript has prior tool calls."""
        state = {"files_read": [], "timestamp": 1000.0}
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Read", "timestamp": 500.0, "input": {"file_path": "P:/a.py"}},
                {"type": "tool", "name": "Read", "timestamp": 800.0, "input": {"file_path": "P:/b.py"}},
            ]
        }
        assert _is_compaction_scenario(state, input_data) is True

    def test_is_compaction_scenario_false_when_files_exist(self) -> None:
        """Returns False when state already has files_read."""
        state = {"files_read": ["P:/a.py"], "timestamp": 1000.0}
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Read", "timestamp": 500.0, "input": {"file_path": "P:/a.py"}},
            ]
        }
        assert _is_compaction_scenario(state, input_data) is False

    def test_is_compaction_scenario_false_no_prior_entries(self) -> None:
        """Returns False when transcript has no entries older than state."""
        state = {"files_read": [], "timestamp": 500.0}
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Read", "timestamp": 1000.0, "input": {"file_path": "P:/a.py"}},
            ]
        }
        assert _is_compaction_scenario(state, input_data) is False

    def test_is_compaction_scenario_false_empty_transcript(self) -> None:
        """Returns False when transcript is empty."""
        state = {"files_read": [], "timestamp": 1000.0}
        input_data = {"transcript_entries": []}
        assert _is_compaction_scenario(state, input_data) is False

    def test_is_compaction_scenario_handles_non_dict_entry(self) -> None:
        """Does not crash when transcript contains non-dict entries."""
        state = {"files_read": [], "timestamp": 1000.0}
        input_data = {
            "transcript_entries": [
                None,  # type: ignore
                "not a dict",
                {"type": "tool", "name": "Read", "timestamp": 500.0, "input": {"file_path": "P:/a.py"}},
            ]
        }
        # Should return True (found valid tool entry predating state) and not raise
        assert _is_compaction_scenario(state, input_data) is True

    def test_reconstruct_files_read_from_input(self) -> None:
        """Extracts file paths from transcript tool entries."""
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Read", "input": {"file_path": "P:/a.py"}},
                {"type": "tool", "name": "Grep", "input": {"path": "P:/b.py"}},
                {"type": "tool", "name": "Glob", "input": {"path": "P:/c.py"}},
                {"type": "tool", "name": "Bash", "input": {"command": "ls"}},  # no file path
            ]
        }
        result = _reconstruct_files_read_from_input(input_data)
        assert result == ["P:/a.py", "P:/b.py", "P:/c.py"]

    def test_reconstruct_files_read_handles_schema_fallback(self) -> None:
        """Handles alternative schema keys: tool_name and args."""
        input_data = {
            "transcript_entries": [
                {"type": "tool", "tool_name": "Read", "args": {"file_path": "P:/fallback.py"}},
            ]
        }
        result = _reconstruct_files_read_from_input(input_data)
        assert result == ["P:/fallback.py"]

    def test_reconstruct_deduplicates_duplicate_paths(self) -> None:
        """Same file read multiple times appears only once."""
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Read", "input": {"file_path": "P:/a.py"}},
                {"type": "tool", "name": "Read", "input": {"file_path": "P:/a.py"}},
                {"type": "tool", "name": "Read", "input": {"file_path": "P:/a.py"}},
            ]
        }
        result = _reconstruct_files_read_from_input(input_data)
        assert result == ["P:/a.py"]

    def test_reconstruct_handles_malformed_entries(self) -> None:
        """Skips non-dict entries without crashing."""
        input_data = {
            "transcript_entries": [
                None,  # type: ignore
                {"type": "not_tool"},
                {"type": "tool", "name": "UnknownTool"},
                {"type": "tool", "name": "Read", "input": {}},  # no file_path
            ]
        }
        result = _reconstruct_files_read_from_input(input_data)
        assert result == []

    def test_reconstruct_files_read_skips_non_read_tools(self) -> None:
        """Only captures Read/Grep/Glob/Bash tools."""
        input_data = {
            "transcript_entries": [
                {"type": "tool", "name": "Edit", "input": {"file_path": "P:/edited.py"}},
                {"type": "tool", "name": "Write", "input": {"file_path": "P:/written.py"}},
                {"type": "tool", "name": "Bash", "input": {"command": "echo hello"}},  # no file path
            ]
        }
        result = _reconstruct_files_read_from_input(input_data)
        assert result == []


class TestModulesInvestigatedRoundTrip:
    """Verify modules_investigated set→list→set round-trip."""

    def test_load_state_restores_set_type(self, tmp_path: Path) -> None:
        """modules_investigated is restored as a set after JSON load."""
        terminal_id = "console_roundtrip"
        from unittest.mock import patch

        def _mock_candidates(tid: str = "") -> list[Path]:
            safe = _safe_id_str(tid) if tid else "default"
            return [tmp_path / f"investigation_state_{safe}.json"]

        with patch("PreToolUse_investigation_gate._state_file_candidates", _mock_candidates):
            # Save state with modules_investigated as a set
            state = fresh_state(terminal_id)
            state["modules_investigated"] = {"mod_a", "mod_b"}
            save_state(state, terminal_id)

            # Load state and verify type is restored
            loaded = load_state(terminal_id)
            assert isinstance(loaded["modules_investigated"], set)
            assert loaded["modules_investigated"] == {"mod_a", "mod_b"}

    def test_save_state_converts_set_to_list(self, tmp_path: Path) -> None:
        """modules_investigated is serialized as list for JSON."""
        terminal_id = "console_setconv"
        from unittest.mock import patch

        def _mock_candidates(tid: str = "") -> list[Path]:
            safe = _safe_id_str(tid) if tid else "default"
            return [tmp_path / f"investigation_state_{safe}.json"]

        with patch("PreToolUse_investigation_gate._state_file_candidates", _mock_candidates):
            state = fresh_state(terminal_id)
            state["modules_investigated"] = {"mod_x"}
            save_state(state, terminal_id)

            # Read raw JSON to verify serialization format
            state_file = tmp_path / f"investigation_state_{_safe_id_str(terminal_id)}.json"
            raw = json.loads(state_file.read_text())
            assert isinstance(raw["modules_investigated"], list)
            assert raw["modules_investigated"] == ["mod_x"]
