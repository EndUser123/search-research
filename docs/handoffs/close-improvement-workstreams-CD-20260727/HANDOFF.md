---
thread_id: close-improvement-workstreams-CD-20260727
parent_handoff_path: none
current_session_id: 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e
current_terminal_id: console
produced_at: 2026-07-27T05:20:00Z
status: open
handoff_type: implementation_plan
accurate_as_of_head: ac15837 (in ~/.grok repo)
---

# Handoff: close-improvement Workstreams C and D (evidence identity + /check performance)

## Context (from /tp re-review + /go implementation session 019fa111)

This session produced a 4-workstream decomposition after a `/tp` review of
a 14-item `/close` improvement document. The decomposition is:

| Workstream | Status | Owner/pointer |
|---|---|---|
| A — Concurrency and Git (execute ADR-008 + private-index CAS as defense-in-depth) | Operational; ADR-008 Layer 1 shipped, Layer 2 deferred | `P:/docs/adrs/ADR-008-concurrent-session-worktree-isolation.md` |
| B — `/close` hermeticity (workspace injection, --no-mutate, session-bound temp attribution) | **DONE this session** | commit `ac15837` in `~/.grok` repo |
| C — Evidence identity (extend attempt receipts with supersession + HEAD + hashes) | **OPEN — this handoff** | below |
| D — `/check` performance (phase timing, read-once, model tiering) | OPEN — existing handoff | `P:/docs/handoffs/check-speed-optimization-20260726/HANDOFF.md` |

Separate workstreams (NOT `/close` work): fleet defects (SQLite leak, DeepSeek
serialization failure), `/go` prompt TDD. These have different owners and
acceptance gates and were explicitly excluded from the `/close` plan.

## Objective for the next session

Implement **Workstream C** — extend the existing `/close` attempt-receipt
schema with supersession and source-pinning fields so consumers can reject
stale-generation packets automatically.

## Why this matters (evidence from session 019fa111)

The original improvement document cited "duplicate attachments, stale call
notifications, changing HEADs, and verdicts generated against different
source generations" as the failure surface. The `/tp` critique confirmed
this is a real gap — `close_runner.py:33` has `ATTEMPT_RECEIPT_SCHEMA_VERSION
= "1.3"` and attempt JSONs carry `schema_version` + `attempt_id` (UUID4),
but there is **no `supersedes_attempt_id` field and no HEAD/hash pinning**.
The repeated stale attachments are not consumer-side rejectable today.

## What's already there (prior art to extend, not duplicate)

- `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py:33` —
  `ATTEMPT_RECEIPT_SCHEMA_VERSION = "1.3"`. Bump to `1.4` for the new fields.
- `close_runner.py:37` — `SUPPORTED_LEDGER_SCHEMA_VERSIONS = frozenset({"1.0", "1.1"})`.
  This is the *ledger* schema (separate from per-attempt receipts). The
  consumer-side check at line 207-209 rejects unknown schema_version — that's
  the gate that should learn to reject superseded attempts too.
- `C:/Users/brsth/.grok/hooks/scripts/mutation_receipt.py:25` —
  `RECEIPT_SCHEMA_VERSION = "2.0"`. This is the *mutation* receipt schema
  (different concept — per-file write receipts, not per-attempt close receipts).
  Don't conflate the two.
- Attempt JSON files at `P:/.artifacts/close-evidence/<session_id>/attempt-<uuid>.json`
  are the producer output. Sample current fields: `schema_version`, `attempt_id`,
  `session_id`, `terminal_state`, `started_at`, `completed_at`, `gate_overrides`.

## Scope (what changes)

### 1. New schema fields on attempt receipts (close_runner.py)

Bump `ATTEMPT_RECEIPT_SCHEMA_VERSION` from `"1.3"` to `"1.4"` and add these
fields to the receipt dict at `close_runner.py:136-150`:

```python
receipt = {
    "schema_version": ATTEMPT_RECEIPT_SCHEMA_VERSION,  # now "1.4"
    "attempt_id": attempt_id,
    "supersedes_attempt_id": supersedes_attempt_id,  # NEW — UUID of prior attempt this one replaces, or None
    "supersede_reason": supersede_reason,  # NEW — "stale_HEAD", "duplicate_run", "verifier_rerun", or None
    "source_head": source_head_sha,  # NEW — HEAD of repo at attempt time (git rev-parse HEAD)
    "source_repo": source_repo_path,  # NEW — e.g. "P:/" or "C:/Users/brsth/.grok" (which repo was the source-of-truth)
    "relevant_file_hashes": relevant_hashes,  # NEW — {path: sha256} for paths in gate scope (handoffs scanned, wiki concepts, etc.)
    "verification_scope": verification_scope,  # NEW — list of paths/scopes the verification covered
    "session_id": session_id,
    # ... existing fields ...
}
```

