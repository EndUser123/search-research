---
thread_id: why-skill-redesign-design-doc-20260730
parent_handoff_path: none
current_session_id: 019fb189-b2ec-70f0-8d30-16a6e7bb5ad7
current_terminal_id: grok-build-terminal
produced_at: 2026-07-30T23:00:00Z
status: closed
handoff_type: investigation
accurate_as_of_head: TBD
---

# /why Skill Redesign — Design Doc In Progress

## Objective (one sentence)

Restructure /why Steps 9, 11, 12, 14, 16 with Toulmin fields, hypothesis diversification, Occam/Hickam convergence, tight feedback loop, Rule of Three, and admit ignorance — without adding new steps.

## Status

OPEN — /design run (ID: 03d74c48) produced a complete design doc + thorough 32-issue review. Writer revision round 1 was interrupted (644s, cancelled). The design doc and review file exist on disk and were partially revised.

## What exists on disk

| Artifact | Path | Status |
|---|---|---|
| Evidence brief (firewall output) | `C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\evidence-brief.md` | Complete (29KB, ~2950 words) |
| Design doc (writer round 1) | `C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\grok-design-doc-03d74c48.md` | Drafted (82KB, 638 lines), partially revised |
| Summary | `C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\grok-design-summary-03d74c48.md` | Written (may be stale) |
| Review (32 issues) | `C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\grok-design-review-03d74c48.md` | Complete review; partially updated by interrupted revision |

**WARNING: temp files will be reaped by the OS.** Copy to a durable location if you want to preserve them. The design doc content is also captured in the wiki concept below.

## Evidence base

The full research + design evidence is in: `P:/.data/wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md` (commit `8dd456b`). This concept contains:
- Toulmin field definitions (CLAIM/MECHANISM/RECURRENCE TEST/COUNTEREXAMPLE/EVIDENCE)
- Occam/Hickam convergence test
- Hermes benchmark findings (tight feedback loop, Rule of Three, hypothesis diversification, admit ignorance)
- Pressure-test results (COUNTEREXAMPLE + EVIDENCE are load-bearing; MECHANISM is fakeable)
- Red-team verdict (REVISE: don't add steps, restructure existing)

## Resumption protocol

1. **Copy the temp files to a durable location** (they will be reaped)
2. **Read the review file** to determine which of the 32 issues are still open (the interrupted revision may have addressed some)
3. **Resume the writer** (spawn a fresh subagent with the design doc + review file) to address remaining open issues
4. **Run the reviewer** again (re-review)
5. **Run the critical friend** (Step 5.5)
6. **Once consensus**: implement the design — it's a single-file edit to `C:\Users\brsth\.grok\skills\why\SKILL.md`

## Key design decisions (from the design doc)

| Step | Modification | Source |
|---|---|---|
| 9 | Hypothesis diversification (3 ranked before drilling) | Riddell + Hermes |
| 11 | Admit ignorance permission | Hermes |
| 12 | Toulmin 5-field structure (CLAIM/MECHANISM/RECURRENCE TEST/COUNTEREXAMPLE/EVIDENCE) | TRACE + pressure-test |
| 14 | Tight feedback loop + Rule of Three | Hermes benchmark |
| 16 | Occam/Hickam convergence test | Medical differential diagnosis |

## Critical review issues to watch (from the 32-issue review)

- **F-05**: Step 9a hypothesis diversification vs Step 11a competing explanations — division of labor not specified
- **F-06**: Step 12 COUNTEREXAMPLE vs Step 16 Occam/Hickam — overlap not clarified
- **F-10**: Implementation plan lacks behavioral verification step
- **F-17**: Missing premise labeling ([FACT]/[INFERENCE])
- **Missing**: Coupling & Code-Smell Inventory (mandatory when touching existing code)

## Hard constraints (from red-team + research)

- Do NOT add new steps (red-team verdict: restructure existing steps only)
- Do NOT add a reflection step (Huang et al.: intrinsic self-reflection degrades accuracy)
- COUNTEREXAMPLE and EVIDENCE are the load-bearing Toulmin fields; MECHANISM needs a specificity constraint

## Last user message (verbatim)

> "/design: redesign /why Steps 9, 11, 12, 14, 16 based on the convergence-gap wiki concept."

## Suggested next invocation

```
/design --fast Resume /why redesign. Read P:/docs/handoffs/why-skill-redesign-design-doc-20260730/HANDOFF.md.
Evidence base: P:/.data/wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md
Copy temp design artifacts from C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\ first (OS will reap).
```

---

## Revision 1 — 2026-07-31T00:30:00Z (session 019fb189)

**Trigger:** auto-update — /why redesign was implemented directly (option 2), not through the design doc loop.

**What changed:** The /why SKILL.md was edited directly with all 5 step restructurings:
- Step 9a: hypothesis diversification (3 ranked before drilling)
- Step 11c: admit ignorance permission
- Step 12: Toulmin 5-field structure (CLAIM/MECHANISM/RECURRENCE TEST/COUNTEREXAMPLE/EVIDENCE)
- Step 14: tight feedback loop + Rule of Three
- Step 16: Occam/Hickam convergence test

Commit: `45fd3e3` (~/.grok). The design doc and review artifacts in temp served their purpose (produced the specification, surfaced 32 issues including critical interaction problems). The critical issues (F-01 through F-06) were addressed inline during direct implementation.

**Status update:** CLOSED — redesign shipped. Open obligation: A/B test against /why-old (harvest item `01KYSR6ATR7QSTR7DYYEMSXV61`).

**Design doc artifacts** (temp, will be reaped): `C:\Users\brsth\AppData\Local\Temp\grok-design-03d74c48\` — design doc, evidence brief, review file. The evidence base lives durably in `P:/.data/wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md`.
