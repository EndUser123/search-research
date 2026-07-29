---
title: "parallel-implement-dispatch"
node_type: capability
created: 2026-07-28
domain: orchestration
---

# parallel-implement-dispatch

**Inputs:** task list with depends_on / track metadata
**Outputs:** executed tasks across parallel subagents (worktree-isolated)

## Procedure

/go dispatches to grok-parallel for independent work streams.
