---
name: constraints
description: Show active project constraints from CLAUDE.md
category: project
version: 1.0.0
status: stable
triggers:
  - /constraints
aliases:
  - /constraints

suggest:
  - /comply
  - /standards
  - /nse
---

# /constraints — Show Project Constraints

Displays active constraints extracted from CLAUDE.md.

## Purpose

Display active project constraints extracted from CLAUDE.md constitution, providing quick reference for behavioral rules and technical standards.

## Project Context

### Constitution/Constraints
- **Evidence-First** - Show actual constraints from CLAUDE.md, not summaries
- **Truthfulness > Agreement** - Display constraints accurately, even if they limit options

### Technical Context
- Loads constraints from `P://CLAUDE.md`
- Extracts via `src.constraints.load_constraints()`
- Returns structured constraint data

### Architecture Alignment
- Works with `/comply`, `/standards`, `/nse`
- Reference for constitutional compliance

## Your Workflow

1. Load CLAUDE.md file
2. Extract constraint sections
3. Parse structured constraint data
4. Display constraints with categories:
   - TDD requirements
   - Python version
   - Linting/formatting standards
   - Testing requirements
   - Other project-specific constraints

## Validation Rules

### Prohibited Actions

- Do NOT display constraints without reading CLAUDE.md
- Do NOT summarize constraints - show actual content
- Do NOT guess constraint values

## PHASE STRUCTURE

```
PHASE 1: LOAD + PARSE (Generation)
    ↓ STOP: Verify CLAUDE.md was actually read
PHASE 2: DISPLAY (Validation — user review)
```

**STOP conditions:**
- Before PHASE 2: Verify actual CLAUDE.md content was loaded (not memory or assumption)
- Never skip to display without reading the file first

**Key separation**: Loading/parsing is Generation. Display verification is Validation (did we get it right?).

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

## Quick Start

```python
from src.constraints import load_constraints

constraints = load_constraints(Path("P://"))
print(f"TDD Required: {constraints.tdd_required}")
print(f"Python Version: {constraints.python_version}")
```
