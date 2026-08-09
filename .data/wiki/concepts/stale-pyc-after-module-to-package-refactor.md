---
title: "Stale pyc after module-to-package refactor: Windows import resolution failure"
created: 2026-08-09
tags: [hook-failure, python, pycache, import-resolution, refactoring, windows, stale-cache, fail-open, exit-code-1]
host: both
agent: grok
verification: session-validated-2026-08-09
cognitive_load: 1
summary: >
  When a Python module file (e.g., quality_gate.py) is refactored into a
  package directory (quality_gate/__init__.py + quality_gate/main.py), the
  old __pycache__/quality_gate.cpython-314.pyc file is NOT automatically
  removed. On Windows, Python's import resolver can intermittently find the
  stale .pyc (expecting the old module structure) alongside the new package
  directory, causing import failures that produce exit code 1 before main()
  runs — bypassing exception handlers. Fix: delete stale .pyc files after
  any module→package refactor. Secondary prevention: add __pycache__ cleanup
  to the refactoring safety protocol.
---

# Stale pyc after module-to-package refactor

## The failure

Session 019fdf3d refactored `quality_gate.py` (83KB monolith) into a
`quality_gate/` package directory with 4 modules. The old
`__pycache__/quality_gate.cpython-314.pyc` was left behind.

When Grok Build's hook dispatch invoked `quality_gate/main.py` via the
Stop event, Python's import resolver intermittently failed because:

1. `__pycache__/quality_gate.cpython-314.pyc` (86KB, old monolith structure)
2. `quality_gate/__init__.py` (new package structure)

Both resolve to the name `quality_gate`. On some invocations, Python's
cache validator prefers the stale `.pyc` (which expects the old flat-module
layout), the import fails, and Python exits 1 before main() runs.

## Why this is hard to diagnose

- **The exception handler never fires.** The import failure happens at
  module-load time, before `main()` is called. The `try: main(); except:
  sys.exit(0)` pattern at the bottom of the script cannot catch it.
- **Exit code 1 is non-blocking.** Per Claude Code docs, exit code 1 from
  a hook is treated as "non-blocking error" — the action proceeds. So the
  functional impact is invisible: Claude is allowed to stop, and the only
  signal is a UI notice the operator may or may not see.
- **The failure is intermittent.** Python's import cache validator uses
  mtime + size comparison. Under concurrent access (multiple fleet
  sessions), the race between cache validation and file system state
  produces intermittent success/failure.
- **Reproduction requires the exact cache state.** Running the hook
  manually (which creates a fresh `.pyc` for the package) resolves the
  issue, making it impossible to reproduce from a clean state.

## The fix

Delete stale `.pyc` files after any module→package refactor:

```powershell
Remove-Item "path/to/__pycache__/old_module.cpython-*.pyc" -Force
```

## Secondary prevention

Add to the refactoring safety protocol (`P:/.claude/rules/refactoring-safety.md`):

> When renaming a module file to a package directory (e.g., `foo.py` →
> `foo/__init__.py`), delete `__pycache__/foo.cpython-*.pyc` immediately
> after the refactor. Python's import resolver on Windows can intermittently
> find the stale bytecode cache alongside the new package directory,
> producing exit code 1 failures that bypass exception handlers.

## Relationship to existing patterns

- `[[hook-failure-mode-taxonomy]]` — A1 (fail-open masks bugs). This is a
  variant: the failure is masked not by fail-open exception handling but by
  the import occurring before the exception handler is registered.
- `[[grok-build-hook-exit-code-1-stderr-as-failure-signal]]` — documents
  that Grok Build reports exit 1 for various reasons. This concept adds a
  new specific cause: stale `.pyc` import resolution failure.

## Falsifier

This concept is wrong if the exit code 1 recurs after the stale `.pyc`
files are deleted. That would mean the root cause is elsewhere (transient
Python startup failure, file lock contention, or a different import issue).
