---
title: "Rhai workflow smoke checks validate parse, not function-call validity"
created: 2026-08-01
source: session-019fb933 (close-check Phase 4 build, /tp critique)
tags: [rhai, workflow, smoke-check, validation, grok-build, function-calls, inline-array, parse-vs-behavior]
summary: >
  Rhai workflow smoke checks (`validate_only: true`) verify the script parses
  and the workflow shell accepts it, but do NOT validate that every function
  call exists at runtime. Two distinct bugs survived multiple smoke-check
  iterations in the close-check workflow: `session_id.substr(0, 7)` (no such
  method) and `#[...]` inline array passed directly to `parallel()`. Both
  parse cleanly, both fail at execution with "Function not found" or "'#' is
  a reserved symbol." Smoke check pass ≠ behavioral correctness.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
relations:
  - target: wiki/concepts/grok-build-workflows-rhai-orchestration.md
    type: extends — adds smoke-check scope limitation to Rhai dialect specifics
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related — the workflow where both bugs were caught
  - target: wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md
    type: refines — Phase 4 Finalize was added in the same session partly because smoke-check confidence was insufficient
---

# Rhai workflow smoke checks validate parse, not function-call validity

## Decision context

**Why this matters:** the Rhai smoke-check pass is the only validation step a workflow author typically gets before live execution. Both bugs in close-check (substr + inline array) passed the smoke check but only surfaced on first live run — after two iterations of edits. Any future workflow author who trusts `validate_only: true` as behavioral validation is going to ship latent runtime bugs.

## The two bugs

### Bug 1: `session_id.substr(0, 7)` — method doesn't exist

The Rhai string type does not expose `substr()`. Available string slicing uses `sub_string()` (the standard library name) or character iteration. The script parsed, the smoke check passed, the runtime error was:

```
dry-run: failed: Function not found: substr (&str | ImmutableString | String, i64, i64) (line 176, position 70)
```

### Bug 2: `parallel(#[ ... ])` — inline array literal is reserved syntax

Rhai treats `#[` as a reserved opening token (likely intended for future array-literal syntax or similar). Passing `#[...]` directly to `parallel()` fails with:

```
script failed to parse: '#' is a reserved symbol (line 513, position 32)
```

The workaround used in the rest of the workflow is the imperative `arr.push(#{...})` pattern, which works fine. The script needs to build the array first, then pass it to `parallel()`.

## What the smoke check actually validates

Rhai's `validate_only: true` (the smoke-check path) verifies:

- Script parses (syntax-level token check, not type-level)
- Workflow shell accepts the script (registered name, declared phases count)
- Canned-host dry-run completes (canned inputs, no live deps)

It does NOT verify:

- Every method called on a value actually exists at runtime
- Inline array/collection literals inside function calls parse under that context
- All code paths were exercised (canned run only hits the happy path)

## The fix and its limits

Two patches landed in commit `322f0d3` (close-check fixes, 13 findings):

1. `substr(0, 7)` → `sub_string(0, 7)` (Rhai stdlib name)
2. `parallel(#[...])` → build array with `.push()`, then pass to `parallel()`

These are mechanical fixes. The structural lesson is: **smoke checks catch syntax errors, not API-availability errors.** A different category of bug that parse-level checks miss.

## What this means for our workspace

**For workflow authors:**

1. After `validate_only: true` passes, run a real (non-canned) execution once before claiming the workflow works. The canned-host dry-run path bypasses real dependencies (git, transcript, harvest, close_runner.py) and won't exercise the failure modes those dependencies introduce.
2. Don't trust the first live run to validate behavior — the first live run **is** the validation. Treat it as high-stakes and watch for errors.
3. When the Rhai error message says "Function not found" or "'X' is a reserved symbol," check the API reference — the script almost certainly parsed but called something that doesn't exist.

**For reviewers (`/review` skill):**

1. When reviewing a workflow that was only smoke-checked (not run live), flag any function calls as `[NOT_PROVEN_AT_RUNTIME]` and require a live run before stamping "behavioral correctness."
2. The existing [[grok-build-workflows-rhai-orchestration]] concept lists Rhai dialect specifics but doesn't yet call out the smoke-check scope limitation. Future edits to that page should add it.

## Falsifier

This finding is wrong if:

- Rhai gains a static type checker / method-resolution pass that runs as part of `validate_only: true`. Currently the smoke check is purely parse-level.
- All close-check-style workflows in the workspace get mandatory live-run validation in their CI/sandbox before ship. (No such pipeline exists today.)
- A future Rhai release accepts `#[...]` as inline array syntax (resolving Bug 2). The substr bug would still need a real fix.

## Receipts

The mechanism claims in this entry are sourced from the following observable artifacts:

- **Smoke check passes parse, not function calls:** observed via workflow tool with validate_only:true returning canned-host success message immediately before live execution failed with the substr/inline-array errors. Smoke-check pass + live fail in the same session = empirical evidence smoke-check is parse-level only. Session transcript line ~165.
- **Bug 1 (substr does not exist) error message:** Function not found: substr with type signature (&str | ImmutableString | String, i64, i64) at line 176 position 70. Observed in ~/.grok/workflows/close-check.rhai line 176 (pre-fix). The fix (sub_string) landed at line 176 post-commit 322f0d3.
- **Bug 2 (inline #[...] in parallel()) error message:** script failed to parse with '#' is a reserved symbol at line 513 position 32. Observed in ~/.grok/workflows/close-check.rhai line 513 (pre-fix). The fix (build array via .push() then pass) is at lines 511-538 post-commit 322f0d3.
- **Smoke-check scope:** validate_only:true uses canned-host inputs and does not exercise real dependencies (git log, transcript, harvest, close_runner.py). Cross-reference: grok-build-workflows-rhai-orchestration line 263 mentions validate_only:true but does not document its scope limitation.

## Sources

- Session 019fb933 transcript, lines 158-176 (close-check smoke-check debug)
- Commit `322f0d3`: "fix(close-check): 13 findings from /tp critique" — both bug fixes landed here
- `~/.grok/workflows/close-check.rhai` — current state, both bugs fixed
- [[grok-build-workflows-rhai-orchestration]] § "Rhai dialect specifics" — related context on what's expressible

## Auto-related

- [[grok-build-workflows-rhai-orchestration]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[skill-catalog]]
- [[code-orchestrates-model-judges-skill-scale]]

