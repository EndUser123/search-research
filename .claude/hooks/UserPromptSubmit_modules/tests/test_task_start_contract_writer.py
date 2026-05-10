"""Tests for task_start_contract_writer module.

Run with: pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_task_start_contract_writer.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure hooks directory is on sys.path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
LIB_DIR = HOOKS_DIR / "__lib"
for d in (str(HOOKS_DIR), str(LIB_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)


@pytest.fixture(autouse=True)
def _isolated_artifacts(tmp_path, monkeypatch):
    """Redirect task_contract._home() to tmp_path so contracts land in tmp_path/.claude/.artifacts/."""
    import __lib.task_contract as _tc
    monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
    yield


# =============================================================================
# TEST 1: Detection patterns
# =============================================================================

class TestTaskClassDetection:
    # Import the detection function directly
    def _detect(self, prompt):
        # Avoid circular import - read the module fresh
        import importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        # Patch sys.modules before exec
        with patch.dict(sys.modules, {"__lib.task_contract": importlib.import_module("__lib.task_contract")}):
            spec.loader.exec_module(mod)
        return mod._detect_task_class(prompt)

    def test_bug_diagnosis_why_question(self):
        result = self._detect("Why is the parser crashing on empty input?")
        assert result == "bug_diagnosis"

    def test_bug_diagnosis_root_cause(self):
        result = self._detect("root cause of the null pointer exception")
        assert result == "bug_diagnosis"

    def test_bug_diagnosis_debug(self):
        result = self._detect("debug why the test is failing")
        assert result == "bug_diagnosis"

    def test_bug_diagnosis_diagnose(self):
        result = self._detect("diagnose the crash at startup")
        assert result == "bug_diagnosis"

    def test_bug_diagnosis_what_cause(self):
        result = self._detect("What is causing the stack overflow?")
        assert result == "bug_diagnosis"

    def test_bug_fix_fix(self):
        result = self._detect("fix the null pointer in handler.py")
        assert result == "bug_fix"

    def test_bug_fix_patch(self):
        result = self._detect("patch the race condition in the worker")
        assert result == "bug_fix"

    def test_bug_fix_resolve(self):
        result = self._detect("resolve the memory leak")
        assert result == "bug_fix"

    def test_implementation_implement(self):
        result = self._detect("implement a rate limiter for the API")
        assert result == "implementation"

    def test_implementation_add(self):
        result = self._detect("add a retry mechanism to the client")
        assert result == "implementation"

    def test_implementation_create(self):
        result = self._detect("create a new module for cache management")
        assert result == "implementation"

    def test_implementation_build(self):
        result = self._detect("build a health check endpoint")
        assert result == "implementation"

    def test_implementation_write(self):
        result = self._detect("write a logging utility")
        assert result == "implementation"

    def test_refactor(self):
        result = self._detect("refactor the auth module to use JWT")
        assert result == "refactor"

    def test_refactor_ing(self):
        result = self._detect("refactoring the database layer")
        assert result == "refactor"

    def test_architecture_architect(self):
        result = self._detect("architect the microservices communication")
        assert result == "architecture_recommendation"

    def test_architecture_design_pattern(self):
        result = self._detect("design pattern for the plugin system")
        assert result == "architecture_recommendation"

    def test_skipped_exploration(self):
        result = self._detect("Should we refactor or consolidate?")
        assert result is None

    def test_skipped_control_stop(self):
        result = self._detect("stop")
        assert result is None

    def test_skipped_control_short(self):
        result = self._detect("actually, re-read the file")
        assert result is None

    def test_skipped_info_request(self):
        result = self._detect("What is the weather like?")
        assert result is None

    def test_skipped_info_about_codebase(self):
        result = self._detect("Tell me about the codebase")
        assert result is None

    def test_skipped_short_imperative(self):
        result = self._detect("run the tests")
        assert result is None

    def test_skipped_empty(self):
        result = self._detect("")
        assert result is None

    def test_skipped_none(self):
        result = self._detect(None)
        assert result is None


# =============================================================================
# TEST 2: Required outputs mapping
# =============================================================================

class TestRequiredOutputs:
    def _detect(self, prompt):
        import importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"__lib.task_contract": importlib.import_module("__lib.task_contract")}):
            spec.loader.exec_module(mod)
        return mod._detect_task_class(prompt)

    def _required_outputs(self, task_class):
        import importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"__lib.task_contract": importlib.import_module("__lib.task_contract")}):
            spec.loader.exec_module(mod)
        return mod._TASK_REQUIRED_OUTPUTS.get(task_class, [])

    def test_bug_diagnosis_outputs(self):
        assert self._detect("Why is X crashing?") == "bug_diagnosis"
        assert self._required_outputs("bug_diagnosis") == [
            "root_cause", "fix", "verification_commands"
        ]

    def test_bug_fix_outputs(self):
        assert self._detect("fix the bug") == "bug_fix"
        assert self._required_outputs("bug_fix") == [
            "root_cause", "fix", "tests", "verification_commands"
        ]

    def test_implementation_outputs(self):
        assert self._detect("implement a feature") == "implementation"
        assert self._required_outputs("implementation") == [
            "fix", "tests", "verification_commands"
        ]

    def test_refactor_outputs(self):
        assert self._detect("refactor the module") == "refactor"
        assert self._required_outputs("refactor") == [
            "fix", "tests", "verification_commands"
        ]

    def test_architecture_recommendation_outputs(self):
        assert self._detect("architect the system") == "architecture_recommendation"
        assert self._required_outputs("architecture_recommendation") == [
            "fix", "verification_commands"
        ]


# =============================================================================
# TEST 3: Contract lifecycle (create, update, replace)
# =============================================================================

class TestContractLifecycle:
    def test_first_prompt_creates_contract(self, tmp_path):
        from __lib.task_contract import load_contract
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        tc_mod = importlib.import_module("__lib.task_contract")

        with patch.dict(sys.modules, {"__lib.task_contract": tc_mod}):
            # Also patch _home inside the loaded module
            mod._home = lambda: tmp_path
            spec.loader.exec_module(mod)

        # No contract exists yet
        assert load_contract("test_terminal") is None

        # Simulate hook call
        mod._ensure_contract("test_terminal", "bug_fix", "fix the null pointer in handler.py")

        # Contract created
        contract = load_contract("test_terminal")
        assert contract is not None
        assert contract["task_id"].startswith("tc-")
        assert contract["status"] == "active"
        assert "null pointer" in contract["description"]
        assert contract["required_outputs"] == ["root_cause", "fix", "tests", "verification_commands"]

    def test_same_task_updates_contract(self, tmp_path):
        from __lib.task_contract import load_contract, save_contract
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        tc_mod = importlib.import_module("__lib.task_contract")

        with patch.dict(sys.modules, {"__lib.task_contract": tc_mod}):
            mod._home = lambda: tmp_path
            spec.loader.exec_module(mod)

        # Pre-create a contract
        save_contract("test_terminal", task_id="tc-abc12345", description="fix the null pointer", required_outputs=["fix"])

        # Second prompt on same task
        action = mod._ensure_contract("test_terminal", "bug_fix", "fix the null pointer in handler.py")

        assert action == "update"
        contract = load_contract("test_terminal")
        assert contract["task_id"] == "tc-abc12345"  # Preserved

    def test_different_task_replaces_contract(self, tmp_path):
        from __lib.task_contract import load_contract, save_contract
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        tc_mod = importlib.import_module("__lib.task_contract")

        with patch.dict(sys.modules, {"__lib.task_contract": tc_mod}):
            mod._home = lambda: tmp_path
            spec.loader.exec_module(mod)

        # Pre-create a contract for a different task
        save_contract("test_terminal", task_id="tc-old", description="implement a feature", required_outputs=["fix"])

        # New task
        action = mod._ensure_contract("test_terminal", "bug_fix", "fix the null pointer")

        assert action == "replace"
        contract = load_contract("test_terminal")
        assert contract["task_id"].startswith("tc-")
        assert contract["task_id"] != "tc-old"


# =============================================================================
# TEST 4: Hook returns empty (no context injection)
# =============================================================================

class TestHookResult:
    def test_hook_returns_empty(self, tmp_path):
        from UserPromptSubmit_modules.base import HookContext
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        tc_mod = importlib.import_module("__lib.task_contract")

        with patch.dict(sys.modules, {"__lib.task_contract": tc_mod}):
            mod._home = lambda: tmp_path
            spec.loader.exec_module(mod)

        # Non-task prompt → empty result
        context = HookContext(
            prompt="What is the weather like?",
            data={},
            session_id="sess-1",
            terminal_id="term-1",
        )
        result = mod.task_start_contract_writer(context)
        assert result.is_empty()

        # Task prompt → empty result (contract written to disk, no injection)
        context2 = HookContext(
            prompt="fix the null pointer",
            data={},
            session_id="sess-1",
            terminal_id="term-2",
        )
        result2 = mod.task_start_contract_writer(context2)
        assert result2.is_empty()  # Hook doesn't inject context - it just writes contract


# =============================================================================
# TEST 5: No terminal_id = skip silently
# =============================================================================

class TestTerminalIdHandling:
    def test_no_terminal_id_skips(self, tmp_path):
        from UserPromptSubmit_modules.base import HookContext
        import importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "task_start_contract_writer",
            HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
        )
        mod = importlib.util.module_from_spec(spec)
        tc_mod = importlib.import_module("__lib.task_contract")

        with patch.dict(sys.modules, {"__lib.task_contract": tc_mod}):
            mod._home = lambda: tmp_path
            spec.loader.exec_module(mod)

        # No terminal_id
        context = HookContext(
            prompt="fix the null pointer",
            data={},
            session_id="sess-1",
            terminal_id="",
        )
        result = mod.task_start_contract_writer(context)
        assert result.is_empty()
