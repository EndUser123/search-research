import test from "node:test";
import assert from "node:assert/strict";
import { renderPrompt, extractJsonEventText, extractResultPayload } from "../src/prompt.mjs";
import { classifyFailure, failureDiagnostics } from "../src/failures.mjs";

const packet = {
  schema_version: "2",
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

test("renders structured output types and typed examples", () => {
  const prompt = renderPrompt({
    ...packet,
    output_schema: {
      required: ["answer"],
      properties: { answer: { type: "array" } },
    },
  });
  assert.match(prompt, /Required output field types:\n- answer: array/);
  assert.match(prompt, /result_payload.*\[\]/);
});

test("reports the isolated worktree as the worker working directory", () => {
  const prompt = renderPrompt({ ...packet, isolated_cwd: "P:/tmp/task/packages/repo" });
  assert.match(prompt, /Working directory: P:\/tmp\/task\/packages\/repo/);
  assert.doesNotMatch(prompt, /Working directory: P:\/repo/);
});

test("extracts a valid structured result payload", () => {
  const text = 'noise\n<external-delegation-result>{"status":"ok","files":["a.ts"]}</external-delegation-result>\n';
  assert.deepEqual(extractResultPayload(text), { status: "ok", files: ["a.ts"] });
});

test("returns null for malformed result payload", () => {
  assert.equal(extractResultPayload("<external-delegation-result>not json</external-delegation-result>"), null);
});

test("extracts text from OpenCode JSON events before parsing the result marker", () => {
  const events = [
    { type: "step_start", part: {} },
    { type: "text", part: { text: '<external-delegation-result>{"status":"ok","value":42}</external-delegation-result>' } },
    { type: "step_finish", part: {} },
  ].map((event) => JSON.stringify(event)).join("\n");
  assert.deepEqual(extractResultPayload(extractJsonEventText(events)), { status: "ok", value: 42 });
});

test("extracts text deltas from PI JSON events before parsing the result marker", () => {
  const events = [
    { type: "message_update", assistantMessageEvent: { type: "text_delta", delta: '<external-delegation-result>{"status":"ok",' } },
    { type: "message_update", assistantMessageEvent: { type: "text_delta", delta: '"value":43}</external-delegation-result>' } },
  ].map((event) => JSON.stringify(event)).join("\n");
  assert.deepEqual(extractResultPayload(extractJsonEventText(events)), { status: "ok", value: 43 });
});

test("preserves protocol markers split across PI streaming deltas", () => {
  const events = [
    { type: "message_update", assistantMessageEvent: { type: "text_delta", delta: "<external-delegation-" } },
    { type: "message_update", assistantMessageEvent: { type: "text_delta", delta: "result>{\"status\":\"ok\",\"value\":44}</external-delegation-" } },
    { type: "message_update", assistantMessageEvent: { type: "text_delta", delta: "result>" } },
  ].map((event) => JSON.stringify(event)).join("\n");
  assert.deepEqual(extractResultPayload(extractJsonEventText(events)), { status: "ok", value: 44 });
});

test("classifies timeout before generic worker failure", () => {
  assert.equal(classifyFailure({ timedOut: true, exitCode: null, stdout: "", stderr: "" }), "timeout");
});

test("classifies missing commands and provider failures", () => {
  assert.equal(classifyFailure({ error: { code: "ENOENT" }, exitCode: null, stdout: "", stderr: "" }), "command_missing");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "401 invalid api key" }), "auth_or_quota");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "connection refused" }), "provider_unavailable");
  assert.equal(classifyFailure({ exitCode: 0, stdout: "Error: RegionError: requires explicit opt in", stderr: "" }), "provider_unavailable");
  assert.equal(classifyFailure({ exitCode: 0, stdout: "invalid_request_error: failed to deserialize developer role", stderr: "" }), "provider_unavailable");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "404 model not found: provider discontinued this route" }), "provider_unavailable");
  assert.equal(classifyFailure({ exitCode: 1, stdout: "", stderr: "context window exceeded" }), "context_limit");
});

test("distinguishes a retired route from a temporary provider failure", () => {
  const result = failureDiagnostics({
    failureClass: "provider_unavailable",
    exitCode: 1,
    stderr: "404 model not found: provider discontinued this route",
  });
  assert.ok(result.signals.includes("route_retired"));
  assert.equal(result.retryable, false);
  assert.equal(result.recovery_state, "route_retired");

  const auth = failureDiagnostics({
    failureClass: "auth_or_quota",
    exitCode: 1,
    stderr: "401 unauthorized; quota unavailable",
  });
  assert.equal(auth.retryable, false);
  assert.equal(auth.recovery_state, "account_or_permission_action");
});

test("classifies protocol and worker failures", () => {
  assert.equal(classifyFailure({ exitCode: 0, stdout: "no marker", stderr: "" }), "protocol_error");
  assert.equal(classifyFailure({ exitCode: 2, stdout: "", stderr: "worker failed" }), "worker_failed");
  assert.equal(classifyFailure({ exitCode: 0, stdout: "result", stderr: 'agent "external-readonly" is a subagent, not a primary agent' }), "identity_mismatch");
});
