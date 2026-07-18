"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const dbPath = path.join("P:/tmp", `ccr-ledger-${process.pid}.sqlite`);
process.env.CCR_REQUEST_DB = dbPath;
const ledger = require("./ccr-request-ledger");

test.after(() => {
  ledger.resetForTests();
  for (const suffix of ["", "-wal", "-shm"]) {
    try { fs.rmSync(`${dbPath}${suffix}`, { force: true }); } catch {}
  }
});

test("records a logical request and exposes lifecycle counters", () => {
  const request = ledger.createRequest({ model: "claude-sonnet", inputTokensEstimate: 120 });
  assert.match(request.requestId, /^proxy-/);
  ledger.updateRequest(request, { route: "minimax/MiniMax-M3[1m]" });
  ledger.markAdmitted(request);
  ledger.finalizeRequest(request, {
    outcome: "completed",
    statusCode: 200,
    outputTokens: 33,
  });

  const snapshot = ledger.metricsSnapshot();
  assert.equal(snapshot.inFlight, 0);
  assert.equal(snapshot.counters.ccr_requests_received_total, 1);
  assert.equal(snapshot.counters.ccr_requests_admitted_total, 1);
  assert.equal(snapshot.counters.ccr_requests_completed_total, 1);
  assert.match(ledger.prometheusMetrics(), /ccr_requests_completed_total 1/);
});

test("records provider attempts without exposing request payloads", () => {
  const request = ledger.createRequest({ model: "claude-opus" });
  ledger.recordAttempt({
    requestId: request.requestId,
    provider: "CCR",
    model: "claude-opus",
    outcome: "completed",
    statusCode: 200,
    correlationQuality: "exact",
  });
  ledger.finalizeRequest(request, { outcome: "cancelled", statusCode: 499 });
  const row = ledger.openDatabase().prepare("SELECT * FROM provider_attempts WHERE request_id = ?").get(request.requestId);
  assert.equal(row.provider, "CCR");
  assert.equal(row.outcome, "completed");
  assert.equal(row.correlation_quality, "exact");
  assert.equal(Object.prototype.hasOwnProperty.call(row, "prompt"), false);
  assert.equal(ledger.metricsSnapshot().counters.ccr_requests_cancelled_total, 1);
});

test("finalization is idempotent", () => {
  const request = ledger.createRequest();
  assert.equal(ledger.finalizeRequest(request, { outcome: "failed", statusCode: 500 }), true);
  assert.equal(ledger.finalizeRequest(request, { outcome: "completed", statusCode: 200 }), false);
  assert.equal(ledger.metricsSnapshot().counters.ccr_requests_failed_total, 1);
});

test("restores logical counters after a proxy restart", () => {
  const before = ledger.metricsSnapshot().counters.ccr_requests_received_total;
  ledger.resetForTests();
  const afterRestart = ledger.metricsSnapshot();
  assert.equal(afterRestart.counters.ccr_requests_received_total, before);
  assert.equal(afterRestart.dbAvailable, true);
});
