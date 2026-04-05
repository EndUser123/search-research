---
name: update_state
description: "Update session state tracking"
version: "1.0.0"
status: stable
category: evolution
triggers:
  - '/update_state'
aliases:
  - '/update_state'
suggest:
  - /catchup
  - /evolve
  - /skills-migrate
  - /sp
---

# Update State - Save Progress Checkpoint

**Purpose:** Create checkpoint before /clear for resumable sessions.

## Project Context

### Constitution / Constraints

- Session continuity: Enable resumption after /clear
- Solo-dev constraint: Simple checkpoint system, no complex state management
- Data safety: Checkpoints stored locally

### Technical Context

- Checkpoint location: P:/.claude/session_data/terminals/{terminal_id}/session_archives/
- Terminal-specific: Each terminal gets its own checkpoint file
- Integrates with /catchup for restoration

### Architecture Alignment

- Checkpoint pattern: Save state before destructive operation (/clear)
- Session handoff: Supports continuity across sessions

## Your Workflow

1. Detect current terminal
2. Load current goal state
3. Capture session data:
   - Current goal and phase
   - Modified files (git status)
   - Next steps
   - Any blockers
4. Save to terminal-specific checkpoint file
5. Display confirmation

## Validation Rules

### Prohibited Actions

- Do NOT create checkpoints without user request
- Do NOT overwrite existing checkpoints without confirmation

### When to Use

- Before /clear when wanting to resume later
- Before significant context switches


## Usage

```
/update-state
```

## What It Does

1. Detects current terminal
2. Loads your current goal state
3. Captures:
   - Current goal and phase
   - Modified files (git status)
   - Next steps
   - Any blockers
4. Saves to terminal-specific checkpoint file

## When to Use

**Before /clear** when you want to resume later:
```
/update-state
/clear
# (later, in new session)
/catchup
```

## Output

```
SESSION CHECKPOINT SAVED: terminal_1
   Goal: Implement video processor
   Phase: Implementation (60%)
   Files: 3 modified
```

## Files

Checkpoint saved to:
```
P:/.claude/session_data/terminals/{terminal_id}/session_archives/{timestamp}.json
```
