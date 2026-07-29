---
title: "completion-gate"
node_type: capability
created: 2026-07-28
domain: testing
---

# completion-gate

**Inputs:** scope files, test commands, claimed completion
**Outputs:** PASS/FAIL — refuses done/fixed/verified until tests pass + scope verified

## Procedure

Check: files exist, tests pass, runtime path verified, dirty-tree clean.
