"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { shapeAnthropicRequest } = require("./ccr-context-shaper");
const { prepareAdmissionBody } = require("./ccr-admission-proxy");

function readResult(id, content, extra = {}) {
  return { role: "user", content: [{ type: "tool_result", tool_use_id: id, content, ...extra }] };
}
function readUse(id, path, extra = {}) {
  return { role: "assistant", content: [{ type: "tool_use", id, name: "read", input: { file_path: path, ...extra } }] };
}

test("baseline request is copied without mutation", () => {
  const body = { model: "claude-sonnet-5", system: "keep me", messages: [{ role: "user", content: "hello" }] };
  const result = shapeAnthropicRequest(body);
  assert.deepEqual(result.body, body);
  assert.notStrictEqual(result.body, body);
  assert.equal(result.changed, false);
});

test("repeated resource keeps newest tool result and replaces only older result", () => {
  const body = { messages: [readUse("r1", "P:/src/router.js"), readResult("r1", "old file contents\n".repeat(80)), readUse("r2", "P:/src/router.js"), readResult("r2", "new file contents")] };
  const result = shapeAnthropicRequest(body);
  assert.equal(result.changed, true);
  assert.match(result.body.messages[1].content[0].content, /^\[CCR-COMPACTED\]/);
  assert.equal(result.body.messages[3].content[0].content, "new file contents");
  assert.equal(result.telemetry.compacted_count, 1);
  assert.notEqual(result.telemetry.bytes_saved, 0);
});

test("different pagination ranges are retained", () => {
  const body = { messages: [readUse("r1", "P:/src/router.js", { start_line: 1, end_line: 10 }), readResult("r1", "lines 1-10"), readUse("r2", "P:/src/router.js", { start_line: 11, end_line: 20 }), readResult("r2", "lines 11-20")] };
  const result = shapeAnthropicRequest(body);
  assert.equal(result.changed, false);
});

test("tiny duplicate results are not compacted or reported as replaced", () => {
  const body = { messages: [readUse("r1", "P:/tiny"), readResult("r1", "x"), readUse("r2", "P:/tiny"), readResult("r2", "y")] };
  const result = shapeAnthropicRequest(body);
  assert.equal(result.changed, false);
  assert.equal(result.telemetry.compacted_count, 0);
  assert.deepEqual(result.telemetry.compacted_resources, []);
});

test("unpaired and unknown tool results remain unchanged", () => {
  const body = { messages: [readResult("missing", "preserve me"), { role: "user", content: "request" }] };
  const result = shapeAnthropicRequest(body);
  assert.deepEqual(result.body, body);
  assert.equal(result.changed, false);
});

test("write, edit, and task results are protected", () => {
  const messages = [];
  for (const [name, first, second] of [["write", "w1", "w2"], ["edit", "e1", "e2"], ["task", "t1", "t2"]]) {
    messages.push(
      { role: "assistant", content: [{ type: "tool_use", id: first, name, input: { file_path: "P:/same" } }] }, readResult(first, `${name} old`),
      { role: "assistant", content: [{ type: "tool_use", id: second, name, input: { file_path: "P:/same" } }] }, readResult(second, `${name} new`),
    );
  }
  const result = shapeAnthropicRequest({ messages });
  assert.equal(result.changed, false);
  assert.equal(result.telemetry.compacted_count, 0);
});

test("system text, user text, and tool definitions are untouched", () => {
  const body = { system: [{ type: "text", text: "immutable system rules" }, { type: "text", text: "task-specific instructions" }], tools: [{ name: "read", description: "read files", input_schema: { type: "object" } }], messages: [{ role: "user", content: "fix the router" }, readUse("r1", "P:/a"), readResult("r1", "first"), readUse("r2", "P:/a"), readResult("r2", "second")] };
  const result = shapeAnthropicRequest(body);
  assert.deepEqual(result.body.system, body.system);
  assert.deepEqual(result.body.tools, body.tools);
  assert.equal(result.body.messages[0].content, body.messages[0].content);
});

test("scoped system filtering is opt-in and preserves unmarked blocks", () => {
  const body = { system: [{ type: "text", text: "immutable system rules" }, { type: "text", text: '<ccr-context scope="coding">coding rules</ccr-context>' }, { type: "text", text: '<ccr-context scope="research">research rules</ccr-context>' }], messages: [{ role: "user", content: "fix the router" }] };
  assert.deepEqual(shapeAnthropicRequest(body).body.system, body.system);
  const result = shapeAnthropicRequest(body, { systemScopes: ["coding"] });
  assert.deepEqual(result.body.system, [body.system[0], body.system[1]]);
  assert.equal(result.telemetry.system_blocks_dropped, 1);
});

test("opaque system strings are never filtered", () => {
  const body = { system: "<ccr-context scope=research>not structured</ccr-context>", messages: [] };
  const result = shapeAnthropicRequest(body, { systemScopes: ["coding"] });
  assert.equal(result.body.system, body.system);
});

test("admission preparation reduces repeated tool output before recounting", () => {
  const body = { model: "claude-sonnet-5", max_tokens: 1000, messages: [readUse("r1", "P:/large.log"), readResult("r1", "old log line\n".repeat(500)), readUse("r2", "P:/large.log"), readResult("r2", "new log line")] };
  const prepared = prepareAdmissionBody(body);
  assert.equal(prepared.telemetry.failed_open, false);
  assert.equal(prepared.telemetry.compacted_count, 1);
  assert.ok(JSON.stringify(prepared.body).length < JSON.stringify(body).length);
});

test("admission preparation fails open on an un-serializable internal value", () => {
  const body = { messages: [] };
  body.cycle = body;
  const prepared = prepareAdmissionBody(body);
  assert.equal(prepared.telemetry.failed_open, true);
  assert.strictEqual(prepared.body, body);
});
