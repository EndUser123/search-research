---
title: "In claude code, I would use this after a task is complete.  Do you have any ideas to enhance it?"
date: "2026-07-11"
mode: "COPILOT"
uuid: "62b5440a-5d30-4236-a880-fcb83d9aaa40"
entry_count: 1
---

## Human

In claude code, I would use this after a task is complete.  Do you have any ideas to enhance it?

## Assistant

Good, I have the full content of the skill. Now I'll analyze it deeply and brainstorm enhancements drawing on your known patterns (hooks, epistemic validation, self-verifying skills, cost optimization).

Here's a thorough breakdown of enhancement ideas for your `/check` skill, organized by impact tier:

***

## What `/check` Does Well (Baseline)

It's a clean, minimal two-phase sequential gate: verify → code-review. The failure table is excellent — clear stop/continue semantics. The "What /check does NOT do" section prevents scope creep. This is solid, purposeful design.[1]

***

## High-Impact Enhancements

### Phase 0: Pre-flight Change Assessment

Before running either phase, inspect `git diff --stat` (or `git diff HEAD --stat`) to determine *what changed*. Use this to:

- **Skip verify** if only non-testable files changed (e.g., `.md`, config, prompts, SKILL files) — avoids a pointless verify run
- **Scope code-review** to only the changed files, reducing noise and token cost
- **Emit a "change class" label** (`test-only`, `logic`, `docs`, `mixed`) in the output so you know what phase ran and why

This directly addresses your cost optimization instinct — don't burn tokens reviewing files that didn't change.[1]

***

### Phase 1.5: Type/Lint Gate (Between Verify and Code-Review)

Insert a lightweight static analysis step between phases:

```yaml
workflow_steps:
  - verify
  - typecheck        # NEW: tsc --noEmit / mypy / pyright
  - code_review
```

Type errors are cheaper to catch than code-review annotations, and they surface a whole class of correctness bugs (wrong argument types, undefined properties) that `/code-review` may miss or handle verbosely. Gate behavior: if typecheck fails, stop — same as verify.[1]

***

### Structured Output / Summary Block

Currently `/check` emits whatever the sub-skills emit. Add a mandatory **summary block** at the end:

```
/check complete ─────────────────────────
  Phase 1 (verify):      ✅ passed  [3 tests]
  Phase 1.5 (typecheck): ✅ passed
  Phase 2 (code-review): ⚠️  2 fixes applied
  Files changed by fixes: src/router.ts, src/types.ts
  Net status: CLEAN
──────────────────────────────────────────
```

This makes `/check` output machine-parseable for your orchestration layer (e.g., a hook that reads the exit status and decides whether to proceed to `/commit` or `/deploy`).[1]

***

### Idempotency Guard

If `git diff` is empty (nothing staged or changed since last commit), `/check` should detect this and exit immediately with `"Nothing to check — working tree is clean."` rather than burning two skill invocations on a no-op.[1]

***

## Medium-Impact Enhancements

### Severity Thresholding for Code-Review

Right now, any code-review output is accepted and applied. Add an optional `--strict` flag:

- Default: apply fixes and proceed
- `--strict`: if code-review finds issues rated `high` severity, stop and report rather than auto-applying

This mirrors your epistemic validation pattern — don't silently mutate if the mutation is high-risk.[1]

### Drift Detection (Post-Fix Re-Verify)

After `/code-review --fix` applies changes, re-run `/verify` once more. Code-review fixes can introduce regressions. This closes the loop and catches the rare but painful case where cleanup breaks a test. Add to failure table:

| Phase outcome | /check behavior |
|---|---|
| Post-fix re-verify fails | Report regression introduced by code-review fix; revert or escalate |

The cost is one extra verify pass, but it catches fix-induced regressions before they silently land.[1]

### Context Injection for Code-Review

Pass the task description (from the preceding `/go` or task prompt, if available in context) to `/code-review` as a `--context` hint. This lets the reviewer evaluate whether the *intent* was achieved, not just whether the code is clean. Without context, code-review can only judge syntax/structure, not correctness of purpose.[1]

***

## Low-Impact / Cosmetic

- **Version bump trigger**: increment `version` on any structural change to the workflow (currently `1.0.0` — adding Phase 0 or 1.5 warrants `1.1.0`)[1]
- **Category tag**: consider `category: quality+gate` instead of `category: quality` to distinguish reactive checks from proactive ones in your skill registry
- **`/check --dry-run`**: report what *would* run (based on change class) without executing — useful for previewing in high-stakes branches

***

## What to NOT Add

Given your explicit design philosophy in the skill's "What /check does NOT do" section:[1]

- **Don't add mutation tests** — that's a QA gate, not a post-task loop
- **Don't add `/simplify-enhanced`** — you deliberately removed it from this workflow; the description says it replaces that manual habit
- **Don't add PR generation** — that's a separate concern and would bloat the skill beyond its single responsibility
- **Don't duplicate `/go` STEP 3-6** — the skill already calls this out; any overlap with `/go`'s pipeline should be conditioned on `if /go did NOT already run`

***

## Suggested Updated `workflow_steps`

```yaml
workflow_steps:
  - preflight_diff      # Phase 0: classify change, skip if clean
  - verify              # Phase 1: smoke tests (skip if docs-only)
  - typecheck           # Phase 1.5: tsc/mypy (optional, configurable)
  - code_review         # Phase 2: --fix, scoped to diff
  - post_fix_verify     # Phase 3: re-verify after fixes (optional, default off)
  - summary             # Always: emit structured /check block
```

The core two-phase contract is preserved — each new step is either a gate or a wrapper around existing work, not new scope.[1]
