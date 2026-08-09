---
title: "Session-scoped artifact redirect pattern"
created: 2026-08-08
agent: grok
host: grok
tags: [design-pattern, session-isolation, dispatch-artifacts, tp-dispatch, delegation]
summary: >
  Transparent redirect of --output paths to a session-scoped subdirectory so
  dispatch artifacts (packed context files for codex/agy/subagents) are not
  deleted by mid-session cleanup. The caller's interface doesn't change; only
  the parent directory does. Implemented in tp_dispatch.py (_resolve_output).
cognitive_load: 1
verification: single-source-verified
last_verified: 2026-08-08
scope: SESSION_SPECIFIC
scope_note: >
  Based on one implementation (tp_dispatch.py). May transfer to any delegation
  infrastructure that writes artifacts a background consumer needs. Upgrade to
  GENERAL scope if it proves transferable across codex, agy, and subagent
  dispatch patterns.
---

# Session-scoped artifact redirect pattern

## The pattern

When a tool writes a temporary artifact that a background consumer (codex,
agy, subagent) will read later, redirect the output to a session-scoped
subdirectory instead of the shared temp root. The caller's `--output` path
stays the same; the redirect is transparent.

```python
def _resolve_output(raw_output: str) -> Path:
    p = Path(raw_output)
    if "tp-dispatch-" in p.parent.as_posix() or not p.as_posix().lower().startswith("p:/tmp/"):
        return p  # already scoped or explicitly placed elsewhere
    session_dir = _session_scope_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir / p.name
```

## Why it works

The agent's cleanup targets the raw path (`Remove-Item "P:/tmp/tp-codex-policy.md"`).
The file actually lives at `P:/tmp/tp-dispatch-<sid>/tp-codex-policy.md`.
The deletion finds nothing; the file survives for the consumer.

The redirect is transparent because:
1. The filename is preserved (callers don't notice)
2. The script prints the actual path (consumers read from the real location)
3. A manifest tracks what was created and why

## When to apply

- Any tool that packs context for a background consumer (codex, agy, subagent)
- Any workflow where the agent might clean up "temp files" mid-session
- Multi-terminal hosts where concurrent dispatch panels need isolation

## When NOT to apply

- One-shot scripts that complete before cleanup runs
- Artifacts the agent intentionally deletes after use (use --cleanup)

## Reference implementation

`~/.grok/skills/tp/__lib/tp_dispatch.py:_resolve_output()` (commit `3ed2fbf`)
+ `~/.grok/hooks/scripts/session_resolver.py` for session identity.

## Falsifier

This pattern is wrong if:
- The session-scoped directory itself gets cleaned up mid-session (same
  problem, one level up) — but this is less likely because the directory
  name signals "active dispatch artifacts"
- The session identity is wrong (two sessions share a directory) — mitigated
  by session_resolver.py's 4-tier fallback
- The consumer can't find the file because the path changed — mitigated by
  printing the actual path in the script output
