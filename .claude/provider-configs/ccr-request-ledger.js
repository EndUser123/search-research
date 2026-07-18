"use strict";

// Small, dependency-free request ledger for the local CCR admission boundary.
// It stores lifecycle summaries only: never prompt text, tool arguments, or
// credentials. Database failures are telemetry failures and must not block
// request forwarding.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

let DatabaseSync;
try {
  ({ DatabaseSync } = require("node:sqlite"));
} catch {
  DatabaseSync = null;
}

const DEFAULT_DB_PATH = "P:/.claude/state/ccr-request-ledger.sqlite";
const SCHEMA_VERSION = 1;
const RETENTION_DAYS = 30;
const MAX_CLEANUP_ROWS = 1000;

const counters = new Map();
const statusCounters = new Map();
let inFlight = 0;
let db = null;
let dbPath = null;
let durationCount = 0;
let durationSumSeconds = 0;

function increment(name, value = 1) {
  counters.set(name, (counters.get(name) || 0) + value);
}

function incrementStatus(statusClass, value = 1) {
  const key = String(statusClass || "unknown");
  statusCounters.set(key, (statusCounters.get(key) || 0) + value);
}

function openDatabase(filename = process.env.CCR_REQUEST_DB || DEFAULT_DB_PATH) {
  if (db) return db;
  if (!DatabaseSync) return null;
  try {
    fs.mkdirSync(path.dirname(filename), { recursive: true });
    db = new DatabaseSync(filename);
    db.exec("PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL; PRAGMA busy_timeout = 1000;");
    db.exec(`
      CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
      );
      CREATE TABLE IF NOT EXISTS logical_requests (
        request_id TEXT PRIMARY KEY,
        received_at TEXT NOT NULL,
        completed_at TEXT,
        model TEXT,
        route TEXT,
        outcome TEXT,
        status_code INTEGER,
        duration_ms REAL,
        input_tokens_estimate INTEGER,
        output_tokens INTEGER,
        admitted INTEGER NOT NULL DEFAULT 0,
        retry_count INTEGER NOT NULL DEFAULT 0,
        fallback_count INTEGER NOT NULL DEFAULT 0
      );
      CREATE TABLE IF NOT EXISTS provider_attempts (
        attempt_id TEXT PRIMARY KEY,
        request_id TEXT,
        observed_at TEXT NOT NULL,
        provider TEXT,
        model TEXT,
        outcome TEXT,
        status_code INTEGER,
        error_class TEXT,
        duration_ms REAL,
        correlation_quality TEXT
      );
      CREATE INDEX IF NOT EXISTS logical_requests_received_idx
        ON logical_requests(received_at);
      CREATE INDEX IF NOT EXISTS provider_attempts_observed_idx
        ON provider_attempts(observed_at);
    `);
    try { db.exec("ALTER TABLE logical_requests ADD COLUMN admitted INTEGER NOT NULL DEFAULT 0"); } catch {}
    const version = db.prepare("SELECT version FROM schema_version LIMIT 1").get();
    if (!version) {
      db.prepare("INSERT INTO schema_version(version) VALUES (?)").run(SCHEMA_VERSION);
    } else if (Number(version.version) !== SCHEMA_VERSION) {
      throw new Error(`unsupported request ledger schema ${version.version}`);
    }
    dbPath = filename;
    cleanupRetention();
    restoreCounters();
    return db;
  } catch {
    try { db?.close(); } catch {}
    db = null;
    return null;
  }
}

function cleanupRetention() {
  if (!db) return;
  try {
    db.prepare(`
      DELETE FROM logical_requests
      WHERE rowid IN (
        SELECT rowid FROM logical_requests
        WHERE received_at < datetime('now', ?)
        ORDER BY received_at ASC
        LIMIT ?
      )
    `).run(`-${RETENTION_DAYS} days`, MAX_CLEANUP_ROWS);
    db.prepare(`
      DELETE FROM provider_attempts
      WHERE rowid IN (
        SELECT rowid FROM provider_attempts
        WHERE observed_at < datetime('now', ?)
        ORDER BY observed_at ASC
        LIMIT ?
      )
    `).run(`-${RETENTION_DAYS} days`, MAX_CLEANUP_ROWS);
  } catch {}
}

