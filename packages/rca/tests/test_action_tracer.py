"""Tests for action_tracer module (Flow-of-Action Paradigm).

Tests action recording, graph construction, and divergence detection.

Author: CSF Development Team
Task: #986
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from rca.action_tracer import (
    Action,
    ActionGraph,
    ActionType,
    ActionTracer,
    classify_action,
    create_tracer_for_session,
    get_expected_path,
    EXPECTED_PATHS,
    hash_output,
)


class TestActionType:
    """Test ActionType enum and classification."""

    def test_action_type_values(self):
        """ActionType enum has expected values."""
        assert ActionType.READ_FILE.value == "read_file"
        assert ActionType.SEARCH_CODE.value == "search_code"
        assert ActionType.TRACE_SYMBOL.value == "trace_symbol"
        assert ActionType.FORM_HYPOTHESIS.value == "form_hypothesis"
        assert ActionType.VERIFY_HYPOTHESIS.value == "verify_hypothesis"


class TestClassifyAction:
    """Test action classification from tool usage."""

    def test_classify_read_file(self):
        """Read tool is classified as READ_FILE."""
        result = classify_action("Read", {"file_path": "test.py"}, "")
        assert result == ActionType.READ_FILE

    def test_classify_search_code(self):
        """Grep tool is classified as SEARCH_CODE."""
        result = classify_action("Grep", {"pattern": "foo"}, "")
        assert result == ActionType.SEARCH_CODE

    def test_classify_serena_trace_symbol(self):
        """Serena find_referencing_symbols is classified as TRACE_SYMBOL."""
        result = classify_action(
            "mcp__plugin_serena_serena__find_referencing_symbols",
            {"name_path": "MyClass"},
            "",
        )
        assert result == ActionType.TRACE_SYMBOL

    def test_classify_serena_search(self):
        """Serena find_symbol is classified as SEARCH_CODE."""
        result = classify_action(
            "mcp__plugin_serena_serena__find_symbol",
            {"name_path_pattern": "MyClass"},
            "",
        )
        assert result == ActionType.SEARCH_CODE

    def test_classify_bash_test(self):
        """Bash with pytest is classified as EXECUTE_TEST."""
        result = classify_action(
            "Bash",
            {"command": "pytest test_file.py"},
            "",
        )
        assert result == ActionType.EXECUTE_TEST

    def test_classify_skill_search(self):
        """Skill with search is classified as SEARCH_HISTORY."""
        result = classify_action(
            "Skill",
            {"skill": "search"},
            "",
        )
        assert result == ActionType.SEARCH_HISTORY

    def test_classify_webfetch(self):
        """WebFetch is classified as FETCH_DOCS."""
        result = classify_action("WebFetch", {"url": "https://example.com"}, "")
        assert result == ActionType.FETCH_DOCS

    def test_classify_task(self):
        """Task tool is classified as VERIFY_HYPOTHESIS."""
        result = classify_action("Task", {"subagent_type": "rca-specialist"}, "")
        assert result == ActionType.VERIFY_HYPOTHESIS


class TestAction:
    """Test Action dataclass."""

    def test_action_creation(self):
        """Action can be created with all fields."""
        action = Action(
            action_id="act_001",
            action_type=ActionType.READ_FILE,
            timestamp="2026-02-16T12:00:00",
            tool_used="Read",
            tool_input={"file_path": "test.py"},
            tool_output_hash="123:abc...def",
            tool_output_preview="# Test file",
            phase=1,
            session_id="rca_123",
            terminal_id="term_abc",
        )

        assert action.action_id == "act_001"
        assert action.action_type == ActionType.READ_FILE
        assert action.phase == 1

    def test_action_to_dict(self):
        """Action can be serialized to dict."""
        action = Action(
            action_id="act_001",
            action_type=ActionType.READ_FILE,
            timestamp="2026-02-16T12:00:00",
            tool_used="Read",
            tool_input={"file_path": "test.py"},
            tool_output_hash="123:abc",
            tool_output_preview="# Test",
            phase=1,
            session_id="rca_123",
            terminal_id="term_abc",
        )

        result = action.to_dict()

        assert result["action_id"] == "act_001"
        assert result["action_type"] == "read_file"
        assert result["phase"] == 1
        assert isinstance(result, dict)

    def test_action_from_dict(self):
        """Action can be deserialized from dict."""
        data = {
            "action_id": "act_001",
            "action_type": "read_file",
            "timestamp": "2026-02-16T12:00:00",
            "tool_used": "Read",
            "tool_input": {"file_path": "test.py"},
            "tool_output_hash": "123:abc",
            "tool_output_preview": "# Test",
            "evidence_refs": [],
            "parent_id": None,
            "phase": 1,
            "session_id": "rca_123",
            "terminal_id": "term_abc",
        }

        action = Action.from_dict(data)

        assert action.action_id == "act_001"
        assert action.action_type == ActionType.READ_FILE
        assert action.parent_action_id is None


class TestActionGraph:
    """Test ActionGraph dataclass."""

    def test_empty_graph(self):
        """ActionGraph can be created empty."""
        graph = ActionGraph(session_id="rca_123")

        assert graph.session_id == "rca_123"
        assert len(graph.actions) == 0
        assert graph.divergence_point is None

    def test_graph_to_dict(self):
        """ActionGraph can be serialized."""
        graph = ActionGraph(
            session_id="rca_123",
            actions=[],
            expected_path_type="error",
        )

        result = graph.to_dict()

        assert result["session_id"] == "rca_123"
        assert result["expected_path"] == "error"
        assert isinstance(result["actions"], list)


class TestActionTracer:
    """Test ActionTracer class."""

    def test_tracer_creation(self, tmp_path):
        """ActionTracer can be created with session ID."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        assert tracer.session_id == "rca_test"
        assert tracer.terminal_id == "term_001"
        assert len(tracer._graph.actions) == 0

    def test_record_action(self, tmp_path):
        """Actions can be recorded."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        action = tracer.record_action(
            action_type=ActionType.READ_FILE,
            tool_used="Read",
            tool_input={"file_path": "test.py"},
            tool_output="# Test file",
            phase=1,
        )

        assert action.action_type == ActionType.READ_FILE
        assert action.phase == 1
        assert action.session_id == "rca_test"

        # Verify added to graph
        assert len(tracer._graph.actions) == 1

    def test_action_parent_link(self, tmp_path):
        """Actions are linked via parent_id."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        action1 = tracer.record_action(
            action_type=ActionType.READ_FILE,
            tool_used="Read",
            tool_input={"file_path": "test.py"},
            tool_output="",
            phase=1,
        )

        action2 = tracer.record_action(
            action_type=ActionType.SEARCH_CODE,
            tool_used="Grep",
            tool_input={"pattern": "foo"},
            tool_output="",
            phase=1,
        )

        # Second action should link to first
        assert action2.parent_action_id == action1.action_id

    def test_get_actions_by_phase(self, tmp_path):
        """Actions can be filtered by phase."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        tracer.record_action(ActionType.READ_FILE, "Read", {}, "", phase=0)
        tracer.record_action(ActionType.SEARCH_CODE, "Grep", {}, "", phase=1)
        tracer.record_action(ActionType.TRACE_SYMBOL, "Serena", {}, "", phase=1)

        phase_0_actions = tracer.get_actions_by_phase(0)
        phase_1_actions = tracer.get_actions_by_phase(1)

        assert len(phase_0_actions) == 1
        assert len(phase_1_actions) == 2

    def test_get_actions_by_type(self, tmp_path):
        """Actions can be filtered by type."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        tracer.record_action(ActionType.READ_FILE, "Read", {}, "", phase=0)
        tracer.record_action(ActionType.READ_FILE, "Read", {}, "", phase=1)
        tracer.record_action(ActionType.SEARCH_CODE, "Grep", {}, "", phase=1)

        read_actions = tracer.get_actions_by_type(ActionType.READ_FILE)

        assert len(read_actions) == 2

    def test_find_divergence_point(self, tmp_path):
        """Divergence point can be detected."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        # Record actions matching expected path
        tracer.record_action(ActionType.SEARCH_HISTORY, "Skill", {}, "", phase=-1)
        tracer.record_action(ActionType.READ_FILE, "Read", {}, "", phase=0)
        # Diverge here: TRACE_SYMBOL expected but got SEARCH_CODE
        tracer.record_action(ActionType.SEARCH_CODE, "Grep", {}, "", phase=1)

        expected = [
            ActionType.SEARCH_HISTORY,
            ActionType.READ_FILE,
            ActionType.TRACE_SYMBOL,  # Expected but not matched
        ]

        divergence = tracer.find_divergence_point(expected)

        assert divergence is not None
        assert divergence.action_type == ActionType.SEARCH_CODE

    def test_no_divergence(self, tmp_path):
        """Returns None when path matches expected."""
        tracer = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        tracer.record_action(ActionType.SEARCH_HISTORY, "Skill", {}, "", phase=-1)
        tracer.record_action(ActionType.READ_FILE, "Read", {}, "", phase=0)

        expected = [
            ActionType.SEARCH_HISTORY,
            ActionType.READ_FILE,
        ]

        divergence = tracer.find_divergence_point(expected)

        assert divergence is None

    def test_save_and_load(self, tmp_path):
        """Action graph can be saved and loaded."""
        # Create and record actions
        tracer1 = ActionTracer(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        tracer1.record_action(ActionType.READ_FILE, "Read", {}, "", phase=1)
        tracer1.save()

        # Load in new tracer
        tracer2 = ActionTracer.load(
            session_id="rca_test",
            terminal_id="term_001",
            state_dir=tmp_path,
        )

        assert len(tracer2._graph.actions) == 1
        assert tracer2._graph.actions[0].action_type == ActionType.READ_FILE

    def test_multi_terminal_isolation(self, tmp_path):
        """Actions are isolated by terminal ID."""
        # Terminal A
        tracer_a = ActionTracer(
            session_id="rca_shared",
            terminal_id="term_a",
            state_dir=tmp_path,
        )
        tracer_a.record_action(ActionType.READ_FILE, "Read", {}, "", phase=1)
        tracer_a.save()

        # Terminal B should get new graph (different terminal)
        tracer_b = ActionTracer(
            session_id="rca_shared",
            terminal_id="term_b",
            state_dir=tmp_path,
        )

        # Terminal B starts fresh
        assert len(tracer_b._graph.actions) == 0

        # Same terminal loads existing data
        tracer_a2 = ActionTracer.load(
            session_id="rca_shared",
            terminal_id="term_a",
            state_dir=tmp_path,
        )
        assert len(tracer_a2._graph.actions) == 1


class TestExpectedPaths:
    """Test expected investigation paths."""

    def test_get_expected_path_error(self):
        """Error problem type has expected path."""
        path = get_expected_path("error")

        assert ActionType.SEARCH_HISTORY in path
        assert ActionType.FORM_HYPOTHESIS in path

    def test_get_expected_path_test(self):
        """Test problem type has expected path."""
        path = get_expected_path("test")

        assert ActionType.EXECUTE_TEST in path

    def test_get_expected_path_unknown(self):
        """Unknown problem type defaults to error path."""
        path = get_expected_path("unknown")

        # Should return error path as default
        assert len(path) > 0


class TestHashOutput:
    """Test output hashing."""

    def test_empty_output(self):
        """Empty output gets special hash."""
        result = hash_output("")
        assert result == "empty"

    def test_short_output(self):
        """Short output is returned directly."""
        result = hash_output("short")
        assert "short" in result

    def test_long_output(self):
        """Long output is truncated in hash."""
        long_output = "a" * 1000
        result = hash_output(long_output)

        # Should contain length prefix
        assert result.startswith("1000:")
        # Should contain preview
        assert "aaa" in result


class TestCreateHelper:
    """Test convenience helper functions."""

    def test_create_tracer_for_session(self):
        """Helper creates configured tracer."""
        tracer = create_tracer_for_session(
            session_id="rca_test",
            terminal_id="term_001",
        )

        assert tracer.session_id == "rca_test"
        assert tracer.terminal_id == "term_001"
        assert isinstance(tracer, ActionTracer)
