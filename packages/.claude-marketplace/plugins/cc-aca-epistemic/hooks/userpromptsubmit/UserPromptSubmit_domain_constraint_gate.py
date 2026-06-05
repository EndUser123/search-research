""""Domain constraint surfacing hook for UserPromptSubmit.

Fires on every user prompt. Detects domain context, queries CKS for matching
constraint entries, and injects them as additionalContext.
"""
from __future__ import annotations

import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

# --- plugin bootstrap ---
import sys as _s
from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

# Add search-research core to sys.path for domain_detector and backend
_SEARCH_ROOT = _P(__file__).resolve().parent.parent.parent.parent / "search-research"
_CORE_DIR = _SEARCH_ROOT / "core"
if str(_CORE_DIR) not in _s.path: _s.path.insert(0, str(_CORE_DIR))
_BACKEND_LOCAL = _SEARCH_ROOT / "core" / "backends" / "local"
if str(_BACKEND_LOCAL) not in _s.path: _s.path.insert(0, str(_BACKEND_LOCAL))

from UserPromptSubmit_modules.base import HookContext, HookResult
from domain_detector import detect_domain

_BACKEND_DOMAIN_CONSTRAINT = "domain_constraint"
_SEARCH_RESEARCH_ROOT = _P(__file__).resolve().parent.parent.parent.parent / "search-research"


def _safe_id(value):
    if not value: return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_constraint_state_path(terminal_id):
    state_dir = _hooks_dir / ".state"
    state_dir.mkdir(exist_ok=True)
    return state_dir / f"domain_constraints_{_safe_id(terminal_id)}.json"


def _build_constraint_context(domains, db_path=None, limit=5):
    try:
        from domain_constraint_backend import create_domain_constraint_backend
        backend = create_domain_constraint_backend(db_path=db_path)
        raw = backend.search(domains, limit=limit)
        if not raw: return None
        parts = ["[DOMAIN CONSTRAINTS]"]
        for r in raw:
            title = r.get("title") or "Constraint"
            content = (r.get("content") or "")[:300]
            parts.append("## " + title)
            parts.append(content)
        return chr(10).join(parts)
    except Exception:
        return None


def _run(context):
    prompt = context.prompt or ""
    terminal_id = context.terminal_id or "unknown"
    if not prompt.strip(): return HookResult.empty()
    dc = detect_domain(prompt)
    if not dc.has_constraints or dc.confidence < 0.6: return HookResult.empty()
    text = _build_constraint_context(dc.domains)
    if not text: return HookResult.empty()
    # Write state file
    state_path = _get_constraint_state_path(terminal_id)
    state = {
        "domains": dc.domains,
        "confidence": dc.confidence,
        "terminal_id": terminal_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
            f.flush()
            os.fsync(f.fileno())
    except Exception: pass
    tokens = len(text) // 4
    return HookResult(context=text, tokens=tokens, priority=0.4)


try:
    from UserPromptSubmit_modules.registry import register_hook
    register_hook("domain_constraint", priority=0.4)(_run)
except ImportError: pass
