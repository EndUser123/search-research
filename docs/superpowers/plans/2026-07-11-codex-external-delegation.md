# Codex External Delegation Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Codex able to delegate bounded, low-ambiguity work to PI or OpenCode by default, while generating the handoff packet itself, preserving evidence, classifying failures, and refusing unsafe or unverifiable execution.

**Architecture:** A tracked Node.js package owns a versioned JSON packet contract, prompt renderer, worker command builder, subprocess runner, retry policy, and artifact capture. A Codex skill points to the package CLI and tells the parent agent when and how to use it. The initial default is read-only external delegation; writes require an explicit packet flag and an isolated working directory supplied by the parent.

**Tech Stack:** Node.js 24, built-in `node:test`, `child_process.spawn`, PowerShell junction for the live skill install, PI 0.80.6, OpenCode 1.2.27.

## Global Constraints

- Do not edit or stage the existing dirty files in `P:\.claude`, `P:\.pi`, `P:\.opencode`, or the repository root unless a task below names the file.
- Do not read, copy, log, or commit API keys, auth files, `.env` files, or provider credentials.
- Default worker mode is read-only; the bridge must reject write packets without `write_scope` and `isolated_cwd`.
- Retry only infrastructure failures for idempotent read-only work; never blindly retry a write or a semantic/contract failure.
- Every invocation writes raw stdout, raw stderr, packet, normalized result, and an attempt manifest under `.codex/state/external-delegation/<task_id>/` unless the caller supplies an alternate artifact directory.
- A successful worker response must contain the required result marker and a valid JSON object; raw model prose is never accepted as a successful packet.

---

### Task 1: Define the package and packet contract

**Files:**
- Create: `P:\packages\codex-external-delegation\package.json`
- Create: `P:\packages\codex-external-delegation\src\contract.mjs`
- Create: `P:\packages\codex-external-delegation\tests\contract.test.mjs`
- Modify: none

**Interfaces:**
- `validatePacket(packet) -> { ok: true, packet } | { ok: false, errors }`
- `validateResult(result) -> { ok: true, result } | { ok: false, errors }`
- Packet required fields: `schema_version`, `task_id`, `worker`, `model`, `objective`, `cwd`, `mode`, `output_schema`, and `verification`.
- Worker values: `pi` or `opencode`.
- Modes: `read_only` or `write`.
- Result statuses: `ok`, `failed`, or `blocked`.

- [x] **Step 1: Write failing contract tests.**

```js
import test from "node:test";
import assert from "node:assert/strict";
import { validatePacket, validateResult } from "../src/contract.mjs";

test("accepts a bounded read-only packet", () => {
  const result = validatePacket({
    schema_version: "1",
    task_id: "task-001",
    worker: "pi",
    model: "minimax/MiniMax-M3",
    objective: "List the files that import module X.",
    cwd: "P:/repo",
    mode: "read_only",
    output_schema: { required: ["files"] },
    verification: { commands: ["rg -n module X"] },
  });
  assert.equal(result.ok, true);
});

test("rejects write packets without isolation and scope", () => {
  const result = validatePacket({
    schema_version: "1",
    task_id: "task-002",
    worker: "opencode",
    model: "opencode-go/deepseek-v4-flash",
    objective: "Edit one file.",
    cwd: "P:/repo",
    mode: "write",
    output_schema: { required: ["files_changed"] },
    verification: { commands: ["npm test"] },
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /write_scope/);
  assert.match(result.errors.join(";"), /isolated_cwd/);
});

test("rejects successful results without the structured result payload", () => {
  const result = validateResult({ status: "ok", text: "I finished." });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /result_payload/);
});
```

- [x] **Step 2: Run the focused test and verify it fails.**

Run: `node --test P:\packages\codex-external-delegation\tests\contract.test.mjs`

Expected: FAIL because `src\contract.mjs` does not exist.

- [x] **Step 3: Implement the minimal contract validators.**

```js
const WORKERS = new Set(["pi", "opencode"]);
const MODES = new Set(["read_only", "write"]);

function errorsForPacket(packet) {
  const errors = [];
  for (const key of ["schema_version", "task_id", "worker", "model", "objective", "cwd", "mode", "output_schema", "verification"]) {
    if (packet?.[key] === undefined || packet[key] === "") errors.push(`missing_${key}`);
  }
  if (packet?.schema_version !== "1") errors.push("unsupported_schema_version");
  if (!WORKERS.has(packet?.worker)) errors.push("invalid_worker");
  if (!MODES.has(packet?.mode)) errors.push("invalid_mode");
  if (packet?.mode === "write") {
    if (!Array.isArray(packet.write_scope) || packet.write_scope.length === 0) errors.push("missing_write_scope");
    if (typeof packet.isolated_cwd !== "string" || packet.isolated_cwd.length === 0) errors.push("missing_isolated_cwd");
  }
  if (!Array.isArray(packet?.verification?.commands) || packet.verification.commands.length === 0) errors.push("missing_verification_commands");
  return errors;
}

export function validatePacket(packet) {
  const errors = errorsForPacket(packet);
  return errors.length ? { ok: false, errors } : { ok: true, packet };
}

export function validateResult(result) {
  const errors = [];
  if (!["ok", "failed", "blocked"].includes(result?.status)) errors.push("invalid_status");
  if (typeof result?.failure_class !== "string") errors.push("missing_failure_class");
  if (result?.status === "ok" && (typeof result?.result_payload !== "object" || result.result_payload === null)) errors.push("missing_result_payload");
  return errors.length ? { ok: false, errors } : { ok: true, result };
}
```

