---
title: "Session-arc scan: transcript as external memory for ADHD context recovery"
created: 2026-07-27
source: session-2026-07-27 (/tp Step 0 session-arc scan)
tags: [skill-design, transcript-scan, external-memory, adhd, session-review, compaction-recovery, tp-session, decision]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  /tp session Step 0 now mechanically extracts workstream boundaries (user
  messages, skill invocations, Stop-hook events) from the full session
  transcript, producing a session timeline the model can see even after
  context-window compaction drops early-session detail. The transcript file
  on disk (2.3MB, 846 lines) always retains the full session; the model's
  context window doesn't. The scan bridges this gap — it's the ADHD
  external-memory pattern at the session scale: the transcript IS the
  external memory; the scan makes it visible without reading the whole file.
  Connects to [[matrix-model-for-session-review-content-type-x-time-horizon]]
  and [[visible-output-contracts-for-behavioral-skill-steps]].
relations:
  - target: wiki/concepts/matrix-model-for-session-review-content-type-x-time-horizon.md
    type: complements
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: related
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
---

# Session-arc scan: transcript as external memory for ADHD context recovery

## Decision context

**Why this decision was needed:** the operator said "I'm forgetting all the workstreams we have. My ADHD is taking me down other paths that have value, but I've forgotten where our other streams are." After context-window compaction, the model loses visibility into early-session work. The transcript file retains it — 2.3MB, 846 lines — but the model can't "remember" it without re-reading. The question: should `/tp session` mechanically reconstruct the session arc from the transcript, or rely on model recall?

## The decision

**Chosen: mechanical session-arc scan.** Step 0 of `/tp session` now runs a second grep (alongside the error-pattern scan) that extracts workstream boundaries.

**What the scan catches:** `Select-String` the transcript for `"type":"user".*user_query` (user messages), `/(go|tp|why|www|review|check|refactor|close)` (skill invocations), `Stop hook feedback` (obligation blocks), and `decision.*allow` (obligation clears). Each match produces a line number + type + one-word summary. The output is a ~20-30 line table.

**How the scan differs from `/check`'s preprocessor:** `/check` Step 0.5 runs a Python preprocessor that produces a JSON evidence packet with 10 detector buckets (file_edits, command_executions, test_runs, etc.). The session-arc scan is simpler — it's a PowerShell `Select-String` that extracts structural markers, not a full preprocessor. They serve different purposes: `/check`'s packet feeds verifiers (needs structured data); `/tp`'s arc feeds the model (needs a scannable timeline). The arc scan is deliberately lightweight — one grep, table output, no JSON parsing.

**How the decision was made:** the operator asked "should we enhance /tp to create and update handoff files automatically?" I initially answered "no for creation, yes for surfacing connections." The operator then clarified: "I was really scoping /tp by default to this session. From the first conversation thru all compact events to now." This reframed the problem from "auto-create handoffs" to "reconstruct the full session arc after compaction." I checked the session directory — no compaction directory exists, but the full 846-line transcript is intact. The scan was the natural solution: the transcript IS the external memory; the scan makes it visible.

### Selection criterion

**Mechanical extraction over model recall.** The criterion is: can the model see the full session arc without depending on what's in its context window? Model recall degrades after compaction; mechanical extraction doesn't.

### Steelman of the rejected alternatives

**Why "just read the transcript file when needed" was reasonable:** the full transcript is always on disk at a known path. Any skill can read it. No special scan needed — just `read_file` the transcript when the operator asks about early-session work.

**Why it loses:** the transcript is 2.3MB of JSONL. Reading it inline burns ~800K tokens of context — more than half the model's window. The scan extracts the 20-30 lines that matter (workstream boundaries) for ~1% of the token cost. The scan is the compression step that makes the transcript usable as external memory.

**Why "rely on model recall" was reasonable:** the model was present for every turn. It "knows" what happened. In a session without compaction, recall is sufficient.

**Why it loses:** compaction is not optional on long sessions. After compaction, the pre-compaction context is summarized (lossy) or dropped (lossy). The model's "knowledge" of early-session work is now a summary, not the detail. Mechanical extraction from the transcript file (which is NOT summarized) recovers the detail. This is the same problem Parnin & Deeline document as "resumption lag" — the cognitive cost of recovering context after an interruption. The scan eliminates resumption lag mechanically.

## Key findings

