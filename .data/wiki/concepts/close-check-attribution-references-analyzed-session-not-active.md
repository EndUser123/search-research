---
title: "Close-check workflow attributes artifacts to the analyzed session, not the active session"
created: 2026-08-01
source: session-019fbf26-08f9-7f12-ace1-15ce7541c140
tags: [close-check, session-attribution, cross-session, workflow, handoff, metadata, source_session]
summary: >
  When close-check examines a prior session, the artifacts it produces
  (handoffs, wiki concepts, /trace reports, /capture opportunities) are
  attributed to the prior session in metadata fields (`source_session:`,
  handoff filename slug, concept frontmatter `source:`), even though the
  active session running close-check is the one that actually generated them.
  This is a near-miss for cross-session attribution confusion: a reader
  looking at `improvement-opportunities-019f902a-20260801.md` would attribute
  it to session 019f902a, but session 019fbf26 (the active one) is the
  actual producer. The pattern is intentional (artifacts belong to the
  session whose state they describe), but downstream consumers need to
  understand the distinction.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - P:/docs/handoffs/improvement-opportunities-019f902a-20260801.md (frontmatter source_session)
  - P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md (active session handoff)
  - P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md (source: session-019f902a)
  - P:/.data/wiki/concepts/close-check-invokes-capture.md (source: session-019f902a)
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: extends
  - target: wiki/concepts/close-check-invokes-capture.md
    type: extends
  - target: wiki/concepts/close-scanner-unavailable-fallback-session-observations-handoff.md
    type: related
  - target: wiki/concepts/rhai-workflow-launch-time-snapshot-staleness.md
    type: related
---

# Close-check workflow attributes artifacts to the analyzed session, not the active session

## Decision context

**Why this matters:** Session 019fbf26-08f9-7f12-ace1-15ce7541c140 was a close-check session that examined a prior session (019f902a-621d-7711-9436-7c6003c57793). The prior session had failed to fully resolve its close gates, so the active session used close-check to investigate, remediate, and write artifacts. The artifacts produced include wiki concepts, handoffs, and improvement opportunities — and every one of them is attributed to the analyzed session in metadata, not the active one.

**The risk:** a future reader who finds `P:/docs/handoffs/improvement-opportunities-019f902a-20260801.md` and reads `source_session: 019f902a-621d-7711-9436-7c6003c57793` in the frontmatter will reasonably conclude session 019f902a produced it. They would be wrong. The active session 019fbf26 produced it while analyzing 019f902a's state. This causes two distinct failure modes (one related to [[rhai-workflow-launch-time-snapshot-staleness]] where the workflow snapshot itself is stale):

