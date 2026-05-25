#!/usr/bin/env python3
"""UserPromptSubmit hook: write expected skill directory to state file.

Phase 2 of the skill-dir correlation system:
  - Writer (this module): detects /skill-name in user prompt and writes
    the expected skill directory to a state file.
  - Gate (PreToolUse_skill_dir_gate.py): intercepts Glob/Grep and blocks
    unscoped searches that don't target the expected skill directory.

State file: P:/.claude/hooks/state/skill_context/skill_context_{terminal_id}.json

Registration: @register_hook("skill_context_writer", priority=8.0)
  Priority 8.0 ensures it runs BEFORE:
    - anti_sycophancy_injector (priority 9.0)
    - skill_enforcer (priority ~10.0)
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# Canonical definitions copied from Stop_skill_dir_correlation_gate.py
_SLASH_SKILL_RE = re.compile(r"/([a-z][a-z0-9-]{1,40})\b", re.IGNORECASE)
_NON_SKILL_NAMES = frozenset({
    "__lib",
    "__pycache__",
    "readme",       # lowercase — candidate is lowercased before check
    "skill_template",
    "skill_schema",
})

_HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Env guard
_ENABLED = os.environ.get("SKILL_CONTEXT_WRITER_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)

# State file location
_STATE_DIR = _HOOKS_DIR / "state" / "skill_context"

# Skill directory resolution paths
_LOCAL_SKILLS_DIR = Path(r"P:\.claude\skills")
_INSTALLED_PLUGINS_JSON = Path(r"C:\Users\brsth\.claude\plugins\installed_plugins.json")



def _resolve_skill_dir(skill_name: str) -> str | None:
    """Return the actual directory path for a skill, or None.

    Checks in order:
    1. Local skills (.claude/skills/)
    2. Plugin cache (installed_plugins.json)

    Returns a forward-slash normalized path string.
    """
    # 1. Local skill
    local_dir = _LOCAL_SKILLS_DIR / skill_name
    if local_dir.is_dir():
        return f".claude/skills/{skill_name}"

    # 2. Plugin cache
    try:
        data = json.loads(_INSTALLED_PLUGINS_JSON.read_text(encoding="utf-8"))
        plugins = data.get("plugins", {})
        for plugin_key, entries in plugins.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                install_path = entry.get("installPath", "")
                if not install_path:
                    continue
                skill_dir = Path(install_path) / "skills" / skill_name
                if skill_dir.is_dir():
                    return skill_dir.as_posix()
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    return None


def _build_valid_paths(
    skill_name: str, expected_dir: str, source_dir: str | None
) -> list[str]:
    """Build list of all valid path representations for a skill.

    Includes cache, source, and junction paths so the gate can match
    regardless of which path variant the LLM uses.
    """
    paths = [expected_dir.replace(chr(92), '/')]

    if source_dir:
        normalized_source = source_dir.replace(chr(92), '/')
        if normalized_source not in expected_dir:
            paths.append(normalized_source)

        # Derive junction: P:/packages/{plugin}/skills/{name}
        # -> P:/packages/.claude-marketplace/plugins/{plugin}/skills/{name}
        parts = normalized_source.split('/')
        if (
            len(parts) >= 5
            and parts[0] == 'P:'
            and parts[1] == 'packages'
            and parts[3] == 'skills'
        ):
            plugin_name = parts[2]
            junction = (
                f'P:/packages/.claude-marketplace/plugins/{plugin_name}'
                f'/skills/{skill_name}'
            )
            if junction not in paths and Path(junction).is_dir():
                paths.append(junction)

    return paths


def _resolve_source_dir(skill_name: str) -> str | None:
    """Return the source directory for a plugin skill, or None.

    Source is P:/packages/<plugin>/skills/<skill_name>/ for marketplace plugins.
    """
    marketplace_json = Path(r"P:/packages/.claude-marketplace/marketplace.json")
    try:
        data = json.loads(marketplace_json.read_text(encoding="utf-8"))
        for plugin in data.get("plugins", []):
            name = plugin.get("name", "")
            source = plugin.get("source", "")
            if not name or not source:
                continue
            # source format: "./plugins/<name>"
            if source.startswith("./plugins/"):
                plugin_name = source[len("./plugins/"):]
            else:
                continue
            skill_src = Path(f"P:/packages/{plugin_name}/skills/{skill_name}")
            if skill_src.is_dir():
                return str(skill_src).replace("/", "\\").replace("\\", "/")
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return None


def _safe_id(value: str) -> str:
    """Sanitize a string for use in filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _skill_context_path(terminal_id: str) -> Path:
    """Return the path to the skill context state file for the given terminal."""
    safe_tid = _safe_id(terminal_id or "default")
    return _STATE_DIR / f"skill_context_{safe_tid}.json"


def _extract_skill_from_prompt(prompt: str) -> str | None:
    """Detect /skill-name in prompt and return the skill name, or None.

    Returns the skill name (lowercased) if found and not a false positive.
    False positives excluded:
      - Single-character candidates (len <= 1)
      - Names in _NON_SKILL_NAMES
    """
    m = _SLASH_SKILL_RE.search(prompt)
    if not m:
        return None
    candidate = m.group(1).lower()
    if len(candidate) <= 1:
        return None
    if candidate in _NON_SKILL_NAMES:
        return None
    return candidate


def _write_atomic(state_file: Path, data: dict) -> None:
    """Atomically write data to state_file using temp-file + os.replace()."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(_STATE_DIR),
        prefix=".tmp_skill_context_",
        suffix=".json",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, separators=(",", ":"))
        os.replace(tmp_path, state_file)
    except Exception:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _delete_if_exists(state_file: Path) -> None:
    """Delete state file if it exists (no error if missing)."""
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass


@register_hook("skill_context_writer", priority=8.0)
def skill_context_writer(context: HookContext) -> HookResult:
    """Detect /skill-name in user prompt and persist expected skill dir to state file."""
    if not _ENABLED:
        return HookResult.empty()

    # Extract prompt text from context
    prompt = context.prompt or ""
    terminal_id = context.terminal_id or os.environ.get("CLAUDE_TERMINAL_ID", "default")
    session_id = context.session_id or ""

    skill_name = _extract_skill_from_prompt(prompt)
    state_file = _skill_context_path(terminal_id)

    if skill_name:
        # Resolve actual skill directory (local or plugin cache)
        resolved_dir = _resolve_skill_dir(skill_name)
        source_dir = _resolve_source_dir(skill_name)

        # Prefer resolved cache path, then source path, then local fallback
        if resolved_dir:
            expected_dir = resolved_dir
        elif source_dir:
            expected_dir = source_dir
        else:
            expected_dir = f".claude/skills/{skill_name}"

        valid_paths = _build_valid_paths(skill_name, expected_dir, source_dir)

        data = {
            "expected_skill": skill_name,
            "expected_dir": expected_dir,
            "source_dir": source_dir or "",
            "valid_paths": valid_paths,
            "resolved": resolved_dir is not None,
            "session_id": session_id,
            "terminal_id": terminal_id,
        }
        try:
            _write_atomic(state_file, data)
        except Exception:
            pass  # Fail open — state file error must not affect prompt processing
    else:
        # No skill in prompt — clear state file if it exists
        _delete_if_exists(state_file)

    return HookResult.empty()
