---
name: csda-concept
description: CSDA Pattern Concept Documentation
version: "1.0.0"
status: "stable"
category: documentation
triggers:
  - /csda-concept
aliases:
  - /csda-concept

suggest:
  - /csda
  - /docs
  - /research
---

# CSDA Pattern Concept

4-layer architecture for Code Structure-Documentation Architecture.

## Purpose

Concept documentation for the 4-layer CSDA architecture pattern.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- Evidence-first, verification-required

### Technical Context
- Part of CSF NIP governance framework
- Complements /csda implementation skill
- Foundational pattern for CSAF bundles

### Architecture Alignment
- Separates concerns across 4 distinct layers
- Each layer has single, well-defined responsibility
- Enables deterministic execution through specification layer

## Your Workflow

1. Understand the 4-layer model
2. Reference /csda for implementation
3. Apply pattern when creating new commands
4. Verify layer separation is maintained

## Validation Rules

- Each layer must have distinct responsibility
- No layer mixing (command logic in spec, or vice versa)
- Specification layer must be deterministic

## Layers

1. Command Interface (.md) - Essential metadata
2. Interface Layer (_inst.md) - Orchestration
3. Specification Layer (_spec.py) - Deterministic logic
4. Documentation (CSAF) - Complete documentation
