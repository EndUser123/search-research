---
description: Validate plugin structure, manifest, and configuration. Trigger when asked to "validate plugin", "check plugin structure", or "plugin validate".
enforcement: advisory
workflow_steps:
  - Run plugin-audit-and-fix.py validate
  - Check manifest required fields
  - Verify directory structure
  - Report validation results
---

# Plugin Validate

Run plugin-audit-and-fix.py to validate plugin structure and manifest compliance.

## Usage

### Validate all plugins
```bash
python3 "P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py" --validate --marketplace-root "P:/packages/.claude-marketplace"
```

## What it validates

- plugin.json exists and has required fields
- Directory structure matches standard layout
- Skills, commands, agents directories are properly formed
- No orphaned or misplaced files