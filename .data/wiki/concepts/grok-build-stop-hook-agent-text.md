---
title: "Grok Build Stop hook: accessing agent text (the chat_history.jsonl workaround)"
created: 2026-07-21
source: session-2026-07-21
tags: [hooks, stop-hook, grok-build, chat-history, workaround, payload, claude-code-compat, llm-judgment]
summary: >
  Grok Build's native Stop event payload provides sessionId, cwd, workspaceRoot but
  NOT the agent's response text (unlike Claude Code's Stop hook which includes `response`).
  The workaround: read `chat_history.jsonl` from the session directory. The hook constructs
  the path from sessionId + workspaceRoot, reads the JSONL, extracts the last `type: "assistant"`
  entry's `content` field. This is the same pattern recommended in the existing
  STOP_PAYLOAD_SCHEMA_LIMITATION.md (Option A: load from transcript). The LLM-judgment
  hook pattern (regex + LLM judge) IS implementable on Grok Build via this workaround.
agent: grok
host: grok
cognitive_load: 3
verification: directly-verified
relations:
  - target: wiki/concepts/llm-judgment-hooks
    type: corrects
  - target: wiki/concepts/mcp-server-sharing-multi-terminal
    type: related
---

# Grok Build Stop hook: accessing agent text

## Correction from previous turn

In the prior `/www` on LLM-judgment hooks, I claimed: "Stop is not a tool event. The Stop payload gives you sessionId, cwd, workspaceRoot — no agent text. Option A as researched does not work on Grok Build."

**This was partially wrong.** The payload limitation is real, but the conclusion ("doesn't work") was wrong. The agent text IS accessible — just not in the payload directly. It's in `chat_history.jsonl`, which the hook can read using fields from the payload.

## The actual payload problem

**Grok Build native Stop event** (verified from `~/.grok/docs/user-guide/10-hooks.md`):

```json
{
  "hookEventName": "Stop",
  "sessionId": "<session-id>",
  "cwd": "P:\\",
  "workspaceRoot": "P:\\"
}
```

That's the base payload. No `response`, no `transcript_path`, no `user_prompt`. (Claude Code's Stop hook DID include `response` — see `P:/.claude/hooks/STOP_PAYLOAD_SCHEMA_LIMITATION.md` — but Claude compat hooks are OFF under Grok Build: `compat.claude.hooks=false`.)

Tool events (`PreToolUse`, `PostToolUse`) additionally get `toolName`, `toolInput`, `toolUseId`, `toolInputTruncated`. Stop is passive — no tool data.

## The workaround: read `chat_history.jsonl`

**Verified this session.** The session directory contains:

```
~/.grok/sessions/<url-encoded-cwd>/<session-id>/
├── chat_history.jsonl     ← full conversation including agent responses
├── events.jsonl           ← structured events (tool calls, MCP calls)
├── updates.jsonl          ← incremental updates
├── summary.json           ← session summary
├── plan.json / plan.md    ← plan mode state
└── ...
```

**Path construction from payload:**
```python
# From the Stop payload:
session_id = data["sessionId"]              # e.g. "019f819a-..."
workspace_root = data["workspaceRoot"]      # e.g. "P:\\"

# URL-encode the workspace root for the path:
from urllib.parse import quote
encoded_cwd = quote(workspace_root, safe="")  # "P%3A%5C"

# Construct the session directory path:
from pathlib import Path
session_dir = Path.home() / ".grok" / "sessions" / encoded_cwd / session_id
chat_file = session_dir / "chat_history.jsonl"
```

**chat_history.jsonl structure (verified 2026-07-21):**

Each line is a JSON object. Entry types:

| `type` field | Content | How to extract text |
|--------------|---------|---------------------|
| `assistant` | Agent's response | `entry["content"]` — string or array of blocks |
| `tool_result` | Tool output | `entry["content"]` — string |
| `reasoning` | Thinking trace | `entry["summary"]` — may be redacted |

**Extracting the last assistant response:**

```python
import json

def get_last_assistant_text(chat_file_path: str) -> str:
    """Read the last assistant response from chat_history.jsonl."""
    last_text = ""
    with open(chat_file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant":
                    content = entry.get("content", "")
                    if isinstance(content, str) and len(content) > 20:
                        last_text = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "")
                                if len(text) > 20:
                                    last_text = text
                                    break
            except json.JSONDecodeError:
                continue
    return last_text
```

**Note:** the field is `type`, not `role`. Claude Code uses `role: "assistant"`; Grok Build uses `type: "assistant"`. The extraction code must check `type`.

## Complete Stop hook implementation (for the alternatives gate)

