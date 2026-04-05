# Plan 03: Hook Directory De-cluttering

## Problem Statement
The `P:/.claude/hooks` root directory contains over 300 files, including many tests, diagnostic scripts, backups, and temporary files. This "flat" structure makes it difficult to find core logic.

## Objectives
- Clean up the root `hooks` directory.
- Improve file discoverability by categorizing files into subdirectories.
- Standardize the location for tests and internal libraries.

## Proposed Changes

### 1. Categorize and Move Files
- **`tests/`**: Move all `test_*.py` files and `run_hook_test.py`.
- **`tools/`**: Move diagnostic and verification scripts (`_check_*.py`, `_verify_*.py`, `_find_*.py`, `query_*.py`, `inspect_*.py`).
- **`__lib/`**: Move internal support modules and logic-heavy files that aren't entry points (`tdd_core.py`, `state_manager.py`, `instrumentationutils.py`, `intent_utils.py`).
- **`_archive/`**: Move all legacy/backup files (`*.patch`, `*.backup*`, `*_v1.py`, `*_v2.py`, `legacy/`).
- **`docs/`**: Ensure all `.md` files (except `CLAUDE.md` and `README.md`) are moved to the `docs/` subdirectory.

### 2. Update Imports
- Perform a global search and replace to update imports after moving modules to `__lib/` or other subdirectories.
- Ensure `sys.path` manipulations in routers are updated to include new locations.

### 3. Git Management
- Update `.gitignore` if any new temporary directories are created.
- Ensure all moved files are correctly tracked by git.

## Success Criteria
- Root `hooks` directory contains primarily entry points (Routers) and essential documentation.
- Total files in root directory reduced from 300+ to <50.
- All hooks and tests continue to run without import errors.
