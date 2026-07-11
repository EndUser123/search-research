import { mkdir, readFile, writeFile } from "node:fs/promises";
import { spawn as defaultSpawn } from "node:child_process";
import { join } from "node:path";
import { validatePacket, validateResult } from "./contract.mjs";
import { buildCommand } from "./commands.mjs";
import { classifyFailure } from "./failures.mjs";
import { extractResultPayload, renderPrompt } from "./prompt.mjs";

const DEFAULT_TIMEOUT_MS = 120_000;
const RETRYABLE_FAILURES = new Set(["timeout", "provider_unavailable", "command_missing", "auth_or_quota"]);

function redactText(value) {
  return String(value)
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, "[REDACTED_API_KEY]")
    .replace(/(api[_-]?key\s*[:=]\s*)([^\s,;]+)/gi, "$1[REDACTED]")
    .replace(/(authorization\s*[:=]\s*bearer\s+)([^\s]+)/gi, "$1[REDACTED]");
}

function redactedPacket(packet) {
  return JSON.parse(redactText(JSON.stringify(packet)));
}

async function killProcessTree(child) {
  if (!child || child.killed) return;
  if (process.platform === "win32" && child.pid) {
    const killer = defaultSpawn("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], {
      windowsHide: true,
      stdio: "ignore",
    });
    killer.unref?.();
  } else {
    child.kill("SIGTERM");
  }
}

function readOnlyRetryAllowed(packet, failureClass) {
  return packet.mode === "read_only" && RETRYABLE_FAILURES.has(failureClass) && Boolean(packet.fallback_model || packet.fallback_worker);
}

function createResult(packet, attempt, details) {
  const payload = details.payload;
  const status = payload?.status === "blocked" ? "blocked" : details.failureClass === "none" ? "ok" : "failed";
  const result = {
    schema_version: "1",
    task_id: packet.task_id,
    status,
    failure_class: status === "ok" ? "none" : details.failureClass,
    worker: packet.worker,
    model: packet.model,
    attempt,
    exit_code: details.exitCode,
    timed_out: details.timedOut,
    result_payload: payload?.result_payload ?? (status === "ok" ? payload : null),
    artifact_dir: details.artifactDir,
  };
  const validation = validateResult(result);
  if (!validation.ok) {
    return {
      ...result,
      status: "failed",
      failure_class: "contract_error",
      contract_errors: validation.errors,
      result_payload: null,
    };
  }
  return result;
}

function collectChild(child, timeoutMs, spawnImpl) {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let error = null;
    let timedOut = false;
    let settled = false;

    child.stdout?.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr?.on("data", (chunk) => { stderr += chunk.toString(); });

    const timer = setTimeout(() => {
      if (settled) return;
      timedOut = true;
      killProcessTree(child, spawnImpl).catch(() => {});
    }, timeoutMs);

    const finish = (exitCode, signal) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, error, exitCode, signal, timedOut });
    };

    child.once("error", (value) => {
      error = value;
      finish(null, null);
    });
    child.once("close", finish);
  });
}

async function runAttempt(packet, attempt, artifactDir, spawnImpl) {
  const prompt = renderPrompt(packet);
  const command = buildCommand(packet, prompt);
  const child = spawnImpl(command.command, command.args, {
    cwd: command.cwd,
    env: { ...process.env, ...(packet.env || {}) },
    shell: false,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const collected = await collectChild(child, packet.timeout_ms || DEFAULT_TIMEOUT_MS, spawnImpl);
  const payload = collected.timedOut ? null : extractResultPayload(collected.stdout) || extractResultPayload(collected.stderr);
  const failureClass = collected.timedOut
    ? "timeout"
    : collected.exitCode === 0 && payload
      ? "none"
      : classifyFailure(collected);
  const details = { ...collected, payload, failureClass, artifactDir };

  await writeFile(join(artifactDir, `attempt-${attempt}.stdout.log`), redactText(collected.stdout), "utf8");
  await writeFile(join(artifactDir, `attempt-${attempt}.stderr.log`), redactText(collected.stderr), "utf8");
  await writeFile(join(artifactDir, `attempt-${attempt}.json`), JSON.stringify({ ...details, error: collected.error?.message || null }, null, 2), "utf8");

  return createResult(packet, attempt, details);
}

export async function runPacket(packet, { artifactDir, spawnImpl = defaultSpawn } = {}) {
  const inputPacket = packet && typeof packet === "object" ? packet : {};
  const validation = validatePacket(inputPacket);
  const resolvedArtifactDir = artifactDir || join(inputPacket.cwd || process.cwd(), ".codex", "state", "external-delegation", inputPacket.task_id || "invalid-packet");
  await mkdir(resolvedArtifactDir, { recursive: true });
  await writeFile(join(resolvedArtifactDir, "packet.json"), JSON.stringify(redactedPacket(inputPacket), null, 2), "utf8");

  if (!validation.ok) {
    const result = {
      schema_version: "1",
      task_id: inputPacket.task_id || "unknown",
      status: "blocked",
      failure_class: "contract_error",
      worker: inputPacket.worker || null,
      model: inputPacket.model || null,
      attempt: 0,
      exit_code: null,
      timed_out: false,
      result_payload: null,
      contract_errors: validation.errors,
      artifact_dir: resolvedArtifactDir,
    };
    await writeFile(join(resolvedArtifactDir, "result.json"), JSON.stringify(result, null, 2), "utf8");
    return result;
  }

  let currentPacket = { ...inputPacket };
  const maxAttempts = currentPacket.mode === "read_only" && (currentPacket.fallback_model || currentPacket.fallback_worker)
    ? Math.min(Math.max(Number(currentPacket.max_attempts || 2), 1), 2)
    : 1;
  let result = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    result = await runAttempt(currentPacket, attempt, resolvedArtifactDir, spawnImpl);
    if (result.status === "ok" || !readOnlyRetryAllowed(currentPacket, result.failure_class) || attempt === maxAttempts) break;
    currentPacket = {
      ...currentPacket,
      worker: currentPacket.fallback_worker || currentPacket.worker,
      model: currentPacket.fallback_model || currentPacket.model,
    };
  }

  await writeFile(join(resolvedArtifactDir, "stdout.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stdout.log`)), "utf8");
  await writeFile(join(resolvedArtifactDir, "stderr.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stderr.log`)), "utf8");
  await writeFile(join(resolvedArtifactDir, "result.json"), JSON.stringify(result, null, 2), "utf8");
  return result;
}

export { redactText };
export { buildCommand } from "./commands.mjs";
