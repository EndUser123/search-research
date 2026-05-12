---
name: contract-status
description: Show contract system health dashboard (writer + Stop stats)
suggest:
  - /status
  - /health
---

# /contract-status

Display contract system health dashboard showing writer + Stop gate telemetry.

## Usage

```
/contract-status
```

## What it shows

- **Contract Writer**: Active contracts, skips, task class breakdown
- **Contract Stop**: Allow/block/silent counts, notable gate activity
- **Anomalies**: HIGH skip rates, uncertain silences

## Examples

```
/contract-status
```

Shows:
```
────────────────────────────────────
Contract Writer: 5 contracts, 2 skips (0 not-task) | Last: 0.5h [bug_fix=3, feature=2]
Contract Stop: 12 allow, 0 block, 2 silent [uncertain_non_completion=2]
────────────────────────────────────
```

## How it works

Reads from:
- `P:/.claude/hooks/logs/diagnostics/task_contract_writer_telemetry.jsonl`
- `P:/.claude/hooks/logs/diagnostics/task_contract_telemetry.jsonl`

Uses `P:/.claude/hooks/tools/contract-telemetry-queries.py` for detailed queries.