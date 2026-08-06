# Codex/Pi Live Acceptance and Default Activation Plan

Status: in progress. Gates 0–2 are complete; Gates 3–4 remain. This document
is not yet a production-activation receipt.

## Target

Reach the following bounded-production definition:

- Codex uses the codex-pi skill automatically for bounded, low-ambiguity,
  independently verifiable work.
- Pi is the automatic worker. A Pi failure halts the task; there is no
  automatic OpenCode fallback.
- OpenCode remains available only through a new, explicit invocation.
- Read-only work cannot edit files.
- Write work runs in a verified Pi worktree, never in the main checkout.
- The selected (model, provider, dispatch path) is recorded and runtime
  identity is verified.
- Codex inspects the result and independently runs the verification commands.
- No ha.json feature or credential file is introduced.

This is the recommended first finish line: bounded interactive production use.
Unattended fleet operation is a separate, harder target described below.

## Current baseline

The source of truth is:

    P:\packages\codex-external-delegation

Evidence already collected on 2026-08-06:

- The full package suite passed: 81 tests, 81 passed, 0 failed.
- external-delegation.mjs check --worker all found Pi 0.82.1 and OpenCode
  1.2.27.
- The batch pilot completed 2 of 2 repetitions successfully through automatic
  Pi routing to minimax/MiniMax-M3.
- The pilot selection confidence was provisional; runtime identity and
  result artifacts were present.
- Package-scoped preflight found no source-discovery conflicts.
- Three activation-slice files are currently uncommitted:
  bin/external-delegation.mjs, skill/SKILL.md, and tests/cli.test.mjs.
- The current result contract checks required-field presence, but not
  task-specific field types. The two pilot responses had different shapes.

Execution notes:

- Gate 0 committed the activation slice as commit fc7abcd.
- The first Pi attempt timed out after 240 seconds without changing its
  isolated worktree; its prompt was ambiguous about the typed property shape.
- The corrected Pi attempt selected MiniMax M3 through Pi, changed exactly the
  four allowed files in an isolated worktree, and returned status ok.
- Parent verification passed: 91 tests, 91 passed, 0 failed; git diff --check
  passed.

## Work plan

### Gate 0 — Parent preserves and integrates the current slice

Parent-only actions:

1. Review the three current activation-slice files and confirm that no
   unrelated files are included.
2. Do not stage, reset, or overwrite other agents' work.
3. Commit only the reviewed package files when explicitly authorized.
4. Rerun the full package test suite after integration.

Pass condition: the intended activation slice has a recorded commit and the
full suite still passes. Until then, the feature is available in the shared
working tree but is not integrated.

### Gate 1 — Delegated result-contract hardening

Delegate only the bounded implementation in the worker prompt below.

Purpose: make machine-consumed worker output safer while preserving the
existing {required: [...]} packet format.

Required behavior:

- Support optional output_schema.properties.
- Support only the primitive JSON types string, number, integer, boolean,
  object, array, and null.
- Use this exact shape: output_schema.properties is an object whose values are
  objects containing one type field, for example
  {"observations": {"type": "array"}}. There is no present flag.
- Validate property definitions when validating a packet.
- On a successful result, check required fields first, then validate the type
  of every declared property whose key is present in result_payload.
- Preserve existing missing-field behavior and backward compatibility for
  packets that have only output_schema.required.
- Convert a type mismatch into status: failed and
  failure_class: contract_error, with deterministic diagnostic fields.
- Add focused regression tests without changing unrelated tests.

The worker must stop after this bounded patch. It must not launch live workers,
change routing policy, change default configuration, or claim production
readiness.

### Gate 2 — Parent verifies the delegated patch

Parent-only actions:

1. Inspect the worker's final diff and reject any out-of-scope changes.
2. Run:

    & 'C:\Users\brsth\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/*.test.mjs

3. Run git diff --check.
4. Confirm no .pi credential configuration, ha.json, Grok Build source,
   or runtime state was changed.

Pass condition: all tests pass, the diff is limited to the allowed files, and
the evidence packet is complete.

### Gate 3 — Codex-originated read-only live acceptance

This cannot be delegated as a readiness decision. Codex must originate the
run and remain the parent.

Before running, create and validate an evidence-driven experiment state with:

- gates.live_authorization: true
- an explicit falsifier
- an explicit abort gate
- an explicit promotion rule
- authority paths covering the package source, worker registries, quota state,
  and the acceptance artifact root

Run two small, real, read-only tasks through codex-pi:

1. Mechanical extraction from the package source.
2. Independent verification of a known source invariant.

For each task, record:

- selected model, provider, and dispatch path;
- quota source and status;
- worker/runtime identity;
- packet, result, stdout, and stderr artifact paths;
- parent verification command and result;
- whether the main checkout changed.

Abort immediately on provider/model mismatch, missing result marker, timeout,
secret-scan hit, unexpected file change, or an unverified result. Do not
fallback to OpenCode.

Pass condition: both tasks complete with valid artifacts and parent-side
verification.

### Gate 4 — Disposable write/worktree acceptance

Use a disposable fixture repository, not the production checkout.

Run one tightly scoped Pi write task with:

- an explicit worktree_request;
- one allowed file;
- no shell or network permission for Pi;
- a deterministic verification command run by Codex after return.

Verify:

