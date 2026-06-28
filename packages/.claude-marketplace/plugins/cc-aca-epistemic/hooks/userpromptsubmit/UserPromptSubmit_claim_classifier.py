"""Claim classifier for UserPromptSubmit - classifies prompt type for conditional routing.

This hook runs at UserPromptSubmit to classify the user prompt into a claim type.
The claim_type is written to .state/claim_type_{terminal}.json so downstream hooks
and Stop gates can use it for short-circuit decisions.

Priority: 0.5 (runs FIRST, before other hooks)
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add hooks dir to path for __lib imports
_HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext, HookResult

# Import the shared claim classifier
from claim_layer_map import classify_claim


def _safe_id(value: str | None) -> str:
    """Convert session/terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_claim_type_path(terminal_id: str) -> Path:
    """Return path to claim type state file."""
    state_dir = Path(os.environ.get("CSF_STATE_DIR") or str(Path("P:/") / ".claude" / "state")) / "cc-aca-epistemic"
    state_dir.mkdir(parents=True, exist_ok=True)
    safe_id = _safe_id(terminal_id)
    return state_dir / f"claim_type_{safe_id}.json"


def _run(context: HookContext) -> HookResult:
    """Classify the user prompt and write claim type to state file."""
    prompt = context.prompt or ""
    session_id = context.session_id or ""
    terminal_id = context.terminal_id or ""

    # Classify the prompt
    claim_type = classify_claim(prompt)

    # Build state file content
    state = {
        "claim_type": claim_type,
        "session_id": session_id,
        "terminal_id": terminal_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_excerpt": prompt[:100] if prompt else "",
    }

    # Write to state file - CRITICAL: ensure immediate persistence
    state_path = _get_claim_type_path(terminal_id)
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        # Non-blocking - log error but don't fail
        print(f"[claim_classifier] Failed to write state: {e}", file=sys.stderr)

    # Return empty result - this hook only writes state, doesn't inject context
    return HookResult.empty()


# Register with registry (runs first, priority 0.5)
try:
    from UserPromptSubmit_modules.registry import register_hook
    register_hook("claim_classifier", priority=0.5)(_run)
except ImportError:
    pass