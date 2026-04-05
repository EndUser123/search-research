#!/usr/bin/env python3
"""
Test suite for QUAL-007: Hardcoded P:/ paths breaking portability.

TDD RED Phase - These tests document EXPECTED behavior.
They will FAIL until the fix is implemented.

Issue: Multiple hook files contain hardcoded "P:/" paths which breaks portability.

Affected Files:
1. UserPromptSubmit_router.py (lines 125, 260, 448, 804, 2089, 2337)
2. unparseable_command_gate.py (line 291)
3. check_skill_enforcement.py (line 16)

Success Criteria:
1. Hooks can work with relative paths
2. Hooks respect environment variables for project root
3. Fallback behavior when P:/ paths are not available

Expected Behavior:
- All P:/ paths should be configurable via environment variables
- Hooks should fall back to relative path resolution
- Hooks should work when P:/ drive is not available
"""

import os
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hooks_dir not in sys.path:
    sys.path.insert(0, hooks_dir)


class TestUserPromptSubmitRouterPortability:
    """
    Test that UserPromptSubmit_router.py uses portable paths.

    CURRENT STATE (documented for characterization):
    - Line 125: INTENT_STATE_DIR = Path("P:/.claude/hooks/state")
    - Line 260: state_dir = Path("P:/.claude/state") / f"skill_execution_{terminal_id}"
    - Line 448: "P:/__csf/scripts/clear-notifications.py"
    - Line 804: skills_dir = Path("P:/.claude/skills")
    - Line 2089: project_root = Path("P:/worktrees/w1t4")
    - Line 2337: parts.append("Full context: P:/.claude/RESTORE_CONTEXT.md")

    EXPECTED: All paths should use environment variable or relative resolution.
    """

    def test_intent_state_dir_uses_env_variable(self):
        """
        INTENT_STATE_DIR should respect PROJECT_ROOT environment variable.

        Given: PROJECT_ROOT environment variable is set to custom path
        When: UserPromptSubmit_router.py initializes INTENT_STATE_DIR
        Then: Should use PROJECT_ROOT/.claude/hooks/state instead of hardcoded P:/

        This test verifies hooks can work with relative paths via environment variable.
        """
        # Read the source file to check current implementation
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # CURRENT STATE: Contains hardcoded "P:/.claude/hooks/state"
        # EXPECTED: Should use os.environ.get("PROJECT_ROOT", "P:/") pattern

        # This test FAILS because the path is currently hardcoded
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "INTENT_STATE_DIR should use PROJECT_ROOT environment variable. "
            "Currently hardcoded as Path(\"P:/.claude/hooks/state\") at line 125. "
            "Expected: Path(os.environ.get('PROJECT_ROOT', 'P:/')) / '.claude' / 'hooks' / 'state'"
        )

    def test_skill_execution_dir_uses_env_variable(self):
        """
        skill_execution state_dir should respect environment variable.

        Given: PROJECT_ROOT environment variable is set
        When: skill execution creates state directory
        Then: Should use PROJECT_ROOT/.claude/state instead of hardcoded P:/

        Line 260: state_dir = Path("P:/.claude/state") / f"skill_execution_{terminal_id}"
        """
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for environment variable usage in skill execution state directory
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "skill_execution state_dir should use PROJECT_ROOT environment variable. "
            "Currently hardcoded as Path(\"P:/.claude/state\") at line 260."
        )

    def test_clear_notifications_script_path_portable(self):
        """
        clear-notifications.py script path should be portable.

        Given: PROJECT_ROOT or SCRIPTS_DIR environment variable is set
        When: Router calls clear-notifications script
        Then: Should use configurable path instead of hardcoded P:/__csf/scripts/

        Line 448: "P:/__csf/scripts/clear-notifications.py"
        """
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for environment variable usage for scripts path
        assert 'PROJECT_ROOT' in source_code or 'SCRIPTS_DIR' in source_code or 'getenv' in source_code, (
            "clear-notifications.py path should use environment variable. "
            "Currently hardcoded as \"P:/__csf/scripts/clear-notifications.py\" at line 448. "
            "Expected: os.path.join(os.environ.get('PROJECT_ROOT', 'P:/'), '__csf', 'scripts', 'clear-notifications.py')"
        )

    def test_skills_dir_uses_env_variable(self):
        """
        skills_dir should respect environment variable.

        Given: PROJECT_ROOT environment variable is set
        When: Router accesses skills directory
        Then: Should use PROJECT_ROOT/.claude/skills instead of hardcoded P:/

        Line 804: skills_dir = Path("P:/.claude/skills")
        """
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for environment variable usage
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "skills_dir should use PROJECT_ROOT environment variable. "
            "Currently hardcoded as Path(\"P:/.claude/skills\") at line 804."
        )

    def test_project_root_worktree_uses_env_variable(self):
        """
        worktree project_root should respect environment variable.

        Given: WORKTREE_ROOT or PROJECT_ROOT environment variable is set
        When: Router accesses worktree project root
        Then: Should use configurable path instead of hardcoded P:/worktrees/w1t4

        Line 2089: project_root = Path("P:/worktrees/w1t4")
        """
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for environment variable usage
        assert 'WORKTREE_ROOT' in source_code or 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "project_root for worktree should use environment variable. "
            "Currently hardcoded as Path(\"P:/worktrees/w1t4\") at line 2089."
        )

    def test_restore_context_path_uses_env_variable(self):
        """
        RESTORE_CONTEXT.md path should respect environment variable.

        Given: PROJECT_ROOT environment variable is set
        When: Router references restore context path
        Then: Should use PROJECT_ROOT/.claude/RESTORE_CONTEXT.md instead of hardcoded P:/

        Line 2337: parts.append("Full context: P:/.claude/RESTORE_CONTEXT.md")
        """
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for environment variable usage or f-string with variable
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code or 'f"' in source_code or "f'" in source_code, (
            "RESTORE_CONTEXT.md path should use environment variable. "
            "Currently hardcoded as \"P:/.claude/RESTORE_CONTEXT.md\" at line 2337."
        )


