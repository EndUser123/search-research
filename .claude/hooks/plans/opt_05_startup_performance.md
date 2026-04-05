# Plan 05: Optimize Hook Startup and Execution Performance

## Problem Statement
While the router approach has already reduced overhead, the "God scripts" still have significant import-time costs due to the number of modules they load eagerly. As the system grows, maintaining <50ms overhead per tool use is critical.

## Objectives
- Ensure all hooks maintain <50ms execution overhead.
- Audit and optimize import paths for all entry points.
- Implement consistent caching for expensive operations.

## Proposed Changes

### 1. Universal Lazy Imports
- Audit `UserPromptSubmit_router.py` and `pre_tool_use.py` for non-lazy imports.
- Use the `lazy_imports.py` utility consistently for all heavy modules (especially those involving `subprocess`, `sqlite3`, or complex regex).

### 2. Regex Compilation Cache
- Ensure all regex patterns used in `intent_utils.py` and validators are compiled once and cached.
- Use `re.compile` at the module level or in a lazy cache.

### 3. File I/O Optimization
- Optimize state file reading/writing (e.g., using `threading` for non-blocking log writes where appropriate).
- Reduce redundant file existence checks by caching results during a single execution turn.

### 4. JSON Parsing Audit
- If JSON parsing becomes a bottleneck in the routers, explore faster alternatives or ensure we are only parsing what is necessary.

## Success Criteria
- Router startup time (pre-execution) is under 20ms.
- Total hook overhead (including all modularized sub-hooks) remains under 50ms for typical operations.
- Measurable reduction in "warm" execution time.
