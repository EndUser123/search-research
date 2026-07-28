---
thread_id: handoff-cleanup-sweep-20260728
parent_handoff_path: none
current_session_id: 019fa94a-6738-7ec0-a516-335604633cf6
current_terminal_id: grok-build-primary
produced_at: 2026-07-28T18:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Handoff — handoff-closure sweep (80% open rate)

## Objective

Triage the 150 open handoffs in `P:/docs/handoffs/`. The fleet-wide friction
taxonomy scan (session 019fa94a) found that 80% of handoffs are status: open.
Many represent completed work that was never marked closed — reducing
signal-to-noise for future sessions that grep handoffs for genuinely open work.

## Why this exists

The corpus mining scan (`P:/tmp/mine_corpora.py`) found:
- 193 handoff files total
- 150 open (80%), 20 closed/resolved (10%), 19 unknown (10%)
- 117 handoffs have deferred/blocked signals

The `/close` continuation_coverage scanner checks for open handoffs but does
not close them — handoff closure is operator-invoked (Rung 4). This means
completed work stays "open" forever unless someone explicitly marks it closed.

## The proposed sweep

For each of the 150 open handoffs:

1. **Check if the work is actually done.** Grep git log for commits referencing
   the handoff's thread_id or topic. Check if the files mentioned in the
   handoff have been modified since the handoff was written.

2. **If done:** update status to `closed`, add a closure note with the commit(s)
   that completed the work.

3. **If partially done:** update status and mark which items are complete vs
   still open.

4. **If genuinely open:** leave as-is. These are real continuation candidates.

5. **If stale (no activity >14 days, no clear continuation path):** mark
   `status: stale` with a note. These are candidates for archival.

## Priority clusters

Based on the scan, these handoff clusters have the most deferred/blocked signals:

| Cluster | Signals | Notes |
|---|---|---|
| `aar-golden-circle-review-packet-20260725` | 77 | Review-only packet, may be resolved |
| `ytis-nlm-fetch-and-migration-20260720` | 15 | Active work area |
| `tp-deferred-opportunities-20260727` | 11 | 4 deferred /tp opportunities |
| `close-aar-mechanical-enforcement` | 10 | Close-skill enforcement |
| `deferred-factory-work-20260726` | 10 | Software-factory deferred items |

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** improved handoff signal-to-noise for all future sessions
- **Non-blocking to:** all other workstreams

## Falsifier

This sweep would be unnecessary if the 80% open rate is actually correct (150
genuinely open work streams). But 150 open work streams for a solo operator is
almost certainly noise, not signal — the real number is likely 15-30 genuinely
open items, with the rest being completed-but-unclosed.