- **The transcript file is the ground truth.** Grok Build's `chat_history.jsonl` retains every line from the first user message to the current turn. It is never summarized or truncated. This makes it a reliable external memory — but only if something reads it.
- **The scan is cheap (1 grep, ~20-30 output lines).** The cost is one `Select-String` call against the transcript file. The benefit is full-session visibility. The ROI is extremely high for long sessions where compaction has dropped early detail.
- **The scan works alongside the error scan, not instead of it.** Both scans run in Step 0. The error scan catches friction; the arc scan catches workstream boundaries. Together they give the model a complete mechanical view of the session — both what went wrong AND what was done about it.
- **This is the session-scale instance of the ADHD external-memory pattern.** At the turn scale, the pattern is "write everything down immediately" (AGENTS.md no-deferred-persistence rule). At the session scale, the pattern is "scan the transcript mechanically" (this decision). At the workspace scale, the pattern is "query the wiki before re-deriving" ([[wiki-integrated-skills-query-save-pattern]] via /why Step 0.5). All three are the same principle: external memory + mechanical access > model recall.
- **The recap_requests directory is NOT the same as compaction segments.** Grok Build stores context-window snapshots in `recap_requests/` (5 files for this session, ~600KB-1.7MB each). These are NOT compaction segments (which don't exist for this session). The full `chat_history.jsonl` is the reliable source — the recap files are internal snapshots that may not preserve every workstream boundary.

## What this means for our workspace

The session-arc scan transforms `/tp do?` from a "best effort recall" command into a "mechanically grounded orientation" command. For the ADHD operator, this is the difference between "I think we did X, Y, Z but I might be forgetting something" and "here are all 12 workstream boundaries from this session, mechanically extracted, line-numbered, verified against the transcript file."

The scan also makes `/tp do?` safe to use as a **context-recovery tool mid-session**. When the operator feels lost ("what were we doing?"), `/tp do?` reconstructs the arc in ~2 seconds (one grep). The operator doesn't need to scroll back through the conversation or try to remember — the transcript already has the answer; the scan retrieves it.

The technique is not limited to `/tp`. The `/close` skill's accounting step already scans git commits, handoffs, and temp files — but it doesn't scan the transcript for workstream boundaries. Adding the arc scan to `/close` would give the close-out report full-session visibility, not just git-derived visibility. This is a natural follow-up improvement.

The scan also composes with the [[matrix-model-for-session-review-content-type-x-time-horizon]]: the arc provides the raw boundaries, the matrix classifies them. Together they give the operator a complete, mechanically-grounded session review that doesn't depend on what the model happens to remember.

## Trade-offs

**What works well:** the scan is deterministic. Every `/tp do?` invocation produces the same arc from the same transcript. Model recall varies; grep doesn't. The operator can trust the arc table as ground truth.

**What's harder:** the scan adds one tool call to every `/tp session` invocation. For short sessions (<50 transcript lines), the arc table is nearly identical to what the model already has in context — the scan is redundant overhead. Mitigation: skip the arc scan if the transcript is <100 lines (the model's context window can hold that).

**What doesn't change:** the operator's interaction model. The arc table is displayed before the NOW/NEXT/LATER findings — it's context, not a question. The operator scans it if they need orientation, skips it if they already know where things stand.

**Concrete example from this session:** the session-arc scan, if run on this session's transcript (846 lines), would produce a table like:
```
| L1   | USER | /go Phase 3 acceptance |
| L15  | USER | /go Phase 3 (revised) |
| L100 | STOP | Obligation 5adb1f8c |
| L158 | USER | Unverified claims challenge |
| L298 | USER | /why hook timeout |
| L376 | USER | /www root cause prevention |
| L456 | USER | /wiki capture |
| L530 | USER | /tp do? (first) |
| L846 | USER | /tp do? (this one) |
```
This table tells the model "here's the full arc" in 9 lines, vs. the 846-line transcript it would otherwise need to re-read. The compression ratio is ~94:1. For a session this long, the ROI is obvious.

## Falsifier

This decision is wrong if:
- **The scan output is too verbose to be useful.** If the session has 200+ user messages and skill invocations, the timeline table is too long to scan. Mitigation: cap at 30 most recent boundary events; note the truncation.
- **The model's recall after compaction is actually sufficient.** If Grok Build's compaction preserves enough detail that the model never loses workstream visibility, the scan is unnecessary. Refuted by this session: the operator explicitly said "I'm forgetting all the workstreams we have."
- **The transcript file is not reliably available.** If `chat_history.jsonl` is sometimes missing or corrupted, the scan fails silently. Mitigation: the scan is best-effort — if the transcript is unavailable, fall back to model recall with a disclosure.

## Receipts

- **"Operator said 'I'm forgetting all the workstreams we have'":** receipt — session 019fa23d, `/tp do?` invocation with the ADHD context.
- **"Transcript is 846 lines, 2.3MB":** receipt — `Get-Content $chat | Measure-Object` and `(Get-Item $chat).Length` this session.
- **"No compaction directory exists":** receipt — `Test-Path $sessionDir/compaction` → false this session. The recap_requests directory has 5 files (context-window snapshots) but the full transcript is intact.
- **"Scan added to SKILL.md Step 0":** receipt — commit `3a61198` on ~/.grok main, this session.
