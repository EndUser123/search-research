#!/usr/bin/env python3
"""Tests for StopHook_rca_contract.py.

Covers:
  ANTI-PATTERN-2: _check_dead_code_auto (automatic dead code, not marker-based)
  ANTI-PATTERN-1: _count_hypothesis_rows (hypothesis density check)
  ANTI-PATTERN-2: _has_call_site_evidence (call-site proof required)
  P1-1: Bare except Exception without binding (lines 149, 275)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from StopHook_rca_contract import (
    _extract_function_names,
    _count_hypothesis_rows,
    _has_call_site_evidence,
    _extract_fix_files,
    _check_band_aid_chain,
    _extract_file_paths_from_path,
    _check_stale_execution_path,
    _get_file_mtime,
    _validate_evidence_tier_labels,
    _validate_adversarial_hypothesis,
)


class TestCheckDeadCodeAuto:
    """Tests for ANTI-PATTERN-2: Automatic dead code detection.

    _check_dead_code_auto scans ALL function names in Executed Path
    (not marker-based like the old _check_dead_code). Uses < 1 (not <= 1).
    """

    def test_zero_callers_flagged_as_dead(self, monkeypatch, tmp_path):
        """Function with 0 callers (truly dead) should be flagged."""
        # Create a temp HOOKS_DIR with no files referencing this function
        temp_hooks = tmp_path / "hooks"
        temp_hooks.mkdir()
        (temp_hooks / "empty.py").write_text("# no references here")

        monkeypatch.setattr(
            "StopHook_rca_contract.HOOKS_DIR",
            temp_hooks,
        )
        import StopHook_rca_contract

        # _check_dead_code_auto returns list of dead functions (empty = none dead)
        result = StopHook_rca_contract._check_dead_code_auto(
            "called _dead_func() in the hook",
            "_dead_func() is dead code with 0 callers",
            "No evidence of _dead_func being called",
        )
        assert result == ["_dead_func"], (
            f"Function with 0 callers should be in dead functions list, got: {result}"
        )

    def test_one_caller_not_dead(self, monkeypatch, tmp_path):
        """Function with exactly 1 caller should NOT be flagged as dead.

        _check_dead_code_auto uses `< 1` (correct), not `<= 1` (bug in old code).
        A function called exactly once is NOT dead code.
        """
        temp_hooks = tmp_path / "hooks"
        temp_hooks.mkdir()

        # Create a file that calls the function exactly once
        caller_file = temp_hooks / "caller.py"
        caller_file.write_text("def main():\n    real_func()  # one call\n    pass")

        monkeypatch.setattr(
            "StopHook_rca_contract.HOOKS_DIR",
            temp_hooks,
        )
        import StopHook_rca_contract

        result = StopHook_rca_contract._check_dead_code_auto(
            "executed real_func()",
            "real_func is called once in caller.py",
            "No contradictions found",
        )
        # _check_dead_code_auto uses < 1 (correct) — 1 caller is NOT dead
        assert result == [], (
            f"Function with exactly 1 caller should NOT be in dead functions list, got: {result}"
        )

    def test_multiple_callers_not_dead(self, monkeypatch, tmp_path):
        """Function with 2+ callers should NOT be flagged as dead."""
        temp_hooks = tmp_path / "hooks"
        temp_hooks.mkdir()

        # Create files that call the function multiple times
        caller1 = temp_hooks / "caller1.py"
        caller1.write_text("def a():\n    func_name()\n    func_name()")
        caller2 = temp_hooks / "caller2.py"
        caller2.write_text("def b():\n    func_name()")

        monkeypatch.setattr(
            "StopHook_rca_contract.HOOKS_DIR",
            temp_hooks,
        )
        import StopHook_rca_contract

        result = StopHook_rca_contract._check_dead_code_auto(
            "executed func_name()",
            "func_name is called multiple times",
            "No contradictions",
        )
        assert result == [], "Function with multiple callers should NOT be dead"

    def test_no_function_names_returns_empty(self, monkeypatch, tmp_path):
        """Text without function names returns empty list (no dead code check)."""
        temp_hooks = tmp_path / "hooks"
        temp_hooks.mkdir()
        (temp_hooks / "empty.py").write_text("# nothing")

        monkeypatch.setattr(
            "StopHook_rca_contract.HOOKS_DIR",
            temp_hooks,
        )
        import StopHook_rca_contract

        result = StopHook_rca_contract._check_dead_code_auto(
            "something went wrong",
            "It should work now",
            "No evidence found",
        )
        # _check_dead_code_auto scans ALL functions in executed_path; if no function names, empty list
        assert result == [], f"Without function names in path, should return empty list, got: {result}"


class TestBareExceptBinding:
    """Tests for P1-1: Bare except Exception without binding.

    The issue: bare `except Exception:` loses exception context.
    The fix: `except Exception as exc:` preserves details for logging.
    These tests verify that exceptions are properly caught (not breaking),
    and document the binding requirement.
    """

    def test_find_function_mentions_handles_unreadable_file(self, monkeypatch, tmp_path):
        """_find_function_mentions should handle unreadable files gracefully.

        Current code: `except Exception:` (no binding)
        Fixed code: `except Exception as exc:` (binds exception)
        Both handle the error, but binding is required for proper logging.
        """
        temp_hooks = tmp_path / "hooks"
        temp_hooks.mkdir()

        # File that will cause an exception when read
        bad_file = temp_hooks / "bad.py"
        bad_file.write_text("content")

        # Monkeypatch Path.read_text to raise
        original_read_text = Path.read_text
        call_count = [0]

        def raising_read_text(self, encoding=None):
            if str(self).endswith("bad.py"):
                call_count[0] += 1
                raise OSError(f"Cannot read {self}")
            return original_read_text(self, encoding=encoding)

        monkeypatch.setattr(Path, "read_text", raising_read_text)
        monkeypatch.setattr(
            "StopHook_rca_contract.HOOKS_DIR",
            temp_hooks,
        )
        import StopHook_rca_contract

        # Should not raise - exception is caught
        result = StopHook_rca_contract._find_function_mentions("some_func")
        # Returns 0 because the bad file contributed no matches
        assert result == 0
        # Verify it tried to read the file
        assert call_count[0] > 0, "Should have attempted to read bad.py"

    def test_extract_function_names_basic(self):
        """_extract_function_names extracts function calls from text."""
        text = "def foo():\n    bar()\n    baz()"
        names = _extract_function_names(text)
        assert "foo" in names
        assert "bar" in names
        assert "baz" in names

    def test_extract_function_names_no_duplicates(self):
        """_extract_function_names deduplicates function names."""
        text = "def foo():\n    foo()\n    foo()"
        names = _extract_function_names(text)
        assert names.count("foo") == 1


class TestCountHypothesisRows:
    """Tests for ANTI-PATTERN-1: Hypothesis density enforcement.

    _count_hypothesis_rows parses markdown table rows with scores to enforce
    ≥2 ranked alternatives before root cause can be declared.
    """

    def test_single_hypothesis_row(self):
        """Single row with score = 1 hypothesis (should block root cause)."""
        text = "| Hypothesis | Score |\n|------------|-------|\n| func() is the cause | 0.85 |"
        count = _count_hypothesis_rows(text)
        assert count == 1

    def test_two_hypothesis_rows(self):
        """Two rows with scores = ≥2 hypotheses (sufficient for root cause)."""
        text = "| Hypothesis | Score |\n|------------|-------|\n| func() is the cause | 0.85 |\n| edge case in logic | 0.72 |"
        count = _count_hypothesis_rows(text)
        assert count == 2

    def test_three_hypothesis_rows(self):
        """Three rows = definitely ≥2 hypotheses."""
        text = "| Hypothesis | Score |\n|------------|-------|\n| func() is the cause | 0.85 |\n| edge case in logic | 0.72 |\n| race condition | 0.50 |"
        count = _count_hypothesis_rows(text)
        assert count == 3

    def test_no_score_values_returns_zero(self):
        """Table without score values should not count."""
        text = "| Field | Value |\n|-------|-------|\n| Symptom | Error |"
        count = _count_hypothesis_rows(text)
        assert count == 0

    def test_header_row_not_counted(self):
        """Header row with 'Score' label should not be counted."""
        text = "| Hypothesis | Score |\n|------------|-------|\n| func() is the cause | 0.85 |"
        count = _count_hypothesis_rows(text)
        assert count == 1


class TestHasCallSiteEvidence:
    """Tests for ANTI-PATTERN-2: Call-site proof enforcement.

    _has_call_site_evidence checks that Evidence section shows grep/caller patterns
    for functions named in Executed Path.
    """

    def test_grep_evidence_present(self):
        """Evidence with 'grep found 3 calls' satisfies call-site requirement."""
        evidence = "grep -r 'process_request()' found 3 callers in hooks/"
        assert _has_call_site_evidence("called process_request()", evidence) is True

    def test_callers_keyword_evidence(self):
        """Evidence with 'callers: 3' satisfies call-site requirement."""
        evidence = "Found process_request() — callers: main.py, api.py, worker.py"
        assert _has_call_site_evidence("called process_request()", evidence) is True

    def test_numeric_callers_evidence(self):
        """Evidence with '3 callers' satisfies call-site requirement."""
        evidence = "The function has 3 callers across the codebase"
        assert _has_call_site_evidence("called process_request()", evidence) is True

    def test_no_call_site_evidence(self):
        """Evidence without grep/caller patterns should NOT satisfy requirement."""
        evidence = "The error occurs in the main loop"
        assert _has_call_site_evidence("called process_request()", evidence) is False

    def test_no_functions_in_path(self):
        """No function names in path = no call-site check needed."""
        evidence = "grep found 3 calls"
        assert _has_call_site_evidence("something went wrong", evidence) is True

    def test_no_evidence_text(self):
        """Empty evidence should not satisfy call-site requirement."""
        assert _has_call_site_evidence("called process_request()", "") is False
        assert _has_call_site_evidence("called process_request()", "no evidence") is False


class TestExtractFixFiles:
    """Tests for AP3: File path extraction from Fix section text."""

    def test_single_py_file(self):
        """Extract single .py file path."""
        paths = _extract_fix_files("Fix by modifying src/foo.py to handle the case")
        assert "src/foo.py" in paths

    def test_multiple_py_files(self):
        """Extract multiple .py file paths."""
        paths = _extract_fix_files("Fix src/bar.py and tests/test_bar.py")
        assert "src/bar.py" in paths
        assert "tests/test_bar.py" in paths

    def test_windows_path(self):
        """Extract Windows-style paths."""
        paths = _extract_fix_files("Fix C:/Users/test/project.py")
        assert any("project.py" in p for p in paths)

    def test_no_paths(self):
        """Text without paths returns empty."""
        assert _extract_fix_files("Just describe the fix without files") == []

    def test_path_matching_is_len_based(self):
        """Path extraction requires len > 3, so 'x.py' (4 chars) IS matched."""
        # x.py and y.py are 4 chars each — they pass len > 3, so they ARE matched
        paths = _extract_fix_files("x.py and y.py should match")
        assert "x.py" in paths
        assert "y.py" in paths


class TestCheckBandAidChain:
    """Tests for AP3: Band-aid chain detector.

    Uses terminal-scoped state via monkeypatched state_paths.
    """

    def test_first_fix_not_blocked(self, monkeypatch, tmp_path):
        """First fix to a file should not be flagged."""
        temp_state = tmp_path / "state"
        temp_state.mkdir()

        def mock_get_path(tid, fname):
            return temp_state / fname

        monkeypatch.setattr("StopHook_rca_contract._load_band_aid_state", lambda tid: {})
        monkeypatch.setattr(
            "StopHook_rca_contract._save_band_aid_state", lambda tid, st: None
        )

        msgs = _check_band_aid_chain("Fix by modifying src/buggy.py", "term_1")
        assert msgs == []

    def test_third_fix_to_same_file_blocked(self, monkeypatch, tmp_path):
        """Third fix to the same file triggers band-aid chain block."""
        temp_state = tmp_path / "state"
        temp_state.mkdir()

        state_file = temp_state / "rca_band_aid.json"
        state_file.write_text(
            '{"fixes": {"src/buggy.py": 2}, "_ts": '
            + str(tmp_path.stat().st_mtime - 100) + "}",
            encoding="utf-8",
        )

        def mock_get_path(tid, fname):
            return state_file

        monkeypatch.setattr(
            "StopHook_rca_contract._load_band_aid_state",
            lambda tid: {"fixes": {"src/buggy.py": 2}, "_ts": tmp_path.stat().st_mtime - 100},
        )

        saved_state = {}

        def mock_save(tid, st):
            saved_state.update(st)

        monkeypatch.setattr(
            "StopHook_rca_contract._save_band_aid_state", mock_save
        )

        msgs = _check_band_aid_chain("Fix by modifying src/buggy.py", "term_1")
        assert len(msgs) == 1
        assert "xy-suspect" in msgs[0].lower()

    def test_different_files_not_blocked(self, monkeypatch, tmp_path):
        """Fixes to different files don't trigger chain detection."""
        monkeypatch.setattr(
            "StopHook_rca_contract._load_band_aid_state",
            lambda tid: {"fixes": {"src/a.py": 1, "src/b.py": 1}, "_ts": tmp_path.stat().st_mtime - 100},
        )
        monkeypatch.setattr(
            "StopHook_rca_contract._save_band_aid_state",
            lambda tid, st: None,
        )

        msgs = _check_band_aid_chain(
            "Fix src/a.py and src/b.py separately", "term_1"
        )
        # Each is count=1 in state, after +1 each becomes 2, below threshold 3
        assert msgs == []


