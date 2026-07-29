---
title: "parallel-fan-out"
node_type: capability
created: 2026-07-28
domain: infrastructure
---

# parallel-fan-out

**Inputs:** task list (independent work items)
**Outputs:** executed tasks across subagents

## Procedure

spawn_subagent per task. Wait-all gate. Worktree isolation when writes conflict.
