---
name: checkpoint_delete
description: Safely delete a checkpoint using the trash recovery system
category: utility
version: 1.0.0
status: stable
triggers:
  - /checkpoint-delete
aliases:
  - /checkpoint-delete
suggest:
  - /checkpoint
  - /checkpoint-list
  - /checkpoint-restore
---

# /checkpoint-delete

Safely delete a checkpoint by moving it to the trash recovery system.

## Purpose

Safely delete checkpoints with recovery capability through trash system.

## Project Context

### Constitution/Constraints
- Follows fail-fast principle - surface issues immediately
- Evidence-first - verify checkpoint exists before deletion
- Solo-dev appropriate - no enterprise-style background services

### Technical Context
- Checkpoints stored in `P:/.claude/checkpoints/`
- Trash recovery in `~/.claude/trash/`
- Metadata preserved for restoration via `/checkpoint-restore`

### Architecture Alignment
- Part of checkpoint management system with `/checkpoint`, `/checkpoint-list`, `/checkpoint-restore`
- Provides safety net before destructive operations

## Your Workflow

1. Identify checkpoint to delete (ID or pattern)
2. Verify checkpoint exists in checkpoints directory
3. Move checkpoint file to trash recovery directory
4. Preserve metadata for potential restoration
5. Report completion with trash location

## Validation Rules

### Prohibited Actions
- Do NOT permanently delete without moving to trash first
- Do NOT bypass trash system
- Do NOT delete checkpoints without user confirmation

## Usage

```
/checkpoint-delete <checkpoint_id>
```

## Examples

```bash
# Delete a specific checkpoint
/checkpoint-delete ckpt_20260107_120000

# Delete by pattern
/checkpoint-delete ckpt_20260107_*
```

## What Happens

1. Checkpoint file is moved to `~/.claude/trash/`
2. Metadata is preserved for restoration
3. Citation and timeline events are NOT deleted
4. Can be restored with `/checkpoint-restore`

## Related

- /checkpoint-restore - Restore deleted checkpoint
- /checkpoint-list - List all checkpoints