function restoreCounters() {
  if (!db) return;
  try {
    const received = db.prepare("SELECT COUNT(*) AS count FROM logical_requests").get();
    counters.set("ccr_requests_received_total", Number(received.count) || 0);
    const outcomes = db.prepare("SELECT outcome, COUNT(*) AS count FROM logical_requests WHERE outcome IS NOT NULL GROUP BY outcome").all();
    for (const row of outcomes) {
      counters.set(`ccr_requests_${row.outcome}_total`, Number(row.count) || 0);
    }
    const admitted = db.prepare("SELECT COUNT(*) AS count FROM logical_requests WHERE admitted = 1").get();
    counters.set("ccr_requests_admitted_total", Number(admitted.count) || 0);
    const attempts = db.prepare("SELECT COUNT(*) AS count FROM provider_attempts").get();
    counters.set("ccr_provider_attempts_total", Number(attempts.count) || 0);
    const statuses = db.prepare("SELECT status_code, COUNT(*) AS count FROM logical_requests WHERE status_code IS NOT NULL GROUP BY status_code").all();
    for (const row of statuses) {
      const statusClass = `${Math.floor(Number(row.status_code) / 100)}xx`;
      statusCounters.set(statusClass, (statusCounters.get(statusClass) || 0) + Number(row.count));
    }
  } catch {}
}

function createRequest(input = {}) {
  const requestId = input.requestId || `proxy-${crypto.randomUUID()}`;
  const receivedAt = input.receivedAt || new Date().toISOString();
  const database = openDatabase();
  increment("ccr_requests_received_total");
  inFlight += 1;
  const handle = {
    requestId,
    receivedAt,
    finalized: false,
    model: input.model || null,
    route: input.route || null,
    inputTokensEstimate: input.inputTokensEstimate ?? null,
    admitted: false,
  };
  try {
    database?.prepare(`
      INSERT OR IGNORE INTO logical_requests
        (request_id, received_at, model, route, input_tokens_estimate)
      VALUES (?, ?, ?, ?, ?)
    `).run(handle.requestId, handle.receivedAt, handle.model, handle.route, handle.inputTokensEstimate);
  } catch {}
  return handle;
}

function updateRequest(handle, input = {}) {
  if (!handle) return;
  Object.assign(handle, {
    model: input.model ?? handle.model,
    route: input.route ?? handle.route,
    inputTokensEstimate: input.inputTokensEstimate ?? handle.inputTokensEstimate,
  });
  try {
    openDatabase()?.prepare(`
      UPDATE logical_requests
      SET model = COALESCE(?, model), route = COALESCE(?, route),
          input_tokens_estimate = COALESCE(?, input_tokens_estimate)
      WHERE request_id = ?
    `).run(handle.model, handle.route, handle.inputTokensEstimate, handle.requestId);
  } catch {}
}

function finalizeRequest(handle, input = {}) {
  if (!handle || handle.finalized) return false;
  handle.finalized = true;
  inFlight = Math.max(0, inFlight - 1);
  const outcome = input.outcome || "failed";
  const statusCode = input.statusCode == null ? null : Number(input.statusCode);
  const completedAt = input.completedAt || new Date().toISOString();
  const durationMs = Math.max(0, new Date(completedAt).getTime() - new Date(handle.receivedAt).getTime());
  durationCount += 1;
  durationSumSeconds += durationMs / 1000;
  const totalName = `ccr_requests_${outcome}_total`;
  increment(totalName);
  if (outcome === "upstream_unavailable") increment("ccr_requests_failed_total");
  incrementStatus(statusCode == null ? "unknown" : `${Math.floor(statusCode / 100)}xx`);
  if (input.fallbackCount) increment("ccr_fallbacks_total", input.fallbackCount);
  if (input.retryCount) increment("ccr_provider_attempts_total", input.retryCount);
  try {
    openDatabase()?.prepare(`
      UPDATE logical_requests
      SET completed_at = ?, outcome = ?, status_code = ?, duration_ms = ?,
          model = COALESCE(?, model), route = COALESCE(?, route),
          input_tokens_estimate = COALESCE(?, input_tokens_estimate),
          output_tokens = ?, retry_count = ?, fallback_count = ?
      WHERE request_id = ?
    `).run(
      completedAt, outcome, statusCode, durationMs,
      input.model ?? handle.model, input.route ?? handle.route,
      input.inputTokensEstimate ?? handle.inputTokensEstimate,
      input.outputTokens ?? null, input.retryCount || 0, input.fallbackCount || 0,
      handle.requestId,
    );
  } catch {}
  return true;
}

