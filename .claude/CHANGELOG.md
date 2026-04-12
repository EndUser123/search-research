# Changelog

All notable changes to Claude Code configuration will be documented in this format.

## [2026-04-11] - Hook Configuration Fix

### Fixed
- **PreToolUse_directory_policy.py**: Removed duplicate subprocess registration from `settings.json`
  - Hook was already correctly registered in in-process dispatch chain via `PreToolUse.py`
  - Duplicate subprocess entry was causing "No stderr output" error messages
  - Configuration change: Removed lines 201-210 from `settings.json` (duplicate PreToolUse_directory_policy.py subprocess entry)

### Root Cause
The hook appeared in both:
1. `PreToolUse.py` IN_PROCESS_HOOKS (line 738) — correct in-process registration
2. `settings.json` PreToolUse section as subprocess command — redundant

When both registrations existed, the in-process version ran first (exiting code 2 to block), then the subprocess version ran and exited code 2 without stderr, triggering Claude Code's "No stderr output" error.

### Verification
- Hook still functions correctly via in-process dispatch
- Path protection enforcement working as expected
- No more duplicate execution or conflicting exit codes

### Notes
- `settings.json` contains sensitive values (CONTEXT7_API_KEY) and is NOT tracked in git
- All configuration changes will be documented in this CHANGELOG.md
