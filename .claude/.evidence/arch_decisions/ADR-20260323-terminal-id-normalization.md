# ADR-20260323: Terminal ID Normalization — Single Source of Truth

**Status**: Accepted
**Date**: 2026-03-23
**Context**: Terminal ID format mismatch between `hook_base.get_terminal_id()` (env_ prefix) and `skill_guard.detect_terminal_id()` (console_ prefix) caused state file path divergence after context compaction.

## Decision

**Option A: Single normalization source per package** — Each package maintains its own canonical `terminal_id.py` module that all internal detection code must use. No duplicate inline normalization functions.

### Implementation

| Package | Canonical Module | Used By |
|---------|----------------|--------|
| `__lib` (hooks) | `__lib/terminal_id.py` | `hook_base.py` |
| `skill_guard` | `skill_guard/utils/terminal_id.py` | `terminal_detection.py` |

### Why Not a Shared Module?

Sharing a single module across `packages/` and `.claude/hooks/` creates import path dependencies between packages. Each package having its own canonical module with identical logic is the correct pattern for this codebase.

## Root Cause

`skill_guard/utils/terminal_detection.py` called a non-existent `_normalize_id()` function instead of importing `normalize_terminal_id` from its own `terminal_id.py`.

## Changes

1. **`terminal_detection.py`** — Fixed import and calls:
   ```python
   from skill_guard.utils.terminal_id import SOURCE_CONSOLE, SOURCE_ENV, normalize_terminal_id
   return normalize_terminal_id(value, SOURCE_ENV)
   ```

2. **`skill_guard/utils/__init__.py`** — Removed `_normalize_id` export, added `normalize_terminal_id`:
   ```python
   from .terminal_id import normalize_terminal_id
   ```

3. **`StopHook_skill_execution_gate.py`** — Cross-prefix fallback (backward compat workaround):
   ```python
   # ADR-20260323 FIX: Cross-prefix fallback
   if terminal_id.startswith("console_"):
       env_path = state_dir / terminal_id.replace("console_", "env_", 1) / "pending_command_intent.json"
   elif terminal_id.startswith("env_"):
       console_path = state_dir / terminal_id.replace("env_", "console_", 1) / "pending_command_intent.json"
   ```

## Multi-Terminal Safety

- **Safe**: Each terminal reads from its own state file (`terminal_{handle}.json`)
- **Isolation key**: `terminal_id` derived from `WT_SESSION`/`GetConsoleWindow()` is stable per terminal
- **No cross-terminal contamination**: State file paths use terminal-specific handles

## Prevention

**Architectural rule**: Any package with shared identifier normalization must have a canonical `terminal_id.py` module. Detection code must import and use `normalize_terminal_id()` — no inline normalization functions.

## Alternative Considered

**Option B: Cross-prefix fallback** (initially applied as workaround) — Detect mismatch and try both prefixes. Works but fragile — doesn't scale to future prefix changes.

**Selected**: Option A (structural fix) over Option B (bandage).
