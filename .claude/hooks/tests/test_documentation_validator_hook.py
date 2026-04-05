"""
Unit tests for PostToolUse documentation validator hook.

Tests hook behavior for general skills validation, configuration parsing,
and mode switching (suggestive/blocking/off).
"""

import os
import sys
from pathlib import Path

# Add package skill to path for DocumentationValidator import
package_skill_path = Path(__file__).resolve().parent.parent.parent / "skills" / "package"
sys.path.insert(0, str(package_skill_path))


class TestHookBehavior:
    """Test hook triggering and validation behavior."""

    # Module reference that will be updated by setup_method
    hook_module = None

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib

        import PostToolUse_documentation_validator
        importlib.reload(PostToolUse_documentation_validator)
        # Set module-level reference for this test class
        TestHookBehavior.hook_module = PostToolUse_documentation_validator
        # Explicitly reset module-level DocumentationValidator cache
        PostToolUse_documentation_validator.DocumentationValidator = None

    def test_hook_validates_write_operations(self):
        """Hook should validate Write operations on .md files."""
        # Create real skill directory with resources/validate_docs.py
        test_skill_root = Path("P:/.claude/skills/test-skill-behavior")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and DocumentationValidator
        result = self.hook_module.run(data)

        assert result == {}  # No issues, empty dict

    def test_hook_validates_edit_operations(self):
        """Hook should validate Edit operations on .md files."""
        # Create real skill directory with resources/validate_docs.py
        test_skill_root = Path("P:/.claude/skills/another-skill")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and DocumentationValidator
        result = self.hook_module.run(data)

        assert result == {}

    def test_hook_skips_non_markdown_files(self):
        """Hook should skip validation for non-markdown files."""
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/.claude/skills/test-skill/script.py"},
            "tool_response": None
        }

        result = self.hook_module.run(data)
        assert result == {}

    def test_hook_skips_non_write_edit_operations(self):
        """Hook should skip validation for Read/Delete operations."""
        data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "P:/.claude/skills/test-skill/SKILL.md"},
            "tool_response": None
        }

        result = self.hook_module.run(data)
        assert result == {}

    def test_hook_validates_general_skills_not_just_package(self):
        """Hook should validate any skills/*/.md file, not just /package."""
        test_cases = [
            "P:/.claude/skills/docs-validate/SKILL.md",
            "P:/.claude/skills/code/SKILL.md",
            "P:/.claude/skills/arch/SKILL.md"
        ]

        # Create real skill directories for each test case
        for file_path in test_cases:
            skill_root = Path(file_path).parent
            skill_root.mkdir(parents=True, exist_ok=True)

            resources_dir = skill_root / "resources"
            resources_dir.mkdir(exist_ok=True)

            # Create validator that returns no issues
            validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
            (resources_dir / "validate_docs.py").write_text(validator_code)

        # Now run the actual tests
        for file_path in test_cases:
            data = {
                "tool_name": "Write",
                "tool_input": {"file_path": file_path},
                "tool_response": None
            }

            # NO MOCK - use real _find_skill_root() and DocumentationValidator
            result = self.hook_module.run(data)

            assert result == {}, f"Should validate {file_path}"

    def test_hook_returns_warning_dict_for_issues(self):
        """Hook should return warning dict when validation finds issues."""
        # Create real skill directory with resources/validate_docs.py
        test_skill_root = Path("P:/.claude/skills/test-skill-warning")

        # Clean up any existing directory to avoid stale validator caching
        if test_skill_root.exists():
            import shutil
            shutil.rmtree(test_skill_root)

        test_skill_root.mkdir(parents=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular ref", "fix": "Fix it"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and DocumentationValidator
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import importlib
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']
        # Reload hook module to clear cached DocumentationValidator
        importlib.reload(hook_module)
        result = self.hook_module.run(data)

        assert "warning" in result
        assert "⚠️" in result["warning"]


class TestConfigurationParsing:
    """Test settings file reading and YAML parsing."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_missing_settings_file_uses_defaults(self):
        """Missing settings file should use default configuration."""
        # Create real skill directory without settings file
        test_skill_root = Path("P:/.claude/skills/test-config-missing")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and _load_settings()
        result = self.hook_module.run(data)

        # Should use defaults: mode=suggestive, validation enabled
        assert result == {}

    def test_valid_settings_file_parsed_correctly(self):
        """Valid settings file should be parsed and applied."""
        # Create real skill directory with valid settings file
        test_skill_root = Path("P:/.claude/skills/test-config-valid")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: blocking
severity_threshold: high
auto_validate: true
---
Settings file content
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and _load_settings()
        result = self.hook_module.run(data)

        # Settings should be applied (blocking mode with no issues = empty result)
        assert result == {}

    def test_invalid_settings_falls_back_to_defaults(self):
        """Invalid settings file should fall back to defaults."""
        # Create real skill directory with invalid settings file
        test_skill_root = Path("P:/.claude/skills/test-config-invalid")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with invalid mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: invalid_mode
severity_threshold: invalid_threshold
---
Settings file content
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and _load_settings()
        result = self.hook_module.run(data)

        # Should fall back to defaults (invalid mode → defaults → empty result)
        assert result == {}


class TestModeSwitching:
    """Test three validation modes: suggestive, blocking, off."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_suggestive_mode_returns_warning(self):
        """Suggestive mode: warning shown, write operation completes."""
        # Create real skill directory with suggestive mode settings
        test_skill_root = Path("P:/.claude/skills/test-mode-suggestive")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns HIGH severity issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with suggestive mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: suggestive
---
Suggestive mode enabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root(), _load_settings(), and DocumentationValidator
        result = self.hook_module.run(data)

        assert "warning" in result
        assert result.get("decision") != "deny"  # Not blocking

    def test_blocking_mode_returns_permission_decision_deny(self):
        """Blocking mode: write operation blocked with permissionDecision=deny JSON."""
        # Create real skill directory with blocking mode settings
        test_skill_root = Path("P:/.claude/skills/test-mode-blocking")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns HIGH severity issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with blocking mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: blocking
---
Blocking mode enabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root(), _load_settings(), and DocumentationValidator
        result = self.hook_module.run(data)

        assert result.get("decision") == "deny"
        assert "reason" in result

    def test_off_mode_skips_validation(self):
        """Off mode: no validation performed."""
        # Create real skill directory with off mode settings
        test_skill_root = Path("P:/.claude/skills/test-mode-off")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator (should NOT be called in off mode)
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        # This should NOT be instantiated in off mode
        raise RuntimeError("DocumentationValidator should not be called in off mode")

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with off mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: off
---
Validation disabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() and _load_settings()
        # DocumentationValidator should NOT be called (no RuntimeError raised)
        result = self.hook_module.run(data)

        assert result == {}  # Off mode returns empty dict


class TestEdgeCases:
    """Test edge cases and error handling."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_graceful_degradation_when_validator_unavailable(self):
        """Hook should return warning when DocumentationValidator unavailable."""
        # Create real skill directory with validate_docs.py that has import error
        test_skill_root = Path("P:/.claude/skills/test-validator-unavailable")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validate_docs.py with intentional import error
        # This will trigger ImportError when hook tries to import it
        validator_code = """
# This file intentionally imports a non-existent module to trigger ImportError
import nonexistent_module_xyz  # This will cause ImportError
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root()
        # Hook will attempt to import validate_docs and get ImportError
        # The hook catches ImportError and returns warning
        result = self.hook_module.run(data)

        assert "warning" in result
        assert "unavailable" in result["warning"].lower()

    def test_skill_root_not_found_returns_empty(self):
        """Hook should return empty dict when skill root cannot be found."""
        # Use a file that DOESN'T have /skills/ in the path
        # This will cause _find_skill_root() to return None
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/random/location/SKILL.md"},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() which returns None for non-skill paths
        result = self.hook_module.run(data)

        assert result == {}

    def test_non_skill_directory_returns_empty(self):
        """Hook should skip validation for files outside skills directories."""
        # Use a file that DOESN'T have /skills/ in the path
        # This will cause _find_skill_root() to return None
        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/another/random/location/file.md"},
            "tool_response": None
        }

        # NO MOCK - use real _find_skill_root() which returns None for non-skill paths
        result = self.hook_module.run(data)

        assert result == {}