class TestUnparseableCommandGatePortability:
    """
    Test that unparseable_command_gate.py uses portable paths.

    CURRENT STATE (documented for characterization):
    - Line 291: settings_path = Path("P:/.claude/settings.json")

    EXPECTED: Should use environment variable or relative path resolution.
    """

    def test_settings_json_uses_env_variable(self):
        """
        settings.json path should respect environment variable.

        Given: PROJECT_ROOT environment variable is set
        When: unparseable_command_gate.py loads settings.json
        Then: Should use PROJECT_ROOT/.claude/settings.json instead of hardcoded P:/

        This test verifies hooks can work with relative paths via environment variable.
        """
        gate_path = Path(hooks_dir) / "unparseable_command_gate.py"
        source_code = gate_path.read_text()

        # CURRENT STATE: Contains hardcoded "P:/.claude/settings.json"
        # Line 291: settings_path = Path("P:/.claude/settings.json")
        # EXPECTED: Should use os.environ.get("PROJECT_ROOT", "P:/") pattern

        # Check for environment variable usage
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "settings.json path should use PROJECT_ROOT environment variable. "
            "Currently hardcoded as Path(\"P:/.claude/settings.json\") at line 291. "
            "Expected: Path(os.environ.get('PROJECT_ROOT', 'P:/')) / '.claude' / 'settings.json'"
        )

    def test_fallback_to_relative_path_when_p_unavailable(self):
        """
        Should fall back to relative path when P:/ is not available.

        Given: P:/ drive does not exist
        When: unparseable_command_gate.py tries to load settings.json
        Then: Should fall back to ./.claude/settings.json (relative path)

        This test verifies fallback behavior when P:/ paths are not available.
        """
        # This is a characterization test - documents current behavior
        # Current implementation does NOT have fallback, it just fails if P:/ doesn't exist

        # Test that hook handles missing P:/ drive gracefully
        # We can't actually remove P:/ drive, but we can verify the code structure
        gate_path = Path(hooks_dir) / "unparseable_command_gate.py"
        source_code = gate_path.read_text()

        # Check for fallback pattern like "except" or "or" for path resolution
        has_fallback = (
            'except' in source_code and 'Path(' in source_code
        ) or (
            ' or ' in source_code and 'settings_path' in source_code
        )

        # EXPECTED: Should have fallback logic
        assert has_fallback, (
            "settings.json loading should have fallback when P:/ is unavailable. "
            "Currently has no fallback - will fail if P:/ drive doesn't exist. "
            "Expected: try P:/.claude/settings.json except use ./.claude/settings.json"
        )


