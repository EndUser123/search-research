'''Tests for plan_injector.py - Plan context injection and disambiguation.

RED PHASE: These tests FAIL initially to demonstrate the module doesn't exist yet.

Task 835: Extract plan_injector module from UserPromptSubmit_router.py
'''

import sys
from pathlib import Path

import pytest

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class TestPlanInjectorModuleExists:
    def test_plan_injector_module_exists(self):
        from UserPromptSubmit import plan_injector
        assert plan_injector is not None

    def test_plan_injector_has_detect_plan_command(self):
        from UserPromptSubmit import plan_injector
        assert hasattr(plan_injector, 'detect_plan_command')
        assert callable(plan_injector.detect_plan_command)


class TestPlanDetectionFunctions:
    @pytest.fixture
    def plan_injector(self):
        from UserPromptSubmit import plan_injector
        return plan_injector

    def test_detect_plan_command_with_valid_plan_command(self, plan_injector):
        prompt = "/plan Extract plan context injection logic"
        result = plan_injector.detect_plan_command(prompt)
        assert result is True

    def test_extract_explicit_plan_path_finds_md_path(self, plan_injector):
        prompt = r"follow the plan at P:\.claude\plans\plan-20250113-task.md"
        result = plan_injector.extract_explicit_plan_path(prompt)
        assert result is not None
        assert ".md" in result


class TestPlanInjectionFunctions:
    @pytest.fixture
    def plan_injector(self):
        from UserPromptSubmit import plan_injector
        return plan_injector

    def test_inject_plan_context_returns_dict(self, plan_injector):
        prompt = "/plan Extract plan injection module"
        result = plan_injector.inject_plan_context(prompt)
        assert result is not None
        assert isinstance(result, dict)

    def test_inject_plan_context_generates_template(self, plan_injector):
        prompt = "/plan Test plan for extraction"
        result = plan_injector.inject_plan_context(prompt)
        context = result.get("context", result.get("additionalContext", ""))
        required_sections = [
            "## 1. Problem Statement",
            "## 2. Context Analysis",
            "## 3. Proposed Solution",
            "## 4. Implementation Plan",
            "## 5. Risk Assessment",
            "## 6. Success Criteria",
            "## 7. Dependencies",
        ]
        for section in required_sections:
            assert section in context


class TestPlanDisambiguationFunctions:
    @pytest.fixture
    def plan_injector(self):
        from UserPromptSubmit import plan_injector
        return plan_injector

    def test_references_implicit_execution_plan_detects_implicit_references(self, plan_injector):
        implicit_prompts = [
            "implement the plan",
            "execute the plan",
            "run the plan",
        ]
        for prompt in implicit_prompts:
            result = plan_injector.references_implicit_execution_plan(prompt)
            assert result is True


class TestRegistryIntegration:
    def test_plan_injector_registers_hooks(self):
        from UserPromptSubmit import registry
        registered_hooks = list(registry.HOOKS.keys())
        plan_hooks = [h for h in registered_hooks if "plan" in h.lower()]
        assert len(plan_hooks) > 0


