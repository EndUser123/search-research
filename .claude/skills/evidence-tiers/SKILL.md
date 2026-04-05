---
name: evidence-tiers
version: "1.0.0"
status: "stable"
description: Confidence ceilings based on evidence quality. Every claim must cite its tier.
category: verification
triggers:
  - 'confidence'
  - 'certainty'
  - 'evidence level'
  - 'claim is'
  - 'verified'
aliases:
  - '/evidence-tiers'
suggest:
  - /research
---

## Purpose

Every claim must cite its tier. Confidence cannot exceed tier ceiling.

## Evidence Tiers

| Tier | Ceiling | Sources |
|------|---------|---------|
| 1 | 95% | Execution artifacts, logs, test output |
| 2 | 85% | Official docs, specs, peer-reviewed |
| 3 | 75% | Static analysis, logical derivation |
| 4 | 50% | Comments, unverified claims, speculation |

## Rules

- High-stakes decisions require Tier 1 or 2
- Mixed tiers: ceiling = lowest tier used
- Tier 4 alone: flag as [UNVERIFIED]

## Examples

**Tier 1 (Execution):**
- "The test passes with exit code 0" — after running pytest
- "File exists at path X" — after ls/stat output

**Tier 2 (Authoritative):**
- "The React docs say useEffect cleanup runs on unmount" — citing official docs
- "Per the spec, this must return a 400" — citing approved specification

**Tier 3 (Derived):**
- "This function has a cyclomatic complexity of 8" — from static analysis
- "The import chain is A→B→C" — from tracing imports

**Tier 4 (Unverified):**
- "I think this is probably the issue" — speculation
- "This might be a race condition" — without evidence

## Trigger

Activate when:
- Making claims about system behavior
- Stating confidence levels
- Verifying information
- Citing evidence for conclusions