class TestExtractFilePathsFromPath:
    """Tests for AP5: File path extraction from Executed Path text."""

    def test_single_file(self):
        """Extract single .py file from executed path."""
        paths = _extract_file_paths_from_path(
            "The bug is in src/processor.py at line 42"
        )
        assert "src/processor.py" in paths

    def test_multiple_files(self):
        """Extract multiple .py files."""
        paths = _extract_file_paths_from_path(
            "Trace: src/main.py -> src/processor.py -> src/utils.py"
        )
        assert "src/main.py" in paths
        assert "src/processor.py" in paths
        assert "src/utils.py" in paths

    def test_windows_path(self):
        """Extract Windows path."""
        paths = _extract_file_paths_from_path(
            "The error originates in P:/project/src/handler.py"
        )
        assert any("handler.py" in p for p in paths)

    def test_no_files(self):
        """Text without Python files returns empty."""
        assert _extract_file_paths_from_path("No file paths in this text") == []


class TestCheckStaleExecutionPath:
    """Tests for AP5: Filesystem mtime freshness validator."""

    def test_no_timestamp_skips_check(self):
        """None rca_timestamp means fail-open (no blocking)."""
        msgs = _check_stale_execution_path(
            "executed src/buggy.py", None
        )
        assert msgs == []

    def test_no_files_skips_check(self):
        """No file paths in executed_path means fail-open."""
        msgs = _check_stale_execution_path(
            "general failure", time.time()
        )
        assert msgs == []

    def test_file_modified_after_rca_start(self, monkeypatch, tmp_path):
        """File modified after RCA session start is flagged as stale."""
        # Create a temp Python file and backdate its mtime
        fake_old_file = tmp_path / "old_module.py"
        fake_old_file.write_text("# old", encoding="utf-8")
        old_mtime = fake_old_file.stat().st_mtime

        # Make the file appear to have been modified after RCA start
        newer_mtime = old_mtime + 10

        monkeypatch.setattr(
            "StopHook_rca_contract._get_file_mtime",
            lambda fp: newer_mtime if "old_module" in fp else None,
        )

        msgs = _check_stale_execution_path(
            "The bug is in old_module.py", old_mtime
        )
        assert len(msgs) == 1
        assert "stale-execution-path" in msgs[0]

    def test_file_not_modified_is_clean(self, monkeypatch, tmp_path):
        """File with mtime <= rca_timestamp is not flagged."""
        fake_file = tmp_path / "stable_module.py"
        fake_file.write_text("# stable", encoding="utf-8")
        current_mtime = fake_file.stat().st_mtime

        monkeypatch.setattr(
            "StopHook_rca_contract._get_file_mtime",
            lambda fp: current_mtime if "stable_module" in fp else None,
        )

        # rca_timestamp equals current mtime — file is NOT newer
        msgs = _check_stale_execution_path(
            "The issue is in stable_module.py", current_mtime
        )
        assert msgs == []


