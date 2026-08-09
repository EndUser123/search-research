---
title: "GROK_SESSION_ID not populated: session identity resolution on Grok Build"
created: 2026-08-08
agent: grok
host: grok
tags: [session-identity, grok-build, env-vars, hooks, multi-terminal, stale-data, platform-bug]
summary: >
  GROK_SESSION_ID is documented as an env var set by the Grok Build runtime
  for hooks, but it is NOT populated as of 2026-08-08. Every hook/script that
  calls os.environ.get("GROK_SESSION_ID") gets an empty string and falls back
  to "unknown-session" or "most recently modified" (a stale-data hazard on
  multi-terminal hosts). The session ID IS available in the hook stdin payload
  (sessionId field) and derivable from the session directory path. The durable
  fix is session_resolver.py: a 4-tier resolver that reads stdin first, then
  env, then session-dir inference, then terminal fallback.
cognitive_load: 2
verification: multi-source-verified
last_verified: 2026-08-08
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: validates — the session-identity gap is a root cause of the stale-data hazards this concept documents
  - target: wiki/concepts/context-firewall-architecture.md
    type: supports — session identity is required for session-scoped isolation
  - target: wiki/concepts/narrative-sufficiency-awareness-enforcement-gap-2026.md
    type: example — "keyed by GROK_SESSION_ID" was a fabricated structural claim; this concept is the correction
---

# GROK_SESSION_ID not populated: session identity resolution on Grok Build

## The problem

Grok Build documents `GROK_SESSION_ID` as an environment variable set for
hooks:

> | `GROK_SESSION_ID` | The unique identifier of the current Grok session. |
> — `~/.grok/docs/user-guide/10-hooks.md:318` (under "Runner-injected variables (always available)")
>
> These variables are set by the hook runner for **every** hook.
> — ibid, line 314

And at line 440:

> Hooks receive `$GROK_EVENT`, `$GROK_MESSAGE`, and `$GROK_SESSION_ID` in the environment.

**The documented contract is not fulfilled by the runtime.** Verified
2026-08-08:

```powershell
> $env:GROK_SESSION_ID
> (empty)
```

The active-surface snapshot hook (`active_surface_snapshot.py:710`), which
runs as a SessionStart hook, resolves to `"unknown-session"` using exactly
this call:

```python
session_id = os.environ.get("GROK_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID") or "unknown-session"
```

The result: `# Active Surface — Grok Build Session unknown-session`.

**This is a platform bug, not a workspace coding error.** 121 files across
the workspace reference `GROK_SESSION_ID`. They were all correctly coding
against the documented API. The spread is proportional to how fundamental
session identity is to multi-terminal isolation — every hook, scanner, and
enforcement mechanism needs it.

### Provenance: where the pattern came from

The pattern did NOT originate from agents inventing an assumption. It came
from reading the official Grok Build documentation and coding to the
documented contract. The docs say `GROK_SESSION_ID` is "always available"
(runner-injected, line 314) and "set by the hook runner for every hook"
(line 313). The workspace followed the spec; the runtime didn't implement
it. This is a **doc-vs-runtime discrepancy**, not a workspace design error.

## Where the session ID IS available

Two reliable sources:

1. **Hook stdin payload** — Grok Build events carry `sessionId` in the JSON
   stdin payload:
   ```json
   {"hookEventName": "session_start", "sessionId": "019fe3ff-...", "cwd": "P:\\", ...}
   ```
   The active-surface hook ignores it (line 9: "Input: JSON on stdin
   (ignored — we use env)"). The data is there; the code doesn't read it.

2. **Session directory path** — `~/.grok/sessions/<encoded-cwd>/<session-id>/`
   The directory name IS a UUID-format session ID. This is reliable for
   CLI tools (which don't receive hook stdin payloads) but requires
   inference (most-recently-modified) to determine which session is "current."

## Impact

Every mechanism that keys on session identity inherits this gap:

| Consumer | What it does | Current behavior |
|---|---|---|
| `active_surface_snapshot.py` | Records session ID in the active-surface snapshot | `"unknown-session"` |
| `tp_dispatch.py` `find_transcript()` | Finds the current session's transcript | Falls back to "most recently modified" (stale-data risk) |
| `tp_dispatch.py` `_session_scope_dir()` | Session-scoped dispatch artifacts | Falls back to terminal ID (terminal-scoped, not session-scoped) |
| `commit_coordinator.py` | Session-scoped commit coordination | Relies on `session_id` parameter (caller-dependent) |
| Quality gate receipts | Per-session evidence files | Keyed by terminal+session, but session from env is empty |

## The durable fix: session_resolver.py

`~/.grok/hooks/scripts/session_resolver.py` — a 4-tier resolver:

| Tier | Source | Reliable? | When available |
|---|---|---|---|
| 1 | stdin JSON `sessionId` field | ✅ High | Inside hook processes |
| 2 | `GROK_SESSION_ID` / `CLAUDE_SESSION_ID` env | ⚠️ Documented but not populated | If the platform bug is fixed |
| 3 | Session-dir inference (most-recently-modified transcript, <120s recency filter) | ⚠️ Heuristic | CLI tools (no stdin) |
| 4 | `CLAUDE_TERMINAL_ID` / `WT_SESSION` | ⚠️ Terminal-scoped, not session-scoped | Fallback |

**The stdin payload is the durable source** because it's populated by the
runtime's event system, not by env-var inheritance (which breaks on Grok
Build). The session-dir inference is the CLI-tool fallback.

## Falsifier

This concept is wrong if:
- A future Grok Build release populates `GROK_SESSION_ID` as an env var
  (then tier 2 fires reliably and the resolver still works — just upgrades
  from heuristic to authoritative)
- The stdin payload format changes (the resolver's `_from_stdin()` would
  need updating, but the tiered architecture absorbs the change)
- A better session-identity mechanism emerges (e.g., a Grok SDK call)

## Reference incidents

- **Session 019fe3ff (2026-08-08):** the agent claimed "keyed by
  GROK_SESSION_ID" for a session-scoped dispatch fix. Verification showed
  the env var was empty. The claim was fabricated — the agent asserted a
  structural property from code intent rather than runtime behavior. This
  concept is the correction.
- **Session-dir inference stale-data risk:** on a multi-terminal host with
  concurrent sessions, "most recently modified transcript" can resolve to
  a sibling session writing concurrently. The <120s recency filter reduces
  but does not eliminate this risk.