function markAdmitted(handle) {
  if (!handle || handle.admitted) return false;
  handle.admitted = true;
  increment("ccr_requests_admitted_total");
  try {
    openDatabase()?.prepare("UPDATE logical_requests SET admitted = 1 WHERE request_id = ?").run(handle.requestId);
  } catch {}
  return true;
}

function recordAttempt(input = {}) {
  const attemptId = input.attemptId || `attempt-${crypto.randomUUID()}`;
  if (!input.outcome || input.outcome === "started") increment("ccr_provider_attempts_total");
  try {
    openDatabase()?.prepare(`
      INSERT INTO provider_attempts
        (attempt_id, request_id, observed_at, provider, model, outcome,
         status_code, error_class, duration_ms, correlation_quality)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(attempt_id) DO UPDATE SET
        request_id = excluded.request_id,
        observed_at = excluded.observed_at,
        provider = excluded.provider,
        model = excluded.model,
        outcome = excluded.outcome,
        status_code = excluded.status_code,
        error_class = excluded.error_class,
        duration_ms = excluded.duration_ms,
        correlation_quality = excluded.correlation_quality
    `).run(
      attemptId, input.requestId || null, input.observedAt || new Date().toISOString(),
      input.provider || null, input.model || null, input.outcome || null,
      input.statusCode == null ? null : Number(input.statusCode),
      input.errorClass || null, input.durationMs == null ? null : Number(input.durationMs),
      input.correlationQuality || "unknown",
    );
  } catch {}
  return attemptId;
}

function recordQuotaFailure() {
  increment("ccr_quota_failures_total");
}

function metricsSnapshot() {
  const databaseAvailable = Boolean(db || openDatabase());
  return {
    counters: Object.fromEntries(counters),
    inFlight,
    statusCounters: Object.fromEntries(statusCounters),
    dbAvailable: databaseAvailable,
    dbPath,
  };
}

function escapeLabel(value) {
  return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n");
}

function prometheusMetrics() {
  const snapshot = metricsSnapshot();
  const lines = [
    "# HELP ccr_requests_in_flight Current logical requests not yet finalized.",
    "# TYPE ccr_requests_in_flight gauge",
    `ccr_requests_in_flight ${snapshot.inFlight}`,
    "# TYPE ccr_request_duration_seconds summary",
    `ccr_request_duration_seconds_count ${durationCount}`,
    `ccr_request_duration_seconds_sum ${durationSumSeconds.toFixed(6)}`,
  ];
  for (const name of [
    "ccr_requests_received_total", "ccr_requests_admitted_total",
    "ccr_requests_completed_total", "ccr_requests_failed_total",
    "ccr_requests_cancelled_total", "ccr_requests_rejected_total",
    "ccr_requests_upstream_unavailable_total", "ccr_provider_attempts_total",
    "ccr_fallbacks_total", "ccr_quota_failures_total",
  ]) {
    lines.push(`# TYPE ${name} counter`, `${name} ${snapshot.counters[name] || 0}`);
  }
  lines.push("# TYPE ccr_request_status_total counter");
  for (const [statusClass, value] of Object.entries(snapshot.statusCounters)) {
    lines.push(`ccr_request_status_total{status_class="${escapeLabel(statusClass)}"} ${value}`);
  }
  return `${lines.join("\n")}\n`;
}

function resetForTests() {
  counters.clear();
  statusCounters.clear();
  inFlight = 0;
  durationCount = 0;
  durationSumSeconds = 0;
  try { db?.close(); } catch {}
  db = null;
  dbPath = null;
}

module.exports = {
  DEFAULT_DB_PATH,
  RETENTION_DAYS,
  createRequest,
  updateRequest,
  markAdmitted,
  finalizeRequest,
  recordAttempt,
  recordQuotaFailure,
  metricsSnapshot,
  prometheusMetrics,
  openDatabase,
  resetForTests,
};