class TestFalsePositiveScenarios:
    """Test that valid documentation doesn't trigger false warnings."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_substantive_see_reference_no_warning(self):
        """Valid 'See reference.md' to file with 50+ lines should not trigger warning."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-false-positive-substantive")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that checks for circular references
        validator_code = """
import re
from pathlib import Path
from typing import Dict, List, Optional

MIN_SUBSTANTIVE_CONTENT_LINES = 50
SEE_REFERENCE_PATTERN = r"See\\s+([^\\s]+\\.md)"

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        self.skill_md = docs_dir / "SKILL.md"

    def validate(self):
        issues = []
        try:
            if not self.skill_md.exists():
                return issues

            content = self.skill_md.read_text(encoding="utf-8")

            # Check for circular references
            issues.extend(self._check_circular_references(content))

        except Exception:
            pass

        return issues

    def _check_circular_references(self, content):
        issues = []
        references = re.findall(SEE_REFERENCE_PATTERN, content)

        for ref in references:
            ref_path = self._resolve_path(ref)
            if not ref_path or not ref_path.exists():
                continue

            ref_content = ref_path.read_text(encoding="utf-8")
            line_count = len(ref_content.split("\\n"))
            if line_count < MIN_SUBSTANTIVE_CONTENT_LINES:
                issues.append({
                    "severity": "HIGH",
                    "type": "circular_reference",
                    "file": str(ref_path.relative_to(self.docs_dir)),
                    "message": f"Circular reference detected between SKILL.md and {ref}",
                    "fix": f"Expand {ref} with substantive content or remove circular reference"
                })

        return issues

    def _resolve_path(self, reference):
        try:
            if ".." in reference or reference.startswith("/"):
                return None
            ref_path = (self.docs_dir / reference).resolve()
            ref_path.relative_to(self.docs_dir.resolve())
            return ref_path
        except Exception:
            return None
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create SKILL.md that references another file
        skill_md_content = """---