- [x] **Step 4: Run the focused tests and commit the contract slice.**

Run: `node --test P:\packages\codex-external-delegation\tests\contract.test.mjs`

Expected: all contract tests pass with exit code 0.

Commit: `git add docs/superpowers/plans/2026-07-11-codex-external-delegation.md packages/codex-external-delegation/package.json packages/codex-external-delegation/src/contract.mjs packages/codex-external-delegation/tests/contract.test.mjs && git commit -m "feat: define external delegation packet contract"`

### Task 2: Render packets and classify worker failures

**Files:**
- Create: `P:\packages\codex-external-delegation\src\prompt.mjs`
- Create: `P:\packages\codex-external-delegation\src\failures.mjs`
- Create: `P:\packages\codex-external-delegation\tests\prompt-failures.test.mjs`
- Modify: `P:\packages\codex-external-delegation\src\contract.mjs`

**Interfaces:**
- `renderPrompt(packet) -> string`
- `classifyFailure({ error, exitCode, timedOut, stdout, stderr }) -> failure_class`
- Required result marker: `<external-delegation-result>{"status":"ok",...}</external-delegation-result>`.

- [x] **Step 1: Add tests for prompt safety and failure classes.** Test `timeout`, `command_missing`, `auth_or_quota`, `context_limit`, `provider_unavailable`, `protocol_error`, and `worker_failed`, plus the requirement that rendered prompts include the objective, allowed scope, forbidden actions, output schema, and verification commands.
- [x] **Step 2: Run the focused tests and verify the new functions fail before implementation.**
- [x] **Step 3: Implement prompt rendering with explicit read-only/write constraints and the result marker.** The renderer must serialize only packet fields, never environment variables or auth files.
- [x] **Step 4: Implement deterministic failure classification in precedence order: timeout, command missing, authentication/quota, context limit, provider unavailable, protocol error, non-zero worker exit, unknown.
- [x] **Step 5: Run focused tests and commit.**

Run: `node --test P:\packages\codex-external-delegation\tests\prompt-failures.test.mjs`

Expected: all tests pass with exit code 0.

Commit: `git add packages/codex-external-delegation/src/contract.mjs packages/codex-external-delegation/src/prompt.mjs packages/codex-external-delegation/src/failures.mjs packages/codex-external-delegation/tests/prompt-failures.test.mjs && git commit -m "feat: render delegation prompts and classify failures"`

### Task 3: Implement PI/OpenCode subprocess execution

**Files:**
- Create: `P:\packages\codex-external-delegation\src\runner.mjs`
- Create: `P:\packages\codex-external-delegation\src\commands.mjs`
- Create: `P:\packages\codex-external-delegation\tests\runner.test.mjs`
- Modify: `P:\packages\codex-external-delegation\src\failures.mjs`

**Interfaces:**
- `buildCommand(packet, promptFile) -> { command, args, env }`
- `runPacket(packet, options?) -> normalized_result`
- `runPacket` must use `spawn` without a shell, enforce a timeout, capture stdout/stderr separately, kill the process tree on timeout, and write artifacts before returning.

- [x] **Step 1: Add mocked-runner tests.** Cover successful PI, successful OpenCode, missing executable, timeout, non-zero exit, malformed result marker, and read-only tool restrictions.
- [x] **Step 2: Run the tests and verify failure before implementation.**
- [x] **Step 3: Implement command construction.** PI uses `pi -p --no-session --mode json --model <model> --thinking off --tools read,grep,find,ls`; OpenCode uses `opencode run --format json --model <model> --variant minimal --dir <cwd>`. Write mode must require explicit `write_scope` and must not silently broaden tools.
- [x] **Step 4: Implement timeout and process-tree cleanup for Windows.** Use `taskkill /T /F /PID` only for the spawned child PID and only after the timeout; preserve the timeout classification even if cleanup fails.
- [x] **Step 5: Implement result-marker extraction and artifact capture.** Save `packet.json`, `stdout.log`, `stderr.log`, `result.json`, and an attempt manifest under the packet artifact directory. Redact strings matching known credential shapes before writing logs.
- [x] **Step 6: Add one retry only for read-only infrastructure failures.** The retry uses the packet’s `fallback_model` or `fallback_worker`; it is forbidden for `write`, `protocol_error`, `contract_error`, or semantic worker failure.
- [x] **Step 7: Run runner tests and commit.**

