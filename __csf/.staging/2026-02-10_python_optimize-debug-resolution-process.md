# Architecture Decision: Optimize Debug Resolution Process

**Date:** 2026-02-10
**Template:** Python
**Query:** how can we optimize the process so that resolution is more efficient?

---

## Decision

Implement **code-first investigation pattern** + **Windows subprocess audit** + **CKS pattern storage**

## Rationale

1. **Code-first pattern** prevents symptom speculation; the terminal flash was solved immediately after reading the hook file
2. **psutil eliminates** the Windows console window issue ([documented pattern since 2012](https://stackoverflow.com/questions/10767259/prevent-python-windows-from-being-focused))
3. **CKS storage** prevents cross-session recurrence; MEMORY.md exists but needs structured pattern entries

## Alternatives Considered

- **Add logging to all subprocess calls** — Would increase noise without fixing root cause; psutil eliminates the problem
- **Hook self-test suite** — High implementation overhead; code-first pattern catches issues earlier
- **Disable investigation gate for symptoms** — Would increase false fixes; gate is correct but needs "symptom → code" mapping

## Risk

- **Psutil dependency** — Already in use (line 414 of SessionStart_semantic_daemon.py); no new dependency
- **Pattern storage format** — CKS schema supports "pattern" type; compatible with existing structure

## Implementation Plan

| Priority | Change | Files |
|----------|--------|-------|
| P0 | Code-first investigation pattern | MEMORY.md (reinforce), /rca SKILL.md (update) |
| P0 | Windows subprocess audit | Audit all hooks for tasklist/wmic, replace with psutil |
| P1 | CKS pattern storage | Add "subprocess focus stealing" pattern entry |
| P2 | Hook self-test | Add startup verification for non-disruptive behavior |

## Confidence

85% — Based on analysis of the actual case where code reading immediately revealed the root cause after multiple sessions of speculation. Web research confirms psutil is the established solution for Windows subprocess focus issues.

## Adversarial Self-Review

Weakest assumption is that "code-first" will actually be followed. The pattern existed before (MEMORY.md documents "Verify before claiming") but wasn't followed. Enforcement may require a hook-level check.

## Sources

- [Prevent python windows from being focused - Stack Overflow](https://stackoverflow.com/questions/10767259/prevent-python-windows-from-being-focused)
- [VSCode Python: How to prevent the debugger stealing focus](https://github.com/microsoft/vscode-python/discussions/22017)
- [Window loses focus when running subprocess - Sublime Forum](https://forum.sublimetext.com/t/window-loses-focus-when-running-subprocess/44022)
- [VSCode issue: Debugger unexpectedly steals focus](https://github.com/microsoft/vscode/issues/162873)
