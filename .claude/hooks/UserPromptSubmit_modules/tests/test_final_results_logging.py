"""Tests for _log_final_results() function in registry.py"""

import json
import tempfile
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import (
    _extract_model_from_transcript,
    _log_execution_trace,
    _log_final_results,
)


class TestLogFinalResultsCreatesCorrectJSONStructure:
    """Test that _log_final_results creates correct JSON structure"""

    def test_log_entry_has_required_fields(self):
        """Final results log entry must have: ts, session_id, terminal_id, num_hooks_run, num_results, results_summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            # Create test context
            context = HookContext(
                prompt="test prompt",
                data={"session_id": "test-session", "terminal_id": "test-terminal"},
                session_id="test-session",
                terminal_id="test-terminal",
            )

            # Create test results
            results = [
                HookResult(context="result1", tokens=10),
                HookResult(context="result2", tokens=20),
            ]

            sorted_hooks = [("hook1", 1.0), ("hook2", 2.0)]

            # Patch the log file path
            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                # Log final results
                _log_final_results(log_file, context, sorted_hooks, results)

                # Verify log entry was created
                assert log_file.exists()
                with open(log_file, encoding="utf-8") as f:
                    content = f.read()

                lines = content.strip().split("\n")
                assert len(lines) == 1

                entry = json.loads(lines[0])

                # Check required fields
                assert "ts" in entry
                assert "session_id" in entry
                assert "terminal_id" in entry
                assert "num_hooks_run" in entry
                assert "num_results" in entry
                assert "results_summary" in entry
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_num_hooks_run_field(self):
        """num_hooks_run should equal length of sorted_hooks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            results = [HookResult(context="x", tokens=5)]
            sorted_hooks = [("hook1", 1.0), ("hook2", 2.0), ("hook3", 3.0)]

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["num_hooks_run"] == 3
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_num_results_field(self):
        """num_results should equal length of results list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            results = [
                HookResult(context="a", tokens=5),
                HookResult(context="b", tokens=10),
                HookResult(context="c", tokens=15),
            ]
            sorted_hooks = [("hook1", 1.0), ("hook2", 2.0)]

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["num_results"] == 3
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_results_summary_structure(self):
        """results_summary should be list of dicts with is_empty, has_context, context_type"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            results = [
                HookResult(context="string result", tokens=5),
                HookResult(context={"key": "value"}, tokens=10),
                HookResult(context=None, tokens=0),
            ]
            sorted_hooks = [("hook1", 1.0)]

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                summary = entry["results_summary"]
                assert len(summary) == 3

                # Check first result (string context)
                assert summary[0]["is_empty"] is False
                assert summary[0]["has_context"] is True
                assert summary[0]["context_type"] == "str"

                # Check second result (dict context)
                assert summary[1]["is_empty"] is False
                assert summary[1]["has_context"] is True
                assert summary[1]["context_type"] == "dict"

                # Check third result (no context)
                assert summary[2]["is_empty"] is True
                assert summary[2]["has_context"] is False
                assert summary[2]["context_type"] is None
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log


class TestLogFinalResultsContextFields:
    """Test that context fields are correctly logged"""

    def test_session_id_from_context(self):
        """session_id should come from context object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="my-session-123",
                terminal_id="term1",
            )

            results = []
            sorted_hooks = []

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["session_id"] == "my-session-123"
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_terminal_id_from_context(self):
        """terminal_id should come from context object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="my-terminal-456",
            )

            results = []
            sorted_hooks = []

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["terminal_id"] == "my-terminal-456"
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log


class TestLogFinalResultsEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_results_list(self):
        """Should handle empty results list gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            results = []
            sorted_hooks = []

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["num_results"] == 0
                assert entry["num_hooks_run"] == 0
                assert entry["results_summary"] == []
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_none_session_id(self):
        """Should handle None session_id gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id=None,
                terminal_id="term1",
            )

            results = []
            sorted_hooks = []

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_final_results(log_file, context, sorted_hooks, results)

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["session_id"] is None
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log


