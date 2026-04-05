---
name: checkpoint_list
description: List/cleanup/validate checkpoints
category: utility
version: 1.0.0
status: stable
triggers:
  - /checkpoint-list
aliases:
  - /checkpoint-list

suggest:
  - /checkpoint
  - /checkpoint-restore
  - /nse
---

# Checkpoint List

List all checkpoints with age, commit, and metadata.

## Purpose

List, cleanup, and validate checkpoints in the checkpoint directory.

## Project Context

### Constitution/Constraints
- Evidence-first - show actual checkpoint data from filesystem
- Investigation before claims - verify checkpoint existence

### Technical Context
- Checkpoints stored in `P:/.claude/checkpoints/` directory
- Each checkpoint has metadata including creation time, commits
- Supports cleanup and validation modes

### Architecture Alignment
- Core checkpoint management command
- Works with `/checkpoint`, `/checkpoint-restore`, `/checkpoint-diff`

## Your Workflow

1. Scan `P:/.claude/checkpoints/` directory for checkpoint files
2. Read metadata from each checkpoint
3. Calculate age based on timestamp
4. Display list with age, commit info, and metadata
5. If `--cleanup` flag: remove old/invalid checkpoints
6. If `--validate` flag: verify checkpoint integrity

## Validation Rules

### Prohibited Actions
- Do NOT list checkpoints without reading directory
- Do NOT assume checkpoint format without verification

## Usage

```bash
/checkpoint-list
/checkpoint-list --cleanup
/checkpoint-list --validate
```

## Implementation

Manages checkpoints stored in P:/.claude/checkpoints/ directory.
