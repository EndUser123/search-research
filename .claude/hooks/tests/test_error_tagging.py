"""Tests for structured error tagging (A2/A3) and layered classification (A4).

Verifies:
- A3: `_error_class_and_code()` in hook_runner.py produces correct
  error_class, failure_code, is_startup_actionable, root_cause_key
- A3: `_error_class_and_code()` in cc_diagnostic_logger.py same contract
- A4: `_classify_error_events()` uses Layer 1 structured fields first,
  falls back to Layer 2 string patterns for legacy records
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

# --- Test A3: hook_runner._error_class_and_code ---

class TestHookRunnerErrorClassAndCode:
    """Regression tests for _error_class_and_code in hook_runner.py."""

    def test_timeout_imminent_returns_timeout_class(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "PreToolUse_test", "timeout_imminent", "Hook timed out", "..."
        )
        assert cls == "timeout"
        assert actionable is False
        assert code == "PreToolUse_test_timeout_imminent"
        assert root == code

    def test_syntax_error_returns_load_failure_not_actionable(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "PostToolUse_syntax", "syntax_error", "Invalid syntax", "..."
        )
        assert cls == "load_failure"
        assert actionable is False
        assert code == "PostToolUse_syntax_syntax_error"

    def test_import_error_returns_load_failure_actionable(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "StopHook_test", "import_error", "No module named 'foo'", "..."
        )
        assert cls == "load_failure"
        assert actionable is True
        assert code == "StopHook_test_import_error"

    def test_runtime_error_name_anomalies_is_known_fixed(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "PostToolUse", "runtime_error",
            "NameError in hook",
            "NameError: name 'anomalies' is not defined"
        )
        assert cls == "known_fixed"
        assert actionable is False

    def test_runtime_error_name_user_prompt_is_known_fixed(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "StopHook", "runtime_error",
            "NameError in main()",
            "NameError: name 'user_prompt' is not defined"
        )
        assert cls == "known_fixed"
        assert actionable is False

    def test_runtime_error_generic_is_actionable(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "PreToolUse_custom", "runtime_error",
            "KeyError: missing key", "..."
        )
        assert cls == "runtime_error"
        assert actionable is True
        assert code == "PreToolUse_custom_runtime_error"

    def test_unknown_error_type_defaults_to_runtime_actionable(self):
        from __lib.hook_runner import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "TestHook", "some_custom_type", "Some error", "..."
        )
        assert cls == "runtime_error"
        assert actionable is True
        assert code == "TestHook_some_custom_type"


# --- Test A3: cc_diagnostic_logger._error_class_and_code ---

class TestDiagnosticLoggerErrorClassAndCode:
    """Regression tests for _error_class_and_code in cc_diagnostic_logger.py."""

    def test_timeout_killed_classification(self):
        from cc_diagnostic_logger import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "MyHook", "timeout_killed", "Hook was killed", "..."
        )
        assert cls == "timeout"
        assert actionable is False
        assert code == "MyHook_timeout_killed"

    def test_module_not_found_is_actionable(self):
        from cc_diagnostic_logger import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "SomeHook", "module_not_found", "No module named 'bar'", "..."
        )
        assert cls == "load_failure"
        assert actionable is True

    def test_known_fixed_runtime_error(self):
        from cc_diagnostic_logger import _error_class_and_code

        cls, code, actionable, root = _error_class_and_code(
            "Hook", "runtime_error",
            "NameError occurred",
            "NameError: name 'anomalies' is not defined"
        )
        assert cls == "known_fixed"
        assert actionable is False


# --- Test A4: layered classification in Stop.py ---

class TestClassifyErrorEventsLayered:
    """Regression tests for _classify_error_events layered strategy."""

    @pytest.fixture
    def log_file(self, tmp_path: Path) -> Path:
        return tmp_path / "cc_errors.jsonl"

    def _write_entry(self, path: Path, fields: dict) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "error",
            "error_type": "test_hook_unknown",
            "error_message": "test message",
            **fields,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def test_layer1_structured_timeout_classification(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 1: structured error_class="timeout"
        self._write_entry(log_file, {
            "error_class": "timeout",
            "failure_code": "TestHook_timeout_exceeded",
            "is_startup_actionable": False,
            "root_cause_key": "TestHook_timeout_exceeded",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert expected == 1
        assert real == 0
        assert known == 0

    def test_layer1_structured_known_fixed_classification(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 1: structured error_class="known_fixed"
        self._write_entry(log_file, {
            "error_class": "known_fixed",
            "failure_code": "PostToolUse_syntax_error",
            "is_startup_actionable": False,
            "root_cause_key": "PostToolUse_syntax_error",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert known == 1
        assert real == 0
        assert expected == 0

    def test_layer1_structured_is_actionable_true(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 1: explicit is_startup_actionable=True
        self._write_entry(log_file, {
            "error_class": "runtime_error",
            "failure_code": "TestHook_runtime_error",
            "is_startup_actionable": True,
            "root_cause_key": "TestHook_runtime_error",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert real == 1
        assert known == 0
        assert expected == 0

    def test_layer1_structured_is_actionable_false(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 1: explicit is_startup_actionable=False (no error_class)
        self._write_entry(log_file, {
            "is_startup_actionable": False,
            "error_message": "some known issue",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert known == 1
        assert real == 0

    def test_layer2_fallback_timeout_patterns(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 2 (legacy): no structured fields, error_type contains timeout_imminent
        self._write_entry(log_file, {
            "error_type": "PreToolUse_timeout_imminent",
            "error_message": "hook timed out",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert expected == 1
        assert real == 0

    def test_layer2_fallback_known_fixed_patterns(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 2 (legacy): no structured fields, msg contains known_fixed pattern
        self._write_entry(log_file, {
            "error_type": "StopHook_runtime_error",
            "error_message": "NameError: name 'user_prompt' is not defined",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert known == 1
        assert real == 0

    def test_layer2_fallback_real_failure_no_pattern(self, log_file: Path):
        from Stop import _classify_error_events

        # Layer 2 (legacy): no structured fields, no known patterns -> real failure
        self._write_entry(log_file, {
            "error_type": "CustomHook_runtime_error",
            "error_message": "KeyError: missing key in config",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 1
        assert real == 1

    def test_mixed_layer1_and_layer2_in_same_file(self, log_file: Path):
        from Stop import _classify_error_events

        # One structured (Layer 1), one legacy (Layer 2)
        self._write_entry(log_file, {
            "error_class": "timeout",
            "is_startup_actionable": False,
            "root_cause_key": "HookA_timeout",
        })
        self._write_entry(log_file, {
            "error_type": "HookB_timeout_imminent",
            "error_message": "timed out",
        })

        total, real, expected, known = _classify_error_events(log_file)
        assert total == 2
        assert expected == 2
        assert real == 0

    def test_empty_file_returns_zeros(self, log_file: Path):
        from Stop import _classify_error_events

        # empty file
        log_file.touch()
        total, real, expected, known = _classify_error_events(log_file)
        assert (total, real, expected, known) == (0, 0, 0, 0)

    def test_nonexistent_file_returns_zeros(self, log_file: Path):
        from Stop import _classify_error_events

        log_file.unlink(missing_ok=True)
        total, real, expected, known = _classify_error_events(log_file)
        assert (total, real, expected, known) == (0, 0, 0, 0)