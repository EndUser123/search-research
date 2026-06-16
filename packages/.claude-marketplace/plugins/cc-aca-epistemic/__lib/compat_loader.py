"""Compatibility loader for cc-aca-epistemic plugin wrapper delegation.

Wrappers in P:/.claude/hooks/ delegate to plugin hooks via this module.
"""
from __future__ import annotations

from pathlib import Path


def delegate(wrapper_path: str) -> None:
    """Load and execute the corresponding plugin hook.

    Args:
        wrapper_path: Absolute path to the wrapper file calling this function

    The wrapper filename determines which plugin hook to load:
    - StopHook_*.py -> hooks/stop/StopHook_*.py
    - PreToolUse_*.py -> hooks/pretool/PreToolUse_*.py
    - etc.
    """
    wrapper_name = Path(wrapper_path).name

    # Map wrapper filename to plugin hook path
    # Wrappers use namespaced format: {hook}_{event}_{gate}.py
    # Plugin hooks are in hooks/{event}/{hook}_{event}_{gate}.py
    plugin_root = Path(__file__).resolve().parent.parent

    # Extract hook type from wrapper name
    # StopHook_cross_validator.py -> stop/StopHook_cross_validator.py
    # PreToolUse_evidence_hierarchy_gate.py -> pretool/PreToolUse_evidence_hierarchy_gate.py
    if wrapper_name.startswith("StopHook_"):
        event_dir = "stop"
        hook_name = wrapper_name  # StopHook_cross_validator.py
    elif wrapper_name.startswith("PreToolUse_"):
        event_dir = "pretool"
        hook_name = wrapper_name  # PreToolUse_evidence_hierarchy_gate.py
    elif wrapper_name.startswith("PostToolUse_"):
        event_dir = "posttool"
        hook_name = wrapper_name
    elif wrapper_name.startswith("UserPromptSubmit_"):
        event_dir = "userpromptsubmit"
        hook_name = wrapper_name
    else:
        raise ImportError(f"Unknown wrapper type: {wrapper_name}")

    hook_path = plugin_root / "hooks" / event_dir / hook_name

    if not hook_path.exists():
        raise ImportError(
            f"Plugin hook not found: {hook_path}"
            f"Wrapper: {wrapper_path}"
        )

    # Load and execute the plugin hook
    import runpy
    runpy.run_path(str(hook_path), run_name="__main__")
