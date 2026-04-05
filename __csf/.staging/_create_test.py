from pathlib import Path

test_content = """'''Tests for plan_injector.py - Plan context injection and disambiguation.

RED PHASE: These tests FAIL initially to demonstrate the module doesn't exist yet.

Task 835: Extract plan_injector module from UserPromptSubmit_router.py
'''

import pytest
from unittest.mock import MagicMock, patch
from typing import Any
import sys
from pathlib import Path

_hooks_dir = Path(__file__).parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class TestPlanInjectorModuleExists:
    def test_plan_injector_module_exists(self):
        from userpromptsubmit import plan_injector
        assert plan_injector is not None

    def test_plan_injector_has_detect_plan_command(self):
        from userpromptsubmit import plan_injector
        assert hasattr(plan_injector, 'detect_plan_command')
        assert callable(plan_injector.detect_plan_command)


class TestPlanDetectionFunctions:
    @pytest.fixture
    def plan_injector(self):
        from userpromptsubmit import plan_injector
        return plan_injector

    def test_detect_plan_command_with_valid_plan_command(self, plan_injector):
        prompt = "/plan Extract plan context injection logic"
        result = plan_injector.detect_plan_command(prompt)
        assert result is True

    def test_extract_explicit_plan_path_finds_md_path(self, plan_injector):
        prompt = "follow the plan at P:\\.claude\\plans\\plan-20250113-task.md"
        result = plan_injector.extract_explicit_plan_path(prompt)
        assert result is not None
        assert ".md" in result


class TestPlanInjectionFunctions:
    @pytest.fixture
    def plan_injector(self):
        from userpromptsubmit import plan_injector
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
        from userpromptsubmit import plan_injector
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
        from userpromptsubmit import registry
        registered_hooks = list(registry.HOOKS.keys())
        plan_hooks = [h for h in registered_hooks if "plan" in h.lower()]
        assert len(plan_hooks) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""

test_file = Path(r"P:\.claude\hooks\userpromptsubmit\tests\test_plan_injector.py")
test_file.parent.mkdir(parents=True, exist_ok=True)
test_file.write_text(test_content, encoding="utf-8")
print(f"Created test file: {test_file}")