Run: `node --test P:\packages\codex-external-delegation\tests\runner.test.mjs`

Expected: all mocked execution tests pass with exit code 0.

Commit: `git add packages/codex-external-delegation/src/runner.mjs packages/codex-external-delegation/src/commands.mjs packages/codex-external-delegation/src/failures.mjs packages/codex-external-delegation/tests/runner.test.mjs && git commit -m "feat: run bounded PI and OpenCode delegation packets"`

### Task 4: Add the CLI and live Codex skill

**Files:**
- Create: `P:\packages\codex-external-delegation\bin\external-delegation.mjs`
- Create: `P:\packages\codex-external-delegation\skill\SKILL.md`
- Create: `P:\packages\codex-external-delegation\skill\agents\openai.yaml`
- Create: `P:\packages\codex-external-delegation\opencode\agents\external-readonly.md`
- Create: `P:\packages\codex-external-delegation\opencode\agents\external-writer.md`
- Create: `P:\packages\codex-external-delegation\README.md`
- Create: `P:\packages\codex-external-delegation\tests\cli.test.mjs`

**Interfaces:**
- CLI command: `node bin/external-delegation.mjs run --packet <path>`
- CLI command: `node bin/external-delegation.mjs check --worker <pi|opencode>`
- CLI command: `node bin/external-delegation.mjs classify --packet <path>`
- Stdin is accepted for `run` when `--packet -` is supplied.

- [x] **Step 1: Add CLI tests for invalid packets, dry-run command output, and JSON result shape.**
- [x] **Step 2: Implement the CLI with stable exit codes:** `0` for `ok`, `20` for worker/infrastructure failure, and `30` for blocked/invalid packet or contract failure.
- [x] **Step 3: Write the skill.** The skill tells Codex to classify the task itself, delegate only bounded low-ambiguity work, default to read-only, generate the packet, invoke the CLI, inspect the result artifacts, and independently verify before accepting the result. It does not ask the user to author the worker prompt.
- [ ] **Step 4: Add a live-install script or documented junction command.** The runtime skill path must point to `P:\packages\codex-external-delegation\skill`, with no copied second source of truth.
- [x] **Step 5: Run CLI tests and commit.**

Run: `node --test P:\packages\codex-external-delegation\tests\cli.test.mjs`

Expected: all CLI tests pass with exit code 0.

Commit: `git add packages/codex-external-delegation/bin packages/codex-external-delegation/skill packages/codex-external-delegation/README.md packages/codex-external-delegation/tests/cli.test.mjs && git commit -m "feat: expose external delegation to Codex"`

### Task 5: Install the live skill and run bounded smoke tests

**Files:**
- Modify runtime only: `C:\Users\brsth\.agents\skills\external-delegation` and `C:\Users\brsth\.codex\skills\external-delegation`
- Create runtime artifacts only: `.codex/state/external-delegation/<task_id>/`
- Modify tracked files: none

- [ ] **Step 1: Verify the junction targets resolve to the tracked package skill directory before creating them.**
- [ ] **Step 2: Create the user-scope junctions and verify `SKILL.md` is readable from both Codex skill roots.**
- [ ] **Step 3: Run command-only checks for `pi --version`, `opencode --version`, and the bridge `check` command.** Provider checks must not print credentials.
- [ ] **Step 4: Run a PI read-only smoke task returning a fixed result payload.** Preserve raw artifacts and verify the normalized result is `status=ok`.
- [ ] **Step 5: Run an OpenCode read-only smoke task returning a fixed result payload.** Preserve raw artifacts and verify the normalized result is `status=ok`.
- [ ] **Step 6: Run failure probes without external model calls:** nonexistent executable, impossible timeout using a local helper, malformed result marker, and write packet missing isolation. Verify each maps to the expected failure class and exit code.
- [ ] **Step 7: Inspect `git status`, the new package diff, and all smoke artifacts for secrets or unintended writes.** Do not claim live readiness unless the fresh commands exit as specified.

### Self-review checklist

- [ ] The packet contract separates parent judgment from worker execution.
- [ ] Read-only is the safe default and write delegation cannot run without explicit scope and isolation.
- [ ] Every worker attempt preserves raw evidence and a normalized result.
- [ ] Retry behavior is bounded and does not duplicate writes.
- [ ] PI and OpenCode failures are classified without treating model prose as truth.
- [ ] The live skill is linked to the tracked package, not copied.
- [ ] Existing dirty files remain untouched and unstaged.
- [ ] Smoke tests cover both worker harnesses and the failure surfaces most likely to occur on Windows and llama.cpp-backed workflows.
