---
title: concurrent-session-commit-collision
created: 2026-07-27
sources: []
relations:
  - target: session-019f9f4f-shipped-work-20260726
    type: handoff
  - target: working-in-the-shared-main-tree-no-worktree
    type: concept
---

# Concurrent session commit collision

## Problem

On this multi-agent host (Grok Build), multiple sessions work in `P:/` without
worktrees. When Session A commits tracked files, Session B's working-tree edits
to those same files can be silently overwritten when the working tree updates.

## Pattern

1. Session A and Session B both edit files in `P:/` shared main tree
2. Session A commits (staging its changes)
3. Session B's uncommitted edits to the same files are at risk
4. If Session B's working tree updates (e.g., from a pull or another tool),
   the uncommitted edits can be lost

## Mitigations (already in AGENTS.md)

- **Commit after each logical unit** (standing auto-commit policy)
- **Prefer worktrees for multi-file project work** (`git worktree add`)
- **Check before committing overlapping files** (`git log --oneline -5 -- <path>`)

## Reference

- AGENTS.md § "Working in the shared main tree (no worktree)"
- Handoff: `session-019f9f4f-shipped-work-20260726`
- Verified 2026-07-25: twice in one session, sibling sessions committed v3 of
  a skill and a sibling wiki concept while this session was working on the
  same area.
