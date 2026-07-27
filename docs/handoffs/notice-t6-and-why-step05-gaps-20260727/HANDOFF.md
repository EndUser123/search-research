---
thread_id: notice-t6-and-why-step05-gaps-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T17:35:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 08f33a2 (~/.grok)
---

# /notice T6 shipped; /why Step 0.5 handoff-query gap + compaction-tier-4 rule identified

## Objective

Ship the two remaining structural fixes from the compaction-inherited-diagnosis finding (`[[compaction-inherited-diagnosis-unverified-propagation]]`): (1) /why Step 0.5 should query open handoffs, not just wiki concepts; (2) compaction summaries should be classified as Tier 4 (unverified claims) in the evidence-tier system. T6 (the /notice trigger) is already shipped.

## The problem (one sentence)

A one-line addition to `/why` Step 0.5 (`rg -l "<keywords>" P:/docs/handoffs/`) would have found the correct diagnosis for the /close failure immediately, short-circuiting the entire wrong-framing RCA arc — but it's not there yet.

## What this session shipped (verified)

- `[FACT]` `/notice` v1.2 (commit `08f33a2`) — T6 trigger + spec/handoff lookup + self-improvement boundary + adaptive detection reframe. Receipt: `C:/Users/brsth/.grok/skills/notice/SKILL.md` version 1.2.0.
- `[FACT]` close_runner BUG-03 fix (commit `9b92ee5`) — `needs_llm_check` moved from DISALLOWED to ALLOWED gate states. Receipt: `close_runner.py:47-48`.
- `[FACT]` Wiki concept `[[compaction-inherited-diagnosis-unverified-propagation]]` (commit `0481182`) documents the failure mode + three structural fixes.

## What remains (two gaps)

### Gap 1: /why Step 0.5 handoff query (one-line fix)

**Current** Step 0.5 queries only wiki:
```powershell
qmd search --collection wiki --query "<failure-shape keywords>" --top-k 5
# Fallback: grep wiki concepts directly
Get-ChildItem P:/.data/wiki/concepts -Filter "*.md" | Select-String -Pattern "<failure-shape keywords>" -List
```

**Missing** — query open handoffs too:
```powershell
# Query open handoffs for prior investigations of the same failure
rg -l "<failure-shape keywords>" P:/docs/handoffs/
```

**Why this matters:** session 019f9f4f — the /why Step 0.5 queried the wiki, found a related concept (different gate: `verify`, not `background_tasks`), and proceeded as if the problem were novel. The open handoff `close-runner-needs-llm-check-block-20260726` had the correct diagnosis. It was never searched.

**The fix:** add the handoff query to Step 0.5 of `/why` SKILL.md. One paragraph addition. The Step 0.5 "VISIBLE-OUTPUT CONTRACT" should require the handoff query receipt alongside the wiki query receipt.

### Gap 2: Compaction summaries classified as Tier 4

**Current** /why Step 4b evidence-tier system:
- Tier 1: execution artifacts (logs, test output, command output from THIS session)
- Tier 2: official docs, specs
- Tier 3: static analysis (reading code)
- Tier 4: comments, unverified claims, speculation

**Missing:** explicit rule that compaction summaries are Tier 4, not Tier 1. A compaction summary is a *narrative about* prior execution, not an execution artifact. Diagnostic claims in compaction summaries cross the session boundary without their backing receipts.

**The fix:** add a bullet to Step 4b Rules: "Compaction summaries are Tier 4 — they are unverified narratives about prior sessions, not execution artifacts. A diagnostic claim from a compaction summary cannot be treated as [FACT] without re-verification in the current session."

**Why this matters:** the post-compaction session inherited "scanner limitation" from the compaction summary and treated it as Tier 1 (established fact). The /why RCA built on it without re-verifying. If the tier had been labeled Tier 4, the Step 1 observation-verification would have caught it.

## Recommended fix path

Both gaps are one-paragraph additions to `/why` SKILL.md:
1. Step 0.5: add handoff query + receipt requirement (~5 lines)
2. Step 4b: add compaction-tier-4 rule to the Rules list (~2 lines)

Estimated effort: 15 minutes including verification.

## Dependencies

- **Requires:** nothing. Both are text edits to an existing SKILL.md.
- **Blocks:** nothing critical.
- **Non-blocking to:** any active work stream.

## Cross-reference couplings

- `C:/Users/brsth/.grok/skills/why/SKILL.md` — the file to edit (Step 0.5 + Step 4b)
- `P:/.data/wiki/concepts/compaction-inherited-diagnosis-unverified-propagation.md` — the finding that motivates both fixes
- `C:/Users/brsth/.grok/skills/notice/SKILL.md` — T6 trigger already shipped (the /notice side of the same fix)

## Last user message (verbatim)

> /handoff

## Provenance

Written from session 019f9f4f after shipping T6 + close_runner fix + wiki concept. The two gaps are the remaining fixes from the compaction-inherited-diagnosis finding. Both are low-effort, high-value one-line additions to /why.