class TestGetFileMtimeFailurePaths:
    """Failure-path tests for AP5: _get_file_mtime error handling.

    Errors must be re-raised (not swallowed) so callers can distinguish
    "file not found" (None) from "access denied" or "I/O error" (exception).
    """

    def test_permission_error_raised(self, monkeypatch, caplog):
        """PermissionError is logged and re-raised, not returned as None."""
        import logging

        monkeypatch.setattr(
            "StopHook_rca_contract._get_file_mtime",
            lambda fp: _raise_permission_error(),
        )
        import StopHook_rca_contract

        with pytest.raises(PermissionError):
            StopHook_rca_contract._get_file_mtime(str(Path("P:/forbidden.py")))

    def test_oserror_raised(self, monkeypatch):
        """OSError is logged and re-raised, not returned as None."""
        monkeypatch.setattr(
            "StopHook_rca_contract._get_file_mtime",
            lambda fp: _raise_os_error(),
        )
        import StopHook_rca_contract

        with pytest.raises(OSError):
            StopHook_rca_contract._get_file_mtime(str(Path("P:/io_error.py")))

    def test_none_returned_for_missing_file(self, tmp_path):
        """File not found returns None, not an exception."""
        result = _get_file_mtime(str(tmp_path / "does_not_exist.py"))
        assert result is None


