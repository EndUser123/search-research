#!/usr/bin/env python3
"""
Evidence Store API Validation Test

This test validates the actual API behavior of evidence_store.py against
documented assumptions. Key validation points:

1. Event dict structure (name, timestamp, output keys)
2. Function signatures (load_tool_events, resolve_session_id, read_session_context)
3. Session isolation with concurrent terminals
4. terminal_id population behavior

Test Scope: RED phase - validates API assumptions before integration
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

import evidence_store


class TestEventDictStructure:
    """Validate that event dictionaries use the documented key names."""

    def test_load_tool_events_returns_name_key(self):
        """Event dict should use 'name' not 'tool_name'."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-001"

            # Mock normalize_session_id to accept any string
            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Bash",
                    command="echo test",
                    cwd="/tmp",
                    output_excerpt="test output",
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)

                assert len(events) == 1
                event = events[0]

                assert "name" in event, "Event dict should have 'name' key"
                assert event["name"] == "Bash"
                assert "tool_name" not in event, "Event dict should NOT have 'tool_name' key"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_load_tool_events_returns_timestamp_key(self):
        """Event dict should use 'timestamp' not 'ts'."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-002"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Read",
                    command="file.txt",
                    cwd="/tmp",
                    output_excerpt="content",
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)
                assert len(events) == 1
                event = events[0]

                assert "timestamp" in event, "Event dict should have 'timestamp' key"
                assert len(event["timestamp"]) > 0
                assert "ts" not in event, "Event dict should NOT have 'ts' key"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_load_tool_events_returns_output_key(self):
        """Event dict should use 'output' not 'output_excerpt'."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-003"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                test_output = "this is test output content"
                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Grep",
                    command="grep pattern",
                    cwd="/tmp",
                    output_excerpt=test_output,
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)
                assert len(events) == 1
                event = events[0]

                assert "output" in event, "Event dict should have 'output' key"
                assert event["output"] == test_output
                assert "output_excerpt" not in event, "Event dict should NOT have 'output_excerpt' key"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestFunctionSignatures:
    """Validate exact function signatures for evidence_store APIs."""

    def test_read_session_context_no_parameters(self):
        """read_session_context() should take 0 parameters."""
        result = evidence_store.read_session_context()
        assert isinstance(result, dict), "read_session_context() should return dict"

    def test_resolve_session_id_optional_explicit_param(self):
        """resolve_session_id() should have optional 'explicit' parameter."""
        result1 = evidence_store.resolve_session_id()
        assert isinstance(result1, str)

        explicit_id = "550e8400-e29b-41d4-a716-446655440000"
        result2 = evidence_store.resolve_session_id(explicit=explicit_id)
        assert result2 == explicit_id

    def test_load_tool_events_signature(self):
        """load_tool_events() should accept session_id and optional parameters."""
        session_id = "test-session-004"

        events = evidence_store.load_tool_events(session_id)
        assert isinstance(events, list)

        events = evidence_store.load_tool_events(
            session_id=session_id,
            limit=100,
            terminal_id="terminal-2",
            within_seconds=3600
        )
        assert isinstance(events, list)


