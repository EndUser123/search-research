# Session-scoped output default pattern

**Created:** 2026-08-11 (session 019ff1a0)
**Status:** ACTIVE
**Scope:** PROBLEM_CLASS — applies to any skill that writes shared artifacts

## The pattern

Any skill that writes artifacts to shared filesystem state (review packets,
AAR run dirs, temp scripts, export files) MUST default its output path to a
session-scoped subdirectory, never to a shared global root.

**Implementation (Python):**

```python
def _default_out_dir():
    session_id = (
        os.environ.get("GROK_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
    )
    if session_id:
        return f"P:/.artifacts/<skill-name>/{session_id}"
    return "P:/.artifacts/<skill-name>/no-session-scope"
```

Then wire it into argparse:

```python
parser.add_argument("--out", type=str, default=_default_out_dir(),
                    help="Output directory (default: session-scoped)")
```

## Why this exists

On this multi-agent host, concurrent sessions share the same `P:/.artifacts/`
root. A skill that writes to the shared root risks:

1. **Filename collisions** — two sessions running `/packet` produce
   `<name>_sig.md` in the same directory; the second overwrites the first.
2. **Stale-data contamination** — a reviewer picks up a packet from a prior
   session thinking it's current.
3. **Invariant violation** — the standing architectural principle (2026-08-10)
   requires session-scoping for ALL shared-filesystem state.

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| Env var fallback chain (GROK → CLAUDE → terminal) | Works across Grok Build and Claude Code; terminal ID is the last resort when session ID is unavailable |
| Loud fallback (`no-session-scope`) not silent | A session writing to a shared root should be visible, not invisible. Silent fallback defeats the invariant. |
| Skill-name subdirectory under `.artifacts/` | Prevents cross-skill collisions (e.g., `/packet` artifacts don't mix with `/aar` artifacts) |

## Reference implementation

`~/.grok/skills/packet/scripts/pack.py` — `_default_out_dir()` function added
in commit `6f55e27` (2026-08-11). The skill's `--out` default changed from
`P:/.artifacts` (shared root) to `P:/.artifacts/<session-id>/` (scoped).

## When NOT to apply

- **Temp files via `tempfile.mkdtemp()`** — already unique per invocation; no
  session-scoping needed.
- **Git-tracked deliverables** — the commit hash is the scope, not the directory.
- **Per-user config files** — `~/.config/<skill>/` is already user-scoped.

## Falsifier

This pattern is wrong if:
- The env var fallback chain proves unreliable across hosts (session ID not
  propagating to the shell on Grok Build — known issue, hence terminal ID
  fallback).
- A better structural mechanism exists (e.g., a skill-creation linter that
  flags shared-directory defaults at authoring time, making the runtime
  fallback unnecessary).

## Related

- [[multi-terminal-isolation-stale-data-immunity]] — the design checklist this pattern implements
- [[caller-context-as-parameter-not-callee-discovery]] — the principle that scope should be passed, not discovered
- AGENTS.md "Standing architectural principle (2026-08-10)" — the governing rule
