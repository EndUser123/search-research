"""Tests for layer6_performance — verifies availability-check behavior."""

import sys
from pathlib import Path
from unittest.mock import patch

# Add the sqa directory to path so 'layers' package can be imported
SQA_DIR = Path(r"P:/.claude/skills/sqa")
sys.path.insert(0, str(SQA_DIR))

import pytest
from layers import layer6_performance


class TestAvailabilityChecks:
    """Test that Agent-based tools are correctly detected as unavailable."""

    def test_is_command_available_returns_false_for_agent_tools(self):
        """adversarial-performance is an LLM subagent — not a CLI tool."""
        # Agent tools should not be found in PATH via shutil.which
        assert layer6_performance._is_command_available("adversarial-performance") is False

    def test_is_command_available_returns_false_for_nonexistent(self):
        """Nonexistent commands return False."""
        assert layer6_performance._is_command_available("nonexistent-cmd-xyz") is False

    def test_is_command_available_true_when_found(self):
        """When shutil.which finds the command, return True."""
        with patch("shutil.which", return_value="/some/path/perf-tool"):
            assert layer6_performance._is_command_available("perf-tool") is True


class TestRunReturnsFindings:
    """Test that run() returns a list regardless of tool availability."""

    def test_run_returns_list(self, tmp_path):
        """run() must return a list, not None."""
        result = layer6_performance.run(tmp_path)
        assert isinstance(result, list)

    def test_run_with_no_python_files_returns_empty_list(self, tmp_path):
        """When target has no Python files, return empty list."""
        result = layer6_performance.run(tmp_path)
        assert result == []


class TestNestedExecutorDetection:
    """Test _has_nested_executor pattern detection."""

    def test_nested_executor_detected(self):
        """ThreadPoolExecutor inside another executor worker = nested."""
        code = '''
with ThreadPoolExecutor(max_workers=4) as executor:
    future = executor.submit(worker)
    def worker():
        with ThreadPoolExecutor() as inner:
            pass
'''
        assert layer6_performance._has_nested_executor(code) is True

    def test_single_executor_not_nested(self):
        """Single executor usage is not nested."""
        code = '''
with ThreadPoolExecutor(max_workers=4) as executor:
    future = executor.submit(worker)
def worker():
    pass
'''
        assert layer6_performance._has_nested_executor(code) is False

    def test_executor_with_independent_function_not_nested(self):
        """Executor calling an independent function (not defined inside) is not nested."""
        code = '''
with ThreadPoolExecutor(max_workers=4) as executor:
    future = executor.submit(process_item)

def process_item():
    pass
'''
        assert layer6_performance._has_nested_executor(code) is False


class TestThreadCpuMismatch:
    """Test _has_thread_cpu_mismatch detection."""

    def test_thread_without_affinity_is_mismatch(self):
        """threading.Thread without cpu_affinity = mismatch."""
        code = "import threading; t = threading.Thread(target=work)"
        assert layer6_performance._has_thread_cpu_mismatch(code) is True

    def test_thread_with_affinity_not_mismatch(self):
        """threading.Thread with cpu_affinity = no mismatch."""
        code = "import threading; t = threading.Thread(target=work); t.start(); set_affinity(0)"
        assert layer6_performance._has_thread_cpu_mismatch(code) is False

    def test_executor_without_affinity_is_mismatch(self):
        """ThreadPoolExecutor without affinity = mismatch."""
        code = "with ThreadPoolExecutor(max_workers=4) as executor: pass"
        assert layer6_performance._has_thread_cpu_mismatch(code) is True

    def test_no_threads_or_executors_not_mismatch(self):
        """Code without threads or executors has no mismatch."""
        code = "def worker(): pass"
        assert layer6_performance._has_thread_cpu_mismatch(code) is False
