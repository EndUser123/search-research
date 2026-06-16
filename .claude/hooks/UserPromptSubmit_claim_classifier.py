"""Claim classifier - writes claim_type state for downstream Stop gates.

Imports classify_claim from the cc-aca-epistemic plugin lib and writes state
to P:/.claude/hooks/.state/ — the location claim_type.py reads from.
Priority 0.5 — must run first so Stop gates see a populated claim_type file.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_EPISTEMIC_LIB = Path("P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib")
if str(_EPISTEMIC_LIB) not in sys.path:
    sys.path.insert(0, str(_EPISTEMIC_LIB))

# State files go to the global hooks dir so claim_type.py can read them
_HOOKS_DIR = Path(__file__).resolve().parent  # P:/.claude/hooks/


def _safe_id(value: str | None) -> str:
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_claim_type_path(terminal_id: str) -> Path:
    state_dir = _HOOKS_DIR / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"claim_type_{_safe_id(terminal_id)}.json"


def _run(context):
    claim_layer = importlib.import_module("claim_layer_map")
    claim_type = claim_layer.classify_claim(context.prompt or "")

    terminal_id = context.terminal_id or ""
    state = {
        "claim_type": claim_type,
        "session_id": context.session_id or "",
        "terminal_id": terminal_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt_excerpt": (context.prompt or "")[:100],
    }

    state_path = _get_claim_type_path(terminal_id)
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"[claim_classifier] Failed to write state: {e}", file=sys.stderr)

    return None  # empty result — this hook only writes state


try:
    registry = importlib.import_module("UserPromptSubmit_modules.registry")
    registry.register_hook("claim_classifier", priority=0.5)(_run)
except Exception:
    pass
