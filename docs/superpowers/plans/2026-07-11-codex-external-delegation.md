# Codex External Delegation Bridge Implementation Plan

> For agentic workers: use a task-by-task implementation workflow with tests and review gates. Every step uses checkbox syntax.

**Goal:** Let Codex delegate bounded work to OpenCode and external models safely, with OpenCode preferred for subscription-backed providers and PI retained for custom/local providers.

**Architecture:** Codex remains the control plane: it classifies the task, selects policy, creates the packet, and owns verification and acceptance. A tracked Node.js bridge owns packet validation, routing, process execution, artifact capture, failure classification, and containment. Headless full approval is an execution mode, not a containment guarantee.

## Authority model

- Egress authority: external-safe, externally-approved, local-only, or blocked.
- Mutation authority: no mutation, disposable staging, repository-isolated write, or host-sandboxed write.
- Execution identity: invocation id, attempt id, packet hash, source revision, worker version, and model.
- Acceptance authority: launch status, protocol status, worker status, verification status, and final acceptance status.

Routing must be explicit. Either the packet names the worker and model, or a router selects them and emits an immutable selection record. The command builder must not silently override an explicit worker choice.

A Git worktree isolates repository changes but does not sandbox arbitrary shell, filesystem, profile, credential, or network access. Repository-isolated execution must be labelled host-trusted unless an actual OS-level boundary exists.

## Global constraints

- OpenCode is the preferred external worker for subscription-backed and mainstream providers.
- PI is an explicit fallback for llama.cpp, unusual APIs, and programmable extensions.
- Headless workers must not wait for interactive approval prompts; use OpenCode noninteractive auto-approval only inside an approved policy tier.
- Default worker mode is read-only; writes to the primary workspace are disabled.
- Unknown or sensitive data cannot be sent to an external provider without explicit egress authority.
- Never put credentials, auth files, .env contents, or arbitrary environment maps in packets or artifacts.
- Retry only idempotent read-only infrastructure failures, at most once.
- Every invocation has collision-resistant identity and writes artifacts under a controlled state root.
- Worker prose is never success; only a bound, schema-valid result can become candidate evidence.

## Task 1: Define the packet and result contracts

Files:

- Create P:\packages\codex-external-delegation\package.json
- Create P:\packages\codex-external-delegation\src\contract.mjs
- Create P:\packages\codex-external-delegation\src\identity.mjs
- Create P:\packages\codex-external-delegation\tests\contract.test.mjs
- Create P:\packages\codex-external-delegation\tests\identity.test.mjs

Interfaces:

- validatePacket(packet) -> valid packet or structured errors.
- validateResult(result, outputSchema, identity) -> valid result or structured errors.
- createInvocation(packet) -> invocation_id, attempt_id, packet_sha256, artifact_dir.

Steps:

- [ ] Write failing tests for required fields, safe task ids, bounded timeout/output limits, valid fallback definitions, invocation identity, packet hashes, and path traversal.
- [ ] Implement packet validation before any filesystem or process side effect.
- [ ] Implement result fields: launch_status, protocol_status, worker_status, verification_status, acceptance_status.
- [ ] Require every declared output-schema field for worker success.
- [ ] Bind result markers to invocation_id, attempt_id, packet_sha256, and schema version.
- [ ] Run node --test tests/contract.test.mjs tests/identity.test.mjs and commit.

## Task 2: Render prompts and classify failures

Files:

- Create P:\packages\codex-external-delegation\src\prompt.mjs
- Create P:\packages\codex-external-delegation\src\failures.mjs
- Create P:\packages\codex-external-delegation\tests\prompt-failures.test.mjs

Interfaces:

- renderPrompt(packet) -> string.
- extractResultPayload(text, identity) -> bound payload or null.
- classifyFailure(details) -> deterministic failure class.

Steps:

