#!/usr/bin/env python3
"""
Integration test: Linter hooks are structurally disabled.

Verifies that lint_hook.py cannot be re-enabled via env var and that
dead hook files have been deleted. Prevents sequential-edit race condition
where ruff --fix strips code between multi-step edits.

Ref: premortem_linter-removal-20260329.md Fix 1 (STRUCTURAL FIX)
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent


def _is_comment_line(line: str) -> bool:
    """Return True if line is fully commented out."""
    return line.lstrip().startswith("#")


def _find_active_registry_calls(content: str) -> list[str]:
    """Find registry.register() calls that are NOT commented out."""
    active_calls = []
    for line in content.splitlines():
        if _is_comment_line(line):
            continue
        if "registry.register" in line:
            active_calls.append(line.strip())
    return active_calls


class TestLinterHooksDisabled:
    """Verify linter hooks are structurally removed from dispatch chain."""

    def test_lint_hook_not_in_posttooluse_registry(self):
        """lint_hook.py must NOT be registered in posttooluse/__init__.py."""
        init_path = HOOKS_DIR / "posttooluse" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")

        # Verify lint_hook is not registered (excluding comments)
        active_calls = _find_active_registry_calls(content)
        for call in active_calls:
            assert not ("registry.register" in call and '"lint"' in call), (
                f"lint_hook is still registered (active call): {call}\n"
                "sequential-edit race condition risk remains"
            )

        # Verify import is removed/commented (via AST)
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "lint_hook" not in alias.name, (
                        f"lint_hook import still present: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module and "lint_hook" in node.module:
                    pytest.fail(f"lint_hook import still present: from {node.module}")

    def test_lint_hook_structural_disable_not_flag_based(self):
        """default_enabled=False is bypassable — verify structural removal instead."""
        lint_hook_path = HOOKS_DIR / "posttooluse" / "lint_hook.py"

        # If file exists, verify it's not registered even if enabled
        if lint_hook_path.exists():
            content = lint_hook_path.read_text(encoding="utf-8")

            # Verify the class still has default_enabled=False (for audit trail)
            # but the real protection is that it's not registered
            if "default_enabled" in content:
                assert "default_enabled = False" in content, (
                    "lint_hook should keep default_enabled=False as historical record"
                )

            # Key check: NOT in registry (active calls only)
            init_path = HOOKS_DIR / "posttooluse" / "__init__.py"
            init_content = init_path.read_text(encoding="utf-8")
            active_calls = _find_active_registry_calls(init_content)
            for call in active_calls:
                assert not ("registry.register" in call and '"lint"' in call), (
                    f"lint_hook registered despite default_enabled=False: {call}\n"
                    "env var LINT_ROUTER_ENABLED=true can bypass it"
                )

    def test_dead_hook_files_deleted(self):
        """PreToolUse_auto_format.py and PreToolUse_mypy_type_check.py must be deleted."""
        dead_files = [
            HOOKS_DIR / "PreToolUse_auto_format.py",
            HOOKS_DIR / "PreToolUse_mypy_type_check.py",
        ]
        for dead_file in dead_files:
            assert not dead_file.exists(), (
                f"Dead hook file still on disk: {dead_file.name} — "
                "creates false editing target per CLAUDE.md Hook Edit Verification"
            )

    def test_orphaned_test_deleted(self):
        """tests/test_code_quality_checks.py must be deleted (imported deleted module)."""
        orphaned_test = HOOKS_DIR / "tests" / "test_code_quality_checks.py"
        assert not orphaned_test.exists(), (
            "Orphaned test still on disk — imports deleted PostToolWrite_code_quality "
            "and will fail on import"
        )

    def test_lint_hook_file_exists_for_reference(self):
        """lint_hook.py should remain on disk as reference (not deleted)."""
        lint_hook_path = HOOKS_DIR / "posttooluse" / "lint_hook.py"
        # This is intentional — file stays for audit, but is not registered
        assert lint_hook_path.exists(), (
            "lint_hook.py should remain on disk as historical reference"
        )

    def test_env_var_cannot_reenable_lint_hook(self):
        """Even if LINT_ROUTER_ENABLED=true, lint_hook must not execute."""
        init_path = HOOKS_DIR / "posttooluse" / "__init__.py"
        content = init_path.read_text(encoding="utf-8")

        # The ONLY protection is structural removal — check active calls only
        active_calls = _find_active_registry_calls(content)
        for call in active_calls:
            assert not ("registry.register" in call and '"lint"' in call), (
                f"lint_hook is registered: {call}\n"
                "LINT_ROUTER_ENABLED=true env var can re-enable it"
            )

        # Verify create_registry() does NOT call LintHook (excluding comments)
        for line in content.splitlines():
            if _is_comment_line(line):
                continue
            assert "LintHook()" not in line, (
                "LintHook() instantiation found in __init__.py — "
                "would be called by create_registry() even with default_enabled=False"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
