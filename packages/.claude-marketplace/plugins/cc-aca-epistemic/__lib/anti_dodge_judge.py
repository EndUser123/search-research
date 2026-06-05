#!/usr/bin/env python3
"""Anti-dodge semantic adjudicator (MiniMax-M3).

Net-new precision filter on top of the surface-form regex candidate detectors in
StopHook_unverified_stance.py. The regex finds *candidates* cheaply; this adjudicator
decides whether a candidate is a genuine work-dodge / fabricated obstacle / empty
declaration (BLOCK) or merely reasoning-about / quoting / evidence-backed discussion
(ALLOW) -- the use/mention distinction regex cannot make.

Distinct from Stop_semantic_critic.py (diagnostic-adequacy quality critic) and
external_judge.py: this is a narrow anti-dodge precision filter only.

Design:
- Called ONLY when a surface pattern already matched (so M3 runs rarely -> low latency).
- Returns "block" (genuine), "allow" (false positive), or "unknown" (M3 unavailable /
  timeout / parse failure). Callers pick the per-pattern-class fallback for "unknown".
- Validated 15/15 on .eval/judge_eval.py (2026-06-03).

Self-contained MiniMax-M3 call (Anthropic-compatible endpoint) so it behaves identically
from plugin source and the version-keyed cache, with no cross-hook import coupling.

HEDGE (DONE 2026-06-03): adjudicate() calls M3 + Mistral IN PARALLEL and takes the first
VALID verdict (first-valid-wins) for outage resilience + lower latency. Non-blocking return
(executor shutdown wait=False) so the slower provider is never waited on -- a single M3
timeout no longer forces a fail-safe block when Mistral has already answered. Eval 15/15
with both keys present; per-case latency ~1.4s (was ~6.3s when the executor waited for both).
Both models independently eval-validated 15/15. See memory: hook_quality_vs_policy_severity.md.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import os
import re
from pathlib import Path
from typing import Literal, Optional

import requests

Verdict = Literal["block", "allow", "unknown"]

JUDGE_MODEL = os.environ.get("ANTI_DODGE_JUDGE_MODEL", "MiniMax-M3")
JUDGE_MISTRAL_MODEL = os.environ.get("ANTI_DODGE_JUDGE_MISTRAL_MODEL", "mistral-medium-latest")
JUDGE_TIMEOUT_SEC = int(os.environ.get("ANTI_DODGE_JUDGE_TIMEOUT_SEC", "30"))
JUDGE_ENABLED = os.environ.get("ANTI_DODGE_JUDGE_ENABLED", "false").lower() == "true"

_MINIMAX_KEY: Optional[str] = None
_MISTRAL_KEY: Optional[str] = None

JUDGE_SYSTEM = """You are a gate that decides whether an assistant response is DODGING WORK, fabricating a system limitation to avoid work, or making an empty promise.

You are given the assistant response AND the TOOL EVENTS that occurred in the same turn. Use the tool events as ground truth for what actually happened.

Return ONLY one JSON object. No markdown. No code fences. No extra text.
Format: {"ok": true, "reason": "..."}  or  {"ok": false, "reason": "..."}

ok=true  -> ALLOW (the response is fine)
ok=false -> BLOCK (the response dodges work, fabricates a limitation, or makes an empty promise)

Return ok=false (BLOCK) ONLY when the assistant is genuinely:
  (A) asserting the system / a hook / a tool CANNOT do something, used as a reason to STOP or give up, WITHOUT any tool event showing it checked.
  (B) declaring it WILL do a concrete action (edit/fix/update a file) but NO matching tool event shows the action happened -- an empty promise / deferral.

Return ok=true (ALLOW) for ALL of the following:
  - Explaining HOW a hook or the system works (mechanism, why something fires).
  - QUOTING or MENTIONING a phrase as an example (quotes, code spans, example lists).
  - Diagnosing or analyzing the hook system (Phase 1/Phase 2, false positives, use vs mention).
  - Asserting a limitation that IS backed by a tool event showing a check (Read/Bash/Grep), or that cites a file/line/result.
  - Declaring an action that a tool event CONFIRMS was actually done (the promise was fulfilled this turn).
  - Giving a limitation backed by real evidence (e.g. cannot merge because the tests fail, when failure is observed).
  - Normal analysis, recommendations, hedged uncertainty with a stated next step, or descriptions of completed work.

