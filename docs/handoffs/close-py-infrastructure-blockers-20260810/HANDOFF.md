---
title: close-py infrastructure blockers — durable fixes needed
status: OPEN
created: 2026-08-10
last_updated_at: 2026-08-10T21:00:00Z
session: 019fe25d-6979-7892-82ae-ebf68232312a
host: grok
chronicity: chronic
---

# close-py infrastructure blockers — durable fixes needed

## Problem

close-py cannot produce CLOSE COMPLETE for ANY session on this host due to 4
recurring infrastructure blockers. Each session hits them and either accepts
CLOSE INCOMPLETE or requires operator waivers. The fixes below are the optimal
long-term solutions.

## Blocker 1: AAR validator phantom episodes

**Symptom:** `validate_aar_report_with_packet` reports 11 episodes when the
report JSON block has 7. The phantom episodes cite event IDs like `chat-L230`
that don't exist in the report or the canonical-events.jsonl.

**Root cause (INFERENCE):** The validator may be reading stale state from:
- `.pyc` cache in `__pycache__/` (stale bytecode from a prior report version)
- Cross-session state in the terminal-scoped run dir (same isolation bug class
  as the /todo scanner session-scoping fix)
- The validator parsing BOTH the markdown table AND the JSON block

**Durable fix:** Clear `.pyc` cache before validation. Add session-scoping
to the run dir (use `<session-id>` not `<terminal-id>` as the artifact path
segment). If phantom episodes persist, debug `_coerce_report` and
`validate_aar_report_with_packet` to find where the extra episodes come from.

**Acceptance criteria:**
- [ ] AAR finalizer can produce `passed: True` for a report with correct JSON
- [ ] No phantom episodes in validation output
- [ ] `validate_aar_report_with_packet` sees exactly the episodes in the JSON block

## Blocker 2: close-py git-state gate not session-scoped

**Symptom:** `cross_repo_clean: false` because the scanner checks the full
git dirty tree (459 uncommitted files), not just this session's changes.

**Root cause (FACT):** The git-state scanner uses `git status --short` which
shows ALL uncommitted changes across all concurrent sessions. This is the
SAME bug class as the /todo scanner session-scoping issue — scanning the
shared dirty tree instead of session-scoped changes.

**Durable fix:** Session-scope the git-state check. Use the session's commit
range (`git log --since=<session-start>`) to identify this session's changes.
Only check dirty state for files that appear in this session's commits or
that this session modified (via mutation receipts or transcript scan).

**Acceptance criteria:**
- [ ] git-state gate checks only this session's files
- [ ] Sibling-session dirty files don't trigger `cross_repo_clean: false`
- [ ] The session's own uncommitted files still trigger the gate

## Blocker 3: Stale ship-py check-receipt

**Symptom:** close-py scan finds an INCONSISTENT check-receipt from an earlier
ship-py run in the same session. The receipt path is stale.

**Root cause (FACT):** `ship-py/019fe25d.../check-receipt/check-run.json` has
status INCONSISTENT because the receipt was written by an earlier ship-py run
that was superseded by a later run.

**Durable fix:** Add a cleanup step to ship-py's detect phase: when a new run
starts, remove or archive stale check-receipts from prior runs in the same
session. Alternatively, make close-py's scan skip receipts older than the
current ship-py state's `started_at`.

**Acceptance criteria:**
- [ ] Stale ship-py receipts don't trigger close-py's verify gate
- [ ] New ship-py runs clean up prior run's receipts
- [ ] Close-py scan only sees the latest ship-py receipt

## Blocker 4: session_observations gate

**Symptom:** close-py requires a session-observations handoff from the session.

**Root cause (FACT):** No automation — the agent must remember to write one.

**Durable fix:** close-py's accounting phase should auto-generate a
session-observations handoff from the session's work classification (the
done/partial/not-started items become the observations). This eliminates the
manual step.

**Acceptance criteria:**
- [ ] Close-py auto-generates session-observations if the accounting phase completes
- [ ] Generated handoff includes work classification, key decisions, and open items

## Related

- [[stop-hook-review-gate-hash-invalidation-loop]] — the Stop-hook loop (already fixed via session_resolver_shared.py)
- [[caller-context-as-parameter-not-callee-discovery]] — the pattern behind all session-ID resolution fixes
- [[fallback-paths-defeat-primary-fix-silent-undermining]] — applies to the git-state gate's full-tree scan
- Fleet-wide handoff: `fleet-wide-grok-session-id-empty-env-20260809` — same root cause class
