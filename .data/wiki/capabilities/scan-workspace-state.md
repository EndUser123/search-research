---
title: "scan-workspace-state"
node_type: capability
created: 2026-08-13
domain: fleet-ops
---

# scan-workspace-state

**Inputs:** workspace filesystem (handoffs, git state, review findings, check states, critique log, wiki markers, dreams, epistemic debt, skill scripts)
**Outputs:** prioritized action items with source attribution

## Procedure

Mechanically scan filesystem for open work across N sources. Cluster noise.
Filter false positives. Produce actionable items ranked by impact.

## Providers

- `/todo` (Step 0 — primary, 16 sources, `scan_functions.py`)
- `/maintain` (fleet health checks)
- `/skill-prune` (stale/duplicate skill entries)
