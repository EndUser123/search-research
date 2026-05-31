#!/usr/bin/env python3
"""TDD Contract Auto-Creation Hook.

When a TDD-requiring skill (/code, /tdd) is invoked, this hook auto-creates
a TDD contract in RED phase so PreToolUse_tdd_contract_gate.py can enforce
"write tests first" before allowing implementation edits.

Design principles:
- Multi-terminal safe via HookContext.terminal_id
- Non-blocking (only creates state, doesn't enforce)
- Bypass mechanism for legitimate opt-out
- No enforcement loops
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

# Add hooks directory for tdd module imports
hooks_dir = Path(__file__).resolve().parent.parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# TDD-requiring skills
TDD_REQUIRED_SKILLS = frozenset({"code", "tdd"})

# Bypass flags
TDD_BYPASS_FLAGS = frozenset({
    "--no-tdd", "--skip-tdd", "--bypass-tdd",
    "--no-test", "--bypass-test", "--bypass-contract"
})

# Environment variable bypass
TDD_CONTRACT_BYPASS_ENV = "TDD_CONTRACT_BYPASS"

# File extraction patterns for /code skill
CODE_FILE_RE = re.compile(
    r"^/code\s+(?:'([^']+)'|\"([^\"]+)\"|([^\s]+?)(?:\s|$))",
    re.IGNORECASE
)

# Simple file path pattern
IMPL_FILE_RE = re.compile(r"([a-zA-Z0-9_\-./\\]+\.py)")


def _is_tdd_bypassed(prompt: str) -> bool:
    """Check if user explicitly opted out of TDD enforcement."""
    normalized = prompt.strip().lower()
    for flag in TDD_BYPASS_FLAGS:
        if flag.lower() in normalized:
            return True

    if os.environ.get(TDD_CONTRACT_BYPASS_ENV) == "1":
        return True

    return False


def _extract_target_file(prompt: str, skill_name: str) -> str | None:
    """Extract the target implementation file from skill invocation.

    Args:
        prompt: User prompt text (e.g., "/code src/module.py --fast")
        skill_name: Skill name (code, tdd)

    Returns:
        Target file path string or None if cannot determine
    """
    normalized = prompt.strip()

    if skill_name == "code":
        # Try CODE_FILE_RE first
        match = CODE_FILE_RE.match(normalized)
        if match:
            for group in match.groups():
                if group and (group.endswith(".py") or "/" in group or "\\" in group):
                    return group
                elif group:
                    py_match = re.search(r"([a-zA-Z0-9_\-./\\]+\.py)", group)
                    if py_match:
                        return py_match.group(1)

        # Fallback: look for any .py file in prompt
        py_match = re.search(r"([a-zA-Z0-9_\-./\\]+\.py)", normalized)
        if py_match:
            return py_match.group(1)

    elif skill_name == "tdd":
        parts = normalized.split()
        if len(parts) >= 2:
            target = parts[1]
            if target.startswith("--"):
                target = parts[2] if len(parts) > 2 else ""
            if target and (target.endswith(".py") or "/" in target or "\\" in target):
                return target
            elif target:
                return f"src/{target}.py"

    return None


def _get_tdd_manager(context: HookContext):
    """Create TDDPhaseStateManager with terminal/session isolation."""
    from tdd.tdd_phase_state import TDDPhaseStateManager

    session_id = context.session_id or "default"
    terminal_id = context.terminal_id or "default"

    return TDDPhaseStateManager(
        session_id=session_id,
        terminal_id=terminal_id,
    )


@register_hook("tdd_contract_auto_gate", priority=2.0)
def tdd_contract_auto_gate(context: HookContext) -> HookResult:
    """Auto-create TDD contract when TDD-requiring skill is invoked.

    Priority 2.0 runs:
    - AFTER skill_enforcer (priority 1.0) has detected the command
    - BEFORE the Skill tool is actually called
    """
    # Check for bypass
    if _is_tdd_bypassed(context.prompt):
        return HookResult.empty()

    # Extract command name inline (avoid fragile cross-module import chain)
    command_match = re.match(r"^/(\w+)", context.prompt.strip())
    command = command_match.group(1) if command_match else None

    if not command or command.lower() not in TDD_REQUIRED_SKILLS:
        return HookResult.empty()

    # Extract target file
    target_file = _extract_target_file(context.prompt, command.lower())
    if not target_file:
        return HookResult.empty()

    # Create contract in RED phase
    try:
        manager = _get_tdd_manager(context)

        existing = manager.get_phase(target_file)
        if existing is not None:
            return HookResult.empty()

        manager.set_phase(target_file, "red")
    except Exception:
        pass

    return HookResult.empty()
