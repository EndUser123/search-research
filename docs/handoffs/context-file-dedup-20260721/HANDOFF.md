---
thread_id: 5c298571-7b40-4cdf-9ddf-cc4599bad45d
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T21:30:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: a58d372
source_transcript: C:/Users/brsth/.grok/sessions/P%3A%5C/019f8082-9298-7561-b03e-3c21afc43115/chat_history.jsonl
---

# Context-file deduplication — @AGENTS.md include strategy

## Objective

Determine whether Grok Build's compat scanner expands `@`-includes in CLAUDE.md files, then apply the appropriate deduplication strategy to eliminate ~1800 lines of duplicate context loaded every session.

## Status

OPEN — test setup committed, waiting for new-session verification.

## Background

The host auto-loads both AGENTS.md (Grok-native) and CLAUDE.md (Claude compat) format files every session. Total: ~2400 lines of context, mostly duplicated across formats. The compat layer (`compat.claude.rules = true`) is the mechanism.

## Research done

Wiki concept: `P:/.data/wiki/concepts/context-file-deduplication-agents-md-as-source.md`

Key findings:
- ETH Zurich study (Feb 2026): context files can *reduce* agent success by 3% when bloated
- Claude Code docs confirm `@AGENTS.md` include syntax is the canonical cross-tool pattern
- Windows caveat: use `@`-import, not symlinks (admin/dev mode required for symlinks)

## Test setup

Commit `377faea` added marker `COMPAT-TEST-MARKER-7KX2A` to `P:/CLAUDE.md`. The file already has `@AGENTS.md` import. On new session start, check:

- **Marker + AGENTS.md content →** `@`-includes ARE expanded → **apply A1 strategy**
- **Marker alone, no AGENTS.md content →** includes NOT expanded → **use B1 strategy**
- **Neither →** `CLAUDE.md` not loaded at all → different problem

## Strategies

**A1 (if includes expand):** Replace `~/.claude/Claude.md`, `P:/.claude/CLAUDE.md` with thin `@AGENTS.md` stubs. ~75% context token reduction. Reversible.

**B1 (if includes don't expand):** Audit Claude files for unique content not in AGENTS.md. Port the unique parts. Then replace with stubs. ~2 hours.

## Backups

Pre-test file snapshots at: `P:/tmp/claude-compat-snapshot-20260721-115051/`
- `P-Claude.md.bak` (24 bytes — original 2-line file)
- `P-.claude-CLAUDE.md.bak` (10368 bytes)
- `home-.claude-Claude.md.bak` (16845 bytes)

## Files to modify (once strategy confirmed)

| File | Current | After A1 | After B1 |
|---|---|---|---|
| `P:/CLAUDE.md` | `@AGENTS.md` + marker | `@AGENTS.md` (remove marker) | Port unique content to AGENTS.md, then stub |
| `P:/.claude/CLAUDE.md` | 10 KB constitution | `@AGENTS.md` stub | Port, then stub |
| `~/.claude/Claude.md` | 16.8 KB global prefs | `@AGENTS.md` stub | Port, then stub |

## Dependencies

- **Requires:** new session to verify compat-marker (same session as Group A hook diagnostics)
- **Blocks:** nothing
- **Non-blocking to:** Groups A and C
