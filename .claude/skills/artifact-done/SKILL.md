---
name: artifact_done
description: Mark an artifact as complete for a tracked item - PRD, ARD, CHANGELOG, README
version: "1.0.0"
status: stable
category: tracking
triggers:
  - /artifact-done
  - "mark artifact done"
  - "complete documentation"
aliases:
  - /artifact-done
  - /artifacts-done
  - /mark-done

suggest:
  - /artifact-audit
  - /comply
  - /build
---

# /artifact-done

## Purpose

Mark an artifact as complete for a tracked item - PRD, ARD, CHANGELOG, README.

## Project Context

### Constitution/Constraints
- Mtime verification required (prevents false completion)
- User-initiated only
- Force option available for pre-tracking updates

### Technical Context
- Script: `P:/.claude/skills/artifact-done/resources/scripts/artifact_done.py`
- Artifact types: changelog, prd, ard, readme
- File pattern matching for each artifact type

### Architecture Alignment
- Part of artifact tracking system (with artifact-add, artifact-audit)
- Integrates with /comply for enforcement clearance
- Supports /build workflow completion

## Your Workflow

1. **Identify Item** - Specify item_id and artifact_type
2. **Verify Modification** - Check file mtime changed since item creation
3. **Mark Complete** - Update tracking system
4. **Confirm Status** - Return updated artifact status

## Validation Rules

### Prohibited Actions
- **NEVER mark done without verification** unless --force specified
- **NEVER skip mtime check** - prevents accidentally marking without actual update

### Required Arguments
- item_id (e.g., TSK-001)
- artifact_type (changelog, prd, ard, readme)
- --project-root (optional, defaults to auto-detect)
- --force (optional, skip mtime verification)

Mark an artifact (PRD, ARD, CHANGELOG, README) as done for a tracked item.

## Usage

```bash
python P:/.claude/skills/artifact-done/resources/scripts/artifact_done.py --project-root P:/ TSK-001 changelog
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| item_id | Yes | Item identifier (e.g., TSK-001) |
| artifact_type | Yes | changelog, prd, ard, or readme |
| --project-root | No | Project directory (defaults to auto-detect) |
| --force | No | Skip mtime verification |

## Artifact Types

| Type | File Patterns |
|------|---------------|
| changelog | CHANGELOG.md, changelog.md, HISTORY.md |
| prd | PRD.md, prd.md, docs/PRD.md |
| ard | ARD.md, ard.md, docs/ARD.md, docs/architecture.md |
| readme | README.md, readme.md |

## Verification

By default, verifies the artifact file was modified since the item was created. Prevents accidentally marking as done without actually updating.

Use `--force` to skip verification (e.g., if the file was updated before tracking began).

## Examples

```bash
# Mark changelog done (with verification)
artifact-done TSK-001 changelog

# Force mark done (skip mtime check)
artifact-done TSK-001 prd --force
```

## Related Commands

- /artifact-add - Add item for tracking
- /artifact-audit - Show pending artifacts
