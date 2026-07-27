---
thread_id: skill-consolidation-grok-verify-check-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T17:30:00Z
status: open
handoff_type: investigation
---

# Skill consolidation investigation: should /grok-verify merge into /check (or other merges)?

## Objective

Investigate whether `/grok-verify` should be merged into `/check`, and whether the other `grok-*` skills (`/grok-safe-git`, `/grok-route`, `/grok-discovery`, `/grok-parallel`, `/grok-go`, `/grok-sdlc`) should be consolidated into their non-prefixed counterparts.

## The problem (one sentence)

The workspace has paired skills (`/grok-verify` + `/check`, `/grok-go` + `/go` aliases, `/grok-sdlc` + `/go`) whose overlapping functionality creates routing confusion and maintenance duplication.

## What we know (verified this session)

### /grok-verify vs /check

**`/grok-verify`** (`~/.grok/skills/grok-verify/SKILL.md`, 140 lines):
- Self-check completion gate: the agent proves ITS OWN work is done
- Steps: restate success criteria → prove code path → run real checks → git hygiene → definition-of-done checklist → verdict
- Emits: VERIFY: PASS / FAIL / BLOCKED
- Designed to run INLINE (same agent that did the work)
- Pairs with `/check` for adversarial subagent verification

**`/check`** (`P:/.grok/skills/check/SKILL.md`, 740+ lines):
- Independent verification: spawns fresh subagents to verify from OUTSIDE
- Steps: evidence packet → deterministic pre-check → concern detection → spawn verifiers (parallel) → merge verdicts → auto-/review escalation
- Emits: CHECK PASS / FAIL
- Designed to spawn SUBAGENTS (independent lens)
- Auto-escalates to `/review` when triggers fire

**Relationship:** they are complementary, not overlapping:
- `/grok-verify` = self-check (can the agent prove its own work?)
- `/check` = independent verification (do fresh subagents confirm it?)
- `/check` SKILL.md line 20: "Pair with `/check` for adversarial subagent verification when the change is non-trivial"

**Open question:** should `/grok-verify` merge into `/check`? The operator's position: they should be investigated for consolidation. Arguments for merge: they share the same SDLC stage (VERIFY), both produce PASS/FAIL verdicts, and `/check` is the more capable skill. Arguments against: they serve different verification modes (self-check vs independent). This needs a fresh investigation, not a conclusion from the current session.

### Other grok-* skills

| Skill | Pair | Relationship | Merge? |
|-------|------|-------------|--------|
| `/grok-verify` | `/check` | Complementary (self vs independent) | ❌ No |
| `/grok-safe-git` | (none) | Unique (concurrent-safe git preflight) | ❌ No |
| `/grok-route` | (none) | Unique (package-local instruction routing) | ❌ No |
| `/grok-discovery` | `/preflight` | Overlap — both do source-authority discovery | ⚠️ Investigate |
| `/grok-parallel` | (none) | Unique (worktree fan-out) | ❌ No |
| `/grok-go` | `/go` | Compatibility alias (explicit redirect) | ❌ Already aliased |
| `/grok-sdlc` | `/go` | Compatibility alias (explicit redirect) | ❌ Already aliased |

**The one real merge candidate:** `/grok-discovery` and `/preflight` — both do "evidence-backed inventory before non-trivial changes." `/grok-discovery` is Grok-native; `/preflight` is at `.agents/skills/`. Need to investigate whether they're functionally identical or have different scopes.

## Recommended investigation

1. **Do NOT merge /grok-verify into /check** — they're complementary
2. **Investigate /grok-discovery vs /preflight** — read both SKILL.md files, compare scope and capability. If functionally identical, merge the Grok-native one and DEPRECATED-mark the other.
3. **Leave the aliases** (`/grok-go`, `/grok-sdlc`) as-is — they're explicit redirects, not duplicates.

## Dependencies

- Requires: nothing blocking
- Blocks: nothing

## Next session protocol

1. Read `~/.grok/skills/grok-discovery/SKILL.md` and `P:/.agents/skills/preflight/SKILL.md`
2. Compare scope, capability, and registration
3. If identical: merge + DEPRECATED-mark the loser
4. If different: document the distinction in the portfolio

## Last user message (verbatim)

> /handoff if /grok-verify should be merged with /check, or the other grok* skills merged with other skills.

## Provenance

Written from session 019f9f4f after reading both `/grok-verify` and `/check` SKILL.md files and comparing their SDLC stages, triggers, and output formats.