- the worktree is registered and points at the intended repository;
- the main checkout is unchanged;
- every changed path is within write_scope;
- a clean worktree can be cleaned up;
- a dirty, scope-violating, or failed worktree is preserved/quarantined;
- the result and lifecycle artifacts are present.

Pass condition: the worker can make the permitted fixture change without any
main-checkout mutation or scope escape.

### Gate 5 — Promote bounded interactive default

After Gates 0–4 pass:

1. Parent records the acceptance evidence and commit.
2. Codex uses codex-pi automatically for bounded work.
3. Codex retains all classification, integration, final judgment, and
   verification responsibility.
4. Monitor the first 5–10 real bounded tasks for selected identity, latency,
   failure class, artifact completeness, and parent acceptance.
5. If a gate fails, stop using the default path and preserve the evidence.

This is the production promotion point for the recommended target.

## Deferred unattended-fleet work

Do not block bounded interactive use on these unless unattended execution is
explicitly required:

- cancellation and process-tree cleanup across a batch;
- resumable, idempotent batch execution;
- artifact retention and cleanup policy;
- durable telemetry and provider reliability feedback;
- quota refresh scheduling and stale-state alerts;
- operator-facing rollback/disable controls.

## Copy-paste prompt for the simpler LLM

~~~text
You are a delegated implementation worker. You are not alone in the
workspace. Preserve existing changes made by other agents and do not make
strategic production-readiness decisions.

Objective:
Implement a minimal, backward-compatible typed result-schema check for the
Codex external-delegation package. Add focused regression coverage and return
an evidence packet. Do not run live providers.

Context:
- Worktree/package: P:\packages\codex-external-delegation
- The package already validates output_schema.required by field presence.
- The current batch pilot showed that two successful worker responses can have
  different types/shapes for the same named field.
- Pi is the default worker, OpenCode is explicit-only, and automatic fallback
  is forbidden.
- The parent already has these unrelated activation-slice changes:
  bin/external-delegation.mjs
  skill/SKILL.md
  tests/cli.test.mjs
- The parent will run shell verification after you return because delegated
  Pi write runs do not have shell permission.

Scope:
- Work directory: P:\packages\codex-external-delegation
- Allowed reads:
  src/contract.mjs
  src/runner.mjs
  src/packet.mjs
  tests/contract.test.mjs
  tests/runner.test.mjs
  package.json
- Allowed writes:
  src/contract.mjs
  src/runner.mjs
  tests/contract.test.mjs
  tests/runner.test.mjs
- Forbidden paths:
  bin/
  skill/
  docs/
  .pi/
  .codex/
  P:\packages\.claude-marketplace\
  P:\.grok\
  P:\.claude\
  any credential, quota, or auth file
- Git actions: do not stage, commit, push, reset, checkout, stash, or clean.

Required implementation:
1. Read the four source/test files before editing.
2. Keep output_schema.required valid exactly as it is today.
3. Add optional output_schema.properties with this exact shape:
   {"observations": {"type": "array"}}.
   Each property value must be an object containing exactly one type from:
   string, number, integer, boolean, object, array, null. A declared present
   property means that its property name exists in result_payload; do not add
   or infer a present flag.
4. Reject malformed property definitions during packet validation.
5. On a successful worker result:
   a. preserve the existing missing-required-field failure behavior;
   b. validate every declared property that is present;
   c. treat integer as Number.isInteger;
   d. distinguish arrays from objects;
   e. treat null as its own type.
6. A type mismatch must return status=failed and
   failure_class=contract_error, clear the result_payload, and provide stable
   diagnostic fields naming the invalid result field, expected type, and
   observed type.
7. Keep blocked-result payload preservation and all existing failure classes
   unchanged.
8. Add only focused tests for:
   - valid typed schema;
   - invalid schema type;
   - correct typed result;
   - wrong typed result;
   - legacy required-only packet/result behavior.
9. Keep the change minimal. Do not refactor unrelated code.

Do not:
- launch Pi, OpenCode, agy, MMX, or any external provider;
- inspect or modify credentials or ha.json;
- change provider selection, quota policy, worker commands, fallback policy,
  worktree policy, CLI behavior, or skill instructions;
- modify the parent activation-slice files;
- edit files outside the allowed write list;
- stage, commit, push, reset, stash, or delete artifacts;
- claim that the system is production-ready.

Stop if:
- any allowed target file has unexpected concurrent edits;
- the required behavior would require changing files outside the allowed
  write list;
- the existing required-only packet format would break;
- you cannot preserve the current missing-field and blocked-result behavior;
- live provider access or shell execution would be required.

Parent verification after return:
& 'C:\Users\brsth\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/*.test.mjs
git diff --check

Final evidence packet. Return these headings exactly:

Objective
Preconditions
Commands
Files read
Files changed
Artifacts produced or inspected
Key observations
Gate verdict
Blockers / uncertainty
Git status summary
Explicit forbidden actions avoided

Do not report a successful test run unless the harness actually permitted and
completed it. Otherwise state that the parent verification commands remain
pending.
~~~

## Parent acceptance checklist

Accept the worker result only if:

- the changed-file list is exactly within the allowed write list;
- no activation-slice, Grok, credential, quota, or runtime-state files changed;
- the evidence packet reports the actual commands and statuses;
- the parent reruns the full test suite and git diff --check;
- the parent inspects the final diff;
- Gates 3 and 4 are still run by Codex and are not inferred from the worker's
  report.
