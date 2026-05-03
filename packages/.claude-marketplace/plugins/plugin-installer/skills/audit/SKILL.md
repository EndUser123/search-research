---
description: Audit all or specific plugins for manifest issues and auto-fix them. Trigger when asked to "audit plugins", "check plugin manifests", "fix plugin issues", or "plugin audit".
enforcement: advisory
workflow_steps:
  - Run plugin-audit-and-fix.py scan (manifests, hooks, structure)
  - Run plugin-audit-and-fix.py --scan-paths (hardcoded path scan)
  - Auto-fix manifest issues found
  - Report audit results
---

# Plugin Audit

Run plugin-audit-and-fix.py to scan and auto-fix manifest issues across the marketplace.

## Usage

### Audit all plugins
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --auto-fix --marketplace-root "P:/packages/.claude-marketplace"
```

## What it checks

- Manifest validity and required fields
- Directory structure compliance
- Version consistency between source and cache
- Junction vs real-dir detection
- enabledPlugins registration status