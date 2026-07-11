import test from "node:test";
import assert from "node:assert/strict";
import { renderPrompt, extractResultPayload } from "../src/prompt.mjs";
import { classifyFailure } from "../src/failures.mjs";

const packet = {
  schema_version: "1",
  task_id: "task-prompt-001",
  worker: "pi",
  model: "minimax/MiniMax-M3",
  objective: "Find all callers of the parser function.",
  cwd: "P:/repo",
  mode: "read_only",
  allowed_paths: ["src/", "tests/"],
  forbidden_actions: ["edit files", "run network commands"],
  output_schema: { required: ["files", "observations"] },
  verification: { commands: ["rg -n parser src tests"] },
};

test("renders all handoff controls and the result marker", () => {
  const prompt = renderPrompt(packet);
  assert.match(prompt, /Find all callers of the parser function/);
  assert.match(prompt, /read_only/);
  assert.match(prompt, /src\//);
  assert.match(prompt, /edit files/);
  assert.match(prompt, /- files[\s\S]*- observations/);
  assert.match(prompt, /rg -n parser src tests/);
  assert.match(prompt, /<external-delegation-result>/);
});

test("extracts a valid structured result payload", () => {
  const text = 'noise\n<external-delegation-result>{"status":"ok","files":["a.ts"]}</external-delegation-result>\n';
  assert.deepEqual(extractResultPayload(text), { status: "ok", files: ["a.ts"] });
});

test("returns null for malformed result payload", () => {
  assert.equal(extractResultPayload("<external-delegation-result>not json</external-delegation-result>"), null);
});

test("classifies timeout before generic worker failure", () => {
  assert.equal(classifyFailure({ timedOut: true, exitCode: null, stdout: "", stderr: "" }), "timeout");
});

test("classifies missing commands and provider failures", () => {
  assert.equal(classifyFailure({ error: { code: "ENOENT" }, exitCode: null, stdout: "", stderr: "" }), "command_missing");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "401 invalid api key" }), "auth_or_quota");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "connection refused" }), "provider_unavailable");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "context window exceeded" }), "context_limit");
});

test("classifies protocol and worker failures", () => {
  assert.equal(classifyFailure({ exitCode: 0, stdout: "no marker", stderr: "" }), "protocol_error");
  assert.equal(classifyFailure({ exitCode: 2, stdout: "", stderr: "worker failed" }), "worker_failed");
});
