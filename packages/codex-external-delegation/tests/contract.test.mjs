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