name: Test Skill
description: Test skill for false positive detection
---

# Test Skill Documentation

This is a comprehensive skill documentation with many lines of content.
It provides detailed explanations and examples.

See reference.md for additional details.
"""
        (test_skill_root / "SKILL.md").write_text(skill_md_content)

        # Create reference.md with 50+ lines (substantive content)
        reference_lines = ["# Reference Documentation\n\n"] + [
            f"This is line {i} of substantive content.\n"
            for i in range(1, 60)  # 60 lines > MIN_SUBSTANTIVE_CONTENT_LINES
        ]
        (test_skill_root / "reference.md").write_text("".join(reference_lines))

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - should return empty dict (no false positive warning)
        result = self.hook_module.run(data)

        assert result == {}  # Substantive file should not trigger warning

    def test_matching_version_references_no_warning(self):
        """Version references that match SKILL.md version should not trigger warning."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-false-positive-version")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that checks for version conflicts
        validator_code = """
import re
from pathlib import Path
from typing import Dict, List, Optional

SKILL_VERSION_PATTERN = r'version:\\s*["\\']?(\\d+\\.\\d+)'
VERSION_PATTERN = r"[vV]ersion\\s+(\\d+\\.\\d+)"

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        self.skill_md = docs_dir / "SKILL.md"

    def validate(self):
        issues = []
        try:
            if not self.skill_md.exists():
                return issues

            content = self.skill_md.read_text(encoding="utf-8")

            # Check for version conflicts
            issues.extend(self._check_version_consistency(content))

        except Exception:
            pass

        return issues

    def _check_version_consistency(self, content):
        issues = []
        skill_version = None
        version_match = re.search(SKILL_VERSION_PATTERN, content)
        if version_match:
            skill_version = version_match.group(1)

        if not skill_version:
            return issues

        for md_file in self.docs_dir.glob("*.md"):
            if md_file.name == "SKILL.md":
                continue

            ref_content = md_file.read_text(encoding="utf-8")
            ref_versions = re.findall(VERSION_PATTERN, ref_content)

            for ref_version in ref_versions:
                if ref_version != skill_version:
                    issues.append({
                        "severity": "MEDIUM",
                        "type": "version_conflict",
                        "file": str(md_file.relative_to(self.docs_dir)),
                        "message": f"Version conflict: SKILL.md has {skill_version}.x but {md_file.name} mentions {ref_version}",
                        "fix": f"Update {md_file.name} to reference version {skill_version}"
                    })

        return issues
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create SKILL.md with version 2.5
        skill_md_content = """---
name: Test Skill
version: 2.5
description: Test skill version checking
---

# Test Skill v2.5

This is version 2.5 of the test skill.

Version 2.5 includes several improvements.
"""
        (test_skill_root / "SKILL.md").write_text(skill_md_content)

        # Create CHANGELOG.md with matching version reference
        changelog_content = """# Changelog

## Version 2.5 (2026-03-07)

- Added new features
- Fixed bugs