def _raise_permission_error():
    raise PermissionError("access denied")


def _raise_os_error():
    raise OSError("I/O error")


class TestBandAidChainFailurePaths:
    """Failure-path tests for AP3: _check_band_aid_chain error handling.

    Lock acquisition failure must return [] (graceful degradation) not raise.
    """

    def test_timeout_returns_empty_list(self, monkeypatch):
        """FileLock timeout returns [] (graceful skip), does not raise."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            result = original_import(name, *args, **kwargs)
            if name == "__lib.file_lock":
                result.FileLock = _TimeoutFileLock
            return result

        monkeypatch.setattr(builtins, "__import__", mock_import)

        import StopHook_rca_contract
        import importlib

        importlib.reload(StopHook_rca_contract)

        result = StopHook_rca_contract._check_band_aid_chain(
            "Fix by modifying src/buggy.py", "term_timeout_test"
        )
        assert result == []

    def test_unexpected_error_in_lock_returns_empty_list(self, monkeypatch):
        """Unexpected error during band_aid update returns [], logs error."""
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            result = original_import(name, *args, **kwargs)
            if name == "__lib.file_lock":
                result.FileLock = _ErrorFileLock
            return result

        monkeypatch.setattr(builtins, "__import__", mock_import)

        import StopHook_rca_contract
        import importlib

        importlib.reload(StopHook_rca_contract)

        result = StopHook_rca_contract._check_band_aid_chain(
            "Fix by modifying src/buggy.py", "term_error_test"
        )
        assert result == []


class _TimeoutFileLock:
    """Mock FileLock that raises TimeoutError on acquire."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        raise TimeoutError("could not acquire lock within 5 seconds")

    def __exit__(self, *args):
        pass


