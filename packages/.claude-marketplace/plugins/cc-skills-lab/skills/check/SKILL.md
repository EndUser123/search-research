---
name: check
description: "Post-task loop: verify -> typecheck (auto-detect, skip if no config) -> code-review (strict=report-only). --apply to auto-fix. Replaces the manual `, /verify + /simplify-enhanced + /code-review --fix` habit."
version: 1.3.0
status: stable
category: quality
enforcement: advisory
triggers:
  - /check
argument-hint: "[--apply]"
workflow_steps:
  - verify
  - typecheck
  - code_review
  - re_verify
---

# /check

Thin wrapper over built-in skills in sequence. No new analysis code -- just running the right
tools in the right order.

## Usage

```
/check              -- report only (verify, typecheck, code-review, re-verify if --apply). Default: show findings, do NOT auto-apply.
/check --apply      -- auto-fix findings from code-review. Re-runs verify afterwards (bounded to 1 iteration).
```

## Phase 1: Verify

Invoke the built-in `/verify` (Skill tool, name `verify`). Let it run to completion.

- If `/verify` exits with failures or reports test failures, report the outcome and stop. Do not proceed.
- If `/verify` passes or is skipped (no test to run), continue.
- **Note when skipped:** if verify had no test harness to run and `--apply` was passed, emit a warning: 
  `"verify was skipped (no test harness); applying code-review auto-fix with zero runtime verification."`

## Phase 1.5: Typecheck (auto-detect)

Between verify and code-review, run static type checking if a typechecker is available for the
changed files.

**Discovery rule:** enumerate changed files from `git diff --name-only HEAD` (or `git diff` if
HEAD looks synthetic -- fail open either way). For each changed file, find the nearest ancestor
directory containing a typecheck config marker. Deduplicate by config path.

| Config marker | Command to run |
|---|---|
| `mypy.ini` or `.mypy.ini` | `mypy <changed_files_in_project>` (nearest ancestor config) |
| `pyproject.toml` with `[tool.mypy]` | `mypy <changed_files_in_project>` |
| `tsconfig.json` | `tsc --noEmit --pretty` (in that directory) |

If no config is found for any changed file, skip silently -- this is an advisory gate, not a
required one.

If the typechecker reports errors, stop. Report the output. Do not proceed to code-review while
there are type errors -- they produce noise (the reviewer comments on type hacks that should be
structural fixes).

**Extensibility:** when a new language emerges (`.clj`, `.go`, `.rs`, ...), add its config
marker and command to the discovery table above. The structure is stable: ancestor config,
dedup, run.

## Phase 2: Code Review

Invoke the built-in `/code-review` (Skill tool, name `code-review`). Let it run to completion --
it reviews the current diff for correctness bugs, reuse, simplification, and efficiency issues.

**Default (strict, report-only):** show findings to the user. Do NOT apply them. The user
reviews and decides what to apply.

**`--apply` mode:** run code-review with `args: "--fix"` to auto-apply findings. WARNING: if
verify was skipped (no test harness), the fixes apply with zero runtime verification -- review
the diff before proceeding.

If the built-in `/code-review` is unavailable or errors, fall back to reviewing `git diff`
(or `git diff HEAD`) manually for correctness, reuse, simplification, and efficiency; do not
abort.

## Phase 2.5: Post-fix Re-Verify

Only runs when `--apply` was passed and code-review actually made changes. Re-runs `/verify` once.

This catches the case where a cleanup fix introduces a regression. Bounded to **one** re-run --
fail and stop if it regresses, do not loop.

When default (report-only, no apply), re-verify is not needed and does not run.

| Phase outcome | /check behavior |
|---|---|
| Verify fails (Phase 1) | Stop. Report the failure. Do not proceed. |
| Verify passes | Proceed to typecheck (Phase 1.5). |
| Verify skipped (no harness) | Proceed with warning if `--apply`. |
| Typecheck fails | Stop. Report errors. Do not proceed. |
| Typecheck skipped | Continue to code-review. |
| Code-review (default strict) | Show findings. Done. |
| Code-review (`--apply`) | Apply fixes. Proceed to re-verify (Phase 2.5). |
| Code-review unavailable | Fall back to manual diff review; proceed. |
| Re-verify fails (Phase 2.5) | Stop. Report regression introduced by auto-fix. |
| Re-verify passes | Done. |
| Re-verify skipped (no changes made) | Done. |

## What /check does NOT do

- It does not replace a full PR review pipeline
- It does not run mutation tests, QA gates, or adversarial review
- It does not duplicate /go STEP 3-6 (on tasks where /go already ran those)
- It does not scope itself from git diff -- let each built-in see the full working tree
- It does not write state artifacts, counters, or logs -- stateless by design for multi-terminal safety

## Rejected designs (do not re-litigate)

These were evaluated and explicitly rejected. Adding them was evaluated and the decision is
closed.

| Feature | Rejected because |
|---|---|
| **Severity-based gating** (/code-review does not emit parseable severity) | Verified 2026-07-10: the built-in outputs no severity field. Strict-by-default is report-only, not severity-gated. |
| **Pre-flight change assessment** (Phase 0, `git diff`-based scoping) | Git is unreliable in this environment (index-lock re-fires, Git-Bash word-splitting, cross-terminal ambiguity). Skips diff-based gating and lets each built-in see the whole tree -- simpler and more robust. |
| **Idempotency guard / no-op exit** | Same root cause: auto-commit fires at Stop, not mid-run. |
| **Structured machine-parseable output summary** | No consumer. Building an output contract before a consumer exists is speculative. Would also break the stateless design (multi-terminal isolation). |
| **`/simplify-enhanced` inclusion** | Deliberately removed from the workflow. /code-review already covers reuse/simplification/efficiency. /simplify-enhanced value-add (FP-resistant dup detector) is kept available as a standalone command when needed, not in every loop. |

