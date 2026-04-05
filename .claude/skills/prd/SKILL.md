---
name: prd
description: Import PRD requirements as TaskMaster tasks with full traceability
version: 1.0.0
status: stable
category: taskmaster
triggers:
  - /prd
aliases:
  - /prd

suggest:
  - /specify
  - /build
  - /nse

execution:
  directive: |
    Manage PRD requirements imports into TaskMaster.
    1. import: Convert FR/NF requirements to tasks with traceability.
    2. status: Check completion status of PRD requirements.
    3. list: List imported PRDs.
    Ensure every task has source='prd', source_id=<path>, and prd_requirement_id set.
  default_args: "list"
  examples:
    - "/prd import P:/projects/auth/prd.md"
    - "/prd status P:/projects/auth/prd.md"
    - "/prd list"

do_not:
  - create tasks without traceability links
  - import duplicate requirements (idempotency required)

output_template: |
  ## PRD Status: [path]
  Total: [N] | Completed: [N] | Pending: [N]
  
  Missing Requirements:
  - [FR-XXX]
---

# PRD Import Command

Convert PRD requirements (FR-XXX, NF-XXX) into TaskMaster tasks with full traceability.

## Purpose

Import PRD requirements as TaskMaster tasks with full traceability.

## Project Context

### Constitution/Constraints
- Evidence-first: Only import requirements that actually exist in PRD
- Spec compliance: Follow PRD structure exactly
- Preserve everything: Import all requirements, don't selectively omit

### Technical Context
- TaskMaster integration for task management
- Traceability fields: source='prd', source_id=<path>, prd_requirement_id=FR-XXX
- PRD files at project root: `P:/projects/{project}/prd.md`

### Architecture Alignment
- Integrates with /specify for project setup
- Supports /build for implementation
- Works with /nse for development guidance

## Your Workflow

### import
1. Parse PRD file for FR-XXX and NF-XXX requirements
2. Create TaskMaster tasks with traceability metadata
3. Report import summary with counts

### status
1. Query TaskMaster for tasks with matching source_id
2. Calculate completion status
3. Show missing requirements

### list
1. Query all PRD-derived tasks
2. Display with task counts and completion

## Validation Rules

### Prohibited Actions
- Do NOT create tasks without traceability links
- Do NOT import duplicate requirements (idempotency required)
- Do NOT skip requirements during import

## Quick Start

```bash
/prd import P:/projects/auth/prd.md
/prd import P:/projects/auth/prd.md --dry-run
/prd status P:/projects/auth/prd.md
/prd list
```

## Subcommands

### import - Import PRD as tasks

```bash
/prd import <path_to_prd.md> [options]
```

**Options:**
- `--dry-run` - Preview without creating tasks
- `--filter FR-1,FR-3` - Only import specific requirements
- `--functional-only` - Only import functional requirements
- `--nf-only` - Only import non-functional requirements

**Examples:**
```bash
/prd import P:/projects/auth/prd.md
/prd import ./PRD.md --dry-run
/prd import ./PRD.md --filter FR-1,FR-2,FR-5
```

### status - Show PRD completion status

```bash
/prd status <path_to_prd.md>
```

**Shows:**
- Total requirements in PRD
- Tasks completed, in progress, pending
- Requirements not yet imported

### list - List all imported PRDs

```bash
/prd list
```

Shows all PRDs with task counts and completion status.

## Traceability

Every task includes:
- `source='prd'` - Marks task as PRD-derived
- `source_id=<prd_path>` - Links back to PRD file
- `prd_requirement_id=FR-XXX` - Links to specific requirement

**Query by PRD:**
```bash
/tm show --source prd --source-id P:/projects/auth/PRD.md
/tm show --prd-requirement FR-1
```

## PRD File Location

PRD files live at project root:
```
P:/projects/{project}/
├── prd.md          ← Product Requirements
├── arch.md         ← Architecture
├── design.md       ← Design
└── README.md
```
