---
name: artifact-add
description: Manually add an item for artifact tracking - tracks pending documentation (PRD, ARD, CHANGELOG).
version: "1.0.0"
status: stable
category: tracking
triggers:
  - /artifact-add
  - "track artifact"
  - "add artifact"
aliases:
  - /artifact-add
  - /artifacts-add

suggest:
  - /artifact-audit
  - /build
  - /nse
---

# /artifact-add

## Purpose

Manually register an item for artifact tracking - tracks pending documentation (PRD, ARD, CHANGELOG).

## Project Context

### Constitution/Constraints
- User-initiated tracking only
- Evidence-based artifact completion (mtime verification)
- Severity-based enforcement (critical/standard/low)

### Technical Context
- Script: `P:/.claude/skills/artifact-add/resources/scripts/artifact_add.py`
- Change types: feature, bug_fix, refactor, breaking, docs
- Severity levels: critical, standard, low

### Architecture Alignment
- Part of artifact tracking system (with artifact-audit, artifact-done)
- Integrates with /build and /nse workflows
- Supports compliance enforcement via /comply

## Your Workflow

1. **Register Item** - Run artifact_add.py with item_id, summary, change_type, files
2. **Assign Severity** - Critical (core files), Standard (features/commands), Low (tests/docs)
3. **Track Artifacts** - Determine which artifacts required based on change type
4. **Create Entry** - Store in project tracking system

## Validation Rules

### Prohibited Actions
- **NEVER auto-track** - manual registration required
- **NEVER skip severity assessment** - required for enforcement timing

### Required Arguments
- item_id (e.g., TSK-001)
- summary (human-readable description)
- change_type (bug_fix, feature, refactor, breaking, docs)
- files (optional, relative paths)

Manually register an item for artifact tracking. Use this after making code changes to track pending documentation.

## Usage

```bash
python P:/.claude/skills/artifact-add/resources/scripts/artifact_add.py --project-root P:/ TSK-001 "Add user auth" feature src/features/api/auth.py
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `item_id` | Yes | Task identifier (e.g., TSK-001) |
| `summary` | Yes | Human-readable description |
| `change_type` | Yes | `bug_fix`, `feature`, `refactor`, `breaking`, `docs` |
| `files` | No | Files changed (relative paths) |
| `--project-root` | No | Project directory (defaults to auto-detect) |

## Change Types

| Type | Artifacts Required |
|------|-------------------|
| feature | changelog, prd, ard (critical), readme (confirm) |
| bug_fix | changelog only |
| breaking | all artifacts required |
| docs | readme only |
| refactor | based on severity |

## Severity Levels

| Severity | Files | Enforcement |
|----------|-------|-------------|
| critical | src/features/api/**, models.py, pyproject.toml | Warn 5min, block 30min |
| standard | src/features/**, commands/** | Warn 30min, block 2hr |
| low | tests/**, docs/** | Reminder only |

## Examples

```bash
# Add a feature (critical severity)
artifact-add TSK-001 "Add user authentication" feature src/features/api/auth.py

# Add a bug fix (standard severity)
artifact-add TSK-002 "Fix login bug" bug_fix src/auth/login.py

# Add docs change (low severity)
artifact-add TSK-003 "Update README" docs README.md
```

## Related Commands

- /artifact-audit - Show pending artifacts
- /artifact-done - Mark artifact complete
