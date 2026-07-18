"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const http = require("node:http");
const fs = require("node:fs");

const FAKE_CCR_PORT = 34761;
const PROXY_PORT = 34762;
process.env.CCR_PORT = String(FAKE_CCR_PORT);
process.env.CCR_ADMISSION_PORT = String(PROXY_PORT);
process.env.CCR_ADMISSION_LOG = "P:/tmp/ccr-context-shaper-live-test.jsonl";
process.env.CCR_REQUEST_DB = `P:/tmp/ccr-admission-${process.pid}.sqlite`;
const proxy = require("./ccr-admission-proxy");
const ledger = require("./ccr-request-ledger");

function sendJson(port, body, requestPath = "/v1/messages") {
  return new Promise((resolve, reject) => {
    const payload = Buffer.from(JSON.stringify(body), "utf8");
    const req = http.request({ host: "127.0.0.1", port, method: "POST", path: requestPath, headers: { "content-type": "application/json", "content-length": payload.length } }, (res) => {
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
      if (body.model === "fail") {
        res.writeHead(503, { "content-type": "application/json" });
        res.end(JSON.stringify({ error: { type: "upstream_unavailable" } }));
        return;
      }
      if (body.model === "slow") {
        setTimeout(() => {
          res.writeHead(200, { "content-type": "application/json" });
          res.end(JSON.stringify({ content: "late" }));
        }, 100);
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({
        received: body,
        receivedContentLength: req.headers["content-length"],
        receivedRequestId: req.headers["x-request-id"],
      }));
    });
  });
  await new Promise((resolve, reject) => fakeCcr.listen(FAKE_CCR_PORT, "127.0.0.1", resolve).on("error", reject));
  await new Promise((resolve, reject) => proxy.server.listen(PROXY_PORT, "127.0.0.1", resolve).on("error", reject));
});
test.after(async () => {
  await new Promise((resolve) => proxy.server.close(resolve));
  await new Promise((resolve) => fakeCcr.close(resolve));
  ledger.resetForTests();
  for (const suffix of ["", "-wal", "-shm"]) {
    try { fs.rmSync(`${process.env.CCR_REQUEST_DB}${suffix}`, { force: true }); } catch {}
  }
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
  assert.match(response.body.receivedRequestId, /^proxy-/);
});

test("counts OpenAI-compatible inference paths and exposes proxy metrics", async () => {
  const body = { model: "local", messages: [{ role: "user", content: "hello" }] };
  for (const requestPath of ["/v1/chat/completions", "/v1/completions", "/completion", "/infill"]) {
    const response = await sendJson(PROXY_PORT, body, requestPath);
    assert.equal(response.status, 200);
  }
  const metrics = await new Promise((resolve, reject) => {
    http.get({ host: "127.0.0.1", port: PROXY_PORT, path: "/metrics" }, (res) => {
      let body = "";
      res.on("data", (chunk) => { body += chunk; });
      res.on("end", () => resolve({ status: res.statusCode, body }));
    }).on("error", reject);
  });
  assert.equal(metrics.status, 200);
  assert.match(metrics.body, /ccr_requests_received_total 5/);
  assert.match(metrics.body, /ccr_requests_completed_total 5/);
});

test("records upstream failures and client cancellation separately", async () => {
  const failure = await sendJson(PROXY_PORT, { model: "fail", messages: [] });
  assert.equal(failure.status, 503);

  await new Promise((resolve, reject) => {
    const payload = Buffer.from(JSON.stringify({ model: "slow", messages: [] }), "utf8");
    const req = http.request({
      host: "127.0.0.1", port: PROXY_PORT, method: "POST", path: "/v1/messages",
      headers: { "content-type": "application/json", "content-length": payload.length },
    });
    req.on("error", () => resolve());
    req.write(payload);
    req.end();
    setTimeout(() => req.destroy(), 10);
  });
  await new Promise((resolve) => setTimeout(resolve, 150));
  const metrics = ledger.prometheusMetrics();
  assert.match(metrics, /ccr_requests_failed_total 1/);
  assert.match(metrics, /ccr_requests_cancelled_total 1/);
});

test("HTTP proxy still rejects a request that remains oversized", async () => {
  const response = await sendJson(PROXY_PORT, { model: "claude-sonnet-5", max_tokens: 128, system: "x".repeat(3_000_000), messages: [{ role: "user", content: "do not forward" }] });
  assert.equal(response.status, 413);
  assert.equal(response.body.error.type, "admission_proxy_context_exceeded");
  assert.match(ledger.prometheusMetrics(), /ccr_requests_rejected_total 1/);
});
