---
name: ralph
description: Ralph Loop - task decomposition and iterative development
version: 1.0.0
status: stable
category: strategy
triggers:
  - /ralph
aliases:
  - /ralph

suggest:
  - /build
  - /tdd
  - /test
---

# Ralph Loop

Interactive development loop with task decomposition and test-driven iteration.

## Purpose

Interactive development loop providing task decomposition and test-driven iteration for systematic feature development.

## Project Context

### Constitution/Constraints
- Test-driven development workflow
- Atomic task decomposition
- Solo-developer optimized

### Technical Context
- Located at: `P:\\\\\\projects/ralph-wiggum-python/scripts/setup-ralph-loop.py`
- Task decomposition into atomic units
- Progress tracking for iterative development

### Architecture Alignment
- Integrates with `/build` for feature development
- Works alongside `/tdd` for test-driven workflows
- Suggests `/test` for test execution

## Your Workflow

**PHASE STRUCTURE:**

```
PHASE 1: DECOMPOSE (Generation) — Break task into atomic units
    ↓ STOP: Present decomposed task list before TDD cycle
PHASE 2: TDD CYCLE (Generation + Validation) — Write test, implement, refactor
    ↓ STOP: Present test result before refactoring
PHASE 3: TRACK + VERIFY (Validation) — Monitor completion, ensure tests pass
```

**STOP conditions separate each phase:**
- Between PHASE 1 and PHASE 2: STOP after task decomposition (present list before starting TDD)
- Between PHASE 2 and PHASE 3: STOP after each TDD iteration (present result before next)

**Key separation**: Decomposition is Generation. TDD cycle mixes Generation (implement) and Validation (tests). Verification is Validation.

1. **Accept Task**: Receive feature description from user
2. **Decompose**: Break task into atomic units
3. **TDD Cycle**: Write test, implement, refactor
4. **Track Progress**: Monitor completion of subtasks
5. **Verify**: Ensure all tests pass before completion

### Ralph Loop Components
- Task decomposition into atomic units
- Test-driven development guidance
- Iterative development workflow
- Progress tracking

## Validation Rules

### Prohibited Actions
- Do not skip test-writing phase
- Do not proceed with failing tests
- Do not create tasks that are not atomic

### Required Outputs
- Decomposed task list with atomic units
- Test results for each iteration
- Progress status updates

## Usage

```bash
/ralph "Implement feature X with tests"
```

The command accepts arguments directly - no special quoting required for most cases.

## Implementation

Located at: `P:\\\\\\projects/ralph-wiggum-python/scripts/setup-ralph-loop.py`

The Ralph Loop provides:
- Task decomposition into atomic units
- Test-driven development guidance
- Iterative development workflow
- Progress tracking

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

