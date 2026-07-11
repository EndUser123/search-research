---
name: check
description: "Post-task loop: verify -> typecheck (auto-detect) -> code-review (strict by default; --apply to force) -> re-verify. Replaces the manual `, /verify + /simplify-enhanced + /code-review --fix` habit."
version: 1.2.0
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
/check              -- full loop (verify, typecheck, code-review, re-verify). STRICT by default: stops before applying if code-review reports high-severity findings.
/check --apply      -- force-apply all findings (low/med/high) without stopping. Use when you have already reviewed and want auto-fix.
```

## Phase 1: Verify

Invoke the built-in `/verify` (Skill tool, name `verify`). Let it run to completion.

- If `/verify` exits with failures or reports test failures, report the outcome and stop. Do not proceed.
- If `/verify` passes or is skipped (no test to run), continue.

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

**Default (strict):** read code-review output for severity markers. If any issue is rated
`high` severity (or equivalent -- exact label depends on the built-in), report them and stop. Do
not auto-apply high-severity findings. Low/medium findings are auto-applied (`--fix`).

**`--apply` mode:** force-apply ALL findings including high-severity, without stopping. Use when
you have already reviewed the diff and want auto-fix.

**Fail-open:** if severity is unparseable, strict falls back to apply mode (do not guess at a
gate the output does not support). This makes default-strict safe-or-equal to default-apply:
identical when severity is unparseable, safer when it is.

If the built-in `/code-review` is unavailable or errors, fall back to reviewing `git diff`
(or `git diff HEAD`) manually for correctness, reuse, simplification, and efficiency; do not
abort.

## Phase 2.5: Post-fix Re-Verify

After code-review applies fixes (or reports they were unnecessary), re-run `/verify` once.

This catches the case where a cleanup fix introduces a regression. Bounded to **one** re-run --
fail and stop if it regresses, do not loop.

| Phase outcome | /check behavior |
|---|---|
| Verify fails (Phase 1) | Stop. Report the failure. Do not proceed. |
| Verify passes | Proceed to typecheck (Phase 1.5). |
| Typecheck fails | Stop. Report errors. Do not proceed. |
| Typecheck skipped | Continue to code-review. |
| Code-review: no high-severity (default strict) | Auto-apply low/med, proceed to re-verify (Phase 2.5). |
| Code-review: high-severity present (default strict) | Stop. Report high-severity findings. |
| Code-review: `--apply` passed | Auto-apply all findings, proceed to re-verify. |
| Code-review unavailable | Fall back to manual diff review; proceed. |
| Re-verify fails (Phase 2.5) | Stop. Report code-review fix introduced a regression. |
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
| **Pre-flight change assessment** (Phase 0, `git diff`-based scoping) | Git is unreliable in this environment (index-lock re-fires, Git-Bash word-splitting, cross-terminal ambiguity). Skips diff-based gating and lets each built-in see the whole tree -- simpler and more robust. |
| **Idempotency guard / no-op exit** | Same root cause: auto-commit fires at Stop, not mid-run, so the diff is populated mid-check. Scoping off that diff would be fragile. |
| **Structured machine-parseable output summary** | No consumer. Building an output contract before a consumer exists is speculative. Would also break the stateless design (multi-terminal isolation). |
| **`/simplify-enhanced` inclusion** | Deliberately removed from the workflow. /code-review already covers reuse/simplification/efficiency. /simplify-enhanced value-add (FP-resistant dup detector) is kept available as a standalone command when needed, not in every loop. |

