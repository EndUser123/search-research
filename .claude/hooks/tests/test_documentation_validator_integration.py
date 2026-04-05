"""
Integration tests for PostToolUse documentation validator hook.

Tests end-to-end validation flow, blocking mode JSON format,
and manual command compatibility.

UPDATED: Eliminates mock.patch usage - uses real skill root detection.
"""

import sys
from pathlib import Path

# Add package skill to path for DocumentationValidator import
package_skill_path = Path(__file__).resolve().parent.parent.parent.parent / "skills" / "package"
sys.path.insert(0, str(package_skill_path))

# Import hook to test
import PostToolUse_documentation_validator as hook_module


class TestEndToEndValidationFlow:
    """Test complete validation flow from Write to warning output."""

    def test_hook_triggers_on_markdown_write(self):
        """Hook should trigger when .md file is written to a skills/ directory."""
        # Use real skill directory path (contains /skills/ pattern)
        test_skill_root = Path("P:/.claude/skills/test-skill-integration")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # Create resources directory with minimal validate_docs.py
        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create minimal validator module
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {
                "severity": "HIGH",
                "type": "test_issue",
                "file": "test.md",
                "message": "Test issue for integration",
                "fix": "Fix the test issue"
            }
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create test .md file path (inside skills/ directory)
        test_file = test_skill_root / "test.md"

        # Simulate Write operation
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_file)},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() which detects /skills/ pattern
        result = hook_module.run(data)

        # Verify warning returned
        assert "warning" in result
        assert "⚠️" in result["warning"]
        assert "1 HIGH" in result["warning"]

    def test_hook_skips_non_markdown_files(self):
        """Hook should not trigger for non-.md files."""
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/.claude/skills/test/script.py"},
            "tool_response": None
        }

        result = hook_module.run(data)
        assert result == {}

    def test_hook_skips_non_skill_directories(self):
        """Hook should skip validation for files outside skills directories."""
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/random/location/SKILL.md"},
            "tool_response": None
        }

        result = hook_module.run(data)
        assert result == {}