This version 2.5 release is compatible with SKILL.md version 2.5.
"""
        (test_skill_root / "CHANGELOG.md").write_text(changelog_content)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "CHANGELOG.md")},
            "tool_response": None
        }

        # NO MOCK - should return empty dict (matching version is not a conflict)
        result = self.hook_module.run(data)

        assert result == {}  # Matching version should not trigger warning

    def test_external_reference_no_warning(self):
        """References to external files should be ignored (not flagged as missing)."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-false-positive-external")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that checks for missing files
        validator_code = """
import re
from pathlib import Path
from typing import Dict, List, Optional

SEE_REFERENCE_PATTERN = r"See\\s+([^\\s]+\\.md)"

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        self.skill_md = docs_dir / "SKILL.md"

    def validate(self):
        issues = []
        try:
            if not self.skill_md.exists():
                return issues

            content = self.skill_md.read_text(encoding="utf-8")

            # Check for missing files
            issues.extend(self._check_reference_completeness(content))

        except Exception:
            pass

        return issues

    def _check_reference_completeness(self, content):
        issues = []
        references = re.findall(SEE_REFERENCE_PATTERN, content)

        for ref in references:
            ref_path = self._resolve_path(ref)
            if not ref_path or not ref_path.exists():
                issues.append({
                    "severity": "MEDIUM",
                    "type": "missing_file",
                    "file": ref,
                    "message": f"Referenced file not found: {ref}",
                    "fix": f"Create {ref} or remove the reference"
                })

        return issues

    def _resolve_path(self, reference):
        try:
            # Reject paths that try to escape the docs directory
            if ".." in reference or reference.startswith("/"):
                return None

            ref_path = (self.docs_dir / reference).resolve()
            ref_path.relative_to(self.docs_dir.resolve())
            return ref_path
        except Exception:
            return None
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create SKILL.md with no "See" references
        skill_md_content = """---
name: Test Skill
description: Test skill with no references
---

# Test Skill Documentation

This documentation has no cross-references to other files.
"""
        (test_skill_root / "SKILL.md").write_text(skill_md_content)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - should return empty dict (no references = no issues)
        result = self.hook_module.run(data)

        assert result == {}  # No references = no false positive warnings

    def test_path_traversal_correctly_rejected(self):
        """Paths with '..' or leading '/' should be rejected (correct behavior, not false positive)."""
        # This test verifies that path security is working correctly
        # Rejected paths are intentional security measures, not false positives

        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-path-security")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that checks for missing files
        validator_code = """
import re
from pathlib import Path
from typing import Dict, List, Optional

SEE_REFERENCE_PATTERN = r"See\\s+([^\\s]+\\.md)"

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir
        self.skill_md = docs_dir / "SKILL.md"

    def validate(self):
        issues = []
        try:
            if not self.skill_md.exists():
                return issues

            content = self.skill_md.read_text(encoding="utf-8")

            # Check for missing files
            issues.extend(self._check_reference_completeness(content))

        except Exception:
            pass

        return issues

    def _check_reference_completeness(self, content):
        issues = []
        references = re.findall(SEE_REFERENCE_PATTERN, content)

        for ref in references:
            ref_path = self._resolve_path(ref)
            # Only flag if resolution succeeded but file doesn't exist
            # Paths that can't be resolved (../, /) are silently skipped
            if ref_path and not ref_path.exists():
                issues.append({
                    "severity": "MEDIUM",
                    "type": "missing_file",
                    "file": ref,
                    "message": f"Referenced file not found: {ref}",
                    "fix": f"Create {ref} or remove the reference"
                })

        return issues

    def _resolve_path(self, reference):
        try:
            # Reject paths that try to escape the docs directory
            if ".." in reference or reference.startswith("/"):
                return None

            ref_path = (self.docs_dir / reference).resolve()
            ref_path.relative_to(self.docs_dir.resolve())
            return ref_path
        except Exception:
            return None
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create SKILL.md with suspicious but safe "See" references
        skill_md_content = """---
name: Test Skill
description: Test skill path security
---

# Test Skill Documentation

See ../external.md for external context.
See /absolute/path.md for absolute reference.

These suspicious references should be silently ignored (security measure).
"""
        (test_skill_root / "SKILL.md").write_text(skill_md_content)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # NO MOCK - should return empty dict (suspicious paths are skipped, not flagged)
        result = self.hook_module.run(data)

        assert result == {}  # Path traversal attempts are skipped, not flagged