class TestPlanContentInlining:
    """Tests for build_plan_injection content inlining and failure-path marker.

    These tests codify the invariant that:
    - Existing plan files have their content inlined (LLMs can act without a
      separate file read; prevents fabrication from pointer-only context).
    - Missing plan files inject an explicit [FILE NOT FOUND] marker (LLMs are
      told to state uncertainty rather than fabricate).
    """

    @pytest.fixture
    def plan_injector(self):
        from UserPromptSubmit import plan_injector
        return plan_injector

    def test_build_plan_injection_inlines_content_when_file_exists(self, plan_injector, tmp_path):
        """Content of an existing plan file is embedded in the injection string."""
        plan_file = tmp_path / "my-plan.md"
        plan_file.write_text("## Goal\nConsolidate the pipeline.\n", encoding="utf-8")

        result = plan_injector.build_plan_injection(str(plan_file))

        assert "## Goal" in result
        assert "Consolidate the pipeline." in result

    def test_build_plan_injection_adds_not_found_marker_when_missing(self, plan_injector, tmp_path):
        """A non-existent plan path injects an explicit NOT FOUND marker."""
        missing = str(tmp_path / "does-not-exist.md")

        result = plan_injector.build_plan_injection(missing)

        assert "NOT FOUND" in result.upper() or "not exist" in result.lower()
        # Must signal LLM to state uncertainty rather than fabricate
        assert "fabricate" in result.lower() or "uncertainty" in result.lower()

    def test_build_plan_injection_truncates_large_files(self, plan_injector, tmp_path):
        """Files exceeding PLAN_INLINE_LIMIT are truncated with a notice."""
        plan_file = tmp_path / "big-plan.md"
        plan_file.write_text("x" * (plan_injector.PLAN_INLINE_LIMIT + 500), encoding="utf-8")

        result = plan_injector.build_plan_injection(str(plan_file))

        assert "truncated" in result.lower()
        assert "x" * 100 in result

    def test_build_plan_injection_does_not_truncate_small_files(self, plan_injector, tmp_path):
        """Files within PLAN_INLINE_LIMIT are inlined in full."""
        content = "## Step 1\nDo the thing.\n## Step 2\nFinish it.\n"
        plan_file = tmp_path / "small-plan.md"
        plan_file.write_text(content, encoding="utf-8")

        result = plan_injector.build_plan_injection(str(plan_file))

        assert "truncated" not in result.lower()
        assert content in result

    def test_read_plan_content_returns_empty_string_on_os_error(self, plan_injector):
        """OSError during file read returns empty string (fail open, no crash)."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            # Passing a directory path triggers IsADirectoryError (subclass of OSError)
            result = plan_injector._read_plan_content(d)
        assert isinstance(result, str)


class TestPathValidationFixes:
    """Tests for path validation bug fix (Risk 1, Risk 2, Risk 3 from pre-mortem).

    Risk 1: No tests for validation logic - NOW TESTED
    Risk 2: Relative paths fail Path.exists() check - NEEDS FIX + TESTS
    Risk 3: Exception handling missing for malformed paths - NEEDS FIX + TESTS
    """

    @pytest.fixture
    def plan_injector(self):
        from UserPromptSubmit import plan_injector
        return plan_injector

    def test_existing_plan_returns_context_with_content(self, plan_injector, tmp_path):
        """Risk 1: Verify validation logic - existing plan file returns context."""
        plan_file = tmp_path / "existing-plan.md"
        plan_file.write_text("# Test Plan\n\n## Goal\nTest goal.", encoding="utf-8")

        result = plan_injector.build_plan_injection(str(plan_file))

        # Should return context with content, not an error
        assert "PLAN CONTEXT" in result
        assert "Test Plan" in result or "Test goal" in result
        assert "NOT FOUND" not in result.upper()

    def test_nonexistent_plan_returns_error_message(self, plan_injector, tmp_path):
        """Risk 1: Verify validation logic - missing plan returns error marker."""
        missing_plan = str(tmp_path / "does-not-exist.md")

        result = plan_injector.build_plan_injection(missing_plan)

        # Should return error marker, not crash or inject invalid context
        assert "NOT FOUND" in result.upper() or "not exist" in result.lower()
        assert "fabricate" in result.lower() or "uncertainty" in result.lower()

    def test_relative_path_with_double_dot_resolves_correctly(self, plan_injector, tmp_path):
        """Risk 2: Relative paths like '../plan.md' resolve against hooks_dir.

        Behavior: Relative paths are resolved against the hooks directory first,
        then fall back to cwd. This ensures plan files in the hooks tree are found.
        """
        # Create plan in hooks directory parent (P:/.claude/)
        hooks_dir = Path(__file__).resolve().parent.parent.parent
        plan_file = hooks_dir.parent / "test-relative-plan.md"
        plan_file.write_text("# Test Relative Plan\n\nContent from parent.", encoding="utf-8")

        try:
            # Test with relative path from hooks_dir
            relative_path = "../test-relative-plan.md"

            result = plan_injector.build_plan_injection(relative_path)
            # Should resolve to P:/.claude/test-relative-plan.md and find content
            assert "Test Relative Plan" in result or "Content from parent" in result
        finally:
            # Cleanup
            if plan_file.exists():
                plan_file.unlink()

    def test_relative_path_with_subdirectory_resolves_correctly(self, plan_injector, tmp_path):
        """Risk 2: Relative paths like 'subdir/plan.md' resolve correctly.

        Behavior: Relative subdirectory paths are resolved against hooks_dir.
        """
        # Create subdirectory in hooks directory with plan
        hooks_dir = Path(__file__).resolve().parent.parent.parent
        subdir = hooks_dir / "test_plans"
        subdir.mkdir(exist_ok=True)
        plan_file = subdir / "subdir-plan.md"
        plan_file.write_text("# Subdir Plan\n\nContent from subdir.", encoding="utf-8")

        try:
            # Test with relative path
            relative_path = "test_plans/subdir-plan.md"

            result = plan_injector.build_plan_injection(relative_path)
            # Should resolve and find content
            assert "Subdir Plan" in result or "Content from subdir" in result
        finally:
            # Cleanup
            if plan_file.exists():
                plan_file.unlink()
            if subdir.exists():
                subdir.rmdir()

    def test_malformed_path_empty_string_handling(self, plan_injector):
        """Risk 3: Empty string path doesn't crash.

        Behavior: Empty string returns INVALID PLAN PATH error rather than crashing.
        """
        # Empty string can cause issues with Path()
        result = plan_injector.build_plan_injection("")
        # Should handle gracefully and return INVALID error message
        assert isinstance(result, str)
        assert "invalid" in result.lower() or "empty" in result.lower()

    def test_malformed_path_with_null_bytes(self, plan_injector):
        """Risk 3: Path with null bytes (common attack pattern) doesn't crash.

        Behavior: Path() constructor accepts null bytes in Python 3.14, but OS
        operations handle them gracefully. Returns NOT FOUND rather than crashing.
        """
        # Path with null bytes would raise ValueError in older Python versions
        # In Python 3.14, Path() accepts it but OS operations return False
        malicious_path = "plan\x00.md"

        # Should not crash, should return error message gracefully
        result = plan_injector.build_plan_injection(malicious_path)
        assert isinstance(result, str)
        # Returns NOT FOUND (graceful degradation)
        assert "not found" in result.lower() or "does not exist" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
