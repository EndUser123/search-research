# HANDOFF: verification_receipt.py hash scope — whole-repo hash can't hold on multi-agent host

## Status
OPEN — discovered 2026-08-11 (session 019fe3ff), /check ops verifier FAIL.

## Objective
Fix `C:/Users/brsth/.grok/scripts/verification_receipt.py` so its diff-hash binding is meaningful on this host. Currently it hashes the ENTIRE `~/.grok` and `P:/` repos (commits + dirty tree). On a multi-agent shared-repo host, sibling sessions commit constantly and the dirty tree always holds other agents' changes, so `hash_match` returns `false` within minutes of any registration. The receipt's `current` flag is therefore permanently stale for every session.

## Evidence (verified 2026-08-11, session 019fe3ff)
- Registered `/review` receipt `--session 019fe3ff --verdict healthy` at 2026-08-12T04:35:23Z (diff_hash `71ff3c8f…`).
- Query immediately after: `{"found": true, "current": false, "verdict": "healthy", "hash_match": false, "receipt_hash": "71ff3c8f…", "current_hash": "2b9c89b8…"}`.
- Cause: sibling commit `12ab08a` (GLM/NVIDIA context windows) landed after registration + extensive dirty-tree content (modified wiki concepts, deleted `SYCOPHANCY.md`, package edits) — all included in the repo-wide hash.
- First registration this session (verdict `needs_attention`) ALSO auto-detected the WRONG session (`019fdf47`) when `--session` was omitted — env-based auto-detect is racy on this host; the `--session` flag is required.

## Acceptance criteria
1. The hash is computed over the session's OWN changed files (session-scoped diff), not the whole repo — OR the mechanism switches to a session-scoped marker (e.g. `git log --since=<session-start>` commit list) that tolerates sibling commits and dirty-tree noise.
2. `--session` auto-detect removed or made fail-closed (never pick a different session than the caller's).
3. `/todo`'s `finding_coverage` scanner still correctly re-suggests `/review` when the reviewed code changes (the hash scope change must not break that signal — the scanner should re-suggest on session-owned file changes, not on sibling noise).
4. Regression tests for: registration with explicit `--session`, query after sibling commit, query after own-file change (should flip to re-suggest), wrong-session auto-detect (should fail closed).

## Scope guard
- Do NOT change the receipt schema fields (`session_id`, `skill`, `verdict`, `diff_hash`) — consumers (`/todo` finding_coverage, `/review` Step 8) read them.
- The change is in hash computation + session resolution only.

## Suggested next invocation
```
/go "Fix verification_receipt.py hash scope: compute the diff hash over the registering session's own changed files (git log --since=<session-start> + session-scoped file list), make --session auto-detect fail-closed, keep the schema, and add regression tests. See P:/docs/handoffs/verification-receipt-hash-scope-20260811/HANDOFF.md"
```

## References
- Session 019fe3ff /check run: `P:/.artifacts/console_77a0d2fd-13d8-4ebe-9b08-fe1de724f65e/grok-check/20260811-221723-248/` (verifier-2.json = ops FAIL).
- Script: `C:/Users/brsth/.grok/scripts/verification_receipt.py` (register/query, `--session` supported since 2026-08-11; `compute_session_diff_hash` includes dirty tree).
