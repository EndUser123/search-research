# Plan 01: Modularize UserPromptSubmit Router

## Problem Statement
`UserPromptSubmit_router.py` has grown to over 3,200 lines. It contains both the routing logic and the implementations of numerous hooks (Unified Injector, Skill Enforcement, Plan Injection, etc.). This makes it difficult to maintain, test, and debug.

## Objectives
- Reduce `UserPromptSubmit_router.py` to <500 lines.
- Move hook implementations into a structured directory: `P:/.claude/hooks/userpromptsubmit/`.
- Standardize the hook interface for better extensibility.

## Proposed Changes

### 1. Create New Package Structure
- Create `P:/.claude/hooks/userpromptsubmit/__init__.py`.
- Create `P:/.claude/hooks/userpromptsubmit/base.py` for shared interfaces.
- Create modules for each major hook:
    - `unified_injector.py`: Logic from `run_unified_injector`.
    - `skill_enforcer.py`: Logic from `run_skill_enforcement`.
    - `plan_injector.py`: Logic from `run_plan_context_injector`.
    - `diagnostic_guard.py`: Logic for diagnostic and speculative checks.
    - `intent_handlers.py`: Logic for explicit research directives and intent-based routing.

### 2. Refactor Router
- Implement a `UserPromptSubmitRegistry` that dynamically loads hooks from the new package.
- Use a configuration-driven approach for hook priority and enabling/disabling hooks.
- Simplify `main()` to focus purely on input parsing, execution orchestration, and output merging.

### 3. Performance Maintenance
- Ensure all new module imports are lazy.
- Keep the in-process execution model to maintain the ~90% overhead reduction.

## Success Criteria
- `UserPromptSubmit_router.py` is under 500 lines.
- All existing functionalities (TDD eval, skill enforcement, etc.) continue to work.
- Unit tests pass for each modularized hook.