class TestExecutionTraceTranscriptPath:
    """Test transcript_path field in execution trace"""

    def test_transcript_path_in_log_entry(self):
        """transcript_path should appear in log entry when provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            result = HookResult(context="result", tokens=10)

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_execution_trace(
                    log_file=log_file,
                    hook_name="test_hook",
                    context=context,
                    result=result,
                    transcript_path="/path/to/transcript.jsonl",
                )

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert "transcript_path" in entry
                assert entry["transcript_path"] == "/path/to/transcript.jsonl"
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_transcript_path_none_graceful(self):
        """Should handle None transcript_path gracefully (no field in log)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            result = HookResult(context="result", tokens=10)

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_execution_trace(
                    log_file=log_file,
                    hook_name="test_hook",
                    context=context,
                    result=result,
                    transcript_path=None,
                )

                with open(log_file) as f:
                    entry = json.loads(f.read())

                # transcript_path should not be in log entry when None
                assert "transcript_path" not in entry
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log


class TestExecutionTraceDurationMs:
    """Test duration_ms field in execution trace"""

    def test_duration_ms_in_log_entry(self):
        """duration_ms should appear in log entry when provided"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            result = HookResult(context="result", tokens=10)

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_execution_trace(
                    log_file=log_file,
                    hook_name="test_hook",
                    context=context,
                    result=result,
                    duration_ms=15.5,
                )

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert "duration_ms" in entry
                assert entry["duration_ms"] == 15.5
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

    def test_duration_ms_rounding(self):
        """duration_ms should be rounded to 2 decimal places"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            result = HookResult(context="result", tokens=10)

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_execution_trace(
                    log_file=log_file,
                    hook_name="test_hook",
                    context=context,
                    result=result,
                    duration_ms=15.456789,  # Should round to 15.46
                )

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert entry["duration_ms"] == 15.46
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log


class TestExecutionTraceModelName:
    """Test model_name field extraction from transcript_path"""

    def test_model_name_from_transcript(self):
        """Should extract model name from transcript path"""
        transcript_path = "session-abc123-claude-sonnet-4-6.jsonl"
        model_name = _extract_model_from_transcript(transcript_path)
        assert model_name == "claude-sonnet-4-6"

    def test_model_name_opus(self):
        """Should extract opus model name"""
        transcript_path = "session-xyz-claude-opus-4-6.jsonl"
        model_name = _extract_model_from_transcript(transcript_path)
        assert model_name == "claude-opus-4-6"

    def test_model_name_haiku(self):
        """Should extract haiku model name"""
        transcript_path = "session-def-claude-haiku-4-5.jsonl"
        model_name = _extract_model_from_transcript(transcript_path)
        assert model_name == "claude-haiku-4-5"

    def test_model_name_none_when_missing(self):
        """Should return None when model pattern not found"""
        transcript_path = "session-abc123.jsonl"
        model_name = _extract_model_from_transcript(transcript_path)
        assert model_name is None

    def test_model_name_none_when_none(self):
        """Should return None when transcript_path is None"""
        model_name = _extract_model_from_transcript(None)
        assert model_name is None

    def test_model_name_caching(self):
        """Should cache model name extractions"""
        transcript_path = "session-abc-claude-sonnet-4-6.jsonl"

        # First call - not cached
        model_name_1 = _extract_model_from_transcript(transcript_path)

        # Second call - should use cache
        model_name_2 = _extract_model_from_transcript(transcript_path)

        assert model_name_1 == model_name_2 == "claude-sonnet-4-6"

    def test_model_name_in_log_entry(self):
        """model_name should appear in log entry when transcript has model"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "ups_execution_trace.jsonl"

            context = HookContext(
                prompt="test",
                data={},
                session_id="session1",
                terminal_id="term1",
            )

            result = HookResult(context="result", tokens=10)

            import UserPromptSubmit_modules.registry as registry_module
            original_log = registry_module._EXECUTION_TRACE_LOG
            registry_module._EXECUTION_TRACE_LOG = log_file

            try:
                _log_execution_trace(
                    log_file=log_file,
                    hook_name="test_hook",
                    context=context,
                    result=result,
                    transcript_path="session-abc-claude-sonnet-4-6.jsonl",
                )

                with open(log_file) as f:
                    entry = json.loads(f.read())

                assert "model_name" in entry
                assert entry["model_name"] == "claude-sonnet-4-6"
            finally:
                registry_module._EXECUTION_TRACE_LOG = original_log

