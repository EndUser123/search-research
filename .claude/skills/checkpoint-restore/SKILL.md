---
name: checkpoint_restore
description: Restore a checkpoint from trash recovery system
category: utility
version: 1.0.0
status: stable
triggers:
  - /checkpoint-restore
aliases:
  - /checkpoint-restore

suggest:
  - /checkpoint
  - /nse
  - /r
---

# /checkpoint-restore

Restore a checkpoint that was previously deleted.

## Purpose

Restore deleted checkpoints from trash recovery system.

## Project Context

### Constitution/Constraints
- Solo-dev appropriate - manual recovery, no automated background service
- Evidence-first - verify checkpoint exists in trash before restore

### Technical Context
- Trash recovery system in `~/.claude/trash/`
- Metadata preserved during deletion for restoration
- Works with checkpoint IDs or `--list` to browse trash

### Architecture Alignment
- Recovery mechanism for `/checkpoint-delete`
- Part of checkpoint safety net

## Your Workflow

1. If `--list`: show all checkpoints in trash
2. If checkpoint ID provided: verify it exists in trash
3. Read metadata from trash checkpoint
4. Restore checkpoint to active checkpoints directory
5. Verify restoration succeeded
6. Report completion

## Validation Rules

### Prohibited Actions
- Do NOT restore without verifying checkpoint exists in trash
- Do NOT assume trash location without checking

## Usage

```
/checkpoint-restore [<checkpoint_id> | --list]
```

## Examples

```bash
/checkpoint-restore --list
/checkpoint-restore ckpt_20260107_120000
/checkpoint-restore
```