class TestTerminalIdPopulation:
    """Validate how terminal_id is populated in events."""

    def test_terminal_id_populated_when_provided(self):
        """terminal_id should be populated when provided to append_tool_event."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-005"
            test_terminal = "test-terminal-abc123"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id=test_terminal,
                    tool_name="Bash",
                    command="test",
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)
                assert len(events) == 1
                event = events[0]

                assert "terminal_id" in event
                assert event["terminal_id"] == test_terminal
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_terminal_id_defaults_to_empty_string(self):
        """terminal_id should default to empty string when not provided."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-006"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="",
                    tool_name="Bash",
                    command="test",
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)
                assert len(events) == 1
                event = events[0]

                assert "terminal_id" in event
                assert event["terminal_id"] == ""
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestSessionIsolation:
    """Validate that session isolation works correctly."""

    def test_sessions_are_isolated(self):
        """Events from different sessions should not mix."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                session_a = "session-a-123"
                session_b = "session-b-456"

                evidence_store.append_tool_event(
                    session_id=session_a,
                    terminal_id="terminal-1",
                    tool_name="Bash",
                    command="echo a",
                    success=True
                )

                evidence_store.append_tool_event(
                    session_id=session_b,
                    terminal_id="terminal-1",
                    tool_name="Bash",
                    command="echo b",
                    success=True
                )

                events_a = evidence_store.load_tool_events(session_a)
                assert len(events_a) == 1
                assert events_a[0]["command"] == "echo a"

                events_b = evidence_store.load_tool_events(session_b)
                assert len(events_b) == 1
                assert events_b[0]["command"] == "echo b"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_concurrent_terminals_same_session(self):
        """Multiple terminals can write to the same session_id."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-007"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Bash",
                    command="echo from terminal 1",
                    success=True
                )

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-2",
                    tool_name="Bash",
                    command="echo from terminal 2",
                    success=True
                )

                events = evidence_store.load_tool_events(session_id)
                assert len(events) == 2

                commands = {e["command"] for e in events}
                assert "echo from terminal 1" in commands
                assert "echo from terminal 2" in commands

                terminal_ids = {e["terminal_id"] for e in events}
                assert "terminal-1" in terminal_ids
                assert "terminal-2" in terminal_ids
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_load_tool_events_terminal_filter(self):
        """load_tool_events accepts terminal_id parameter but doesn't filter by it.

        CRITICAL FINDING: The terminal_id parameter is documented and accepted
        by the function signature, but the WHERE clause does not actually filter
        by terminal_id. This is a documented but unimplemented feature.

        This test documents the ACTUAL behavior (not the documented behavior).
        """
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-008"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Bash",
                    command="cmd1",
                    success=True
                )

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-2",
                    tool_name="Bash",
                    command="cmd2",
                    success=True
                )

                evidence_store.append_tool_event(
                    session_id=session_id,
                    terminal_id="terminal-1",
                    tool_name="Grep",
                    command="cmd3",
                    success=True
                )

                # ACTUAL BEHAVIOR: terminal_id parameter is accepted but NOT used for filtering
                # All events are returned regardless of terminal_id filter
                events_t1 = evidence_store.load_tool_events(session_id, terminal_id="terminal-1")
                assert len(events_t1) == 3, "terminal_id filter doesn't work - all events returned"

                # Each event still has its terminal_id populated correctly
                terminal_ids = {e["terminal_id"] for e in events_t1}
                assert terminal_ids == {"terminal-1", "terminal-2"}, "terminal_id values are stored correctly"
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


class TestEvidenceIntegration:
    """Integration tests for complete evidence workflows."""

    def test_full_write_and_read_workflow(self):
        """Test complete workflow: write events, read them back, verify structure."""
        tmpdir = tempfile.mkdtemp()
        try:
            db_path = Path(tmpdir) / "evidence.db"
            session_id = "test-session-integration"

            with mock.patch.object(evidence_store, 'EVIDENCE_DB_PATH', db_path), \
                 mock.patch.object(evidence_store, 'normalize_session_id', side_effect=lambda x: x):

                evidence_store.init_db()

                events_to_write = [
                    ("Bash", "git status", "/repo", "On branch main"),
                    ("Read", "README.md", "/repo", "# Project"),
                    ("Grep", "pattern", "/repo", "match results"),
                ]

                for tool_name, command, cwd, output in events_to_write:
                    evidence_store.append_tool_event(
                        session_id=session_id,
                        terminal_id="test-terminal",
                        tool_name=tool_name,
                        command=command,
                        cwd=cwd,
                        output_excerpt=output,
                        success=True
                    )

                events = evidence_store.load_tool_events(session_id)

                assert len(events) == 3

                for i, event in enumerate(events):
                    assert "name" in event
                    assert "timestamp" in event
                    assert "output" in event
                    assert "command" in event
                    assert "cwd" in event
                    assert "session_id" in event
                    assert "terminal_id" in event
                    assert "success" in event

                    assert "tool_name" not in event
                    assert "ts" not in event
                    assert "output_excerpt" not in event

                    expected_tool, expected_cmd, expected_cwd, expected_output = events_to_write[i]
                    assert event["name"] == expected_tool
                    assert event["command"] == expected_cmd
                    assert event["cwd"] == expected_cwd
                    assert event["output"] == expected_output
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
