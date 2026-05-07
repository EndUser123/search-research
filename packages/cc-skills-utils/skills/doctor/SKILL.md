---
name: doctor
description: Plugin Cluster Diagnostic & Repair Tool
version: 1.0.0
category: maintenance
triggers:
  - /doctor
---

# /doctor - Plugin Cluster Diagnostic

Diagnostic tool for the `cc-skills-*` plugin cluster. Verifies cross-plugin connectivity, identity health, and structural integrity.

## ⚡ EXECUTION DIRECTIVE

**When /doctor is invoked, execute:**

```bash
python P:\\\\packages/cc-skills-utils/skills/doctor/scripts/doctor_main.py
```

## Diagnostics Performed

1.  **Identity Handshake:** Verifies `identity.json` exists and matches the current session ID.
2.  **Structural Audit:** Detects orphaned junctions in the marketplace.
3.  **Version Alignment:** Identifies version drift between clustered plugins.
4.  **Hook Latency:** Measures the overhead of the bundled orchestrators.

## Usage

- `/doctor`: Run standard diagnostic suite.
- `/doctor --fix`: Attempt to repair orphaned junctions or corrupted caches.
