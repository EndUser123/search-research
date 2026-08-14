# Handoff: ship-py regret-scan scope contamination

## Status
CLOSED — subsumed by ship-close-py-session-scope-isolation-20260813

## Problem

The ship-py `regret-scan` phase (v2.5) reads the dirty tree instead of
session-scoped files, causing it to block on findings from sibling-session
work and pre-existing uncommitted changes.

## Evidence

Session 019ffb95 (2026-08-13) ran `/ship-py` after editing `/www` SKILL.md.
The regret-scan phase blocked with 10 findings, ALL from files outside
the session scope:

| File | Source |
|------|--------|
| `.data/wiki/sources/transcripts/fe26785c-*.md` | Sibling session wiki work |
| `hooks/tests/test_quality_gates_frontmatter.py` | Pre-existing dirty tree |
| `state/observation-tool-log/*.jsonl` | Fleet state logs |

None of the 10 findings were from files the session touched. The
`UNBOUNDED_FILE_CREATION` pattern matched legitimate test code and wiki
content that happened to contain `mkdir()` and `write_text()` calls.

## Root cause

The regret-scan phase does not filter its input to session-scoped files.
It scans the full dirty tree, which on a multi-agent host includes
sibling-session work, test fixtures, and state logs.

This is the same multi-terminal isolation pattern documented in
`[[multi-terminal-isolation-stale-data-immunity]]` — scope detection
must default to session-scoped, never the shared dirty tree.

## Fix

1. The regret-scan phase should consume the detect phase's
   `session_files` list (already produced by detect) and only scan
   those files.
2. Fallback: if no session files detected, scan the git diff (committed
   work) rather than the dirty tree.
3. The `UNBOUNDED_FILE_CREATION` pattern needs a severity review —
   matching `mkdir()` in test fixtures and wiki content is a false
   positive. The pattern should exclude test directories or require
   additional context (e.g., production code path, not test fixture).

## Acceptance criteria

- [ ] regret-scan only scans session-scoped files (from detect phase)
- [ ] Test fixtures and wiki content are excluded from regret patterns
- [ ] A ship-py run with sibling-session dirty tree activity completes
      without false-positive blocks

## Files to modify

- `~/.grok/skills/ship-py/__lib/phases/regret_scan.py` — scope filter
- `~/.grok/skills/ship-py/__lib/phases/regret_scan.py` — pattern
  exclusion for test/wiki paths