- [ ] Test prompt scope, forbidden actions, output schema, verification profile, identity, and egress policy.
- [ ] Require exactly one bounded result marker; reject duplicate, oversized, truncated, malformed, or foreign markers.
- [ ] Implement deterministic failure precedence: timeout, command missing, auth/quota, context limit, provider unavailable, protocol error, worker failure, unknown.
- [ ] Run focused tests and commit.

## Task 3: Implement deterministic worker execution

Files:

- Create P:\packages\codex-external-delegation\src\commands.mjs
- Create P:\packages\codex-external-delegation\src\runner.mjs
- Create P:\packages\codex-external-delegation\tests\runner.test.mjs

Interfaces:

- routePacket(packet) -> worker, model, reason, policy_version.
- buildCommand(packet, promptSource) -> command, args, cwd, env.
- runPacket(packet) -> normalized result and artifact path.

Steps:

- [ ] Add mocked tests for OpenCode success, PI fallback, missing executable, timeout, non-zero exit, malformed output, duplicate marker, output overflow, and cleanup failure.
- [ ] Make OpenCode the default external route; require explicit fallback to PI.
- [ ] Fix Windows launch without directly spawning .cmd with shell:false. Prefer an underlying executable or a carefully quoted ComSpec strategy.
- [ ] Pass large prompts through stdin or a file rather than a Windows command-line argument.
- [ ] Enforce timeout, output, prompt, and artifact limits. Ensure cleanup failure cannot leave runPacket pending forever.
- [ ] Use a minimal environment allowlist; reject packet-supplied environment overrides.
- [ ] Run tests and commit.

## Task 4: Add CLI, skill, and agent profiles

Files:

- Create P:\packages\codex-external-delegation\bin\external-delegation.mjs
- Create P:\packages\codex-external-delegation\skill\SKILL.md
- Create P:\packages\codex-external-delegation\skill\agents\openai.yaml
- Create P:\packages\codex-external-delegation\opencode\agents\external-readonly.md
- Create P:\packages\codex-external-delegation\opencode\agents\external-writer.md
- Create P:\packages\codex-external-delegation\README.md
- Create P:\packages\codex-external-delegation\tests\cli.test.mjs

CLI interfaces:

- run --packet path-or-stdin
- check --worker pi|opencode|all
- classify --packet path-or-stdin

Steps:

- [ ] Add CLI tests for invalid packets, dry runs, route selection, result shape, and stable exit codes.
- [ ] Implement the CLI without hidden routing changes or arbitrary verification shell execution.
- [ ] Document OpenCode preference, PI fallback conditions, headless operation, egress policy, artifact paths, and acceptance authority.
- [ ] Add a tracked live-install script or documented junction command.
- [ ] Run CLI tests and commit.

## Task 5A: Separate egress authority from mutation authority

Files:

- Create P:\packages\codex-external-delegation\src\policy.mjs
- Create P:\packages\codex-external-delegation\src\staging.mjs
- Create P:\packages\codex-external-delegation\tests\policy-staging.test.mjs
- Modify P:\packages\codex-external-delegation\src\contract.mjs
- Modify P:\packages\codex-external-delegation\src\runner.mjs

Interfaces:

- classifyEgress(packet) -> external_safe | external_approved | local_only | blocked.
- materializeReadOnly(packet) -> staging_cwd, manifest_path, source_revision.
- The staging manifest records canonical source, destination, type, size, and hash.

Steps:

- [ ] Add failing tests proving that unknown/private data cannot route to an external provider without explicit egress authority.
- [ ] Define egress policy independently from mutation policy. Unknown or sensitive inputs default to local_only or blocked.
- [ ] Materialize Tier 1 staging from only declared files.
- [ ] Reject traversal, junctions, symlinks, NTFS reparse points, absolute links, and case-insensitive path escapes.
- [ ] Keep credentials out of staged inputs and use a minimal process environment.
- [ ] Run policy and staging tests, including an unchanged canary outside the staging tree, and commit.

## Task 5B: Define repository-isolated writes without overstating host isolation

