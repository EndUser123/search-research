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

test("rejects successful results without the structured result payload", () => {
  const result = validateResult({ status: "ok", text: "I finished." });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(";"), /result_payload/);
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
