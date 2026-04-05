---
name: checkpoint_diff
description: Compare two checkpoints with commits, files, and metadata
category: utility
version: 1.0.0
status: stable
triggers:
  - /checkpoint-diff
aliases:
  - /checkpoint-diff

suggest:
  - /checkpoint-list
  - /search
  - /nse
---

# Checkpoint Diff

Display differences between two checkpoints.

## Purpose

Compare two checkpoints showing commits, files, and metadata changes.

## Project Context

### Constitution/Constraints
- Evidence-first - show actual differences, not summaries
- Investigation before diagnostic claims - read checkpoint metadata

### Technical Context
- Checkpoints stored in `P:/.claude/checkpoints/` directory
- Metadata includes commits, types, messages, modified files
- Validation checklist included in checkpoint data

### Architecture Alignment
- Part of checkpoint management suite
- Enables understanding of what changed between states

## Your Workflow

1. Identify two checkpoints to compare
2. Read metadata from both checkpoint files
3. Extract commits with change detection
4. Compare file counts and modified file lists
5. Display structured diff showing commits, types, messages, files

## Validation Rules

### Prohibited Actions
- Do NOT speculate about differences without reading checkpoint files
- Do NOT assume checkpoint IDs exist without verification

## Usage

```bash
/checkpoint-diff checkpoint1 checkpoint2
/checkpoint-diff --latest manual_20260107_120000
```

## Shows

- Commits (with change detection)
- Types
- Messages
- Modified files (with count diff)
- Validation checklist

## Implementation

Checks checkpoints stored in P:/.claude/checkpoints/ directory and compares metadata between them.
