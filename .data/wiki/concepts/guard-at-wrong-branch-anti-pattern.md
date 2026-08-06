---
title: "Guard-at-wrong-branch: error-handling code placed in a branch that only runs when the error didn't occur"
concept_type: "failure-mode"
created: 2026-08-06
source: session-019fc927 (close_accounting.py REV-001 from /review)
tags: [failure-mode, error-handling, control-flow, guard-placement, transferable-pattern, code-review]
agent: grok
host: both
cognitive_load: 2
verification: source-verified
summary: >
  When adding error-handling guards to existing code, the guard must be placed
  BEFORE the branch that short-circuits on the error condition — not inside a
  branch that's only reached when the error DIDN'T occur. This sounds obvious
  in the abstract but is a recurring failure mode when the existing control
  flow already has early returns/branches that consume the error state before
  the guard can fire. The pattern: a function returns a default value (e.g.,
  total: 0) on error, and the caller's `if total == 0:` branch fires before
  the `else:` block where the error guard was added.
relations:
  - target: wiki/concepts/stop-hook-state-file-keyword-trap
    type: related
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write
    type: related
---

# Guard-at-wrong-branch: error-handling code placed in a branch that only runs when the error didn't occur

## Decision context

**Why this knowledge was needed:** during session 019fc927, a `/review` of
close_accounting.py found that the `git_errored` guard added to handle git
scan failures was dead code. The guard was placed inside the `else:` block
(line 2536) of a conditional chain where `elif remaining == 0:` (line 2523)
fires first when `scan_git_status` returns `total: 0` on error. The guard
could never execute in the exact scenario it was written for.

## The mechanism (source-verified)

`scan_git_status()` returns `{"total": 0, ..., "error": "..."}` on failure
(lines 1702, 1780). In `resolve_gates()`:

```python
remaining = git_status.get("total", 0)     # gets 0 on error
# ...
elif remaining == 0:                        # FIRES on error (total=0)
    gates["git_state"] = {"state": "pre_satisfied", ...}  # false clean
else:                                       # only runs when remaining > 0
    git_errored = bool(git_status.get("error"))  # guard placed HERE
    # ... git_errored is checked, but this branch never runs on error
```

The guard was correct in isolation — it checked the right field and escalated
correctly. But it was placed inside a branch that's structurally unreachable
when the error occurs, because the error produces the same `total: 0` value
that the "clean tree" branch consumes.

## The general pattern

This is not unique to close_accounting.py. It manifests whenever:

1. A function returns a **default/fallback value** on error (e.g., `total: 0`,
   `result: None`, `data: []`)
2. The caller has an **early branch** that matches the fallback value (e.g.,
   `if total == 0:`, `if not result:`, `if not data:`)
3. The error guard is added **after** the early branch, inside a block that
   only runs when the value is non-default

The guard author sees the error field (`git_status.get("error")`) and reasons:
"I need to check this before proceeding." But they place the check at the
level where the *consequence* of the error matters (the dirty-tree handling),
not at the level where the *cause* of the error is first observable (before
the `remaining == 0` branch).

## Detection

This pattern is hard to detect by reading the guard alone — the guard looks
correct. It requires tracing the control flow from the error source through
all branches that consume the error's side effects (the `total: 0` return
value).

**Code review question:** "When the error condition occurs, does execution
reach this guard? Trace the value of the error field through each branch from
the function return to the guard location."

**Static analysis hint:** if a function returns `{default_value, "error": X}`
and the caller has `if default_value:` before `if error:`, the error check is
structurally unreachable on error.

## What this means for our workspace

1. **Error guards must precede the branch that consumes the error's side
   effects.** In the close_accounting.py case, the fix was to add
   `elif bool(git_status.get("error")):` BEFORE `elif remaining == 0:`,
   so the error check fires before the false-clean branch.

2. **This is a code review checklist item.** When reviewing code that adds
   error handling to existing conditional chains: trace the error value from
   source to guard. If any earlier branch consumes the error's side effect
   (the default return value), the guard is dead code.

3. **The pattern extends beyond error handling.** Any guard placed after a
   branch that short-circuits on the condition the guard checks is dead code.
   The general principle: guard placement must precede the branch it protects.

## Falsifier

This concept is wrong if: the guard-at-wrong-branch pattern never recurs
(after 10 code reviews, no instance is found), OR it turns out the pattern
is already captured by an existing concept (e.g., a linter rule that detects
unreachable code). As of this session, no existing wiki concept names this
specific failure mode, and the close_accounting.py instance was caught only
by a multi-specialist `/review` with control-flow tracing.

## Receipts

- `close_accounting.py:1702` — `scan_git_status` returns `total: 0` on git failure
- `close_accounting.py:1780` — `scan_git_status` returns `total: 0` on exception
- `close_accounting.py:2523` (pre-fix) — `elif remaining == 0:` fires on error (total=0)
- `close_accounting.py:2536` (pre-fix) — `git_errored` guard placed inside unreachable `else:` block
- `close_accounting.py:2529-2534` (post-fix) — `elif bool(git_status.get("error")):` added BEFORE `remaining == 0` branch
- `/review` findings: `P:/.artifacts/console_b96b0592-1ffe-4116-8b77-4d8b/grok-review/session-full/20260806-120512/findings.json` (REV-001)
- Fix commit: `d6999cb` in ~/.grok

## Cross-references

- [[stop-hook-state-file-keyword-trap]] — related failure mode in the same session; both stem from coupling between state files and control flow
- [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — the principle of reading source before claiming how code works; this pattern was missed initially because the code wasn't traced from error source to guard
- [[enforcement-code-needs-its-own-mechanical-tests]] — enforcement code (gates, guards) needs test coverage; the dead guard would have been caught by a test that simulates the git-error condition
- [[lexical-vs-semantic-verification-gap]] — the guard checks the right field (lexical correctness) but is structurally unreachable (semantic incorrectness); the same gap between "looks right" and "is right"

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[claude-code-hooks]]
- [[codebase-knowledge-graph-mapping]]

