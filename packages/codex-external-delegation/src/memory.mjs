import { randomUUID } from "node:crypto";
import { mkdir, readdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import { join, relative } from "node:path";

export const MEMORY_SCHEMA_VERSION = "delegation-memory.v1";

function own(value, key) {
  return value !== null && typeof value === "object" && Object.prototype.hasOwnProperty.call(value, key);
}

function safePart(value) {
  return String(value || "unknown").replace(/[^A-Za-z0-9._-]/g, "_").slice(0, 160) || "unknown";
}

function numeric(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function timestampMs(value, fallback) {
  if (value instanceof Date && Number.isFinite(value.getTime())) return value.getTime();
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Date.parse(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function reportedMetrics(packet, result) {
  const payload = result?.result_payload;
  const candidates = [result, payload, payload?.usage];
  const metrics = {};
  const aliases = {
    input_tokens: ["input_tokens", "prompt_tokens"],
    output_tokens: ["output_tokens", "completion_tokens"],
    total_tokens: ["total_tokens"],
    cost_usd: ["cost_usd", "cost"],
  };
  for (const [name, keys] of Object.entries(aliases)) {
    for (const candidate of candidates) {
      if (!candidate || typeof candidate !== "object") continue;
      const key = keys.find((entry) => own(candidate, entry));
      if (!key) continue;
      const value = numeric(candidate[key]);
      if (value !== null) metrics[name] = value;
      break;
    }
  }
  return Object.keys(metrics).length ? metrics : undefined;
}

export function historyRootForArtifact(artifactDir) {
  return join(artifactDir, "..", "history");
}

export function buildHistoryEntry(packet, result, { startedAt, endedAt, artifactDir } = {}) {
  const fallbackNow = Date.now();
  const startedMs = timestampMs(startedAt, fallbackNow);
  const endedMs = timestampMs(endedAt, fallbackNow);
  const entry = {
    schema_version: MEMORY_SCHEMA_VERSION,
    entry_id: `${safePart(result?.session_id || packet?.session_id)}--${safePart(result?.task_id || packet?.task_id)}--${safePart(result?.run_id || packet?.run_id || result?.invocation_id || packet?.invocation_id)}--${randomUUID()}`,
    session_id: result?.session_id || packet?.session_id || null,
    task_id: result?.task_id || packet?.task_id || null,
    parent_run_id: packet?.parent_run_id || null,
    invocation_id: result?.invocation_id || packet?.invocation_id || null,
    run_id: result?.run_id || packet?.run_id || null,
    task_type: packet?.task_type || packet?.role || packet?.selected_lane || "unclassified",
    task_class: packet?.task_class || packet?.mode || "unclassified",
    worker: result?.worker || packet?.worker || null,
    provider: result?.provider || packet?.requested_provider || null,
    model: result?.model || packet?.model || null,
    started_at: new Date(startedMs).toISOString(),
    ended_at: new Date(endedMs).toISOString(),
    duration_ms: Math.max(0, endedMs - startedMs),
    attempt: Number.isInteger(result?.attempt) ? result.attempt : null,
    timeout: result?.timed_out === true,
    failure_class: result?.failure_class || "unknown",
    status: result?.status || "unknown",
    result_contract: result?.failure_class === "contract_error" ? "invalid" : result?.status === "ok" || result?.status === "blocked" ? "valid" : "not_available",
    artifact_dir: artifactDir || result?.artifact_dir || null,
    artifact_id: result?.artifact_dir || artifactDir || null,
  };
  if (result?.worktree_lifecycle || result?.scope_violation || result?.failure_class?.includes("worktree") || result?.failure_class === "scope_violation") {
    entry.worktree_scope = {
      lifecycle: result.worktree_lifecycle || null,
      scope_violation: result.scope_violation || null,
      outcome: result.failure_class === "scope_violation" ? "scope_violation" : result.worktree_lifecycle?.disposition || null,
    };
  }
  const verification = result?.verification || result?.verification_outcome || result?.result_payload?.verification;
  if (verification !== undefined) entry.verification = verification;
  const metrics = reportedMetrics(packet, result);
  if (metrics) entry.reported_metrics = metrics;
  return entry;
}

export async function writeHistoryEntry(entry, historyRoot) {
  if (!entry || entry.schema_version !== MEMORY_SCHEMA_VERSION || !entry.entry_id) throw new Error("malformed_history_entry");
  const taskDir = join(historyRoot, safePart(entry.task_id));
  await mkdir(taskDir, { recursive: true });
  const finalPath = join(taskDir, `${safePart(entry.entry_id)}.json`);
  const tempPath = join(taskDir, `.${safePart(entry.entry_id)}.${randomUUID()}.tmp`);
  await writeFile(tempPath, `${JSON.stringify(entry, null, 2)}\n`, { encoding: "utf8", flag: "wx" });
  try {
    await rename(tempPath, finalPath);
  } catch (error) {
    try { await unlink(tempPath); } catch { /* best effort cleanup */ }
    throw error;
  }
  return { path: finalPath, entry_id: entry.entry_id };
}

async function jsonFiles(root) {
  const files = [];
  async function visit(dir) {
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); } catch (error) {
      if (error.code === "ENOENT") return;
      throw error;
    }
    for (const item of entries) {
      const path = join(dir, item.name);
      if (item.isDirectory()) await visit(path);
      else if (item.isFile() && item.name.endsWith(".json")) files.push(path);
    }
  }
  await visit(root);
  return files;
}

export async function readHistory(historyRoot) {
  const entries = [];
  const skipped = [];
  for (const path of await jsonFiles(historyRoot)) {
    try {
      const value = JSON.parse(await readFile(path, "utf8"));
      if (value?.schema_version !== MEMORY_SCHEMA_VERSION || !value.entry_id || !value.task_id) throw new Error("invalid_schema");
      entries.push(value);
    } catch (error) {
      skipped.push({ path: relative(historyRoot, path), reason: error.message });
    }
  }
  entries.sort((a, b) => String(a.ended_at).localeCompare(String(b.ended_at)));
  return { entries, skipped };
}

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function summarize(entries) {
  const total = entries.length;
  const ok = entries.filter((entry) => entry.status === "ok").length;
  const timeouts = entries.filter((entry) => entry.timeout === true || entry.failure_class === "timeout").length;
  const verificationEntries = entries.filter((entry) => entry.verification?.status || entry.verification?.outcome);
  const verificationPasses = verificationEntries.filter((entry) => ["pass", "passed", "ok"].includes(entry.verification.status || entry.verification.outcome)).length;
  return {
    entries: total,
    success_rate: total ? ok / total : null,
    timeout_rate: total ? timeouts / total : null,
    median_duration_ms: median(entries.map((entry) => entry.duration_ms).filter(numeric)),
    verification_pass_rate: verificationEntries.length ? verificationPasses / verificationEntries.length : null,
  };
}

export function summarizeHistory(entries) {
  const groups = new Map();
  for (const entry of entries) {
    const key = `${entry.task_type || "unknown"}\u0000${entry.model || "unknown"}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(entry);
  }
  return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([key, group]) => {
    const [task_type, model] = key.split("\u0000");
    return { task_type, model, ...summarize(group) };
  });
}

export { reportedMetrics };
