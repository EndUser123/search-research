---
title: "Session identity resolution on Grok Build: process-tree walk against active_sessions.json"
created: 2026-08-05
source: session-019fc99e (session resolver implementation)
tags: [session-id, process-tree, active-sessions, grok-build, multi-terminal, isolation]
host: grok
agent: grok
cognitive_load: 2
verification: empirically-tested
---

# Session identity resolution on Grok Build

## The problem

Grok Build does not set `GROK_SESSION_ID` (or any session ID) in the process
environment. Skills and hooks that need session identity — `/todo`,
`/close`, `/aar`, `/handoff`, auto-verify hooks — had no way to discover
which session they were running in.

The AAR skill's `session_resolver.py` documented this gap explicitly:
"Grok Build does not expose a `GROK_SESSION_ID` env var (verified empirically)."

## The solution: process-tree walk

Grok Build maintains `~/.grok/active_sessions.json` — its own authoritative
registry of active sessions, mapping `pid` → `session_id`.

The shared resolver (`~/.grok/hooks/scripts/session_resolver.py`) works by:
1. Reading `active_sessions.json` to get the PID → session_id mapping
2. Walking up the process tree from `os.getpid()` using Windows
   `CreateToolhelp32Snapshot` (via `ctypes`)
3. Finding the ancestor PID that matches an entry in the registry
4. Returning that session ID

Typical walk depth: 2 levels (python → pwsh → grok-build process).

## Why this approach

- **No hook needed** — `active_sessions.json` is maintained by Grok Build itself
- **No cache file** — the registry IS the primary source; nothing to go stale
- **Multi-terminal isolated** — each Grok Build process has a unique PID; the
  process tree walk finds the specific ancestor that owns this terminal's session
- **Stale-data immune** — Grok Build manages entries on session start/end

## Forward compatibility

The resolver checks `GROK_SESSION_ID` env var first. If Grok Build later
exposes it (matching how Claude Code sets `CLAUDE_SESSION_ID`), the resolver
uses it directly and the process-tree walk becomes a fallback.

## Consumers

All former `os.environ.get("GROK_SESSION_ID", "")` call sites migrated:
- `skills/todo/__lib/scan_functions.py` (6 call sites)
- `skills/todo/__lib/scan_transcript.py` (1 call site)
- `skills/close/__lib/coverage_scan.py`
- `hooks/scripts/close_enforcement_gate.py`
- `hooks/PostToolUse_auto_verify.py`
- `hooks/PreToolUse_skill_staleness.py`

## Verified

- Resolves correct session ID on this host (PID 11676 → session 019fc99e)
- Multi-terminal isolation: two terminals with different PIDs get different sessions
- Stale-data immunity: 25h-old binding files rejected (TTL check, removed in v2)
- Graceful None when no terminal ID or registry unavailable
