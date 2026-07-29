---
thread_id: tp-opportunity-scan-gate-20260728
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-28T12:35:00Z
status: closed
handoff_type: investigation
accurate_as_of_head: LATEST
---

# /tp opportunity-scan gate — check for existing handoffs before surfacing as opportunity

## Objective (one sentence)

Add a structural gate to the `/tp` opportunity scan that checks whether a track
already has a handoff with directions and acceptance criteria before surfacing
it as a "research opportunity" — if it does, the disposition is execute or defer,
not research.

## Status

CLOSED — implemented this session (019fa276, 2026-07-29). Two pieces:

1. `workspace_opportunity_scan.py` gained `scan_open_handoffs()` — scans `P:/docs/handoffs/` for OPEN handoffs, parses frontmatter status, checks for acceptance criteria sections, separates into `EXECUTE_OR_DEFER` vs `RESEARCH`. Commit `a63a785`.

2. `/tp` SKILL.md `/tp explore` section gained "Opportunity scan gate" instruction. Commit `66f37fc`.

Wiki concept `research-to-execution-ratio-self-reinforcing-pattern` updated with implementation receipt + amended falsifier. Commit `0232601`.

## Producing context

The research-to-execution-ratio pattern (wiki concept
`research-to-execution-ratio-self-reinforcing-pattern`) identified that the /tp
opportunity scan treats "has an open handoff with a direction" as equivalent to
"is an open opportunity." It is not — an open handoff with acceptance criteria
is execution-ready work, not a research opportunity. This caused a /www cycle
that confirmed 5 of 6 pre-existing handoffs instead of discovering new
directions.

## The fix

In the `/tp` SKILL.md's opportunity scan section (or `/tp explore`), add a
pre-filter step:

1. Before surfacing a track as an "opportunity," grep `P:/docs/handoffs/` for
   the track's keywords.
2. If a handoff exists with `status: open` and contains direction + acceptance
   criteria:
   - Tag it as `EXECUTE_OR_DEFER` (not `RESEARCH`)
   - Do NOT route it to `/www` for investigation
   - Surface it to the operator as "execution-ready: <handoff path>"
3. Only tracks with genuinely open uncertainties (no handoff, or handoff with
   open questions) should be tagged `RESEARCH` and routed to `/www`.

## Acceptance criteria

1. When `/tp explore` or `/tp session` surfaces an opportunity, it checks for
   existing handoffs first
2. Tracks with existing handoffs are tagged `EXISTING_WORKSTREAM` not `RESEARCH`
3. The operator sees "execution-ready" items separated from "research-needed"
   items

## Falsifier

The gate is wrong if it prevents legitimate research on tracks that happen to
have handoffs but whose direction has materially changed. Mitigation: the gate
tags as `EXECUTE_OR_DEFER`, not `BLOCK` — the operator can still choose to
research if the context has changed.

## Related

- Wiki: `research-to-execution-ratio-self-reinforcing-pattern`
- AAR: HL-01 (research-to-execution ratio is the binding constraint)
