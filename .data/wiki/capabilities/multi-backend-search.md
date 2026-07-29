---
title: "multi-backend-search"
node_type: capability
created: 2026-07-28
domain: discovery
---

# multi-backend-search

**Inputs:** `query` (string), `backends` (list, from registry), `shape` (optional)
**Outputs:** ranked results [{url, title, snippet, source}], `backends_called` (list)

## Procedure

Read search-fleet.toml for enabled providers. Fire all in parallel. RRF-merge results.
