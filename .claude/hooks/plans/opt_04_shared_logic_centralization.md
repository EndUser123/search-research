# Plan 04: Centralize Shared Logic and Utilities

## Problem Statement
Common utility functions (session ID detection, terminal identification, intent classification) are duplicated across `UserPromptSubmit_router.py`, `PostToolUse_router.py`, and other scripts. This leads to inconsistent behavior and maintenance overhead.

## Objectives
- Eliminate code duplication across routers.
- Provide a robust, single source of truth for common hook operations.
- Centralize intent detection patterns.

## Proposed Changes

### 1. Expand `shared_utils.py`
- Move `get_session_id` and `detect_terminal_id` into `shared_utils.py`.
- Consolidate session-specific directory resolution logic.
- Add robust path normalization utilities that handle Windows/Unix differences consistently.

### 2. Enhance `intent_utils.py`
- Move all intent detection regex patterns (diagnostic, speculative, research directives) from `UserPromptSubmit_router.py` to `intent_utils.py`.
- Provide a unified `classify_intent(prompt)` function that all hooks can use.

### 3. Centralize Logging and Timing
- Move performance tracking and `log_performance` logic to `__lib/instrumentation.py` (or similar).
- Standardize the `DEBUG` flag behavior across all hooks.

## Success Criteria
- Zero duplication of `get_session_id` and `detect_terminal_id` across the codebase.
- `UserPromptSubmit_router.py` uses `intent_utils` for all its classification needs.
- Maintenance changes to session detection only need to be made in one place.