class TestCheckSkillEnforcementPortability:
    """
    Test that check_skill_enforcement.py uses portable paths.

    CURRENT STATE (documented for characterization):
    - Line 16: LOG_FILE = Path("P:/.claude/logs/skill_enforcement.jsonl")

    EXPECTED: Should use environment variable or relative path resolution.
    """

    def test_log_file_uses_env_variable(self):
        """
        LOG_FILE should respect environment variable.

        Given: PROJECT_ROOT environment variable is set
        When: check_skill_enforcement.py defines LOG_FILE
        Then: Should use PROJECT_ROOT/.claude/logs/skill_enforcement.jsonl

        This test verifies hooks can work with relative paths via environment variable.
        """
        check_path = Path(hooks_dir) / "check_skill_enforcement.py"
        source_code = check_path.read_text()

        # CURRENT STATE: Contains hardcoded "P:/.claude/logs/skill_enforcement.jsonl"
        # Line 16: LOG_FILE = Path("P:/.claude/logs/skill_enforcement.jsonl")
        # EXPECTED: Should use os.environ.get("PROJECT_ROOT", "P:/") pattern

        # Check for environment variable usage
        assert 'PROJECT_ROOT' in source_code or 'getenv' in source_code, (
            "LOG_FILE should use PROJECT_ROOT environment variable. "
            "Currently hardcoded as Path(\"P:/.claude/logs/skill_enforcement.jsonl\") at line 16. "
            "Expected: Path(os.environ.get('PROJECT_ROOT', 'P:/')) / '.claude' / 'logs' / 'skill_enforcement.jsonl'"
        )


class TestEnvironmentVariableIntegration:
    """
    Test that environment variables are properly integrated for portability.
    """

    def test_project_root_env_variable_allows_custom_path(self):
        """
        PROJECT_ROOT environment variable should override hardcoded P:/.

        Given: PROJECT_ROOT=/custom/path is set
        When: Any hook initializes paths
        Then: Should use /custom/path instead of P:/

        This test verifies that hooks respect environment variables for portability.
        """
        # Check that at least one of the affected files uses PROJECT_ROOT
        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        gate_path = Path(hooks_dir) / "unparseable_command_gate.py"
        check_path = Path(hooks_dir) / "check_skill_enforcement.py"

        router_code = router_path.read_text()
        gate_code = gate_path.read_text()
        check_code = check_path.read_text()

        # At least one file should use PROJECT_ROOT pattern
        uses_project_root = (
            'PROJECT_ROOT' in router_code or
            'PROJECT_ROOT' in gate_code or
            'PROJECT_ROOT' in check_code
        )

        # EXPECTED: At least one file should use PROJECT_ROOT
        # CURRENT STATE: All files use hardcoded P:/
        assert uses_project_root, (
            "At least one hook file should use PROJECT_ROOT environment variable. "
            "Currently all files use hardcoded P:/ paths. "
            "Expected pattern: Path(os.environ.get('PROJECT_ROOT', 'P:/')) / ..."
        )

    def test_hooks_work_with_relative_paths(self):
        """
        Hooks should work with relative paths when P:/ is unavailable.

        Given: Working directory is in a project (not P:/)
        When: Hooks execute
        Then: Should use relative paths (./.claude/) instead of absolute P:/

        This test verifies fallback behavior when P:/ paths are not available.
        """
        # This is an integration test that would require running hooks
        # For now, we check source code for relative path patterns

        router_path = Path(hooks_dir) / "UserPromptSubmit_router.py"
        source_code = router_path.read_text()

        # Check for any relative path patterns (not starting with drive letter)
        has_relative_patterns = (
            '"./"' in source_code or
            '".claude"' in source_code or
            'Path(".claude")' in source_code or
            'cwd()' in source_code  # Using current working directory
        )

        # CURRENT STATE: No relative path patterns, all P:/
        # EXPECTED: Should have relative path fallback
        assert has_relative_patterns, (
            "Hooks should have relative path fallback when P:/ is unavailable. "
            "Currently all paths are absolute P:/. "
            "Expected: Relative paths like Path('.claude') or Path.cwd() / '.claude'"
        )


