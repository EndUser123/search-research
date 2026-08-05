---
thread_id: stale-handoff-cleanup-20260805
parent_handoff_path: none
current_session_id: 019fce56-da32-79c3-85f1-1ff2d6677580
parent_session: none
current_terminal_id: grok-main
produced_at: 2026-08-05T06:00:00-06:00
last_updated_by: 019fce56-da32-79c3-85f1-1ff2d6677580
last_updated_at: 2026-08-05T06:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 7cf15174d33e97c16ba5aa2d1bb8c032a57798b8
---

# Handoff — Stale handoff cleanup (188 open, 166 stale)

## 1. Objective

Triage and close stale handoffs: 188 open handoffs, 166 stale (>1 day old with no recent activity).

## 2. Status

OPEN — discovered by `/todo` scanner, never previously handed off as a cleanup task.

## 3. Producing context

- **Date:** 2026-08-05
- **Source:** `/todo` scanner (`handoffs` source)

## 4. Read-first list

1. Run `/handoff list` to see all open handoffs with age, status, and ownership
2. Prioritize by age: oldest first (>90 days = almost certainly closeable)

## 5. Verified facts

- [FACT] 188 open handoffs (4 today, 18 1-day-old, 166 stale) — verified by `/todo` scan 2026-08-05T04:57Z
- [FACT] Stale handoffs accumulate because `/close` and `/handoff close` are not consistently run across sessions

## 6. Current state

Handoffs accumulate monotonically. Most stale handoffs are from sessions that completed their work but never closed the handoff file. The work is done; the artifact is stale.

## 7. Task packets

### AC-01: Bulk triage stale handoffs
- **Goal:** Review all 166 stale handoffs; close completed ones, flag open ones
- **Acceptance:** `/todo` scanner shows <20 open handoffs (only genuinely open work)
- **Falsifier:** any stale handoff that actually has open work gets closed incorrectly
- **Verification:** run `/handoff list` after cleanup to confirm

## 8. Open decisions

None.

## 9. Hard constraints

- Do NOT close a handoff without reading its Status field — some stale handoffs may have genuinely open work
- Do NOT delete handoff files — mark status CLOSED and update the frontmatter

## 10. Cross-reference couplings

- Some handoffs reference each other via `parent_handoff_path` — closing a parent should verify children

## 11. Other outstanding streams

None for this work.

## 12. Explicit non-goals

- Do NOT merge or consolidate handoff files
- Do NOT redesign the handoff format

## 13. Resumption protocol

1. Run `/handoff list` to get the full inventory
2. For each stale handoff: read Status field → if CLOSED or work is done, mark closed
3. For genuinely open work: update the handoff with current status

## 14. Suggested next invocation

`/skill-prune` — this skill handles knowledge hygiene for stale artifacts

## 15. Last user message (verbatim)

> "are those open items captured?"

## 16. Epistemic labels

- [FACT] counts verified by `/todo` scanner
- [INFERENCE] "most stale handoffs are completed work" — pattern from prior close sessions

## 17. Suggested skills for next session

- `/skill-prune` — stale artifact cleanup
- `/maintain` — fleet maintenance orchestrator

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-05T06:00 | 019fce56... | created — backlog-to-handoff bridge |
