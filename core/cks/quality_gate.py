#!/usr/bin/env python3
"""CKS capture-side quality gate.

Judges every candidate CKS entry (decision, correction, memory chunk) BEFORE
ingest, using cheap models (MiniMax-M3 + Mistral in parallel, first-valid-wins
— same hedge pattern as cc-aca-epistemic anti_dodge_judge.py, validated there).

Why an LLM judge and not a regex: measured 2026-07-03 that a title regex passes
86/104 known-junk decision fragments — surface form does not discriminate.

Verdicts:
  "accept"  — entry is self-contained, reusable knowledge; ingest it.
  "reject"  — fragment / context-free / not reusable; drop it, log to reject stream.
  "unknown" — no provider reachable; FAIL-OPEN (ingest) but log the bypass.

Calibration contract (CLAUDE.md: every enforcement gate ships with
measured_tp_on_corpus before it can block): run calibrate_quality_gate.py.
"""
from __future__ import annotations

import concurrent.futures as _cf
import json
import os
import re
import time
from pathlib import Path
from typing import Literal, Optional

import requests

Verdict = Literal["accept", "reject", "unknown"]

GATE_ENABLED = os.environ.get("CKS_QUALITY_GATE_ENABLED", "true").lower() in ("1", "true", "yes")
JUDGE_M3_MODEL = os.environ.get("CKS_QUALITY_GATE_M3_MODEL", "MiniMax-M3")
JUDGE_MISTRAL_MODEL = os.environ.get("CKS_QUALITY_GATE_MISTRAL_MODEL", "mistral-medium-latest")
JUDGE_TIMEOUT_SEC = int(os.environ.get("CKS_QUALITY_GATE_TIMEOUT_SEC", "30"))

REJECT_LOG = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state")) / "cks_quality_gate_rejects.jsonl"

JUDGE_SYSTEM = """You are a quality gate for a PERSISTENT knowledge base used by a coding assistant.
Each candidate entry will be re-read months later, in a fresh session, with zero surrounding context.

Return ONLY one JSON object. No markdown. No code fences. No extra text.
Format: {"ok": true, "reason": "..."} or {"ok": false, "reason": "..."}

ok=true  -> ACCEPT: store the entry.
ok=false -> REJECT: drop the entry.

ACCEPT only when ALL hold:
  - The TITLE is a self-contained statement (a reader who sees only the title knows the topic).
  - The CONTENT states a reusable fact, decision, correction, or procedure AND enough context to apply it later.
  - Someone solving a similar problem months from now would benefit from retrieving this.

REJECT when ANY hold:
  - The title is a mid-sentence fragment (e.g. "(req 6)", "waits on task #1052.", "does NOT hold yet, because...").
  - The content depends on session-local referents that are not explained (task numbers, "the file above", "option A") — the entry is meaningless without the original conversation.
  - It records transient status ("still running", "awaiting user approval") rather than durable knowledge.
  - It is an empty template, placeholder, or trivially short.

When unsure, return ok=false — pollution is worse than one lost entry.
"""


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


def _build_user(title: str, content: str, entry_type: str) -> str:
    content = (content or "")[:3000]
    return f"Entry type: {entry_type}\nTitle: {title}\n\nContent:\n<<<\n{content}\n>>>"


def _call_m3(user: str) -> bool | None:
    key = _load_env_key("MINIMAX_API_KEY")
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
                "model": JUDGE_M3_MODEL,
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
    key = _load_env_key("MISTRAL_API_KEY")
    if not key:
        return None
    try:
        resp = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
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
        if isinstance(content, list):
            content = "".join(c.get("text", "") for c in content if isinstance(c, dict))
        return _parse(content if isinstance(content, str) else "")
    except Exception:
        return None


def judge_entry(title: str, content: str, entry_type: str = "knowledge") -> Verdict:
    """Judge one candidate entry. Parallel M3+Mistral, first VALID verdict wins."""
    if not GATE_ENABLED:
        return "accept"
    user = _build_user(title, content, entry_type)
    callers = []
    if _load_env_key("MINIMAX_API_KEY"):
        callers.append(_call_m3)
    if _load_env_key("MISTRAL_API_KEY"):
        callers.append(_call_mistral)
    if not callers:
        return "unknown"

    ex = _cf.ThreadPoolExecutor(max_workers=len(callers))
    result: bool | None = None
    try:
        futs = [ex.submit(c, user) for c in callers]
        for fut in _cf.as_completed(futs, timeout=JUDGE_TIMEOUT_SEC + 5):
            try:
                r = fut.result()
            except Exception:
                r = None
            if r is not None:
                result = r
                break
    except Exception:
        pass
    finally:
        ex.shutdown(wait=False, cancel_futures=True)

    if result is None:
        return "unknown"
    return "accept" if result else "reject"


def gate_entry(title: str, content: str, entry_type: str = "knowledge", source: str = "") -> bool:
    """Production entry point: True = ingest, False = drop.

    "unknown" (no provider) FAILS OPEN to ingest, but logs the bypass so the
    gate's own availability is auditable.
    """
    verdict = judge_entry(title, content, entry_type)
    if verdict == "accept":
        return True
    try:
        REJECT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(REJECT_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": int(time.time()),
                "verdict": verdict,
                "entry_type": entry_type,
                "source": source,
                "title": (title or "")[:200],
            }) + "\n")
    except Exception:
        pass
    return verdict == "unknown"  # fail-open only on provider outage


if __name__ == "__main__":
    # Smoke: one obvious junk title, one obvious good entry.
    junk = judge_entry("(req 6)", "waits on task #1052.", "decision")
    good = judge_entry(
        "Stop hook stdout schema: block vs allow shapes",
        "Stop hooks must emit {\"decision\": \"block\", \"reason\": ...} to block; "
        "to allow, emit NOTHING or {}. decision:\"approve\" and continue:false are both "
        "invalid and cause 'JSON validation failed' in Claude Code.",
        "knowledge",
    )
    print(f"junk -> {junk} (expect reject), good -> {good} (expect accept)")
