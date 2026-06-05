#!/usr/bin/env python3
"""Closed-loop recommendation-rubric reinforcement (gate -> LLM judge -> next-turn correction).

Replaces the prior regex pair (recommendation_intent + recommendation_compliance_recorder +
static rubric injector). A MiniMax-judged base rate of 48% non-compliance over genuine
recommendation turns (measured 2026-06-01) showed the static regex injector was not producing
compliant comparative recommendations. This module closes the loop:

  1. record_at_stop(data): cheap recall gate on the user prompt; if it could be a
     recommendation turn, spawn a DETACHED subprocess to judge it (so Stop never blocks).
     The subprocess writes a one-line correction to a terminal-scoped state file IFF the
     turn was a genuine recommendation that missed the rubric.
  2. consume_pending_correction(): UserPromptSubmit reads + clears that correction next turn.

External LLM use complies with hook_external_llm_policy.md (fail-open: no key / error /
timeout -> silent no-op). Disable via RECOMMENDATION_JUDGE_ENABLED=false.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state")) / "recommendation_loop"
_JUDGE_TIMEOUT_S = 20


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", s)[:80]


# NOTE: Not using shared_utils.resolve_session_id() / terminal_detection.resolve_terminal_key()
# because this module is kept stdlib-only (zero local-lib imports) to remain plugin-portable.
# The payload extraction below mirrors what Stop.py already does for session/terminal id.
def _scope_key(data: dict | None) -> str:
    """Isolation key for a conversation/terminal, resolved from the hook payload.

    Prefers session_id (always present in the Claude Code hook payload and unique per
    conversation -> unique per terminal), then payload terminal_id, then WT_SESSION.
    Makes BOTH multi-terminal isolation AND cross-session staleness immunity event-based
    (different conversation -> different key -> different file): no clock, no dependency on
    a possibly-absent CLAUDE_TERMINAL_ID env. Returns "" only if no identity resolvable.
    """
    d = data or {}
    raw = (
        d.get("session_id") or d.get("sessionId") or d.get("CLAUDE_SESSION_ID")
        or d.get("terminal_id") or d.get("terminalId") or d.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("WT_SESSION") or ""
    )
    return _safe(str(raw).strip())


# Public alias for cross-module use (injector resolves the key from its own payload).
scope_key = _scope_key


def _pending_path(key: str) -> Path:
    return _STATE_DIR / f"pending_correction_{key}.json"


# Recall-oriented gate (cost control only; the JUDGE is the real detector). False positives
# are harmless: the judge returns is_recommendation=false and no correction is written.
_RECALL = re.compile(
    r"\b(optimal|best\s+(?:way|approach|option|solution|choice|path|design|practice)|"
    r"what'?s?\s+the\s+best|recommend|recommendation|highest[\s-]roi|next\s+highest|"
    r"which\s+(?:option|approach|one|path|design|is\s+better)|should\s+(?:we|i)\b|"
    r"\bbetter\b|worth\s+it|what\s+should\s+(?:we|i)|what\s+do\s+you\s+think)\b",
    re.IGNORECASE,
)


def _gate(prompt: str) -> bool:
    return bool(prompt) and bool(_RECALL.search(prompt))


_SYS = (
    "You judge whether an assistant's answer to a recommendation / 'best option' / "
    "'highest-ROI' question follows this rubric: it names AT LEAST TWO viable options AND "
    "states the selection criterion (the axis being optimized) AND says why the chosen option "
    "wins on that axis. Tables, prose, or bullets all count. If the user's question was NOT "
    "actually asking for a recommendation or decision, set is_recommendation=false. "
    "Reply STRICT JSON only: "
    '{"is_recommendation": true|false, "compliant": true|false, '
    '"correction": "<one specific sentence telling the assistant what to add next time, empty if compliant>"}.'
)


def _load_key():
    k = os.environ.get("MINIMAX_API_KEY", "").strip().strip('"')
    if k:
        return k
    env = Path("P:/.env")
    if env.exists():
        try:
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("MINIMAX_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"')
        except OSError:
            return None
    return None


def _parse_judge(text: str):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(0))
    except (ValueError, TypeError):
        return None
    return {
        "is_recommendation": bool(j.get("is_recommendation")),
        "compliant": bool(j.get("compliant")),
        "correction": str(j.get("correction", "")).strip()[:400],
    }


def judge(prompt: str, response: str):
    """Call MiniMax to judge rubric compliance. Returns verdict dict or None (fail-open)."""
    key = _load_key()
    if not key:
        return None
    try:
        import requests
    except ImportError:
        return None
    body = {
        "model": "MiniMax-M3",
        "max_tokens": 1200,  # M3 emits a thinking block first; needs headroom for the JSON
        "system": _SYS,
        "messages": [{
            "role": "user",
            "content": f"USER QUESTION:\n{prompt[:800]}\n\nASSISTANT ANSWER:\n{response[:4000]}",
        }],
    }
    try:
        resp = requests.post(
            "https://api.minimax.io/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json=body,
            timeout=_JUDGE_TIMEOUT_S,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return _parse_judge(text)
    except Exception:
        return None


def _job_path(key: str) -> Path:
    # One job file per scope, overwritten each Stop -> newest-wins supersede (no clock,
    # no orphan accumulation). Obsolete judge requests are replaced, not time-swept.
    return _STATE_DIR / f"job_{key}.json"


def _write_correction(correction: str, key: str) -> None:
    if not key:
        return
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _pending_path(key).write_text(
            json.dumps({"correction": correction}), encoding="utf-8",
        )
    except OSError:
        pass


def consume_pending_correction(key: str):
    """Read + delete this scope's pending correction. Single-use; None if absent/corrupt.

    Staleness is structural, not time-based: a correction lives under its originating
    conversation's scope key, so a different session/terminal can never read it, and the
    same scope reads it exactly once (deleted on read) before any newer Stop overwrites it.
    """
    if not key:
        return None
    p = _pending_path(key)
    try:
        if not p.exists():
            return None
        obj = json.loads(p.read_text(encoding="utf-8"))
        p.unlink(missing_ok=True)
    except (OSError, ValueError):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    corr = str(obj.get("correction", "")).strip()
    return corr or None


def _enabled() -> bool:
    return os.environ.get("RECOMMENDATION_JUDGE_ENABLED", "true").lower() != "false"


def record_at_stop(data: dict) -> None:
    """Stop-side entry: gate, then spawn a DETACHED judge subprocess (never blocks Stop)."""
    if not _enabled():
        return
    key = _scope_key(data)
    if not key:
        return  # cannot isolate -> do nothing (no shared 'default' bucket)
    prompt = data.get("user_prompt") or data.get("prompt") or ""
    response = data.get("response") or data.get("raw_response") or ""
    if not _gate(prompt) or len(response) < 120:
        return
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        job = _job_path(key)  # overwrite supersedes any prior un-run job for this scope
        job.write_text(json.dumps({
            "prompt": prompt, "response": response, "scope_key": key,
        }), encoding="utf-8")
        import subprocess
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP on Windows; 0 (no-op) on POSIX.
        creationflags = (0x00000008 | 0x00000200) if os.name == "nt" else 0
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--judge-job", str(job)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )
    except Exception:
        pass  # fail-open: no correction this turn


def _run_job(job_path: str) -> None:
    """Subprocess entry: judge one (prompt,response) job and persist a correction if warranted."""
    try:
        jp = Path(job_path)
        job = json.loads(jp.read_text(encoding="utf-8"))
        jp.unlink(missing_ok=True)
    except (OSError, ValueError):
        return
    key = str(job.get("scope_key", "")).strip()
    verdict = judge(job.get("prompt", ""), job.get("response", ""))
    if not verdict:
        return
    if verdict["is_recommendation"] and not verdict["compliant"] and verdict["correction"]:
        msg = (
            "Reminder from the last recommendation turn - it missed the rubric: "
            f"{verdict['correction']} "
            "When recommending, name >=2 viable options, the selection criterion, and why the winner wins."
        )
        _write_correction(msg, key)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--judge-job":
        _run_job(sys.argv[2])
