---
thread_id: b8c9d0e1-2f3a-4b5c-6d7e-8f9a0b1c2d3e
parent_handoff_path: none
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 21ca62d
---

# Instrument discovery-to-fix ratio: measure whether the workspace is a research engine or an execution engine

## Objective

Track the ratio of handoffs created vs. handoffs closed per session. If the ratio is worsening over time, the workspace is generating problems faster than it solves them. If stable or improving, the backlog is normal accumulation.

## Status

OPEN — baseline measurement taken (2026-07-27); instrumentation not built.

## Baseline measurement (2026-07-27)

| Date | Created | Open | Closed | Close rate |
|------|---------|------|--------|------------|
| 2026-07-18 | 1 | 0 | 1 | 100% |
| 2026-07-20 | 4 | 3 | 1 | 25% |
| 2026-07-21 | 8 | 8 | 0 | 0% |
| 2026-07-22 | 32 | 29 | 3 | 9% |
| 2026-07-23 | 12 | 9 | 2 | 17% |
| 2026-07-24 | 19 | 16 | 2 | 11% |
| 2026-07-25 | 13 | 9 | 1 | 8% |
| 2026-07-26 | 40 | 36 | 0 | 0% |
| 2026-07-27 | 44 | 35 | 4 | 9% |
| **Total** | **174** | **142** | **19** | **11%** |

**Discovery-to-fix ratio:** 174 created / 19 closed = **9.2:1** (9.2 problems discovered for every 1 resolved).

**Trajectory:** the ratio is **worsening**. Early sessions (07-18 to 07-21) had manageable ratios. Starting 07-22, the creation rate jumped to 32+/day while the close rate stayed flat. The last 3 days (07-25 through 07-27) produced 97 handoffs and closed only 5.

## Read-first list

1. `P:/.data/wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern.md` — documents the pattern
2. `P:/.data/wiki/concepts/complexity-magnet-subsystem-bug-accumulation.md` — the close-scanner as a specific instance
3. This handoff's baseline table above

## Task packet: build the instrumentation

- **goal:** Add a discovery-to-fix ratio report to `/close`. The scanner already counts handoffs; extend it to track created vs. closed by session date and report the ratio trend.
- **in scope:** `close_accounting.py` — add a `scan_handoff_lifecycle` function that groups handoffs by creation date, counts created vs. closed, computes the ratio, and reports the trend (improving/stable/worsening)
- **out of scope:** handoff staleness detection (separate task), bulk triage workflow (separate task)
- **acceptance:** `/close` output includes a line like `Discovery-to-fix ratio: 9.2:1 (worsening — 97 created, 5 closed in last 3 sessions)`
- **falsifier:** if the ratio doesn't correlate with workspace health (high ratio = more stale work; low ratio = more work shipped), the metric isn't useful
- **verification:** re-run `/close` after implementation — the ratio line should appear in the summary
- **disposition:** HANDOFF

## Research findings (item 4: are session-observations read?)

**Question:** Do future sessions actually read session-observations handoffs?

**Method:** grep all 987 session transcripts in `~/.grok/sessions/P%3A%5C/` for the string "session-observations".

**Result:** **112 of 987 sessions (11.4%) reference "session-observations."**

| Metric | Value |
|--------|-------|
| Total session transcripts | 987 |
| Sessions referencing "session-observations" | 112 (11.4%) |
| Sessions NOT referencing it | 875 (88.6%) |

**Interpretation:** session-observations handoffs ARE read — 112 sessions found and referenced them. But 88.6% of sessions don't reference them, which could mean either (a) most sessions don't have observations worth reading, or (b) most sessions don't know to look. The 11.4% hit rate is higher than expected for a write-only archive (which would be near 0%), confirming the observations have real readership.

**Implication:** session-observations handoffs are not ceremony. They're a functional part of the workspace's knowledge transfer. Continue writing them.

## Open decisions

None — the instrumentation is scoped and the baseline is measured.

## Resumption protocol

1. Read this handoff's baseline table
2. Implement `scan_handoff_lifecycle` in `close_accounting.py`
3. Add the ratio line to the close summary template
4. Test by re-running `/close`

## Suggested next invocation

```
/go "Add discovery-to-fix ratio reporting to /close. Read P:/docs/handoffs/handoff-discovery-to-fix-ratio-instrumentation-20260727/HANDOFF.md for the baseline data and spec. Add scan_handoff_lifecycle to close_accounting.py that groups handoffs by creation date, counts created vs closed, computes the ratio, and reports the trend. Add the ratio line to the close summary template."
```

## Explicit non-goals

- Do NOT build a full handoff triage system — that's a separate task
- Do NOT add staleness detection yet — measure first, then decide on triage
- Do NOT change the handoff format
