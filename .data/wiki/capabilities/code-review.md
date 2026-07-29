---
title: "code-review"
node_type: capability
created: 2026-07-28
domain: review
---

# code-review

**Inputs:** diff/branch/PR/package path, `lenses` (correctness, security, etc.)
**Outputs:** FINDINGS.md + findings.json on disk with verified severity

## Procedure

Infer target+lenses. Spawn per-lens specialists. Verify each finding against source.
