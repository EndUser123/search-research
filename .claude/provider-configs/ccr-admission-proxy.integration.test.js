"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");

const FAKE_CCR_PORT = 34761;
const PROXY_PORT = 34762;
process.env.CCR_PORT = String(FAKE_CCR_PORT);
process.env.CCR_ADMISSION_PORT = String(PROXY_PORT);
process.env.CCR_ADMISSION_LOG = "P:/tmp/ccr-context-shaper-live-test.jsonl";
const proxy = require("./ccr-admission-proxy");

function sendJson(port, body) {
  return new Promise((resolve, reject) => {
    const payload = Buffer.from(JSON.stringify(body), "utf8");
    const req = http.request({ host: "127.0.0.1", port, method: "POST", path: "/v1/messages", headers: { "content-type": "application/json", "content-length": payload.length } }, (res) => {
      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => resolve({ status: res.statusCode, body: JSON.parse(Buffer.concat(chunks).toString("utf8")) }));
    });
    req.on("error", reject);
    req.end(payload);
  });
}

let fakeCcr;
test.before(async () => {
  fakeCcr = http.createServer((req, res) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ received: body, receivedContentLength: req.headers["content-length"] }));
    });
  });
  await new Promise((resolve, reject) => fakeCcr.listen(FAKE_CCR_PORT, "127.0.0.1", resolve).on("error", reject));
  await new Promise((resolve, reject) => proxy.server.listen(PROXY_PORT, "127.0.0.1", resolve).on("error", reject));
});
test.after(async () => {
  await new Promise((resolve) => proxy.server.close(resolve));
  await new Promise((resolve) => fakeCcr.close(resolve));
});

test("HTTP proxy forwards shaped body and corrected content length", async () => {
  const body = { model: "claude-sonnet-5", max_tokens: 128, messages: [
    { role: "assistant", content: [{ type: "tool_use", id: "r1", name: "read", input: { file_path: "P:/large.log" } }] },
    { role: "user", content: [{ type: "tool_result", tool_use_id: "r1", content: "old output\n".repeat(500) }] },
    { role: "assistant", content: [{ type: "tool_use", id: "r2", name: "read", input: { file_path: "P:/large.log" } }] },
    { role: "user", content: [{ type: "tool_result", tool_use_id: "r2", content: "new output" }] },
  ] };
  const response = await sendJson(PROXY_PORT, body);
  assert.equal(response.status, 200);
  assert.match(response.body.received.messages[1].content[0].content, /^\[CCR-COMPACTED\]/);
  assert.equal(response.body.received.messages[3].content[0].content, "new output");
  assert.equal(response.body.receivedContentLength, String(Buffer.byteLength(JSON.stringify(response.body.received), "utf8")));
});

test("HTTP proxy still rejects a request that remains oversized", async () => {
  const response = await sendJson(PROXY_PORT, { model: "claude-sonnet-5", max_tokens: 128, system: "x".repeat(3_000_000), messages: [{ role: "user", content: "do not forward" }] });
  assert.equal(response.status, 413);
  assert.equal(response.body.error.type, "admission_proxy_context_exceeded");
});
