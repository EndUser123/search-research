---
title: "capability-routed-search"
node_type: capability
created: 2026-07-28
domain: discovery
---

# capability-routed-search

**Inputs:** `query` (string), `intent` (auto|time_sensitive|domain_scoped|deep|academic|github)
**Outputs:** ranked results, `dispatch_plan` (which backends fired)

## Procedure

python ~/.grok/scripts/search_fleet.py plan "<query>". Execute plan. Fuse.