class TestPerformanceBaselines:
    """Performance tests to ensure hook runs within acceptable time limits."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_fast_path_no_issues_performance(self):
        """Hook execution time for fast path (no issues) should be <100ms."""
        import time

        # Create real skill directory with no issues
        test_skill_root = Path("P:/.claude/skills/test-perf-fast-path")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues (fast path)
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []  # No issues = fast path
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = self.hook_module.run(data)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        assert result == {}  # Fast path returns empty dict
        assert elapsed_ms < 100, f"Hook execution took {elapsed_ms:.2f}ms, expected <100ms"

    def test_validation_with_issues_performance(self):
        """Hook execution time with validation issues should be <500ms."""
        import time

        # Create real skill directory with validation issues
        test_skill_root = Path("P:/.claude/skills/test-perf-with-issues")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns issues (exercises full validation path)
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        # Simulate validation work
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular", "fix": "Fix"},
            {"severity": "MEDIUM", "type": "version_conflict", "file": "b.md", "message": "Version mismatch", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = self.hook_module.run(data)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        assert "warning" in result  # Should return warning
        assert elapsed_ms < 500, f"Hook execution took {elapsed_ms:.2f}ms, expected <500ms"

    def test_off_mode_performance(self):
        """Hook execution time for off mode (no validation) should be <50ms."""
        import time

        # Create real skill directory with off mode
        test_skill_root = Path("P:/.claude/skills/test-perf-off-mode")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that should NOT be called in off mode
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        raise RuntimeError("Should not be called in off mode")

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with off mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: off
---
Validation disabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = self.hook_module.run(data)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        assert result == {}  # Off mode returns empty dict
        assert elapsed_ms < 50, f"Off mode execution took {elapsed_ms:.2f}ms, expected <50ms"

    def test_blocking_mode_performance(self):
        """Hook execution time for blocking mode with HIGH issues should be <100ms."""
        import time

        # Create real skill directory with blocking mode
        test_skill_root = Path("P:/.claude/skills/test-perf-blocking-mode")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns HIGH severity issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with blocking mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: blocking
---
Blocking mode enabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = self.hook_module.run(data)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        assert result.get("decision") == "deny"  # Blocking mode returns deny
        assert "reason" in result
        assert elapsed_ms < 100, f"Blocking mode execution took {elapsed_ms:.2f}ms, expected <100ms"


class TestGracefulDegradationLogging:
    """Test graceful degradation behavior and logging."""

    @staticmethod
    def setup_method():
        """Reload hook module before each test to clear module-level cache."""
        import importlib
        importlib.reload(hook_module)
        # Explicitly reset module-level DocumentationValidator cache
        hook_module.DocumentationValidator = None
        # Clear Python's import cache to prevent importing wrong validate_docs.py
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']

    def test_import_error_returns_warning_not_exception(self):
        """ImportError in validator returns warning dict, doesn't raise exception."""
        # Create real skill directory with validator that causes ImportError
        test_skill_root = Path("P:/.claude/skills/test-degradation-import-error")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validate_docs.py with import error
        validator_code = """
# This will cause ImportError when imported
import nonexistent_module_xyz
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Should NOT raise exception, should return warning dict
        result = self.hook_module.run(data)

        assert "warning" in result  # Returns warning, not exception
        assert "unavailable" in result["warning"].lower()  # Describes the problem

    def test_validation_error_returns_warning_not_exception(self):
        """Exception during validation returns warning dict, doesn't raise exception."""
        # Create real skill directory with validator that raises exception
        test_skill_root = Path("P:/.claude/skills/test-degradation-validation-error")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that raises exception during validate()
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        raise RuntimeError("Intentional validation error for testing")
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Should NOT raise exception, should return warning dict
        result = self.hook_module.run(data)

        assert "warning" in result  # Returns warning, not exception
        assert "validation error" in result["warning"].lower()  # Describes the problem

    def test_invalid_mode_falls_back_to_suggestive(self):
        """Invalid mode in settings file falls back to 'suggestive' (default)."""
        # Create real skill directory with invalid mode
        test_skill_root = Path("P:/.claude/skills/test-degradation-invalid-mode")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with INVALID mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: invalid_mode_name
