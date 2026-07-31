---
thread_id: recap-handoff-cross-invocation-20260731
parent_handoff_path: none
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 3c773c60-e09f-490c-a96b-b14fa5208849
produced_at: 2026-07-31T05:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 32395cc
---

# Handoff — /recap retrospective synthesis + /recap↔/handoff cross-invocation

## Objective

Enhance /recap to produce true retrospective output (not handoff-shaped forward-looking output) and wire cross-invocation between /recap and /handoff so each proactively suggests the other when conditions warrant.

## Status

OPEN — enhancements shipped. Future cross-invocation pairs identified but deferred to organic integration via meta-checkpoint.

## Read-first list

1. `~/.grok/skills/recap/SKILL.md` — new retrospective synthesis sections + cross-invocation table
2. `~/.grok/skills/handoff/SKILL.md` — Step 0 complexity check (suggests /recap for complex sessions)
3. `P:/.data/wiki/concepts/cross-invocation-skills-proactively-suggest-complementary-skills.md` — pattern with 8 identified pairs

## Verified facts

- [FACT] /recap SKILL.md now has 3 retrospective synthesis sections: causation chains, meta-level narrative, quality assessment (commit `1f38689`)
- [FACT] /recap has active cross-invocation: suggests /handoff, /debrief, /wiki when conditions detected (commit `1f38689`)
- [FACT] /handoff has complexity check pre-step: suggests /recap for sessions with ≥3 streams or ≥1 compaction (commit `1f38689`)
- [FACT] 8 complementary skill pairs identified in wiki concept (commit `4b6b6e6`)

## Current state

**Done (committed):**
- /recap retrospective synthesis (3 new output sections)
- /recap active cross-invocation table
- /handoff complexity check pre-step
- Wiki concept for the cross-invocation pattern

**NOT done (deferred to organic integration):**
- Cross-invocation for 7 other identified pairs (see wiki concept table)
- These will be applied when future sessions touch those skills, driven by the meta-checkpoint Q4

## Resumption protocol

No immediate action needed. The pattern propagates organically. The next session that touches /review, /close, /why, /check, /harvest, or /aar will be prompted by the meta-checkpoint to ask "should this cross-invoke?"

## Suggested next invocation

No action needed unless the operator wants to accelerate a specific pair integration.
