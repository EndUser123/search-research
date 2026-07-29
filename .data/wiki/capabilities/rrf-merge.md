---
title: "rrf-merge"
node_type: capability
created: 2026-07-28
domain: discovery
---

# rrf-merge

**Inputs:** `results_json` (JSON mapping source→ranked list), `k` (int, default 60)
**Outputs:** fused ranked list [{url, title, rrf_score, rrf_backends}]

## Procedure

use_tool("search__fuse", {"results_json": "...", "k": 60})
