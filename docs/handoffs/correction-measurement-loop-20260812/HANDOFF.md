---
title: "Correction-measurement loop (deferred — trigger-based)"
created: 2026-08-12
status: open
session_id: 019ff2ae-915b-70e2-99ec-ccd70f72fe2e
tags: [measurement, correction-tracking, behavioral, deferred]
---

# Correction-measurement loop

## Objective

Measure whether the empowerment-over-prohibition block in AGENTS.md is reducing needless-confirmation questions across sessions. The wiki documents a ~50% compliance ceiling for prose rules. Without measurement, we cannot tell whether interventions are working.

## Trigger condition

Build only if the needless-questioning pattern (agent asks permission on reversible actions it already has the answer to) recurs in 2-3 more sessions. If it doesn't recur, the empowerment block is sufficient and no infrastructure is needed.

## Structural approach (if trigger fires)

**NOT lexical pattern matching.** The original proposal used regex on the transcript (`disagree|wrong|shouldn|...`) which produces high false positives on normal technical discussion.

Instead: **turn-boundary shape detector**:
- Operator turn <15 words
- Follows agent turn >200 words
- Contains question mark or imperative verb

This catches the correction shape ("Is this a question without a point?", "recommendation") without matching normal technical discussion ("why are you using that library?").

## Acceptance criteria

- SessionEnd hook writes `P:/.artifacts/corrections/<session-id>.json` with structural correction count
- `/close` step surfaces "N correction-pattern matches this session" (reads aggregated trend)
- False positive rate <50% (the falsifier from the original scope)

## Key files

- `~/.grok/scripts/scan_corrections.ps1` — existing lexical scanner (needs rewrite to structural)
- `~/.grok/skills/close/SKILL.md` — /close step integration (or close-py accounting phase)
- `P:/.data/wiki/concepts/evidence-first-default-and-needless-confirmation.md` — the wiki concept

## Effort

M (15-60 min) — rewrite scanner, add SessionEnd hook, add close-py integration.
