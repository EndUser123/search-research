---
title: "Obligation ledger (action-time, write-ahead)"
created: 2026-08-12
status: open
session_id: 019ff2ae-915b-70e2-99ec-ccd70f72fe2e
tags: [obligation-ledger, architecture, write-ahead-log, ISCG]
---

# Obligation ledger (action-time, write-ahead)

## Objective

Fix the Instruction-to-State Closure Gap (ISCG) documented in `[[instruction-to-state-closure-gap-obligation-ledger]]`. Obligations currently live in working memory (lossy). The fix shifts them to a durable ledger generated at action time.

## Scope

Three layers:

1. **PostToolUse hooks** generate obligation entries atomically when files are written. E.g., writing to SKILL.md generates "reindex skill catalog" + "check hooks that import from this skill".

2. **Agent-generated obligations** — when the agent states intent to defer or makes a decision, it writes a ledger entry in the same turn (structural enforcement of the "no deferred persistence" rule).

3. **close-py clearance** — reads the obligation ledger and verifies every entry is cleared. Replaces ad-hoc gate discovery with structured obligation verification.

## Reference architectures

- **LogAct** (Meta, arXiv:2604.07988) — agents as state machines playing a durable shared log. Intentions appended before execution.
- **SuperLocalMemory 4.0** (arXiv:2608.08253) — transactional obligation ledger with atomic SQLite commits.
- **PostToolUse obligation generation** (2026 production pattern) — standard pattern: PostToolUse hook on Write|Edit generates JSONL ledger entries.

## Acceptance criteria

- PostToolUse hook writes to `P:/.artifacts/obligations/<session-id>.jsonl` on every file write
- close-py reads the ledger and blocks CLOSE COMPLETE if entries are unresolved
- Obligation rules are declarative (not hardcoded per-file) — e.g., a config maps file patterns to obligation templates

## Key files

- `P:/.data/wiki/concepts/instruction-to-state-closure-gap-obligation-ledger.md` — the design concept
- `~/.grok/hooks/scripts/` — PostToolUse hook location
- `~/.grok/skills/close-py/__lib/phases/` — close-py phase integration

## Effort

L (>60 min) — requires hook design, obligation rule format, close-py integration, and testing.
