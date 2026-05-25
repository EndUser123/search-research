#!/usr/bin/env python3
"""PostToolUse Hook - SQA Phase Tracker.

Tracks layer-specific tool invocations during SQA execution windows.
Detects when characteristic tools for each layer are invoked (or NOT invoked).

SQA Layer -> Tool Mapping:
  L1_SYNTACTIC    -> ruff, mypy
  L2_SEMANTIC     -> verify, diagnose
  L3_STRUCTURAL   -> meta-review, harden
  L4_REQUIREMENTS  -> gto, spec-compliance
  L5_SECURITY     -> adversarial-security, adversarial-performance
  L6_PERFORMANCE   -> perf
  L7_OPERATIONAL   -> hook-audit, hook-inventory

Execution window detection:
  - Bash command matches SQA invocation pattern (python orchestrator.py, sqa skill, etc.)
  - Layer marker file written by orchestrator during _run_layer()

Characteristic tool detection:
  - After each Bash tool, check if cmd matches current layer's characteristic tools
  - If a layer completes without any characteristic tool invocations, warn

Environment Variables:
  - SQA_PHASE_TRACKER_ENABLED: Enable/disable (default: true)
  - SQA_PHASE_TRACKER_STATE_DIR: State directory (default: .claude/state/sqa_phase/)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path for imports
hooks_root = Path(__file__).resolve().parent.parent
if str(hooks_root) not in sys.path:
    sys.path.insert(0, str(hooks_root))

hooks_lib = hooks_root / "__lib"
if str(hooks_lib) not in sys.path:
    sys.path.insert(0, str(hooks_lib))

from posttooluse.base import PostToolUseHook

# ---------------------------------------------------------------------------
# Layer -> Characteristic Tools mapping
# ---------------------------------------------------------------------------

SQA_LAYER_TOOLS: dict[str, list[str]] = {
    "L1_SYNTACTIC": ["ruff", "mypy"],
    "L2_SEMANTIC": ["verify", "diagnose"],
    "L3_STRUCTURAL": ["meta-review", "harden"],
    "L4_REQUIREMENTS": ["gto", "spec-compliance"],
    "L5_SECURITY": ["adversarial-security", "adversarial-performance"],
    "L6_PERFORMANCE": ["perf"],
    "L7_OPERATIONAL": ["hook-audit", "hook-inventory"],
}

# SQA invocation patterns (Bash commands that start an SQA run)
SQA_INVOCATION_PATTERNS = [
    re.compile(r"python.*orchestrator\.py", re.IGNORECASE),
    re.compile(r"\bsqa\b", re.IGNORECASE),
    re.compile(r"csf-analyze", re.IGNORECASE),
    re.compile(r"csf-batch", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

_SQA_PHASE_TRACKER_STATE_DIR: str | None = None


def _get_state_dir() -> Path:
    """Get state directory for phase tracker."""
    global _SQA_PHASE_TRACKER_STATE_DIR
    if _SQA_PHASE_TRACKER_STATE_DIR:
        return Path(_SQA_PHASE_TRACKER_STATE_DIR)

    env_dir = os.environ.get("SQA_PHASE_TRACKER_STATE_DIR")
    if env_dir:
        _SQA_PHASE_TRACKER_STATE_DIR = env_dir
        return Path(env_dir)

    # Default: hooks state directory
    hook_file = Path(__file__).resolve()
    # P:/.claude/hooks/posttooluse/posttooluse_sqa_phase_tracker.py
    # -> P:/.claude/hooks/posttooluse
    # -> P:/.claude/hooks
    # -> P:/.claude
    claude_root = hook_file.parent.parent.parent
    state_dir = claude_root / "state" / "sqa_phase"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _get_terminal_id() -> str:
    """Get terminal ID for isolation."""
    try:
        from __lib.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except (ImportError, AttributeError, OSError):
        return "default"


def _get_layer_marker_path() -> Path:
    """Get path to layer marker file (written by orchestrator)."""
    terminal_id = _get_terminal_id()
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", terminal_id) or "default"
    return _get_state_dir() / f"layer_marker_{safe_id}.json"


def _get_invocation_state_path() -> Path:
    """Get path to invocation tracking state file."""
    terminal_id = _get_terminal_id()
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", terminal_id) or "default"
    return _get_state_dir() / f"invocation_state_{safe_id}.json"


def _is_sqa_invocation(cmd: str) -> bool:
    """Check if command is a SQA invocation."""
    for pattern in SQA_INVOCATION_PATTERNS:
        if pattern.search(cmd):
            return True
    return False


def _extract_layer_from_marker() -> str | None:
    """Read current layer from marker file (written by orchestrator)."""
    marker_path = _get_layer_marker_path()
    if not marker_path.exists():
        return None
    try:
        data = json.loads(marker_path.read_text())
        return data.get("layer")
    except (json.JSONDecodeError, OSError):
        return None


def _write_layer_marker(layer: str | None) -> None:
    """Write layer marker file (called by orchestrator during _run_layer)."""
    marker_path = _get_layer_marker_path()
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(json.dumps({"layer": layer}))
    except OSError:
        pass


def _get_layer_for_tool(cmd: str) -> str | None:
    """Find which SQA layer a command belongs to."""
    cmd_name = cmd.split()[0] if isinstance(cmd, str) else str(cmd)
    cmd_lower = cmd_name.lower()
    for layer, tools in SQA_LAYER_TOOLS.items():
        for tool in tools:
            if tool in cmd_lower:
                return layer
    return None


def _load_invocation_state() -> dict[str, Any]:
    """Load invocation tracking state."""
    state_path = _get_invocation_state_path()
    if not state_path.exists():
        return {"sqa_active": False, "layers_invoked": {}, "characteristic_invoked": set()}
    try:
        data = json.loads(state_path.read_text())
        # Ensure required keys exist
        data.setdefault("sqa_active", False)
        data.setdefault("layers_invoked", {})
        data.setdefault("characteristic_invoked", set())
        return data
    except (json.JSONDecodeError, OSError):
        return {"sqa_active": False, "layers_invoked": {}, "characteristic_invoked": set()}


def _save_invocation_state(state: dict[str, Any]) -> None:
    """Save invocation tracking state."""
    state_path = _get_invocation_state_path()
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert set to list for JSON serialization
        serializable = {k: (list(v) if isinstance(v, set) else v) for k, v in state.items()}
        state_path.write_text(json.dumps(serializable, indent=2))
    except OSError:
        pass


def _is_characteristic_tool(layer: str, cmd: str) -> bool:
    """Check if cmd is a characteristic tool for the given layer."""
    if layer not in SQA_LAYER_TOOLS:
        return False
    cmd_lower = cmd.lower()
    for tool in SQA_LAYER_TOOLS[layer]:
        if tool in cmd_lower:
            return True
    return False


# ---------------------------------------------------------------------------
# Public helper - called by orchestrator to write layer marker
# ---------------------------------------------------------------------------

def write_layer_marker(layer: str | None) -> None:
    """Public API for orchestrator to write layer marker.

    Usage in orchestrator.py:
        from posttooluse_sqa_phase_tracker import write_layer_marker
        write_layer_marker("L1_SYNTACTIC")  # Before running layer
        write_layer_marker(None)             # After all layers complete
    """
    _write_layer_marker(layer)


# ---------------------------------------------------------------------------
# PostToolUse Hook
# ---------------------------------------------------------------------------

class SQAPhaseTrackerHook(PostToolUseHook):
    """
    Tracks SQA layer execution and warns if characteristic tools are not invoked.

    This hook monitors Bash tool executions during SQA runs and detects:
    1. When SQA execution window starts/ends
    2. Which layer is currently active (via layer marker file)
    3. Whether characteristic tools for each layer were invoked

    If a layer completes without any characteristic tool invocations, a warning
    is injected into the context to alert the user.
    """

    env_var = "SQA_PHASE_TRACKER_ENABLED"
    default_enabled = True
    tool_matcher = {"Bash"}

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """Process Bash tool execution for SQA phase tracking."""
        if tool_name != "Bash":
            return {}

        cmd: str = tool_input.get("command", "")
        if not isinstance(cmd, str):
            return {}

        # Check if this is an SQA invocation (starts a new SQA run)
        if _is_sqa_invocation(cmd):
            state = _load_invocation_state()
            state["sqa_active"] = True
            state["layers_invoked"] = {}
            state["characteristic_invoked"] = set()
            _save_invocation_state(state)
            return {}

        # Check current layer from marker
        current_layer = _extract_layer_from_marker()

        # Load current state
        state = _load_invocation_state()

        # If no SQA active and no layer marker, nothing to do
        if not state["sqa_active"] and not current_layer:
            return {}

        # Track characteristic tool invocations
        if current_layer and _is_characteristic_tool(current_layer, cmd):
            char_set = set(state.get("characteristic_invoked", []))
            char_set.add(current_layer)
            state["characteristic_invoked"] = char_set

            # Track per-layer invocations too
            layers_invoked = dict(state.get("layers_invoked", {}))
            if current_layer not in layers_invoked:
                layers_invoked[current_layer] = []
            layers_invoked[current_layer].append(cmd.split()[0] if " " in cmd else cmd)
            state["layers_invoked"] = layers_invoked
            _save_invocation_state(state)
            return {}

        # Check if layer is ending (marker changed to different layer or None)
        # This is a simplified check - we warn if the previous layer had no characteristic tools
        prev_layer = state.get("last_layer")
        if prev_layer and prev_layer != current_layer:
            char_invoked = set(state.get("characteristic_invoked", []))
            if prev_layer not in char_invoked:
                # Previous layer had no characteristic tool invocations - warn
                layer_tools = SQA_LAYER_TOOLS.get(prev_layer, [])
                warning = (
                    f"\n\n[SQA PHASE TRACKER] Layer {prev_layer} completed "
                    f"without invoking any characteristic tools: {layer_tools}\n"
                    f"This may indicate the layer analysis was skipped or ran without expected tools."
                )
                # Clear the flag for this layer since we warned
                char_invoked.add(prev_layer)
                state["characteristic_invoked"] = char_invoked
                _save_invocation_state(state)
                return {"injection": warning}

        # Update last seen layer
        if current_layer:
            state["last_layer"] = current_layer
            _save_invocation_state(state)

        return {}

    def on_sqa_complete(self) -> dict[str, Any]:
        """Call when SQA run completes (end of execution window).

        Returns warning dict if any layer had no characteristic tool invocations.
        This can be called by orchestrator after all layers complete.
        """
        state = _load_invocation_state()
        if not state["sqa_active"]:
            return {}

        char_invoked = set(state.get("characteristic_invoked", []))
        warnings: list[str] = []

        for layer in SQA_LAYER_TOOLS:
            if layer not in char_invoked:
                layer_tools = SQA_LAYER_TOOLS.get(layer, [])
                warnings.append(
                    f"  {layer}: no characteristic tools invoked "
                    f"(expected: {', '.join(layer_tools)})"
                )

        # Reset state
        state["sqa_active"] = False
        state["characteristic_invoked"] = set()
        state["layers_invoked"] = {}
        state["last_layer"] = None
        _save_invocation_state(state)

        if warnings:
            header = "\n\n[SQA PHASE TRACKER] SQA Run Complete - Missing Characteristic Tools:\n"
            return {"injection": header + "\n".join(warnings)}

        return {}
