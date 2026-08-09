# HANDOFF: L4 "order the lab" protocol + GROK_SESSION_ID 121-file migration

## Status
OPEN — two coupled work items from AAR O1 + O2

## Objective
1. **O1 (L4 protocol):** Design and implement an "order the lab" protocol — a systematic way to request multi-session fleet work without ad-hoc handoff sprawl.
2. **O2 (121-file migration):** Migrate 121 files from `os.environ.get('GROK_SESSION_ID')` to `session_resolver.resolve_session_id()` across the workspace.

## Context
- These are from a sibling session's AAR (opportunities O1 and O2)
- The GROK_SESSION_ID env var is documented as "always available" in the Grok Build docs (10-hooks.md:318) but the evidence shows it is NOT exported to shell subprocesses on this host
- `session_resolver.py` was built as the fix — resolves session ID from tier-3 fallback (session dir scan)
- 121 files still use the old pattern; the migration is mechanical but wide

## Acceptance criteria
- O1: L4 protocol design document produced
- O2: All 121 files migrated, tests pass, grep confirms zero remaining `os.environ.get('GROK_SESSION_ID')` calls

## Suggested next invocation
```
/go Read P:/docs/handoffs/l4-protocol-and-session-id-migration-20260808/HANDOFF.md and implement both items. Start with O2 (mechanical migration) since O1 (protocol design) benefits from the migration being complete.
```

## References
- Session 019fdf3d AAR report
- `~/.grok/hooks/scripts/session_resolver.py` — the resolver to use
- `~/.grok/docs/user-guide/10-hooks.md:318` — documents GROK_SESSION_ID as "always available" (evidence shows otherwise)
