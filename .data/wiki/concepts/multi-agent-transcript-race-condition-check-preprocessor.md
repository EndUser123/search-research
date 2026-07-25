---
title: "Multi-agent transcript race condition in /check preprocessor"
created: 2026-07-25
source: session-019f94c9
tags: [multi-agent, race-condition, check-skill, preprocessor, transcript-discovery, bug, root-cause]
summary: >
  The /check preprocessor discovered the session transcript by scanning ALL
  chat_history.jsonl files and picking the most recently modified one. On a
  multi-agent host with 5+ concurrent Grok sessions writing to the same
  directory, this is a race condition — the scan returns whichever session
  flushed last, not the invoking session. Every /check on this host was
  extracting deterministic evidence from a random concurrent session's
  transcript. Fixed by constructing the path directly from the session ID.
agent: grok
host: grok
cognitive_load: 3
verification: verified-2026-07-25
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/multi-terminal-coordination-windows.md
    type: same-family
---

# Multi-agent transcript race condition in /check preprocessor

## The bug (one sentence)

`/check`'s transcript discovery scanned all `chat_history.jsonl` files by `LastWriteTime` and picked the newest — on a multi-agent host, this returns a random concurrent session's transcript, not the invoking session's.

## How the discovery happened

During a `/check` run in session `019f94c9`, the preprocessor reported it found the transcript at session `019f97b2` — a different session. The operator flagged this as a MAJOR problem. Investigation showed 5 concurrent sessions writing transcripts to the same `~/.grok/sessions/P%3A%5C/` directory:

| Session | Last write | What it is |
|---------|-----------|------------|
| `019f97b7` | 11:23:46 PM | Concurrent Grok session (1s newer) |
| **`019f94c9`** | **11:23:45 PM** | **This session (lost the race)** |
| `019f97ae` | 11:23:37 PM | Another session |
| `019f96f5` | 11:23:24 PM | Another session |
| `019f97b5` | 11:23:24 PM | /check verifier subagent |

This session lost the race by 1 second. With N concurrent sessions, the probability of winning is ~1/N — on this host, ~20%.

## The buggy code

```powershell
# OLD CODE (buggy):
$transcript = Get-ChildItem -Path $sessionsRoot -Recurse -Filter "chat_history.jsonl" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
```

This scans the entire sessions directory recursively, sorts by write time, and takes the first result. The comment in the code said *"Allowed: immutable discovery of THIS terminal's own session, not a peer's"* — but the implementation violated its own comment by scanning the entire root.

## Why it was never caught

1. **Single-session assumption:** the code was written when the host ran one Grok session at a time. The multi-agent fleet grew around it.
2. **Silent degradation:** `/check` didn't fail — it produced an evidence packet, just from the wrong session. The LLM verifiers compensated by using conversation context, so the verdicts were still grounded. The deterministic evidence layer was garbage-in-garbage-out, but the final PASS/FAIL was usually correct because it relied on LLM judgment.
3. **No mismatch signal:** the preprocessor had no way to know it was reading the wrong transcript. The session ID wasn't compared against the scan result.

## The fix

Construct the transcript path directly from the session ID instead of scanning:

```powershell
# NEW CODE (deterministic):
$sessionId = $env:GROK_SESSION_ID
if (-not $sessionId) { $sessionId = $env:CLAUDE_SESSION_ID }
# On Grok Build, session ID env vars are NOT exported to shell subprocesses.
# The LLM injects its own session ID as a literal from system context.
if (-not $sessionId) { $sessionId = "LLM_FILL_FROM_CONTEXT" }
$encodedCwd = [System.Uri]::EscapeDataString((Get-Location).Path)
$directPath = Join-Path $sessionsRoot "$encodedCwd/$sessionId/chat_history.jsonl"
```

The fallback scan retains a **mismatch warning** — if it finds a transcript whose session ID doesn't match the current session, it prints:

```
TRANSCRIPT MISMATCH: scan found session 'X' but current session is 'Y'. Evidence packet may be unreliable.
```

## Why the env vars are empty

On Grok Build, `GROK_SESSION_ID` and `CLAUDE_SESSION_ID` exist in the Grok process context but are **NOT exported to shell subprocesses** spawned by `run_terminal_command`. Verified 2026-07-25:

```
GROK_SESSION_ID: []
CLAUDE_SESSION_ID: []
```

The LLM knows its own session ID from system context (it appears in the prompt file path, compaction segment paths, and session directory). The fix requires the LLM to inject its session ID as a literal string into the PowerShell script before running it. This is a manual step — the code cannot auto-discover the session ID from env vars alone.

## Impact

Every `/check` invocation on this multi-agent host prior to the fix (commit `9a1fe7a`, 2026-07-25) extracted deterministic evidence from a potentially wrong session's transcript. The evidence packet's `claim_verbs`, `unverified_claim_candidates`, `test_runs`, `failures`, and `scope_files` were all potentially garbage. The LLM verifiers masked this by using conversation context directly, but the deterministic evidence layer was compromised.

The `/close` scanner was NOT affected — `close_accounting.py` uses `$env:GROK_SESSION_ID` for session-scoped filtering via a different code path (the identity resolution in the Python scanner, not the PowerShell transcript discovery in `/check`'s SKILL.md).

## Generalization

This is the same class of bug as other multi-agent shared-filesystem issues on this host:

- **Git working tree races** — concurrent agents committing to the same tree (documented in AGENTS.md "Working in the shared main tree")
- **File editing collisions** — concurrent edits to the same file (documented in file-editing-protocol.md)
- **State file namespace pollution** — fixed via hash-based naming in hooks

The pattern: code written for a single-agent host is later run in a multi-agent context, and the single-agent assumption becomes a race condition. The fix is always the same — replace implicit discovery (scan + sort) with explicit identity (construct from a known session/process ID).
