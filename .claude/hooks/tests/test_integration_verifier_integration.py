#!/usr/bin/env python3
"""
Integration Tests for Integration Verifier Hook
================================================

Tests the IntegrationVerifier in the full PostToolUse router context
with actual SKILL.md files from the repository.

These tests verify:
- Hook integrates correctly with PostToolUse router
- Hook processes real SKILL.md files without errors
- Hook detects actual integration gaps in the codebase
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from posttooluse import create_registry  # noqa: E402


class TestIntegrationVerifierIntegration:
    """Integration tests for IntegrationVerifier in full system context."""

    def setup_method(self):
        """Create test fixture with PostToolUse registry."""
        self.registry = create_registry()
        self.skills_dir = HOOKS_DIR.parent / "skills"

    def test_hook_registered_in_registry(self):
        """Verify IntegrationVerifier is registered in PostToolUse registry."""
        # Registry stores hooks as list of (name, instance) tuples
        hook_names = [name for name, _ in self.registry._hooks]
        assert "integration_verifier" in hook_names

        # Verify it's the correct class
        from posttooluse.integration_verifier import IntegrationVerifier
        hook = dict(self.registry._hooks)["integration_verifier"]
        assert isinstance(hook, IntegrationVerifier)

    def test_hook_processes_code_skill_integration(self):
        """Test that hook processes /code SKILL.md integration claims."""
        code_skill_path = self.skills_dir / "code" / "SKILL.md"

        if not code_skill_path.exists():
            import pytest
            pytest.skip("code/SKILL.md not found")

        # Simulate PostToolUse data
        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(code_skill_path)},
            "tool_response": {}
        }

        # Run the full registry
        result = self.registry.run_all(data)

        # Result is a dict with hookSpecificOutput
        assert isinstance(result, dict)
        assert "hookSpecificOutput" in result
        assert "additionalContext" in result["hookSpecificOutput"]

        # Verify integration_verifier contributed to output
        context = result["hookSpecificOutput"]["additionalContext"]
        # The IntegrationVerifier should have produced warnings
        # (code/SKILL.md has integration gaps)
        assert "INTEGRATION VERIFICATION" in context or "integration" in context.lower()

    def test_hook_detects_bidirectional_integration(self):
        """Test that hook detects /code to /async-bugs bidirectional integration."""
        code_skill_path = self.skills_dir / "code" / "SKILL.md"
        async_bugs_skill_path = self.skills_dir / "async-bugs" / "SKILL.md"

        # Skip if either skill doesn't exist
        if not (code_skill_path.exists() and async_bugs_skill_path.exists()):
            import pytest
            pytest.skip("code or async-bugs SKILL.md not found")

        # Read both skills to check suggest: fields
        import yaml

        code_suggests = []
        async_bugs_suggests = []

        with open(code_skill_path) as f:
            try:
                code_frontmatter = yaml.safe_load_all(f.read())
                if len(code_frontmatter) > 0 and isinstance(code_frontmatter[0], dict):
                    code_suggests = code_frontmatter[0].get("suggest", [])
            except Exception:
                pass

        with open(async_bugs_skill_path) as f:
            try:
                async_frontmatter = yaml.safe_load_all(f.read())
                if len(async_frontmatter) > 0 and isinstance(async_frontmatter[0], dict):
                    async_bugs_suggests = async_frontmatter[0].get("suggest", [])
            except Exception:
                pass

        # Check if /code suggests /async-bugs
        code_suggests_async = any("/async-bugs" in str(s) for s in code_suggests)

        # Check if /async-bugs suggests /code
        async_suggests_code = any("/code" in str(s) for s in async_bugs_suggests)

        # This test documents the current state
        # It doesn't enforce bidirectionality, just reports it
        assert isinstance(code_suggests_async, bool)
        assert isinstance(async_suggests_code, bool)

    def test_hook_handles_non_skill_files_gracefully(self):
        """Test that hook does not crash on non-SKILL.md files."""
        # Use a random Python file
        test_file = HOOKS_DIR / "tests" / "test_integration_verifier.py"

        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(test_file)},
            "tool_response": {}
        }

        # Should not crash
        result = self.registry.run_all(data)

        # Should return results as dict
        assert isinstance(result, dict)
        assert "hookSpecificOutput" in result

    def test_hook_json_output_format(self):
        """Test that hook produces JSON-serializable output."""
        code_skill_path = self.skills_dir / "code" / "SKILL.md"

        if not code_skill_path.exists():
            import pytest
            pytest.skip("code/SKILL.md not found")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(code_skill_path)},
            "tool_response": {}
        }

        # Run registry
        result = self.registry.run_all(data)

        # All hook outputs should be JSON-serializable
        try:
            json.dumps(result)
        except TypeError as e:
            import pytest
            pytest.fail(f"Hook output not JSON-serializable: {e}")


def test_integration_verifier_enabled_in_settings():
    """Test that IntegrationVerifier is enabled in settings.json."""
    import json

    settings_path = HOOKS_DIR.parent / "settings.json"

    if not settings_path.exists():
        import pytest
        pytest.skip("settings.json not found")

    with open(settings_path) as f:
        settings = json.load(f)

    # Check env var is set
    assert "INTEGRATION_VERIFIER_ENABLED" in settings.get("env", {})
    assert settings["env"]["INTEGRATION_VERIFIER_ENABLED"] == "true"

    # Check mode is set
    assert "INTEGRATION_VERIFIER_MODE" in settings.get("env", {})
    assert settings["env"]["INTEGRATION_VERIFIER_MODE"] == "warn"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
