---
title: "Session close-out: characterization-claim receipt rule + Option B escalation + maintain test-fire"
created: 2026-08-06
session: 019fc303
status: OPEN
assignee: unassigned
---

# Session close-out handoff: three open items from /insight + /aar

## Summary

Three actionable items surfaced by the /insight + /aar + /why close-out sequence
that were not implemented in-session. Each has a clear fix and no blocking
dependency.

## Item 1: Characterization-claim receipt rule extension

**Source:** /why --persist investigation (`why-quota-tier-conflation-20260806`)
**Priority:** HIGH — 3 of 5 operator corrections this session were characterization errors
**Chronicity:** chronic — the pattern recurs across sessions (asserting-runtime-behavior-from-memory)

**Fix:** Extend the receipt rule in `~/.grok/AGENTS.md` to explicitly cover characterization claims:

> Characterization claims — "X uses Y quota model," "X supports Z feature," "X works by W mechanism" — require the same receipts as causal claims. If you haven't run the verification command this session, label [INFERENCE].

Add "quota model" to the domain examples alongside runtime/platform/library behavior.

**Effort:** 5 minutes (one paragraph addition to existing rule)
**Falsifier:** If the agent runs `/usage` or `/model-quota` before making quota claims, the conflation cannot occur.

## Item 2: Option B — instance→class escalation instruction

**Source:** /insight finding #8, /aar opportunity O2
**Priority:** HIGH — chronic cross-session pattern
**Chronicity:** chronic — recurs in every session where the agent fixes defects

**Fix:** Add a one-line instruction to the AGENTS.md file-editing protocol:

> After fixing a defect, check: is this defect a one-off or a class? If a class, escalate to the abstraction before declaring that fix done.

This fires at every fix, not just at session end. Lightweight (one question, not a 4-question checklist).

**Effort:** 2 minutes (one line addition)
**Note:** This was proposed in an earlier arc of this session but never implemented.

## Item 3: Test-fire /maintain --dry-run

**Source:** /insight finding #15, /aar opportunity O4
**Priority:** MED — the skill has never been executed end-to-end despite 7 defect fixes
**Chronicity:** acute — specific to this session's work

**Fix:** Run `/maintain --dry-run` after the REV-003 lock fix is implemented (handoff: `maintain-lock-noop-fix-20260802`). Verify the full flow works end-to-end.

**Effort:** 15 minutes (after REV-003 fix)
**Dependency:** REV-003 must be fixed first (the concurrent lock is currently a no-op)
