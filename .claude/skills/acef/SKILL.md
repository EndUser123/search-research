---
name: acef
description: Agentic Command Engineering Framework for creating composable engineering assets
version: "1.0.0"
status: stable
category: framework
triggers:
  - /acef
aliases:
  - /acef

suggest:
  - /build
  - /design
  - /orchestrator
---

# The Agentic Command Engineering (ACE) Framework v3.7

## Purpose

Create a robust ecosystem of composable engineering assets for LLM-guided development.

## Project Context

### Constitution/Constraints
- Consult project constitution (CLAUDE.md) before authoring
- Single responsibility per command
- Input quality gates required for vague inputs
- No role-setting in instruction files

### Technical Context
- Main documentation: `P:/__csf/src/csf/cli/nip/acef.md`
- Levels 1-9 complexity scale from basic to feature agent
- Option 3 Hybrid file structure: entry point stub + LLM instructions + human docs + tests

### Architecture Alignment
- Part of CSF NIP command ecosystem
- Integrates with CSDA pattern for documentation
- Skills-indexed for discoverability

## Your Workflow

1. **Consult Constitution** - Read CLAUDE.md for project-specific constraints
2. **Read Framework Documentation** - Access `P:/__csf/src/csf/cli/nip/acef.md`
3. **Determine Complexity Level** - Assess task (1-9 scale)
4. **Select File Structure** - Use Option 3 Hybrid pattern
5. **Author Command** - Apply core principles: separate persona, structured formatting, enumerate paths
6. **Validate** - Ensure single responsibility, standardized errors, input gates

## Validation Rules

- **Single Purpose**: Each command must have one well-defined purpose
- **No Role-Setting**: Instruction files must not set persona/role
- **Path Enumeration**: All logical paths must be explicitly defined
- **Input Validation**: Vague inputs must trigger quality gates
- **Evidence-Based**: Claims must cite sources with file:line references

**See main documentation:** `P:/__csf/src/csf/cli/nip/acef.md`

## Quick Reference

**EXECUTE this command using:** `P:/__csf/src/csf/cli/nip/acef.md`

To read the framework documentation:
```bash
Read: P:/__csf/src/csf/cli/nip/acef.md
```

## Framework Overview

### Levels of Agentic Complexity

| Level | Type | Description |
|-------|------|-------------|
| 1-2 | Basic | Simple, linear tasks |
| 3-4 | Intermediate | Tasks with conditional logic, loops, or delegation |
| 5-7 | Advanced | Tasks that generate code, prompts, or self-improve |
| 8 | Orchestrator | Analyzes request and delegates to specialist agent |
| 9 | Feature Agent | Executes multi-step project plans |

### Core Authoring Principles

1. Adhere to the Constitution - Consult project constitution first
2. Input Quality Gate - Validate and enhance vague inputs
3. Separate Persona from Task - No role-setting in instruction files
4. Structured Formatting - Use markdown, keywords (CRITICAL, NEVER)
5. Enumerate All Paths - Define all logical paths explicitly
6. Single Responsibility - One well-defined purpose per command
7. Standardized Errors - Predictable error messages

### Command File Structure (Option 3 Hybrid)

| File | Purpose |
|------|---------|
| .claude/commands/<command>.md | Entry point stub |
| src/.../<command>_inst.md | LLM instructions |
| src/.../<command>_help.md | Human documentation |
| src/.../<command>_tests.md | Test definitions |

## Usage

To access the full ACE Framework documentation including templates, validation checklists, and ecosystem tooling, read the main file.
