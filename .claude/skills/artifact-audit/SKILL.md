---
name: artifact_audit
description: Show pending artifact updates grouped by severity - PRD, ARD, CHANGELOG, README status
version: "1.0.0"
status: stable
category: tracking
triggers:
  - /artifact-audit
  - "artifact audit"
  - "pending documentation"
aliases:
  - /artifact-audit
  - /artifacts-audit
  - /audit-artifacts

suggest:
  - /artifact-add
  - /comply
  - /nse
---

# /artifact-audit

## Purpose

Show pending artifact updates grouped by severity - PRD, ARD, CHANGELOG, README status.

## Project Context

### Constitution/Constraints
- User-initiated audit only
- Severity-based grouping (critical, standard, low)
- Evidence-based status verification

### Technical Context
- Script: `P:/.claude/skills/artifact-audit/resources/scripts/artifact_audit.py`
- JSON output option for scripting
- Exit code 1 if pending items exist

### Architecture Alignment
- Part of artifact tracking system (with artifact-add, artifact-done)
- Integrates with /comply for enforcement
- Supports /build workflow gating

## Your Workflow

1. **Scan Project** - Auto-detect project root
2. **Group by Severity** - Critical, Standard, Low
3. **Show Status Icons** - Pending (⏳), Confirm (?), Done (✓)
4. **Display Enforcement Timeline** - Warn/Block times by severity
5. **Return Exit Code** - 1 if pending, 0 if clean

## Validation Rules

### Prohibited Actions
- **NEVER claim clean without scanning** - run actual audit
- **NEVER hide critical items** - always show highest severity first

### Required Output Format
- Group by severity level
- Show item_id and summary
- List each artifact with status icon
- Display enforcement timeline

Show all pending artifact updates for the current project. Groups by severity with artifact status.

## Usage

```bash
python P:/.claude/skills/artifact-audit/resources/scripts/artifact_audit.py --project-root P:/
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| --project-root | No | Project directory (defaults to auto-detect) |
| --json | No | Output as JSON instead of formatted text |

## Output Format

```
CRITICAL (1)
--------------------------------------------------
  TSK-001: Add user authentication
    ⏳ard ⏳changelog ⏳prd ?readme

STANDARD (1)
--------------------------------------------------
  TSK-002: Fix login bug
    ⏳changelog

LOW (1)
--------------------------------------------------
  TSK-003: Update README
    ?readme
```

## Status Icons

| Icon | Meaning |
|------|---------|
| ⏳ | Pending (required) |
| ? | Confirm (optional) |
| ✓ | Done |

## Enforcement Timeline

| Severity | Warn | Block |
|----------|------|-------|
| Critical | 5 min | 30 min |
| Standard | 30 min | 2 hours |
| Low | Never | Never |

## Exit Code

Returns 1 if pending items exist, 0 otherwise.

## Examples

```bash
# Check pending artifacts
artifact-audit

# JSON output for scripting
artifact-audit --json
```

## Related Commands

- /artifact-add - Add item for tracking
- /artifact-done - Mark artifact complete
