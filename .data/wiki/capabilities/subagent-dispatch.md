---
title: "subagent-dispatch"
node_type: capability
created: 2026-07-28
provides: [fresh-lens-spawn, model-pool-selection, inline-fallback-disclosure]
---

# subagent-dispatch

**Inputs:** `prompt` (string, the task), `context_bundle` (≤500 tokens), `model_pool` (from wiki query or override), `capability_mode` (read-only|execute|all)
**Outputs:** `subagent_result` (content), `model_used` (slug), `pool_failures` (list), `dispatch_mode` (spawn|inline-fallback)

## Step 1: Query wiki for pool candidates

```
grep pattern="spawn_subagent pool model real-prompt reliable reasoning cross-family free" path="P:/.data/wiki/concepts/" -i
```

Read [[model-tool-calling-capability-matrix]] and [[model-pool-selection-policy-speed-quota-diversity]].

## Step 2: Apply criteria (all must hold)

1. Real-prompt reliability (not just READY probes)
2. Reasoning OR code lane
3. Cost-aware (free > subscription > paid)
4. Family diversity (prefer cross-family from parent)

## Step 3: Apply hard exclusions

- `go-kimi-k3`: NOT in any auto-pool (cost + reliability)
- `nemotron` (all variants): NOT in any auto-pool (serde errors)

## Step 4: Spawn (pool, not chain)

Try each candidate in order. If spawn returns content (not 429/401/serialization/empty), record which ran + which failed, break.

```python
spawn_subagent(
    description="<task>",
    subagent_type="general-purpose",
    capability_mode="execute",
    model="<slug>",  # explicit, not omitted
    background=True,
    prompt=<prompt with absolute paths only>
)
```

If ALL fail → inline fallback with mandatory disclosure:

```
⚠️ INLINE FALLBACK: fresh subagent could not be spawned (error: <reason>).
Running inline — structurally weaker. Treat output as provisional.
```

## Step 5: Record for telemetry

```bash
python P:/.agents/scripts/log_spawn.py \
    --model <slug> --caller <skill> \
    --success <true|false> --latency <ms> \
    --domain <domain> --notes "<pool pos | inline>"
```
