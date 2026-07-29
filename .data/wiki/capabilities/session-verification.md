---
title: "session-verification"
node_type: capability
created: 2026-07-28
domain: testing
---

# session-verification

**Inputs:** session context (conversation, git diff, evidence packet)
**Outputs:** PASS/FAIL verdict per concern, run_dir with verifier outputs

## Procedure

Build evidence packet. Spawn per-concern verifiers. Merge verdicts.
