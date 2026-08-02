---
thread_id: skill-output-propagation-20260801
parent_handoff_path: none
current_session_id: 019fbf02-d3dd-7f72-9ad2-4538790c0a82
created: 2026-08-01
status: open
assigned_to: <unclaimed>
---

# Skill Output Pattern Propagation: 0-Proceed acceptance trigger + skill-chain composition surfacing

## Objective

Two skill-improvement patterns that worked well in /tp should propagate to other skills.

### Pattern 1: `0 - Proceed with All recommendations` acceptance trigger

`/tp do?` emits a numbered action list ending with `0 - Proceed with All recommendations.`
The operator replies `0` and the agent executes every item in the same turn.
This worked perfectly in session 019fbf02 — one keystroke executed 5 action items.

**Propagation targets:**
- `/todo` — produces a prioritized action list but no batch-accept trigger
- `/check` — surfaces multiple fixes but no batch-accept
- Any skill that emits a numbered action list

**Implementation:** add a `0 - Proceed with All recommendations.` line to the
output format, with the same acceptance-trigger semantics (reply `0`/`y`/`yes`
→ execute all).

### Pattern 2: Skill-chain composition surfacing

The operator ran /recap-grok → /todo → /tp do? → /wiki → /handoff in sequence.
The agent noticed the pattern during /tp do? but should have surfaced it earlier
(during /todo when the chain was already 3 skills deep). The value is in
surfacing the composition WHILE the operator is still in the chain, not after.

**Implementation:** when the operator invokes a 3rd skill in a recognizable
sequence, surface: "You've run X → Y → Z. This is a [session-close /
debugging / implementation] workflow. Consider [automated composition /
shorter path]."

**Effort:** M per skill (output format edit + acceptance logic)

## Status

OPEN — not started.

## Acceptance criteria

- [ ] `/todo` output ends with `0 - Proceed` when it contains actionable items
- [ ] `/check` output ends with `0 - Proceed` when it surfaces multiple fixes
- [ ] Skill-chain detection surfaces after 3rd skill in a recognized sequence

## Evidence

- Session 019fbf02: /tp do? `0 - Proceed` worked perfectly (5 items executed)
- Session 019fbf02: skill chain observed during /tp do? finding #6
