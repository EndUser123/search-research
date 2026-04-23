---
name: Self-Referential Refactor & Terminal ID Fix
created: 2026-04-21
source: session 493a609c-7f86-44c8-9387-7482d29d5219
sha256: d9f6a9cd02d0fa6baf136b0db978d9bf91e67d6fcdb0cc92c36131ac1afd5483
tags: refactor, terminal-id, artifacts, self-referential, multi-terminal
---

# Self-Referential Refactor & Terminal ID Fix

## Session Summary

Ran `/refactor` on the refactor skill package itself (self-referential refactoring), then discovered and fixed a terminal ID resolution bug in `deduplicate.py`.

## Key Decisions & Findings

### 1. Self-Referential /refactor on Refactor Skill

Ran the full 15-step DISCOVER → DEDUPLICATE → CLASSIFY_DEBT → PRIORITIZE → PLAN → EXECUTE workflow on `P:/packages/cc-skills-sdlc/skills/refactor/`.

**Discoveries:**
- `code_scanner.py` had a P0 `NameError` — `from pathlib import Path` was missing (fixed by hook formatter before this session)
- 10 reference files were at package-root `references/` instead of `skills/refactor/references/` where SKILL.md resolves `references/`
- Stale artifacts: `scripts/__pycache__/`, `.claude/state/`
- SKILL.md Reference Files table was incomplete (1 entry + "planned" note)

**Actions taken:**
- Moved 10 reference files to `skills/refactor/references/` via `git mv`
- Updated SKILL.md Reference Files table to full 11-entry listing
- Cleaned up stale directories

### 2. Terminal ID Resolution Bug

User challenged: "Are you sure Terminal ID is correct? I thought it was WT_SESSION."

**Investigation revealed:**
- `canonical_terminal_id()` in `P:/packages/search-research/core/terminal_id.py` is the authoritative source
- Production priority chain: `CLAUDE_TERMINAL_ID` (override) → `WT_SESSION` (Windows Terminal, real production source) → `ConEmuServerPID` → `console_unknown`
- `WT_SESSION` is the actual mechanism on Windows 11 — `CLAUDE_TERMINAL_ID` is only an explicit override/testing escape hatch
- `deduplicate.py` had a broken fallback that **never checked WT_SESSION** — went straight from `CLAUDE_TERMINAL_ID` to hash

**Fix applied to `deduplicate.py`:**
- Try `canonical_terminal_id()` from `core.terminal_id` first
- Local fallback matches full priority chain: `CLAUDE_TERMINAL_ID` → `WT_SESSION` → `ConEmuServerPID` → hash
- Updated docstring to reflect correct priority

### 3. Artifact Path Convention

Reinforced understanding:
- Path: `P:/.claude/.artifacts/{terminal_id}/{skill_name}/`
- `terminal_id` provides multi-terminal isolation (each terminal gets its own artifact tree)
- Stable across compaction events within same terminal session
- No collisions between terminals in different sessions

**Cross-terminal exception:** Append-only logs consumed across terminals (e.g., `skill_coverage/`) use shared paths without terminal_id nesting.

## Files Modified

| File | Change |
|------|--------|
| `skills/refactor/scripts/deduplicate.py` | Fixed terminal_id resolution to use canonical chain |
| `skills/refactor/skills/refactor/SKILL.md` | Updated Reference Files table to full 11-entry listing |
| `skills/refactor/skills/refactor/references/*.md` | 10 files moved from package-root `references/` |
| `skills/refactor/scripts/__pycache__/` | Removed (stale) |
| `skills/refactor/.claude/state/` | Removed (stale) |

## Key Reference

- [[claude-hooks-v3]] — Claude Code Hooks Guide (related hooks context)

## Related

- Terminal ID resolution is governed by `canonical_terminal_id()` in `P:/packages/search-research/core/terminal_id.py`
- Artifact path convention documented in `P:/.claude/CLAUDE.md` and skill SKILL.md files
- Multi-terminal isolation is a core design principle for all skill artifact writing
