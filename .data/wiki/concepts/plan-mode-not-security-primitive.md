---
title: "Plan mode is not a security primitive"
created: 2026-07-20
source: AAR report 3 (console_b6a64919, 20260720-144745)
tags: [plan-mode, security, containment, architecture]
host: both
agent: grok
verification: single-source-verified
cognitive_load: 2
summary: >
  Plan mode is a thinking phase, not a security gate. Expecting it to
  contain high-risk operations misframes its design. The safety layer
  (hooks, permissions, deny lists) is orthogonal to plan mode.
---

# Plan mode is not a security primitive

## The misconception

"Let's use plan mode to gate dangerous operations." This treats plan mode as a containment mechanism — a layer that prevents writes/deletes/pushes until the user approves.

**Plan mode is not that.** Plan mode is a cognitive phase where the model reasons before acting. Its safety properties are incidental (the model doesn't write while planning), not designed (there's no enforcement layer preventing writes).

## Why it matters

If you rely on plan mode for safety, you get a false sense of containment. The model can exit plan mode at any time. The real safety layer is:

- **PreToolUse hooks** (block tool calls before execution)
- **Permission deny lists** (e.g., `Edit(P:/.claude/**)`)
- **Safe-git gates** (block destructive git operations)

These are enforced structurally. Plan mode is enforced conversationally.

## Evidence

- **R3 L3** (session 2026-07-20): `19-plan-mode.md` describes plan mode as a thinking phase with subagent/bash bypass as designed limitations. The safety story is permission-based, not plan-mode-based.

## Related

- `P:/docs/adrs/19-plan-mode.md` — the plan mode design doc

## Auto-related

- [[grok-build-plan-mode-structured-thinking]]

