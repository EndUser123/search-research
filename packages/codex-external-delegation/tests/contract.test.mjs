import test from "node:test";
import assert from "node:assert/strict";
import { validatePacket, validateResult } from "../src/contract.mjs";

test("accepts a bounded read-only packet", () => {
  const result = validatePacket({
    schema_version: "2",
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
    schema_version: "2",
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

test("keeps pre-provision write packets strict by default but classifiable", () => {
  const packet = {
    schema_version: "2",
    task_id: "task-deferred-worktree",
    worker: "pi",
    model: "deepseek-ai/deepseek-v4-flash",
    objective: "Edit one file in an isolated worktree.",
    cwd: "P:/repo",
    mode: "write",
    write_scope: ["src/example.mjs"],
    worktree_request: { worktreeRoot: "P:/tmp/worktrees", intendedFiles: ["src/example.mjs"] },
    output_schema: { required: ["files_changed"] },
    verification: { commands: ["git diff --check"] },
  };
  assert.equal(validatePacket(packet).ok, false);
  const classified = validatePacket(packet, { allowWorktreeRequest: true });
  assert.equal(classified.ok, true);
});

test("rejects write scopes that escape or use absolute paths", () => {
  const result = validatePacket({
    schema_version: "2",
    task_id: "task-unsafe-scope",
    worker: "pi",
    model: "MiniMax-M3",
    objective: "Edit one file.",
    cwd: "P:/repo",
    mode: "write",
    write_scope: ["../outside"],
    isolated_cwd: "P:/tmp/task/repo",
    output_schema: { required: ["files_changed"] },
    verification: { commands: ["git diff --check"] },
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /invalid_write_scope/);
});

test("rejects successful results without the structured result payload", () => {
  const result = validateResult({ status: "ok", text: "I finished." });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /result_payload/);
});

test("requires at least one named output field", () => {
  const result = validatePacket({
    schema_version: "2",
    task_id: "task-empty-output-schema",
    worker: "pi",
    model: "MiniMax-M3",
    objective: "Return evidence.",
    cwd: "P:/repo",
    mode: "read_only",
    output_schema: { required: [] },
    verification: { commands: ["git status --short"] },
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /missing_output_schema_required/);
});

// Regression for the v2 canonical-schema migration. The bridge accepts only
// schema_version === "2"; any other version (including the legacy "1")
// is rejected with `unsupported_schema_version` so consumers can never
// silently accept a packet using the old contract shape.
test("rejects legacy schema_version 1 packets", () => {
  const result = validatePacket({
    schema_version: "1",
    task_id: "task-legacy-001",
    worker: "pi",
    model: "minimax/MiniMax-M3",
    objective: "Legacy shape should be rejected.",
    cwd: "P:/repo",
    mode: "read_only",
    output_schema: { required: ["files"] },
    verification: { commands: ["rg -n module X"] },
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /unsupported_schema_version/);
});

test("rejects missing schema_version", () => {
  const result = validatePacket({
    task_id: "task-no-version",
    worker: "pi",
    model: "minimax/MiniMax-M3",
    objective: "Missing version should be rejected.",
    cwd: "P:/repo",
    mode: "read_only",
    output_schema: { required: ["files"] },
    verification: { commands: ["rg -n module X"] },
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /unsupported_schema_version/);
});