---
Invalid mode should fall back to 'suggestive'
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Should fall back to defaults (suggestive mode) and return empty dict
        result = self.hook_module.run(data)

        assert result == {}  # Falls back to default mode, no issues

    def test_malformed_settings_falls_back_to_defaults(self):
        """Malformed settings file falls back to default settings."""
        # Create real skill directory with malformed settings
        test_skill_root = Path("P:/.claude/skills/test-degradation-malformed-settings")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "test_issue", "file": "a.md", "message": "Test", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with malformed YAML
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
invalid yaml syntax [ unclosed bracket
---
This is malformed YAML
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Should fall back to defaults (suggestive mode) and return warning
        result = self.hook_module.run(data)

        assert "warning" in result  # Should return warning with issues

    def test_missing_resources_directory_continues_normally(self):
        """Missing resources/ directory continues normally (validator unavailable)."""
        # Create real skill directory WITHOUT resources/
        test_skill_root = Path("P:/.claude/skills/test-degradation-no-resources")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # NO resources directory - validator unavailable

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Should continue normally, return empty dict (no validator = no issues)
        result = self.hook_module.run(data)

        assert result == {}  # No validator = no issues, returns empty


class TestWarningDeduplication:
    """Test warning deduplication prevents showing the same warning multiple times."""

    # Module reference that will be updated by setup_method
    hook_module = None

    def setup_method(self):
        """Reload hook module before each test to clear module-level cache."""
        import importlib

        import PostToolUse_documentation_validator
        importlib.reload(PostToolUse_documentation_validator)
        # Set module-level reference for this test class
        TestWarningDeduplication.hook_module = PostToolUse_documentation_validator
        PostToolUse_documentation_validator.DocumentationValidator = None
        import sys
        if 'validate_docs' in sys.modules:
            del sys.modules['validate_docs']
        # Clear warning deduplication state
        state_file = Path("P:/.claude/state/warning_deduplication_state.json")
        if state_file.exists():
            state_file.unlink()

    @staticmethod
    def teardown_method():
        """Clean up warning deduplication state after tests."""
        state_file = Path("P:/.claude/state/warning_deduplication_state.json")
        if state_file.exists():
            state_file.unlink()

    def test_duplicate_warning_shown_only_once(self):
        """Same warning on consecutive writes should only show once."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-dedup-same-warning")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns same issue repeatedly
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        # Always returns the same issue
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular ref", "fix": "Fix it"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # First call - should show warning
        result1 = self.hook_module.run(data)
        assert "warning" in result1
        assert "Circular ref" in result1["warning"]

        # Second call with same issue - should NOT show warning (deduplicated)
        result2 = self.hook_module.run(data)
        assert result2 == {}  # Warning deduplicated, not shown again

    def test_different_warnings_both_shown(self):
        """Different warnings should both be shown (not deduplicated)."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-dedup-different-warnings")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns different issues on each call
        # Use module-level counter to persist across instances (hook creates new instance each call)
        validator_code = """
_call_count = 0

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        global _call_count
        _call_count += 1
        # Return different issue each time
        if _call_count == 1:
            return [
                {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "First issue", "fix": "Fix 1"}
            ]
        else:
            return [
                {"severity": "MEDIUM", "type": "version_conflict", "file": "b.md", "message": "Second issue", "fix": "Fix 2"}
            ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # First call - should show first warning
        result1 = self.hook_module.run(data)
        assert "warning" in result1
        assert "First issue" in result1["warning"]

        # Second call - should show second warning (different from first)
        result2 = self.hook_module.run(data)
        assert "warning" in result2
        assert "Second issue" in result2["warning"]

    def test_warning_deduplication_respects_severity(self):
        """Warnings with different severity but same type/message are deduplicated."""
        # Create real skill directory
        test_skill_root = Path("P:/.claude/skills/test-dedup-same-type-diff-severity")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns same issue with different severity
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        # Same type+message but different severity - should still deduplicate
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Same issue", "fix": "Fix it"},
            {"severity": "MEDIUM", "type": "circular_reference", "file": "a.md", "message": "Same issue", "fix": "Fix it"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # First call - should show warnings
        result1 = self.hook_module.run(data)
        assert "warning" in result1
        assert "Same issue" in result1["warning"]

        # Second call with same issues - should be deduplicated
        result2 = self.hook_module.run(data)
        assert result2 == {}  # Warning deduplicated

    def test_warning_deduplication_across_skills(self):
        """Warnings are deduplicated per-skill, not globally."""
        # Create two different skill directories
        test_skill_1 = Path("P:/.claude/skills/test-dedup-skill-1")
        test_skill_1.mkdir(parents=True, exist_ok=True)
        test_skill_2 = Path("P:/.claude/skills/test-dedup-skill-2")
        test_skill_2.mkdir(parents=True, exist_ok=True)

        for skill_root in [test_skill_1, test_skill_2]:
            resources_dir = skill_root / "resources"
            resources_dir.mkdir(exist_ok=True)

            # Create validator that returns same issue
            validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Same issue", "fix": "Fix it"}
        ]
"""
            (resources_dir / "validate_docs.py").write_text(validator_code)

        # First skill - should show warning
        data1 = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_1 / "SKILL.md")},
            "tool_response": None
        }
        result1 = self.hook_module.run(data1)
        assert "warning" in result1
        assert "Same issue" in result1["warning"]

        # Second skill with SAME issue - should also show warning (per-skill deduplication)
        data2 = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_2 / "SKILL.md")},
            "tool_response": None
        }
        result2 = self.hook_module.run(data2)
        assert "warning" in result2  # Different skill, so warning shows again

    def test_warning_deduplication_no_issues_performance(self):
        """Deduplication check should not add overhead when no issues."""
        import time

        # Create real skill directory with no issues
        test_skill_root = Path("P:/.claude/skills/test-dedup-perf-no-issues")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns no issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return []  # No issues
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        # Measure execution time
        start_time = time.perf_counter()
        result = self.hook_module.run(data)
        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        assert result == {}  # No issues
        assert elapsed_ms < 100, f"Deduplication check added {elapsed_ms:.2f}ms overhead, expected <100ms"