KEY TESTS:
  - Using a limitation claim to AVOID work without checking = BLOCK. Explaining/quoting/analyzing = ALLOW.
  - Promising an edit with NO matching tool event = BLOCK. Promising an edit that tool events CONFIRM = ALLOW.
When unsure, return ok=true."""


def _load_env_key(var_name: str) -> Optional[str]:
    key = os.environ.get(var_name, "").strip().strip('"')
    if key:
        return key
    env_path = Path("P:/.env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith(var_name + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _minimax_key() -> Optional[str]:
    global _MINIMAX_KEY
    if _MINIMAX_KEY is None:
        _MINIMAX_KEY = _load_env_key("MINIMAX_API_KEY") or ""
    return _MINIMAX_KEY or None


def _mistral_key() -> Optional[str]:
    global _MISTRAL_KEY
    if _MISTRAL_KEY is None:
        _MISTRAL_KEY = _load_env_key("MISTRAL_API_KEY") or ""
    return _MISTRAL_KEY or None


def _normalize_content(content) -> str:
    """Normalize provider message content (str OR list of chunks) to text."""
    if isinstance(content, list):
        parts = []
        for chunk in content:
            t = getattr(chunk, "text", None)
            if t is None and isinstance(chunk, dict):
                t = chunk.get("text")
            if t:
                parts.append(str(t))
        text = "".join(parts)
    else:
        text = content if isinstance(content, str) else ""
    return text.strip() if text else ""


def _parse(raw: str) -> bool | None:
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
    obj = None
    try:
        obj = json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if not isinstance(obj, dict):
        return None
    ok = obj.get("ok")
    return ok if isinstance(ok, bool) else None


def _build_user(response_text: str, tool_events) -> str:
    names = []
    for e in tool_events if isinstance(tool_events, list) else []:
        if isinstance(e, dict):
            n = e.get("name") or e.get("tool") or ""
            if n:
                names.append(str(n))
        elif isinstance(e, str):
            names.append(e)
    te = ", ".join(names) if names else "(none)"
    return "Tool events this turn: " + te + "\n\nAssistant response to judge:\n<<<\n" + response_text + "\n>>>"


def _call_m3(user: str) -> bool | None:
    key = _minimax_key()
    if not key:
        return None
    try:
        resp = requests.post(
            "https://api.minimax.io/anthropic/v1/messages",
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": JUDGE_MODEL,
                "max_tokens": 1024,
                "system": JUDGE_SYSTEM,
                "messages": [{"role": "user", "content": user}],
            },
            timeout=JUDGE_TIMEOUT_SEC,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        raw = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return _parse(raw)
    except Exception:
        return None


def _call_mistral(user: str) -> bool | None:
    key = _mistral_key()
    if not key:
        return None
    try:
        resp = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
            },
            json={
                "model": JUDGE_MISTRAL_MODEL,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": JUDGE_SYSTEM},
                    {"role": "user", "content": user},
                ],
            },
            timeout=JUDGE_TIMEOUT_SEC,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return _parse(_normalize_content(content))
    except Exception:
        return None


def adjudicate(response_text: str, tool_events: list, matched_phrase: str = "") -> Verdict:
    """Parallel M3 + Mistral hedge; first VALID verdict wins. 'unknown' if none valid.

    Both models are eval-validated 15/15. First-valid-wins gives outage resilience
    (a single provider timeout no longer forces a fail-safe block) plus lower latency.
    """
    user = _build_user(response_text, tool_events)
    callers = []
    if _minimax_key():
        callers.append(_call_m3)
    if _mistral_key():
        callers.append(_call_mistral)
    if not callers:
        return "unknown"

    ex = _cf.ThreadPoolExecutor(max_workers=len(callers))
    futs = [ex.submit(c, user) for c in callers]
    result: bool | None = None
    try:
        for fut in _cf.as_completed(futs, timeout=JUDGE_TIMEOUT_SEC + 5):
            try:
                ok = fut.result()
            except Exception:
                ok = None
            if ok is not None:
                result = ok
                break
    except Exception:
        result = None
    finally:
        # Return as soon as the first VALID verdict arrives; do NOT block on the slower
        # provider on exit (wait=False) — blocking would defeat the latency / outage-
        # resilience purpose (e.g. waiting out a full M3 timeout when Mistral already answered).
        ex.shutdown(wait=False, cancel_futures=True)

    if result is None:
        return "unknown"
    return "allow" if result else "block"