Files:

- Create P:\packages\codex-external-delegation\src\writes.mjs
- Create P:\packages\codex-external-delegation\tests\writes.test.mjs
- Modify P:\packages\codex-external-delegation\src\runner.mjs
- Modify P:\packages\codex-external-delegation\README.md

Interfaces:

- createWriteWorkspace(packet) -> cwd, source_revision, dirty_state_policy.
- verifyChangedPaths(workspace, write_scope) -> changed_paths and acceptance result.

Steps:

- [ ] Add tests for committed-only, selected-dirty-file, and unsupported dirty-state policies.
- [ ] Create a disposable worktree or equivalent repository boundary only for explicitly authorized repository-isolated writes.
- [ ] Verify changed paths with git diff/status plus a filesystem canary.
- [ ] Reject writes outside write_scope and report that a worktree is repository isolation, not a host sandbox.
- [ ] Keep host-sandboxed write mode disabled until an actual OS-level boundary is implemented and tested.
- [ ] Run write tests without external model calls and commit.

## Task 5C: Make artifacts and acceptance auditable

Files:

- Modify P:\packages\codex-external-delegation\src\runner.mjs
- Modify P:\packages\codex-external-delegation\bin\external-delegation.mjs
- Create P:\packages\codex-external-delegation\tests\promotion.test.mjs
- Modify P:\packages\codex-external-delegation\README.md

Steps:

- [ ] Store artifacts under task_id/invocation_id/attempt_id with atomic creation and collision rejection.
- [ ] Capture packet hash, source revision, worker/model/runtime versions, route reason, input manifest, raw streams, normalized result, verification evidence, and acceptance decision.
- [ ] Add final secret scanning, retention, disk-full, orphaned-prompt, and output-limit handling. Redaction is defense in depth, not the primary secret boundary.
- [ ] Add an explicit promotion decision artifact. Passing worker tests must not automatically enable default routing or writes.
- [ ] Add concurrency tests proving identical task ids do not share artifacts or results.
- [ ] Run the full test suite and review the complete artifact set before committing.

## Task 6: Install the live skill and run bounded smoke tests

Files:

- Modify runtime only: C:\Users\brsth\.agents\skills\external-delegation and C:\Users\brsth\.codex\skills\external-delegation
- Create runtime artifacts only under the controlled state root
- Modify tracked files: none

Steps:

- [ ] Verify or create junctions only after the tracked package and skill pass tests.
- [ ] Verify SKILL.md is readable from both Codex skill roots.
- [ ] Run command-only checks for opencode --version, pi --version, and bridge check --worker all.
- [ ] Run an OpenCode headless smoke task first; preserve artifacts and verify normalized status plus identity binding.
- [ ] Run a PI compatibility smoke task; preserve artifacts and verify normalized status plus identity binding.
- [ ] Run failure probes without provider calls: missing executable, impossible timeout, malformed/duplicate/foreign marker, path escape, egress denial, and write packet without a valid worktree.
- [ ] Inspect git status, package diff, artifact manifests, secret scans, and canaries. Do not claim live readiness until every fresh command exits as specified.

## Promotion gate and self-review

- [ ] Concurrent identical task ids produce separate artifacts.
- [ ] A copied marker from another invocation is rejected.
- [ ] Worker failed or blocked status cannot become success.
- [ ] Missing required output fields cannot produce success.
- [ ] Windows launch passes spaces, quotes, ampersands, pipes, and parentheses without shell injection.
- [ ] Unknown/private input cannot route externally without egress authority.
- [ ] Tier 1 rejects junction, symlink, reparse-point, absolute-path, and traversal escapes.
- [ ] A filesystem canary outside the staging/worktree remains unchanged.
- [ ] Independent verification failure prevents acceptance even when worker_status is ok.
- [ ] Write mode remains disabled unless its actual advertised boundary is proven.
- [ ] Default routing is an explicit promotion change with a recorded policy version.