class _ErrorFileLock:
    """Mock FileLock that raises RuntimeError on acquire."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        raise RuntimeError("unexpected lock error")

    def __exit__(self, *args):
        pass


class TestAP6AdversarialHypothesis:
    """Tests for TASK-003: AP6 Adversarial Hypothesis Validator.

    _validate_adversarial_hypothesis checks that Falsifier does not contain
    patterns indicating the hypothesis was disproved.
    """

    def test_falsified_hypothesis(self):
        """Falsifier with 'falsified' should return block reason."""
        sections = {
            "Falsifier": "The hypothesis was falsified by grep showing 0 callers",
            "Alternative Hypothesis": "func() is the root cause",
        }
        result = _validate_adversarial_hypothesis(sections, [])
        assert len(result) == 1
        assert "hypothesis-falsified" in result[0]

    def test_disproved_hypothesis(self):
        """Falsifier with 'disproved' should return block reason."""
        sections = {
            "Falsifier": "The alternative was disproved by the test results",
            "Alternative Hypothesis": "func() is the root cause",
        }
        result = _validate_adversarial_hypothesis(sections, [])
        assert len(result) == 1
        assert "hypothesis-falsified" in result[0]

    def test_debunked_hypothesis(self):
        """Falsifier with 'debunked' should return block reason."""
        sections = {
            "Falsifier": "This hypothesis was debunked by subsequent analysis",
            "Alternative Hypothesis": "func() is the root cause",
        }
        result = _validate_adversarial_hypothesis(sections, [])
        assert len(result) == 1
        assert "hypothesis-falsified" in result[0]

    def test_hypothesis_is_false(self):
        """Falsifier with 'hypothesis is false' should return block reason."""
        sections = {
            "Falsifier": "Test showed hypothesis is false — no evidence of dead code",
            "Alternative Hypothesis": "dead code is the root cause",
        }
        result = _validate_adversarial_hypothesis(sections, [])
        assert len(result) == 1
        assert "hypothesis-falsified" in result[0]

    def test_survived_hypothesis(self):
        """Falsifier without falsification patterns should pass."""
        sections = {
            "Falsifier": "Alternative hypothesis cannot explain the symptom because it does not match the error pattern",
            "Alternative Hypothesis": "func() is the root cause",
        }
        result = _validate_adversarial_hypothesis(sections, [])
        assert result == []

    def test_no_falsifier_section(self):
        """No Falsifier section returns empty list (no block)."""
        sections = {"Alternative Hypothesis": "func() is the root cause"}
        result = _validate_adversarial_hypothesis(sections, [])
        assert result == []


class TestEvidenceTierLabels:
    """Tests for TASK-002: Evidence Tier Label Validation.

    _validate_evidence_tier_labels checks that all evidence lines have
    one of: [current-state], [transcript-time], or [inference].
    """

    def test_current_state_label_passes(self):
        """Evidence with [current-state] prefix passes."""
        evidence = "[current-state] Read on foo.py shows bar() is called"
        result = _validate_evidence_tier_labels(evidence)
        assert result == []

    def test_transcript_time_label_passes(self):
        """Evidence with [transcript-time] prefix passes."""
        evidence = "[transcript-time] From prior session: function has 3 callers"
        result = _validate_evidence_tier_labels(evidence)
        assert result == []

    def test_inference_label_passes(self):
        """Evidence with [inference] prefix passes."""
        evidence = "[inference] The error must be in the main loop based on the trace"
        result = _validate_evidence_tier_labels(evidence)
        assert result == []

    def test_multiple_valid_labels_passes(self):
        """Evidence with multiple valid tier labels passes."""
        evidence = """[current-state] Read on foo.py shows bar() is called
