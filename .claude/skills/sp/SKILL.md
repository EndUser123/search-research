---
name: sp
description: Scratchpad worktrees - lock-free with Sapling
version: "1.0.0"
status: stable
category: evolution
triggers:
  - /sp
aliases:
  - /sp

suggest:
  - /scratchpad
  - /sap
  - /git-sapling
---

# Scratchpad Worktrees

Alias for `/scratchpad`. Uses sl (Sapling) for lock-free git operations.

## Purpose

Scratchpad worktrees alias - lock-free operations using Sapling.

## Project Context

### Constitution/Constraints
- See /scratchpad for full documentation
- Lock-free operations required for parallel terminal usage
- No git index.lock conflicts with sl

### Technical Context
- Alias for scratchpad skill
- Worktrees at P:/worktrees/<name>/
- Uses sl (Sapling SCM) for operations

### Architecture Alignment
- Part of scratchpad module
- Integrates with sap workflow
- Shortcut alias for convenience

## Your Workflow

Use `/sp` as shorthand for `/scratchpad` commands:
- create <name> - Create worktree
- list - List all worktrees
- commit <branch> <message> - Commit changes
- push <branch> - Push branch (lock-free)

## Validation Rules

Same as /scratchpad skill.

---

## Commands

| Command | Description |
|---------|-------------|
| `create <name>` | Create worktree at P:/worktrees/NAME/ |
| `list` | List all worktrees |
| `commit <branch> <message>` | Commit changes (git, no lock issue) |
| `push <branch>` | Push branch (lock-free with sl) |

## Examples

```bash
/sp create experiment-1              # Create worktree
/sp list                              # List worktrees
/sp commit experiment-1 "fix bug"     # Commit changes
/sp push experiment-1                 # Push (no lock conflicts)
```

See `/scratchpad` for full documentation.
