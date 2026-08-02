---
title: "Agentic SDLC verification layer divergence — consolidation candidates"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [agentic-sdlc, verification, skill-consolidation, close-check, capture]
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - ~/.grok/skills/capture/SKILL.md
  - ~/.grok/skills/close/SKILL.md
  - P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
  - P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: refines
  - target: wiki/concepts/close-check-invokes-capture.md
    type: related
---

# Agentic SDLC verification layer divergence — consolidation candidates

## What the session revealed

The `/close` scanner flagged consolidation candidates that need operator decision. These are improvements to the skill ecosystem, not knowledge to persist — they belong in the improvement stream (task backlog or handoff), not wiki concepts.

### Candidate 1: Remove deprecated skill aliases (safe)

| Skill | Status | Action |
|---|---|---|
| `check-work` | `status: deprecated` | Remove — `/check` is strict superset |
| `code-review` | `status: deprecated`, `disable-model-invocation: true` | Remove — `/review` absorbed the maintainability lens |

### Candidate 2: Do NOT remove active compat aliases

| Skill | Status | Why keep |
|---|---|---|
| `grok-go` | Active compat alias | Makes `/grok-go` work; removing breaks the alias |
| `grok-sdlc` | Active compat alias | Makes `/grok-sdlc` and `/sdlc` work; removing breaks the alias |

### Candidate 3: Do NOT remove verification-before-completion junction

| Path | Status | Why keep |
|---|---|---|
| `~/.agents/skills/verification-before-completion` | Junction into superpowers repo | Not a duplicate — same file exposed through two namespaces. Removing the junction breaks the `.agents` namespace path. |

### Candidate 4: `/close-check` should invoke `/capture`

The close-check workflow replaces `/close` but doesn't invoke `/capture`. The capture skill scans for 7 categories of improvement opportunity. Without it, improvement opportunities slip through at session close.

### Candidate 5: `/www` lifecycle script reference staleness

The `/www` SKILL.md references `wiki_after_write.py` and `wiki_state.py` as if they're globally available. They live in the cc-skills-sdlc plugin scope, not `P:/.data/wiki/scripts/`. Fixed in-session but the pattern is generalizable.

## Why these are Tier 2 (operator decision)

These are improvements that require the operator to decide:
- Which deprecated skills to remove (the scanner can't know if aliases are still used by external consumers)
- Whether `/close-check` should invoke `/capture` (architectural decision about close pipeline)
- Whether the `/www` lifecycle reference fix should be applied to the plugin's SKILL.md too (not just the user-scope copy)

## Receipts

- `~/.grok/skills/check-work/SKILL.md` — `status: deprecated` confirmed
- `~/.grok/skills/code-review/SKILL.md` — `status: deprecated`, `disable-model-invocation: true` confirmed
- `~/.grok/skills/grok-go/SKILL.md` — active compat alias confirmed
- `~/.grok/skills/grok-sdlc/SKILL.md` — active compat alias confirmed
- `~/.agents/skills/verification-before-completion` — junction confirmed by `fsutil reparsepoint query`
- `~/.grok/skills/www/SKILL.md` line 268 — stale reference confirmed and fixed