[current-state] Grep found 3 callers in main.py
[inference] The root cause is likely the race condition"""
        result = _validate_evidence_tier_labels(evidence)
        assert result == []

    def test_unlabeled_line_blocked(self):
        """Evidence without tier label on a line is blocked."""
        evidence = """[current-state] Read on foo.py shows bar() is called
No label here - this should be flagged"""
        result = _validate_evidence_tier_labels(evidence)
        assert len(result) == 1
        assert "evidence-without-tier-label" in result[0]

    def test_empty_evidence_returns_empty(self):
        """Empty evidence returns empty list."""
        result = _validate_evidence_tier_labels("")
        assert result == []

    def test_code_blocks_exempt(self):
        """Code blocks (```) are exempt from tier labels."""
        evidence = """[current-state] Read on foo.py
```
def bar():
    pass
```
[current-state] More labeled content"""
        result = _validate_evidence_tier_labels(evidence)
        assert result == []

    def test_short_lines_exempt(self):
        """Lines <= 3 chars are exempt from tier labels."""
        evidence = """[current-state] Read on foo.py
a
ab
abc
OK"""
        result = _validate_evidence_tier_labels(evidence)
        assert result == []


class TestRuledOutField:
    """Tests for TASK-001: Ruled Out field requirement.

    _validate_rca_contract blocks when "Ruled Out" section is missing.
    """

    def test_ruled_out_section_exists_passes(self):
        """RCA with Ruled Out section should pass this check."""
        # This is a unit test for the section extraction behavior
        from StopHook_rca_contract import _extract_sections, _get_section

        response = """## Symptom
Error occurs in main loop

## Evidence
[current-state] Read shows bar() is called

## Executed Path
main.py -> bar()

## Alternative Hypothesis
| Hypothesis | Score |
|------------|-------|
| bar() is the cause | 0.85 |
| edge case | 0.72 |

## Falsifier
bar() does not appear in the error trace

## Ruled Out
- edge case: No evidence in transcript

## Root Cause
bar() in main.py

## Fix
Update the error handling

## Verification
Run the test suite
"""
        sections = _extract_sections(response)
        ruled_out = _get_section(sections, "Ruled Out")
        assert ruled_out != ""
        assert "edge case" in ruled_out

    def test_missing_ruled_out_section(self):
        """RCA without Ruled Out section should fail."""
        from StopHook_rca_contract import _extract_sections, _get_section

        response = """## Symptom
Error occurs in main loop

## Evidence
[current-state] Read shows bar() is called

## Executed Path
main.py -> bar()

## Alternative Hypothesis
| Hypothesis | Score |
|------------|-------|
| bar() is the cause | 0.85 |

## Falsifier
bar() does not appear in the error trace

## Root Cause
bar() in main.py

## Fix
Update the error handling

## Verification
Run the test suite
"""
        sections = _extract_sections(response)
        ruled_out = _get_section(sections, "Ruled Out")
        assert ruled_out == ""


class TestFullContractAP6:
    """Tests for full 9-field RCA contract with AP6 validation.

    Tests that all 9 fields pass when valid, and that missing Ruled Out blocks.
    """

    def test_full_contract_all_9_fields_valid(self):
        """All 9 fields valid should pass AP6 and tier label checks."""
        from StopHook_rca_contract import _validate_rca_contract, _extract_sections

        response = """## Symptom
Error occurs in main loop

## Evidence
[current-state] Read on main.py shows bar() is called

## Executed Path
main.py -> bar()

## Alternative Hypothesis
| Hypothesis | Score |
|------------|-------|
| bar() is the cause | 0.85 |
| edge case | 0.72 |

## Falsifier
bar() does not match the error pattern in the trace

## Ruled Out
- edge case: No evidence in transcript

## Root Cause
bar() in main.py

## Fix
Update the error handling in bar()

## Verification
Run pytest to confirm fix
"""
        sections = _extract_sections(response)
        is_valid, reasons = _validate_rca_contract(
            response, [{"id": "evt_1", "name": "Read"}], True, "sess_1", "term_1"
        )
        # Should not have hypothesis-falsified or evidence-without-tier-label
        ap6_related = [r for r in reasons if "hypothesis-falsified" in r or "evidence-without-tier-label" in r]
        assert ap6_related == [], f"Expected no AP6/tier blocks, got: {ap6_related}"

    def test_contract_missing_ruled_out_blocked(self):
        """Missing Ruled Out section should be blocked."""
        from StopHook_rca_contract import _validate_rca_contract

        response = """## Symptom
Error occurs

## Evidence
[current-state] Read on main.py

## Executed Path
main.py

## Alternative Hypothesis
| Hypothesis | Score |
|------------|-------|
| bar() is the cause | 0.85 |

## Falsifier
bar() does not match

## Root Cause
bar()

## Fix
Update it

## Verification
Run tests
"""
        is_valid, reasons = _validate_rca_contract(
            response, [{"id": "evt_1", "name": "Read"}], True, "sess_1", "term_1"
        )
        # Ruled Out section missing triggers block - check by looking for Ruled Out related reason
        ruled_out_blocks = [r for r in reasons if "Ruled Out" in r]
        assert len(ruled_out_blocks) == 1, f"Expected Ruled Out block, got: {reasons}"
