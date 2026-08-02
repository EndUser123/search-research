---
title: Improvement Opportunities — Session 019f902a
type: handoff
domain: lifecycle
created: 2026-08-01
source_session: 019f902a-621d-7711-9436-7c6003c57793
host: grok
status: open
---

## Improvement Stream — Tier 2 (operator decision needed)

These findings are routed to the improvement stream (actionable items, NOT wiki concepts). Each needs an operator decision before being persisted as a task or handoff.

---

### 1. Enhance quality_gate.py Stop hook to check exit codes

**Category:** Experience improvement / system gap
**Signal:** The Stop hook detects that a verification command ran but not whether it passed. Agent could run `pytest`, get 5 failures, and claim done.
**Recommendation:** Add exit code checking to the verification scan in `quality_gate.py`. The hook already tracks `verification_ran` — extend it to also track `verification_passed` by checking the exit code of the verification command.
**Effort:** ~2 hours
**Priority:** Medium

### 2. Add file-coverage check to quality_gate.py Stop hook

**Category:** System gap
**Signal:** The hook tracks which files were modified but not whether tests for those specific files ran. Any test command satisfies the gate regardless of relevance.
**Recommendation:** Add file-coverage matching (modified files -> relevant test files) to the Stop hook's verification scan. This is a harder problem — requires mapping source files to test files.
**Effort:** ~3 hours
**Priority:** Medium

### 3. Fix /go H6 pack to stop referencing dead grok-verify skill

**Category:** System gap
**Signal:** /go SKILL.md line 484 says "Execute grok-verify" — proven by transcript scan that grok-verify never fires across 20 sessions. The H6 pack is dead prose that creates a false sense of verification enforcement.
**Recommendation:** Either delete grok-verify and update /go to reference the Stop hook as the real enforcement, or update H6 to document that grok-verify is advisory and the Stop hook is the actual gate.
**Effort:** 10 min (delete + update) or 0 min (document only)
**Priority:** High

### 4. Add forward synthesis mode to /tp

**Category:** Experience improvement
**Signal:** The operator asked "what should we do next" and /tp went into critical-friend mode instead of producing forward recommendations. No skill in the workspace synthesizes session findings into prioritized forward recommendations with short/medium/long horizons.
**Recommendation:** Add a /tp forward-synthesis mode or create a new /synthesize skill that produces prioritized forward recommendations from session findings.
**Effort:** ~4 hours (new skill)
**Priority:** Medium

### 5. Decide on grok-verify and verification-before-completion disposition

**Category:** System gap
**Signal:** Both skills are dead weight at the VERIFY gate. grok-verify never fires. verification-before-completion is a skill document that describes how to do something the Stop hook already enforces structurally.
**Recommendation:** Operator decision needed on whether to delete grok-verify, update /go references, and accept verification-before-completion as inert documentation, or invest in making them actually fire.
**Effort:** Decision only, then 10 min implementation
**Priority:** High

---

## Coverage Check

| Check | Result |
|-------|--------|
| /aar ran | No — 2 corrections recovered from transcript |
| /wiki ran | No — 3 durable knowledge items recovered |
| Decisions promoted | No — 4 architectural decisions recovered |
| Corrections captured | 1 uncaptured correction found (operator corrected /plan characterization) |
| Friction addressed | 1 uncaptured friction point (/tp marathon design session — 77 assistant responses across 4 review rounds) |

---

## Tier 1 Auto-Capture (already persisted)

| Finding | Output | Status |
|---------|--------|--------|
| Agentic SDLC domain classification | Wiki concept | Persisted |
| Verification-before-completion enforcement gap | Wiki concept | Persisted |
| Disconfirmation pass technique | Wiki concept | Persisted |
| /plan is a skill, not a mode | AGENTS.md rule | Persisted |

---

## Next Actions

1. Operator decides on Tier 2 findings (items 1-5 above)
2. If accepted, route to /friction or task backlog
3. Run /capture again after decisions are made to update coverage status