---
title: "Session-scoped output redirect pattern for multi-terminal CLI dispatch"
created: 2026-08-09
source: session-2026-08-09 (tp_dispatch.py._resolve_output technique)
tags: [technique, multi-terminal, session-isolation, cli-dispatch, transferable-pattern, file-routing]
agent: grok
host: grok
cognitive_load: 2
verification: observed
summary: >
  When dispatching CLI tools (codex, agy, pi) from a multi-terminal host,
  redirect output to a session-scoped path rather than a shared path.
  The _resolve_output() technique in tp_dispatch.py creates a per-session
  directory under P:/tmp/tp-dispatch-<session-id>/ and routes all CLI output
  files there. This prevents cross-terminal file collision and makes cleanup
  session-scoped. The pattern generalizes to any CLI dispatch system that
  writes output files.
relations:
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: instance-of — this is a concrete implementation of the isolation principle
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration.md
    type: related — Rhai workflows face the same cross-terminal output collision
---

# Session-scoped output redirect pattern

## Decision context

**The problem:** `/tp` dispatches cross-model CLIs (codex, agy, pi) that write output files. If two terminals run `/tp` simultaneously, the output files collide — one terminal's CLI overwrites the other's. The original code used `P:/tmp/tp-<model>-<topic>.md` as the output path, which is shared across all terminals.

**The fix:** `tp_dispatch.py._resolve_output()` creates a per-session directory:
```
P:/tmp/tp-dispatch-<session-id>/tp-codex-<topic>.md
P:/tmp/tp-dispatch-<session-id>/tp-agy-<topic>.md
```

The session ID scopes the output. Two terminals produce different directories. No collision.

The pattern generalizes to any multi-agent system where CLI tools write shared output files. See [[multi-terminal-isolation-stale-data-immunity]] for the broader isolation principle and [[concurrent-cdp-auth-contention]] for a related cross-terminal collision pattern. Also related: [[grok-build-workflows-rhai-orchestration]] faces the same cross-terminal output collision in Rhai workflow dispatch.

## The pattern

```python
def _resolve_output(session_id: str, filename: str) -> Path:
    """Resolve output to a session-scoped directory."""
    dispatch_dir = Path(f"P:/tmp/tp-dispatch-{session_id}")
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    return dispatch_dir / filename
```

**Properties:**
- Session-scoped: each terminal gets its own directory
- Collision-proof: different sessions → different paths
- Cleanable: `rm -rf P:/tmp/tp-dispatch-<session-id>/` removes one session's artifacts
- Discoverable: the session ID in the path makes ownership visible

## What this means for our workspace

This pattern applies to any CLI dispatch system that writes output files:
- `/tp` cross-model critique dispatch
- `/review` parallel reviewer dispatch
- `/design` multi-architect draft synthesis
- Any future orchestrator that shells out to CLIs

The pattern should be extracted from `tp_dispatch.py` into a shared helper (e.g., `session_scoped_output(session_id, filename)`) that any skill can import.

## Falsifier

This pattern is wrong if:
- Session IDs are not reliably available (they're not in env vars on this host — `session_resolver.py` provides the fallback)
- The directory creation adds measurable latency (it doesn't — `mkdir(parents=True, exist_ok=True)` is <1ms)
- The pattern leads to directory accumulation (mitigated by session-scoped cleanup or OS temp reaping)

## Auto-related

- [[skill-catalog]]
- [[agent-reliability-patterns-and-production-validation]]
- [[skill-graph]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]

