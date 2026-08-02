---
thread_id: ship-skill-extraction-20260802
parent_handoff_path: none
current_session_id: 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e
current_terminal_id: console
produced_at: 2026-08-02T00:00:00Z
status: open
handoff_type: implementation_plan
accurate_as_of_head: current main on both repos
---

# Handoff: Extract /ship from /go stub into standalone skill

## Context

Session 019fa111 discovered that `/ship` is a compatibility stub that says
"read /go SKILL.md § ship profile and execute it fully." The stub design
caused the LLM to skip the review and verify phases (Phase 1 and Phase 3)
because the ship-relevant instructions are diluted across 1,180 lines of
non-ship `/go` content. The operator confirmed `/ship` should be its own
full skill.

## Root cause

The stub pattern ("read another skill and execute part of it") is
structurally weaker than owning the phases directly. The LLM cherry-picks
the easy parts (run ship_receipt.py, fill fields) and skips the hard parts
(review specialist, fix-loop, LLM-judgment checks).

## Scope

### What to extract from /go SKILL.md

Lines 800-1020 (the `ship` profile section). This contains:
- Phase 0: Detect what to ship (multi-repo, branch detection)
- Phase 1: Self-review (inline + 1 specialist subagent)
- Phase 2: Fix-loop (max 2 iterations)
- Phase 3: Verify (mechanical receipt + LLM-judgment checks)
- Phase 4: Safe-merge (stash check, merge, post-merge test)
- Phase 5: Auto-close prep (handoff update, wiki promotion)
- Ship receipt format (mandatory output)
- SHIP BLOCKED output format
- Merge decision matrix
- Hard rules for ship

### What stays in /go

- Profile table entry for `ship` changes from full profile to delegation:
  `ship` → "invoke `/ship` skill directly" (same pattern as `review` → `/review`)
- `ship-check` profile stays in `/go` (lightweight verify-only, not publish pipeline)
- `/go`'s Examples table: `/go ship` → "delegates to `/ship` skill"

### What to create

1. **`~/.grok/skills/ship/SKILL.md`** — full standalone skill (~350 lines):
   - Frontmatter: `depends_on: [check, review, handoff, grok-safe-git]`
   - Purpose: verify-and-publish pipeline
   - 5 phases extracted from /go (adapted to be self-contained)
   - Phase-log mandatory validation (already exists in ship_receipt.py)
   - Receipt format
   - Hard rules

2. **Keep `~/.grok/skills/go/__lib/ship_receipt.py`** in place — `/ship` references it by absolute path. No need to move it.

3. **Update `/go` SKILL.md**:
   - Lines 800-1020: replace with a 3-line delegation entry
   - Profile table (line ~349): `ship` → "delegate to `/ship` skill"
   - Examples table: update `/go ship` entry

## Acceptance criteria

- [ ] `/ship` SKILL.md exists as a standalone skill with all 5 phases
- [ ] `/ship` frontmatter declares `depends_on: [check, review, handoff]`
- [ ] `/go` SKILL.md ship section replaced with delegation pointer
- [ ] `/go` profile table routes `ship` → `/ship` skill (like `review` → `/review`)
- [ ] `/go` Examples table updated
- [ ] `/ship` references `~/.grok/skills/go/__lib/ship_receipt.py` by absolute path
- [ ] Phase-log validation requirement preserved in `/ship` SKILL.md
- [ ] Merge decision matrix preserved in `/ship` SKILL.md
- [ ] SHIP BLOCKED output format preserved
- [ ] `/ship` skill description updated in frontmatter to reflect standalone status
- [ ] Tests: `/go` still parses, `/ship` loads correctly

## Why this matters

The stub design caused a real quality failure in session 019fa111: 3 code
changes were declared "SHIP DONE" without running Phase 1 (review) or Phase 3
(LLM-judgment checks). The operator caught it. The structural fix is to make
`/ship` own its phases so the LLM's context window is filled with ship-relevant
instructions at 100% density, not 20%.

## Design decision (from /tp analysis)

**Why standalone, not a thicker stub:** The stub pattern fails because the LLM
loads the entire `/go` SKILL.md (1,180 lines) to find 250 lines of ship
instructions. The ship-relevant content is at ~20% density. A standalone skill
gets 100% density. The difference between "read another skill and find the
relevant part" and "this IS the skill" is the difference between
context-dilution and context-focus.

**Why not move ship_receipt.py:** It already works at its current path. Moving
it would break any concurrent sessions that reference it. `/ship` references
it by absolute path (`~/.grok/skills/go/__lib/ship_receipt.py`).

## Related artifacts

- `/go` SKILL.md: lines 800-1020 (source material for extraction)
- `/ship` SKILL.md: current stub (to be replaced)
- `~/.grok/skills/go/__lib/ship_receipt.py`: mechanical receipt generator (stays)
- Wiki concept `cross-module-call-graph-audit-false-negative`: the pattern that
  made the stub failure visible

## Status

OPEN — ready for implementation. Estimated effort: ~1 hour (extract, adapt,
update /go, verify both skills parse).