class TestIntelligentModeSelection:
    """Test intelligent mode recommendation and auto-selection."""

    # Module reference that will be updated by setup_method
    hook_module = None

    def setup_method(self):
        """Reload hook module to pick up code changes."""
        import sys

        # Remove module from cache to force fresh import
        modules_to_remove = [
            'PostToolUse_documentation_validator',
            'tests.test_documentation_validator_hook.hook_module'
        ]

        for mod_name in modules_to_remove:
            if mod_name in sys.modules:
                del sys.modules[mod_name]

        # Re-import the module (this will load fresh from disk)
        import PostToolUse_documentation_validator

        # Update the class-level reference
        TestIntelligentModeSelection.hook_module = PostToolUse_documentation_validator
        # Also set as instance attribute for convenience
        self.hook_module = PostToolUse_documentation_validator

        # Update sys.modules for the test module
        sys.modules['tests.test_documentation_validator_hook.hook_module'] = PostToolUse_documentation_validator

    def test_recommend_mode_no_issues(self):
        """No issues should recommend 'off' mode."""
        issues = []
        result = self.hook_module._recommend_mode(issues)
        assert result == "off"

    def test_recommend_mode_three_high_issues(self):
        """3+ HIGH issues should recommend 'blocking' mode."""
        issues = [
            {"severity": "HIGH", "message": "Issue 1"},
            {"severity": "HIGH", "message": "Issue 2"},
            {"severity": "HIGH", "message": "Issue 3"},
        ]
        result = self.hook_module._recommend_mode(issues)
        assert result == "blocking"

    def test_recommend_mode_one_high_issue(self):
        """1-2 HIGH issues should recommend 'suggestive' mode."""
        issues = [
            {"severity": "HIGH", "message": "Issue 1"},
        ]
        result = self.hook_module._recommend_mode(issues)
        assert result == "suggestive"

    def test_recommend_mode_many_medium_issues(self):
        """5+ MEDIUM issues should recommend 'suggestive' mode."""
        issues = [
            {"severity": "MEDIUM", "message": f"Issue {i}"}
            for i in range(5)
        ]
        result = self.hook_module._recommend_mode(issues)
        assert result == "suggestive"

    def test_recommend_mode_few_issues(self):
        """Few issues should recommend 'off' mode."""
        issues = [
            {"severity": "MEDIUM", "message": "Issue 1"},
            {"severity": "MEDIUM", "message": "Issue 2"},
        ]
        result = self.hook_module._recommend_mode(issues)
        assert result == "off"

    def test_should_ask_user_first_time(self):
        """First time validating (no settings file) should ask user."""
        test_skill_root = Path("P:/.claude/skills/test-ask-first-time")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # No settings file exists
        settings = {}
        result = self.hook_module._should_ask_user("suggestive", settings, test_skill_root)
        assert result is True  # Should ask

    def test_should_ask_user_mode_escalation(self):
        """Mode escalation (suggestive → blocking) should ask user."""
        test_skill_root = Path("P:/.claude/skills/test-ask-escalation")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # Create settings file with suggestive mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: suggestive
