#!/usr/bin/env python3
"""
PostToolUse path-error observer (ADVISORY — logs only, never blocks).

Purpose: gather the corpus of "acted on unverified path/state" failures so a
future gate decision has TP/FP data. This session (2026-07-08) hit three:
  - cd into P:/packages/search-research (wrong path from SKILL.md doc)
  - ModuleNotFoundError: No module named 'core' (same root cause)
  - find on a path that resolved outside the project

Root cause this observes: acting on documentation/state without verifying
against current filesystem. The fix is upstream (model discipline + a future
gate); this hook only MEASURES so the gate decision is evidence-based.

Why advisory-only: per feedback_gate_discrimination_rule, ship no gate until
TP/FP is measured on a real corpus. This IS the measurement.

Signal: post-execution shell/interpreter error signatures in Bash tool_output.
Tight regexes (shell-emitted, not file-content) keep FP low:
  - "No such file or directory"
  - "cannot access '...' No such file"
  - "ModuleNotFoundError: No module named"
  - "ImportError: No module named"
  - "FileNotFoundError"
  - "cd: ...: No such file or directory"
  - "The system cannot find the path"

Output: P:/.claude/hooks/.state/path_errors_{terminal}.jsonl
  {"ts","tool","cmd_head","signature","output_snippet"}

No stdout on success (PostToolUse allow = silence). Never exit non-zero.
"""

from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / ".state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Tight signatures — shell/interpreter-emitted, not file content.
# Order matters only for the "signature" label assigned.
SIGNATURES = [
    (r"No such file or directory", "no_such_file"),
    (r"cannot access '[^']*':\s*No such file", "cannot_access"),
    (r"ModuleNotFoundError: No module named '([^']+)'", "module_not_found"),
    (r"ImportError: No module named '([^']+)'", "import_no_module"),
    (r"FileNotFoundError: \[Errno 2\]", "file_not_found"),
    (r"cd:\s*[^:]+:\s*No such file or directory", "cd_no_such_dir"),
    (r"The system cannot find the path", "win_path_not_found"),
    (r"fatal: not a git repository", "not_a_git_repo"),
    (r"path .* does not exist", "explicit_path_missing"),
]
_COMPILED = [(re.compile(p), label) for p, label in SIGNATURES]


def _log_path() -> Path:
    tid = os.environ.get("WT_SESSION") or os.environ.get("CLAUDE_SESSION_ID") or "shared"
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", tid)[:48]
    return STATE_DIR / f"path_errors_{safe}.jsonl"


def _extract_text(payload: dict) -> tuple[str, str]:
    """Return (tool_name, text_to_scan). Only scan Bash output (where shell
    errors live). Read/Write errors come through differently and are noisier."""
    tool = payload.get("tool_name") or payload.get("tool") or ""
    if tool.lower() != "bash":
        return tool, ""
    resp = payload.get("tool_response") or payload.get("tool_result") or {}
    if isinstance(resp, dict):
        text = resp.get("output") or resp.get("content") or resp.get("stdout") or ""
    else:
        text = str(resp)
    if not isinstance(text, str):
        text = json.dumps(text)
    return tool, text


def main() -> int:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        payload = json.loads(raw)
    except Exception:
        return 0  # never break the agent on a malformed payload

    tool, text = _extract_text(payload)
    if not text:
        return 0

    cmd = ""
    tin = payload.get("tool_input") or {}
    if isinstance(tin, dict):
        cmd = str(tin.get("command") or tin.get("cmd") or "")[:160]

    hits = []
    seen_labels = set()
    for rx, label in _COMPILED:
        if label in seen_labels:
            continue
        m = rx.search(text)
        if m:
            seen_labels.add(label)
            # capture the matched line + a little context
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 80)
            hits.append({"signature": label, "snippet": text[start:end].replace("\n", " ")[:200]})

    if not hits:
        return 0

    from datetime import datetime, timezone
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "cmd_head": cmd,
        "hits": hits,
    }
    try:
        with open(_log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return 0  # logging failure must never break the agent

    return 0  # advisory: always allow


if __name__ == "__main__":
    sys.exit(main())
