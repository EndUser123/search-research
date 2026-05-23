---
name: standards
description: Read and enforce CSF NIP standards
version: "1.0.0"
status: stable
enforcement: strict
category: standards
triggers:
  - /standards
aliases:
  - /standards

suggest:
  - /init
  - /csf-nip-dev
---

# CSF NIP Standards

Read and enforce CSF NIP standards.

## Purpose

Read and enforce CSF NIP development standards.

## Project Context

### Constitution/Constraints
- Follow P://__csf/docs/standards_inst.md for authoritative standards
- CSF NIP ecosystem has specific development patterns
- Standards are constitutional, not optional

### Technical Context
- Standards document: P://__csf/docs/standards_inst.md
- Enforced via comply skill
- Integrates with csf-nip-dev for detailed patterns

### Architecture Alignment
- Part of CSF NIP standards system
- Works with comply, csf-nip-dev skills
- Enforced by various hooks

## Your Workflow

When invoked:
1. Read P://__csf/docs/standards_inst.md
2. Identify relevant standards for current task
3. Apply standards to code/implementation
4. Validate compliance

## Validation Rules

- Standards from standards_inst.md are authoritative
- No deviation without explicit user approval
- Document any exceptions required

---

## Execution

When invoked, read P://__csf/docs/standards_inst.md and enforce CSF NIP standards.

## Reference

See: P://__csf/docs/standards_inst.md

## Evidence-First Principles

### E1 — Evidence before claims
Before claiming code is absent, unchanged, or non-existent — search the codebase and verify with tools first. Claims of absence are only valid after confirmed Read/Grep/git failures.

### E4 — Investigate before asking
Do NOT answer without reading relevant source files first. Do not ask the user for information you can obtain yourself via Read, Grep, Bash, git, or available MCP tools.

### E5 — Anti-lazy escape hatch
Prohibited:
- "I assume", "I think", "probably" without tool verification
- Claiming something doesn't exist without confirmed tool failure
- Skipping evidence gathering because the answer seems obvious

## PHASE STRUCTURE

```
PHASE 1: READ + IDENTIFY (Generation) — Read P:/__csf//docs//standards_inst.md, identify relevant standards
    ↓ STOP: Present identified standards before application
PHASE 2: APPLY (Generation) — Apply standards to code/implementation
    ↓ STOP: Present applied changes before validation
PHASE 3: VALIDATE (Validation) — Verify compliance against standards document
```

**STOP conditions:**
- Between PHASE 1 and PHASE 2: STOP after relevant standards identified (confirm coverage)
- Between PHASE 2 and PHASE 3: STOP after standards applied (present changes for review)
- Between PHASE 3 and end: STOP after compliance validated (user sees result)

**Key separation**: Reading and identification is Generation. Application is Generation. Validation is Validation.