---
Suggestive mode
""")

        settings = self.hook_module._load_settings(test_skill_root)
        result = self.hook_module._should_ask_user("blocking", settings, test_skill_root)
        assert result is True  # Should ask (escalation)

    def test_should_ask_user_mode_deescalation(self):
        """Mode de-escalation (blocking → suggestive) should ask user."""
        test_skill_root = Path("P:/.claude/skills/test-ask-deescalation")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # Create settings file with blocking mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: blocking
---
Blocking mode
""")

        settings = self.hook_module._load_settings(test_skill_root)
        result = self.hook_module._should_ask_user("suggestive", settings, test_skill_root)
        assert result is True  # Should ask (de-escalation)

    def test_should_not_ask_user_same_mode(self):
        """Same mode should NOT ask user (non-intrusive)."""
        test_skill_root = Path("P:/.claude/skills/test-no-ask-same-mode")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        # Create settings file with suggestive mode
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
mode: suggestive
---
Suggestive mode
""")

        settings = self.hook_module._load_settings(test_skill_root)
        result = self.hook_module._should_ask_user("suggestive", settings, test_skill_root)
        assert result is False  # Should NOT ask (same mode)

    def test_report_findings_format(self):
        """Dry-run report should show findings and recommended mode."""
        test_skill_root = Path("P:/.claude/skills/test-report-findings")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        issues = [
            {"severity": "HIGH", "type": "circular", "message": "Circular ref", "file": "a.md", "fix": "Fix it"},
            {"severity": "MEDIUM", "type": "missing", "message": "Missing file", "file": "b.md", "fix": "Add file"},
        ]

        result = self.hook_module._report_findings(issues, "suggestive", test_skill_root)

        assert "warning" in result
        assert "DRY-RUN" in result["warning"]
        assert "1 HIGH, 1 MEDIUM" in result["warning"]
        assert "SUGGESTIVE" in result["warning"]
        assert "Circular ref" in result["warning"]
        assert "Missing file" in result["warning"]

    def test_auto_validate_flow_with_issues(self):
        """Auto-validate should show dry-run report on first run."""
        # Disable deduplication for testing (prevents state file interference)
        os.environ["DISABLE_WARNING_DEDUPLICATION"] = "true"

        test_skill_root = Path("P:/.claude/skills/test-auto-validate")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns HIGH issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular", "message": "Circular", "file": "a.md", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with auto_validate enabled
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
auto_validate: true
mode: off
---
Auto-validation enabled
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        result = self.hook_module.run(data)

        # Should show dry-run report (not block, not regular warning)
        assert "warning" in result
        assert "DRY-RUN" in result["warning"]
        assert "Recommended mode: SUGGESTIVE" in result["warning"]
        # Should NOT show regular warning format
        assert "⚠️  Documentation validation:" not in result["warning"]

    def test_auto_validate_uses_recommended_mode(self):
        """Auto-validate should use recommended mode after first run."""
        # Disable deduplication for testing (prevents state file interference)
        os.environ["DISABLE_WARNING_DEDUPLICATION"] = "true"

        test_skill_root = Path("P:/.claude/skills/test-auto-recommended")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns HIGH issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular", "message": "Circular", "file": "a.md", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with recommended mode already set
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
auto_validate: true
mode: suggestive
---
Auto-validation with recommended mode
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        result = self.hook_module.run(data)

        # Should use recommended mode (suggestive) and show regular warning
        assert "warning" in result
        assert "⚠️  Documentation validation:" in result["warning"]
        # Should NOT show dry-run report (mode already set)
        assert "DRY-RUN" not in result["warning"]

    def test_auto_validate_off_mode_shows_dry_run(self):
        """Auto-validate with mode=off should show DRY-RUN to inform user."""
        test_skill_root = Path("P:/.claude/skills/test-auto-skip")
        test_skill_root.mkdir(parents=True, exist_ok=True)

        resources_dir = test_skill_root / "resources"
        resources_dir.mkdir(exist_ok=True)

        # Create validator that returns issues
        validator_code = """
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular", "message": "Circular", "file": "a.md", "fix": "Fix"}
        ]
"""
        (resources_dir / "validate_docs.py").write_text(validator_code)

        # Create settings file with mode already set to off
        claude_dir = test_skill_root / ".claude"
        claude_dir.mkdir(exist_ok=True)

        settings_file = claude_dir / "docs-validate.local.md"
        settings_file.write_text("""---
auto_validate: true
mode: off
---
Validation off
""")

        data = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(test_skill_root / "SKILL.md")},
            "tool_response": None
        }

        result = self.hook_module.run(data)

        # Should show DRY-RUN report because mode=off but issues exist
        # System informs user of recommended mode before skipping validation
        assert "warning" in result
        assert "DRY-RUN" in result["warning"]
        assert "Recommended mode: SUGGESTIVE" in result["warning"]
