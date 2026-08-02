---
title: "Session close improvement capture gap"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [capture, close-check, session-lifecycle, improvement-opportunity, coverage-gap]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - ~/.grok/skills/capture/SKILL.md (the capture skill itself)
  - P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
  - Session transcript lines 209-232 (close sequence)
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: refines
---

# Session close improvement capture gap

## What happened

The `/close` scanner at the end of session 019f902a-621d-7711-9436-7c6003c57793 identified three gates needing attention (wiki_lifecycle, stale path references, close-check adoption). The close scanner surfaced these as needing operator decision, but the `/capture` skill was not invoked to systematically scan the full session for improvement opportunities across all 7 categories.

The session produced several uncaptured findings:
1. **Stale path references** — 9 references across 5 files pointing workspace-scope paths to user-scope skills (review, refactor). Fixed in-session but not captured as a reusable pattern.
2. **/www lifecycle script reference staleness** — `/www` SKILL.md referenced plugin-internal scripts that don't exist at the documented path. Fixed in-session.
3. **Close-check adoption** — `/close-check` replaces `/close` as the session readiness gate. The close scanner still references `/close` as the primary mechanism.
4. **Skill consolidation candidates** — `check-work` and `code-review` are deprecated aliases safe to remove; `grok-go` and `grok-sdlc` are active compatibility aliases that must not be removed. The `/close` scanner flagged these but didn't distinguish between safe and unsafe removals.

## Why this matters

The `/capture` skill exists precisely to catch these patterns mechanically. When `/capture` is not invoked as part of the close pipeline (or when `/close-check` replaces `/close` but `/capture` is not updated to match), improvement opportunities slip through — especially the "knowledge stream" findings that should be persisted as wiki concepts or AGENTS.md rules.

## The gap

`/close-check` is the new close mechanism, but `/capture` was designed for `/close`. The close-check workflow needs to invoke `/capture` (or equivalent) to ensure improvement opportunities are systematically captured before the session ends.

## Falsifier

If `/close-check` already invokes `/capture` or an equivalent scan, this gap is closed. If `/close-check` is used but `/capture` is not invoked, the gap persists.

## Receipts

- Session transcript lines 209-232 — close sequence without `/capture` invocation
- `~/.grok/skills/capture/SKILL.md` — the capture skill, invoked by `/close` not `/close-check`
- `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check replaces close
- `P:/.data/wiki/concepts/skill-catalog-scope-inconsistency-causes-cascading-read-failures.md` — stale path pattern documented
- `P:/.data/wiki/concepts/www-lifecycle-script-reference-staleness.md` — lifecycle script staleness documented
