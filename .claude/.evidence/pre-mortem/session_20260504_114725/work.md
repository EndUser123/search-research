plugin-installer audit_source_cache_drift fix

Target: plugin-audit-and-fix.py audit_source_cache_drift() function
Context: Fixing 3 compounding bugs in source-cache drift detection

## What was changed

1. Added  for semver numeric sort (line ~342-350)
2. Rewrote  to detect 3 drift types:
   - stale_version_dirs: old version directories in cache
   - source_modified: files in source changed since cache
   - cache_only: files in cache not in source
3. Fixed hardcoded P:/packages/ path → uses plugins_dir param

Key changes in audit_source_cache_drift():
- version_dirs sorted by _version_key, reverse=True (latest first)
- current_version_dir = version_dirs[0] (now correctly picks latest)
- stale_versions = [d for d in version_dirs if d != current_version_dir]
- cache_files_set built alongside src_files_set
- auto-fix: rmdir stale, robocopy source→cache for modified, warn for cache_only

## Files

- P:/packages/plugin-installer/scripts/plugin-audit-and-fix.py (source)
- P:/packages/.claude-marketplace/plugins/plugin-installer/skills/plugin-installer/SKILL.md (skill)