1. **Session attribution confusion** — the "real" producer of the artifact is hidden behind the analyzed session's ID. If a future session encounters the artifact and runs `git blame` or transcript search expecting to find it in 019f902a's transcript, the search will not find it (it lives in 019fbf26's chat_history.jsonl).
2. **Provenance and audit gaps** — if an audit asks "which session wrote wiki concept X?" the frontmatter answer is wrong. The producer was a different session than the one named in `source:`.

## The pattern, in concrete form

When close-check runs `wf_019fbf3c872070d3b0bba44facdfd293` (the recovered launch of session 019fbf26) against the analyzed session `019f902a-621d-7711-9436-7c6003c57793`, the workflow's Phase 3 (Remediate) runs `/capture`, `/friction`, `/handoff`, `/trace`, and `/wiki` as auto-act subagents. Each subagent receives pre-packed evidence about the analyzed session, not the active session, and produces artifacts attributed to the analyzed session.

| Artifact | Field | Value | Active session |
|---|---|---|---|
| `improvement-opportunities-019f902a-20260801.md` | `source_session` | `019f902a-621d-7711-9436-7c6003c57793` | 019fbf26 |
| `close-check-workflow-replaces-close-for-session-readiness.md` | frontmatter `source:` | `session-019f902a-621d-7711-9436-7c6003c57793` | 019fbf26 |
| `close-check-invokes-capture.md` | frontmatter `source:` | `session-019f902a-621d-7711-9436-7c6003c57793` | 019fbf26 |
| `/trace` report | analyzed | `~/.agents/scripts/log_spawn.py` modifications from 019f902a | 019fbf26 |
| `P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md` | `session_id` | `019fbf26-08f9-7f12-ace1-15ce7541c140` | 019fbf26 (this one is correctly attributed to the active session) |

The active session is the producer in all five cases. The frontmatter reflects the analyzed session everywhere except the session-observations handoff.

## Why this is intentional

The artifacts belong to the analyzed session's lifecycle state. The improvement opportunities describe what session 019f902a should have done; the wiki concepts describe properties of close-check that emerged from examining 019f902a; the /trace report analyzes code modifications from 019f902a's pre-session state. The `source:` field is "the session whose state this describes," not "the session whose LLM ran this prompt." This is consistent with how human-authored documentation cites the subject, not the author.

**But it is a tradeoff.** The convention makes the analyzed session the source of truth, which is correct for downstream consumers (operators reading the artifact want to know what state the analyzed session was in). However, it makes the producer session invisible to anyone auditing "who wrote this." There is no field in the frontmatter for "producer session" or "authored_by."

## What this means for our workspace

1. **When investigating an artifact's production history, do not trust `source_session` / `source:` alone.** Search for the filename slug in `~/.grok/sessions/` to find the actual producer. The slug `019f902a` is the analyzed session, not necessarily the producer.

2. **When close-check produces a new artifact, the convention is to attribute it to the analyzed session.** This is correct for the analyzed-session-as-subject case. The active-session-as-producer case is lost unless a separate field names it.

3. **Operators reading handoffs and wiki concepts for the first time should expect them to be authored by a prior session, not the active one.** If "this session just wrote this" is the assumption, it is wrong for close-check-produced artifacts.

4. **The session-observations handoff is the exception** — it is correctly attributed to the active session (e.g., `session-observations-019fbf26-20260801.md` has `session_id: 019fbf26-...`). This is because it describes the active session's own state, not the analyzed session's.

## Open question

Should the frontmatter include an explicit `producer_session:` field for close-check-produced artifacts? Pros: closes the audit gap. Cons: doubles the metadata burden and forces the convention on authors who don't usually need it. No current wiki concept commits to either choice.

## Falsifier

This concept is wrong if:
- A further close-check is found where artifacts are attributed to the **active** session, not the analyzed session. If the convention is symmetric, the "analyzed vs active" distinction described here is moot.
- The frontmatter fields examined (`source_session`, `source:`) are found to be documentary convention rather than enforced metadata. If scripts and tools ignore these fields, the attribution risk is theoretical.
- The artifacts in question are correctly attributed in some other way (e.g., a separate `producer_session:` field exists and is populated). If the producer is recorded elsewhere, the gap described here is closed.

## Receipts

- `P:/docs/handoffs/improvement-opportunities-019f902a-20260801.md` line 5: `source_session: 019f902a-621d-7711-9436-7c6003c57793`. Producer was session 019fbf26 (verified by the workflow's path: `wf_019fbf3c872070d3b0bba44facdfd293` state.json references active session).
- `P:/docs/handoffs/improvement-opportunities-019f902a-20260801.md` body content: 11 improvement opportunities across 7 categories, generated by Phase 3 `/capture` subagent during session 019fbf26.
- `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` line 4: `source: session-019f902a-621d-7711-9436-7c6003c57793`. Producer was session 019fbf26 per workflow state.
- `P:/.data/wiki/concepts/close-check-invokes-capture.md` line 4: same `source:` field. Same producer.
- `P:/docs/handoffs/session-observations-019fbf26-20260801/HANDOFF.md` — the active-session handoff, correctly attributed to 019fbf26.
- `C:/Users/brsth/.grok/sessions/P%3A%5C/019fbf26-08f9-7f12-ace1-15ce7541c140/workflows/wf_019fbf3c872070d3b0bba44facdfd293/state.json` — the recovered launch, all 5 remediation subagents completed (`capture`, `friction`, `handoff`, `trace`, `wiki`).
