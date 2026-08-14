---
title: "scan-code-quality"
node_type: capability
created: 2026-08-13
domain: review
---

# scan-code-quality

**Inputs:** code diff, files, or package paths
**Outputs:** verified findings with file:line citations, severity ratings

## Procedure

Analyze code for defects, correctness, coverage, security, maintainability.
Produce structured findings with evidence. Write to disk for downstream
consumption.

## Providers

- `/review` (multi-model parallel review → FINDINGS.md)
- `/check` (session verification → PASS/FAIL)
- `/grok-verify` (completion gate → block or allow)
- `/trace` (manual logic trace → findings list)
