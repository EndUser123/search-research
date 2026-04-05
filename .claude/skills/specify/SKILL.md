---
name: specify
description: Create TSK project and Step 1 specification
version: "1.0.0"
status: stable
category: specification
triggers:
  - /specify
aliases:
  - /specify

suggest:
  - /build
  - /design
  - /arch
---

# Specify - Create TSK and Specification

CWO14 Step 1: Create TSK project and generate specification.

## Purpose

Create TSK project and generate Step 1 specification.

## Project Context

### Constitution/Constraints
- Hook blocks writes to P:/__csf/ root (use TSK directory instead)
- TSK directories use context-aware placement
- TaskMaster integration required for tracking

### Technical Context
- CWO14 Step 1 workflow
- TSK ID format: TSK-YYMMDD-FeatureName-HHMM
- Directory structure: {Context-aware TSK directory}/specify.md
- specify.md template includes functional/non-functional requirements, user stories

### Architecture Alignment
- Part of CWO workflow orchestration
- Integrates with TaskMaster for project tracking
- Works with build, design, arch skills

## Your Workflow

1. **Resolve or Create TSK** - Query TaskMaster, create if needed
2. **Create TSK directory** - Context-aware using `create_context_aware_tsk_directory()`
3. **Generate specify.md** - Write to TSK directory with requirements and user stories
4. **Update TaskMaster** - Set TSK as active, record Step 1 complete

## Validation Rules

### Prohibited Actions
- Writing specify.md to P:/__csf/ root (hook will block)
- Writing to P:/__csf/specify.md (use TSK directory instead)
- Creating TSK directories without TSK- prefix
- Creating specification without TaskMaster entry

---

## IMMEDIATE Workflow

1. **Resolve or Create TSK** - Query TaskMaster, create if needed
2. **Create TSK directory** - Context-aware using `create_context_aware_tsk_directory()`
3. **Generate specify.md** - Write to TSK directory
4. **Update TaskMaster** - Set TSK as active, record Step 1 complete

## DO NOT

- Write `specify.md` to `P:/__csf/` root (hook will block)
- Write to `P:/__csf/specify.md` (use TSK directory instead)
- Create TSK directories (use TSK- prefix only)

## Usage

```bash
/specify "user authentication with OAuth2"
/specify "payment API" --type api
/specify "experimental feature" --new-tsk
/specify "complex feature" --interactive
```

## TaskMaster Resolution

**FIRST, before any file creation:**

1. Check for existing active TSK
2. If found and contextually related, reuse it
3. If not found or unrelated, create new TSK
4. TSK ID Format: `TSK-YYMMDD-FeatureName-HHMM`

## Directory Structure

```
{Context-aware TSK directory}/
├── specify.md           # Step 1 output
├── project.json         # Metadata
└── evidence/
    └── step_01/
```

## specify.md Template

```markdown
# Specification: {Feature Name}

**TSK:** {TSK-ID}
**Created:** {timestamp}
**Status:** Draft

## Overview
{Feature description}

## Requirements
### Functional Requirements
- FR-1: {requirement}

### Non-Functional Requirements
- NFR-1: {requirement}

## User Stories
### US-1: {Story Title}
**As a** {user type}
**I want** {goal}
**So that** {benefit}
```

## Prevention Checklist (Before Implementation)

Before writing code, verify:

- [ ] **Integration Points Defined**: All external systems, APIs, and modules identified
- [ ] **Import Paths Verified**: Required packages and module imports confirmed available
- [ ] **Path Calculations Tested**: Any file path logic verified against actual structure
- [ ] **Configuration Documented**: Environment variables, settings, and config files specified
- [ ] **Tests Outlined**: Test scenarios including error paths documented

**Pattern Reference**: Path manipulation and import errors are common "missing discoveries" — verify early.

## Integration

- TaskMaster: Creates/updates TSK entry
- CWO14 Engine: Creates Step 1 artifact
- Quality Gates: Validates specification completeness
