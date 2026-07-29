---
title: "source-authority-discovery"
node_type: capability
created: 2026-07-28
domain: discovery
---

# source-authority-discovery

**Inputs:** `capability` or `entrypoint` tokens, `scope` paths
**Outputs:** evidence packet JSON (source, registration, invocation, test paths)

## Procedure

python discovery_audit.py --scope <paths> --target <tokens> --output <json>