### 2. Consumer-side stale-generation rejection

In whatever skill consumes attempt receipts (grep for `attempt_id` consumers):
if `supersedes_attempt_id` is set AND a prior attempt with that ID exists in
the same session's evidence dir, the consumer MUST:
1. Mark the prior attempt as `superseded` (do not delete; keep for audit trail)
2. Use only the new attempt's verdict
3. Log the supersession event

### 3. HEAD/hash pinning at attempt-write time

In `close_runner.py`, before writing the attempt JSON, capture:
- `git -C <workspace> rev-parse HEAD` → `source_head`
- `git -C <workspace> rev-parse --show-toplevel` → `source_repo`
- For each path in the gate's evidence scope (handoffs scanned, wiki concepts
  scanned, etc.): compute sha256 → `relevant_file_hashes`

### 4. Schema-version bump compatibility test

Add a test that constructs an attempt JSON with the old schema (1.3) and
verifies the consumer-side loader either (a) upgrades it gracefully with
null/None supersession fields, or (b) rejects it with a clear error. Pick
the policy explicitly — I lean toward (a) for backward compat with existing
attempt files on disk.

## Acceptance criteria

- [ ] `ATTEMPT_RECEIPT_SCHEMA_VERSION == "1.4"` and the new fields appear in
      every newly-written attempt JSON.
- [ ] Existing attempt JSONs (schema 1.3) on disk either load successfully
      with null supersession fields OR are rejected with a clear error message
      (document the chosen policy).
- [ ] Consumer (the loader at `close_runner.py:207-210`) rejects attempts
      whose `source_head` does not match the current HEAD, with a configurable
      override for "I know HEAD moved, accept anyway."
- [ ] Consumer marks prior attempts as `superseded` when a new attempt has
      `supersedes_attempt_id` pointing at them.
- [ ] Tests cover: (a) writing a 1.4 receipt, (b) reading a 1.3 receipt
      (backward compat), (c) rejecting a stale-HEAD receipt, (d) supersession
      chain handling.

## Out of scope

- **Producer-side supersession detection** (automatically deciding when to
  mark an attempt as superseding another) — this is a separate concern. The
  initial implementation can require the caller to pass `supersedes_attempt_id`
  explicitly. Auto-detection of stale HEAD reruns is a follow-up.
- **Cross-session supersession** — supersession within one session is the
  scope. Cross-session (session A's attempt supersedes session B's) is a
  different problem.
- **Workstream D** (`/check` performance) — has its own handoff at
  `P:/docs/handoffs/check-speed-optimization-20260726/HANDOFF.md`. Execute
  that handoff; don't fold it into this one.
- **Phase timing for `/close`** — the original improvement doc listed this
  as a Workstream B item. It's actually separable; deferred.

## Related artifacts

- **Wiki concept (new, this session):** `P:/.data/wiki/concepts/single-repo-verification-false-negative-on-multi-repo-workspace.md`
  — the meta-finding about cross-repo `git log` false negatives. Directly
  relevant: `source_repo` field in the new schema would have prevented the
  `c4e9897` false refutation (the consumer would have seen source_repo
  was `~/.grok` and queried the right repo).
- **Commit:** `ac15837` in `~/.grok` repo — Workstream B implementation
  (workspace injection, --no-mutate, session-bound temp attribution).
- **Original 14-item doc:** the source document that motivated this work
  (visible in session 019fa111 transcript turns 1 and 2).
- **`/tp` critique log entries:** `214425c847f0` (initial REVISE, partially
  wrong), `ab9ac769201c` (re-review PROCEED after operator's rebuttal).

## Dependencies

- Requires: nothing (Workstream B is shipped; this builds on the same Config
  infrastructure if needed, but the changes are in close_runner.py not
  close_accounting.py).
- Blocks: nothing.
- Non-blocking to: Workstream D (different file, different concern).

## Status

OPEN — ready for implementation. Estimated effort: ~2-4 hours (4 new fields,
consumer-side rejection logic, backward-compat policy decision, ~6 tests).
