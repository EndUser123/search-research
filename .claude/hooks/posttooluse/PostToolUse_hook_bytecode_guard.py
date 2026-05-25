#!/usr/bin/env python3
"""Post-Edit Hook Bytecode Guard.

Clears stale .pyc bytecode after Edit/Write/MultiEdit on hook .py files.
Detects in-session edits to hook files and immediately invalidates the
Python module cache so the next hook invocation picks up fresh source.

Architecture note:
- Layer 1 (HookImporter): proactive mtime tracking — handles cross-session and
  subprocess cases where a fresh process instance loads the hook
- Layer 2 (hook_runner.py PYTHONDONTWRITEBYTECODE): prevents subprocess from writing
  new .pyc that could outlive the parent process
- Layer 3 (path_sanitizer.py): validates hook names and paths before construction
- Layer 4 (this hook): closes the gap for in-session edits — when you edit a hook
  mid-session, this guard clears the bytecode cache immediately so the next
  PostToolUse invocation (which creates a fresh HookImporter with empty
  _source_mtimes) doesn't accidentally load stale bytecode

This hook runs AFTER the edit already succeeded. It is non-blocking (advisory).
The goal is cache hygiene, not preventing the edit.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook


class HookBytecodeGuard(PostToolUseHook):
    """Clear bytecode cache after in-session edits to hook .py files."""

    tool_matcher = {"Edit", "Write", "MultiEdit"}
    env_var = "HOOK_BYTECODE_GUARD_ENABLED"
    default_enabled = True

    # Hooks directory — resolved once at class level for performance
    _hooks_dir: Path | None = None

    @classmethod
    def _get_hooks_dir(cls) -> Path | None:
        """Return the hooks directory path, or None if not determinable."""
        if cls._hooks_dir is not None:
            return cls._hooks_dir

        # hook_importer.py lives in __lib/
        try:
            hook_importer_path = Path(__file__).parent.parent / "__lib" / "hook_importer.py"
            if hook_importer_path.exists():
                hooks_dir = hook_importer_path.parent.parent
                cls._hooks_dir = hooks_dir.resolve()
                return cls._hooks_dir
        except Exception:
            pass

        # Fallback: try standard location
        try:
            standard = Path(r"P:/.claude/hooks").resolve()
            if standard.exists():
                cls._hooks_dir = standard
                return cls._hooks_dir
        except Exception:
            pass

        return None

    @classmethod
    def _clear_hook_bytecode(cls, hook_name: str, hooks_dir: Path) -> None:
        """Clear version-tagged .pyc/.pyo for a specific hook."""
        pycache_dir = hooks_dir / "__pycache__"
        if not pycache_dir.exists():
            return

        version_tag = f"cpython-{sys.version_info.major}{sys.version_info.minor}"
        for ext in (".pyc", ".pyo"):
            pyc_file = pycache_dir / f"{hook_name}.{version_tag}{ext}"
            try:
                pyc_file.unlink(missing_ok=True)
            except OSError:
                pass

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return {"passed": True, "skipped": True, "reason": "no_file_path"}

        path = Path(file_path)

        # For MultiEdit, file_path might be relative or have forward slashes
        if not path.exists() or not path.is_absolute():
            cwd = Path.cwd()
            resolved = cwd / file_path if not path.is_absolute() else path
            if resolved.exists():
                path = resolved
            else:
                return {"passed": True, "skipped": True, "reason": "file_not_found"}

        # Only handle .py files
        if not file_path.endswith(".py"):
            return {"passed": True, "skipped": True, "reason": "not_python"}

        # Only handle files under the hooks directory
        hooks_dir = self._get_hooks_dir()
        if hooks_dir is None:
            return {"passed": True, "skipped": True, "reason": "hooks_dir_not_found"}

        try:
            resolved_path = path.resolve()
        except OSError:
            return {"passed": True, "skipped": True, "reason": "path_resolution_failed"}

        try:
            hooks_dir_resolved = hooks_dir.resolve()
        except OSError:
            return {"passed": True, "skipped": True, "reason": "hooks_dir_resolution_failed"}

        # Check: is the edited file under the hooks directory?
        try:
            resolved_path.relative_to(hooks_dir_resolved)
        except ValueError:
            # Not under hooks dir — not our concern
            return {"passed": True, "skipped": True, "reason": "outside_hooks_dir"}

        # Extract hook name from filename (e.g., "my_hook.py" -> "my_hook")
        hook_name = resolved_path.stem

        # Validate hook name to prevent injection via path traversal
        try:
            from __lib.path_sanitizer import validate_hook_name

            validated = validate_hook_name(hook_name)
        except (ValueError, ImportError):
            # If validation fails or import fails, skip silently
            return {"passed": True, "skipped": True, "reason": "validation_failed"}

        # Clear the bytecode for this hook
        self._clear_hook_bytecode(validated, hooks_dir_resolved)

        # Invalidate Python's internal module finder cache
        # This ensures that if the module is already in sys.modules, the next
        # import will re-scan the filesystem rather than trusting stale metadata
        importlib.invalidate_caches()

        # Also remove from sys.modules if already loaded — forces fresh import
        # on next hook invocation
        if validated in sys.modules:
            del sys.modules[validated]

        # Also clean the parent package key if it exists (e.g., "posttooluse.my_hook")
        # to prevent import machinery from returning a stale package-level reference
        module_to_check = [
            k for k in sys.modules
            if k == validated or k.startswith(f"{validated}.")
        ]
        for mod in module_to_check:
            del sys.modules[mod]

        return {
            "passed": True,
            "metadata": {
                "hook_name": validated,
                "cache_cleared": True,
                "sys_modules_cleaned": len(module_to_check),
            },
        }