```python
#!/usr/bin/env python3
"""
Stop hook: alternatives-before-architectural-implementation gate.

Fires on Stop event. Reads chat_history.jsonl to get the last assistant response.
Checks whether the response contains architectural implementation language
without a preceding ALTERNATIVES GATE block.

Two-layer: regex (fast) → LLM judge (semantic, only on regex hit).
Fail-open: if anything breaks, allow the response (don't kill conversation).
"""

import json
import sys
import re
from pathlib import Path
from urllib.parse import quote

# --- Read payload from stdin ---
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open

session_id = data.get("sessionId", "")
workspace_root = data.get("workspaceRoot", data.get("cwd", ""))

if not session_id or not workspace_root:
    sys.exit(0)  # fail-open: can't find session

# --- Construct chat_history.jsonl path ---
encoded_cwd = quote(workspace_root, safe="")
chat_file = Path.home() / ".grok" / "sessions" / encoded_cwd / session_id / "chat_history.jsonl"

if not chat_file.exists():
    sys.exit(0)  # fail-open

# --- Extract last assistant response ---
last_text = ""
try:
    with open(chat_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant":
                    content = entry.get("content", "")
                    if isinstance(content, str) and len(content) > 20:
                        last_text = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                t = block.get("text", "")
                                if len(t) > 20:
                                    last_text = t
                                    break
            except json.JSONDecodeError:
                continue
except Exception:
    sys.exit(0)  # fail-open

if not last_text:
    sys.exit(0)  # fail-open

# --- Layer 1: regex check for architectural implementation language ---
# Does the response describe building/creating an architectural component?
ARCH_PATTERNS = [
    r"\b(?:created|built|wrote|implemented|set up)\s+(?:a\s+)?(?:new\s+)?(?:MCP|mcp|hook|server|daemon|dispatch|router|config\.toml)",
    r"\b(?:search-mcp|search_fleet|server\.py)\b",
]

# Does the response contain an alternatives gate?
GATE_PATTERN = r"ALTERNATIVES GATE|alternatives?\s*(?:gate|block|considered)|≥\s*2\s*(?:viable\s*)?options"

has_arch = any(re.search(p, last_text, re.I) for p in ARCH_PATTERNS)
has_gate = bool(re.search(GATE_PATTERN, last_text, re.I))

if not has_arch:
    sys.exit(0)  # not architectural, allow

if has_gate:
    sys.exit(0)  # gate was emitted, allow

# --- Layer 2: LLM judge (only if Layer 1 hit and no gate found) ---
# Call Gemini Flash or MiniMax for semantic classification
# (omitted for brevity — see llm-judgment-hooks.md for the pattern)
# For now: advisory only (warn, don't block)

# Write advisory to stderr (appears as feedback to agent)
print(
    "ARCHITECTURAL DECISION DETECTED without ALTERNATIVES GATE. "
    "If this turn created/built an architectural component (MCP, hook, config, dispatch chain), "
    "emit an ALTERNATIVES GATE block (≥2 options, selection criterion, why chosen) "
    "in your next response before further implementation.",
    file=sys.stderr,
)

# Advisory: exit 0 (warn only, don't block)
# To make it blocking: exit 2 instead
sys.exit(0)
```

## What this enables

| Enforcement level | Mechanism | Reliability |
|-------------------|-----------|-------------|
| **Advisory** (current recommendation) | Stop hook reads chat_history, prints warning to stderr | Low — agent may ignore |
| **Blocking** | Same hook but `exit 2` instead of `exit 0` | Medium — agent must address the warning |
| **LLM judge** | Layer 2 Gemini/MiniMax call classifies architectural-vs-trivial | High — catches false positives on trivial config edits |

## The `events.jsonl` alternative

If you need tool events (what tools were called, not just the response text), `events.jsonl` has structured entries:

```json
{"ts": "...", "type": "mcp_tool_call_started", "server_name": "search", "tool_name": "query", "call_id": "...", "timeout_sec": 6000}
```

This can be used to detect: "did the agent call Write/Edit on an architectural file path?" — which is a stronger signal than regex on the response text.

## Authority sources

| Source | Score | Finding |
|--------|-------|---------|
| `~/.grok/docs/user-guide/10-hooks.md` | 12 | Official Grok Build hook events + payload fields |
| `P:/.claude/hooks/STOP_PAYLOAD_SCHEMA_LIMITATION.md` (2026-06-18) | 12 | Documents Claude Code Stop payload: `user_prompt`, `response`, `transcript_path`; missing `tool_events`; recommends Option A (load from transcript) |
| Live probe of `chat_history.jsonl` (this session) | 12 | Verified: `type: "assistant"` entries contain response text; file is readable; path constructable from payload fields |
| [Grok Build changelog](https://x.ai/build/changelog) | 11 | "Stop hook runs now appear inline on the turn-completed line" — confirms Stop hooks fire natively |
| [Simon Willison](https://simonwillison.net/2026/Jul/15/grok-build/) (2026-07-15) | 10 | Grok Build open-sourced (844K lines Rust); hook implementation in source |

## Relationship to existing concepts

- **Corrects** [[llm-judgment-hooks]] — the previous concept said "Option A does not work on Grok Build." This was wrong. It works via chat_history.jsonl.
- **Related** [[mcp-server-sharing-multi-terminal]] — HTTP hooks could POST agent text to a shared judge server

## Sources

- `~/.grok/docs/user-guide/10-hooks.md` (Grok Build official docs)
- `P:/.claude/hooks/STOP_PAYLOAD_SCHEMA_LIMITATION.md` (2026-06-18, host-verified)
- Live probe: `chat_history.jsonl` at `~/.grok/sessions/P%3A%5C/<sid>/chat_history.jsonl` (2026-07-21)
- https://x.ai/build/changelog
- https://simonwillison.net/2026/Jul/15/grok-build/ (open-source analysis)

## Staleness

Grok Build hook payloads may change with platform updates. The chat_history.jsonl structure is stable within a major version. If the Stop payload gains a `response` field in a future update, the workaround becomes unnecessary (but still works).

## Auto-related

- [[grok-build-disabled-hooks-per-hook-layer]]
- [[grok-build-compat-layer-marketplace-plugin-skills]]
- [[grok-build-plan-mode-structured-thinking]]
- [[grok-build-cc-aca-actually-enabled]]
- [[wiki-lifecycle-state-file]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