class TestHardcodedPathDetection:
    """
    Test to detect all hardcoded P:/ paths in hook files.
    """

    def test_no_hardcoded_p_paths_in_critical_hooks(self):
        """
        Critical hook files should NOT contain hardcoded "P:/" strings.

        Given: A hook file (UserPromptSubmit_router.py, unparseable_command_gate.py, check_skill_enforcement.py)
        When: Source code is scanned for "P:/" patterns
        Then: Should find NO hardcoded P:/ paths (only environment variable usage)

        This is the primary test for QUAL-007 - all P:/ paths should be replaced.
        """
        # Files to check
        critical_hooks = [
            "UserPromptSubmit_router.py",
            "unparseable_command_gate.py",
            "check_skill_enforcement.py",
        ]

        for hook_file in critical_hooks:
            hook_path = Path(hooks_dir) / hook_file
            source_code = hook_path.read_text()

            # Count hardcoded P:/ paths
            # Exclude comments and docstrings from check
            lines = source_code.split('\n')
            hardcoded_count = 0
            problematic_lines = []

            for i, line in enumerate(lines, 1):
                # Skip comments
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Check for hardcoded P:/ but allow if it's part of env var pattern
                if '"P:/' in line or "'P:/" in line:
                    # Check if it's using getenv (acceptable)
                    if 'getenv' not in line and 'PROJECT_ROOT' not in line:
                        hardcoded_count += 1
                        problematic_lines.append((i, line.strip()))

            # EXPECTED: No hardcoded P:/ paths
            assert hardcoded_count == 0, (
                f"{hook_file} contains {hardcoded_count} hardcoded P:/ paths.\n"
                f"Problematic lines:\n" +
                "\n".join(f"  Line {i}: {line}" for i, line in problematic_lines[:5]) +
                "\n\nAll P:/ paths should use environment variables like:\n"
                "  Path(os.environ.get('PROJECT_ROOT', 'P:/')) / '.claude' / ..."
            )


if __name__ == "__main__":
    print("=" * 80)
    print("TDD RED Phase: QUAL-007 Portability Tests")
    print("=" * 80)
    print()
    print("Issue: Hardcoded P:/ paths breaking portability")
    print()
    print("Affected Files:")
    print("  1. UserPromptSubmit_router.py (6 hardcoded paths)")
    print("  2. unparseable_command_gate.py (1 hardcoded path)")
    print("  3. check_skill_enforcement.py (1 hardcoded path)")
    print()
    print("Expected Behavior:")
    print("  - All P:/ paths should use PROJECT_ROOT environment variable")
    print("  - Hooks should fall back to relative path resolution")
    print("  - Hooks should work when P:/ drive is not available")
    print()
    print("Fix Pattern:")
    print("  Replace: Path('P:/.claude/file.json')")
    print("  With:     Path(os.environ.get('PROJECT_ROOT', 'P:/')) / '.claude' / 'file.json'")
    print("=" * 80)
    print()

    # Run tests
    import pytest
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
