import { mkdir, readFile, writeFile } from "node:fs/promises";
import { spawn as defaultSpawn } from "node:child_process";
import { join } from "node:path";
import { validatePacket, validateResult } from "./contract.mjs";
import { buildCommand, spawnSpec } from "./commands.mjs";
import { classifyFailure } from "./failures.mjs";
import { extractJsonEventText, extractResultPayload, renderPrompt } from "./prompt.mjs";

const DEFAULT_TIMEOUT_MS = 120_000;
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

function createResult(packet, attempt, details) {
  const payload = details.payload;
  const isBlocked = payload?.status === "blocked";
  const status = isBlocked ? "blocked" : details.failureClass === "none" ? "ok" : "failed";
  // When the worker itself emits a status: "blocked" payload (e.g. policy
  // refusal like a read-only worker declining to mutate), classify it
  // distinctly as worker_blocked. A policy-enforced refusal is neither
  // a generic failure nor a contract error — it is the worker honouring
  // its profile.
  const failure_class = isBlocked
    ? "worker_blocked"
    : status === "ok"
      ? "none"
      : details.failureClass;
  // Preserve the worker's own payload on blocked, so blocked_reason and
  // observations remain in the envelope; only null the payload when
  // the run did not produce any usable result (e.g. timeout, crash).
  const preserve_payload = isBlocked || status === "ok";
  const result = {
    schema_version: "2",
    task_id: packet.task_id,
    session_id: packet.session_id || null,
    run_id: packet.run_id || null,
    request_id: packet.request_id || null,
    invocation_id: packet.invocation_id || null,
    status,
    failure_class,
    worker: packet.worker,
    model: packet.model,
    attempt,
    exit_code: details.exitCode,
    timed_out: details.timedOut,
    result_payload: preserve_payload
      ? (payload?.result_payload ?? payload ?? null)
      : null,
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
  const launch = spawnSpec(command.command, command.args);
  const child = spawnImpl(launch.command, launch.args, {
    cwd: command.cwd,
    env: { ...process.env, ...(packet.env || {}) },
    shell: false,
    windowsHide: true,
    stdio: [command.stdin === null ? "ignore" : "pipe", "pipe", "pipe"],
  });
  if (command.stdin !== null) child.stdin.end(command.stdin);
  const collected = await collectChild(child, packet.timeout_ms || DEFAULT_TIMEOUT_MS, spawnImpl);
  const payload = collected.timedOut
    ? null
    : extractResultPayload(collected.stdout)
      || extractResultPayload(extractJsonEventText(collected.stdout))
      || extractResultPayload(collected.stderr);
  const classifiedFailure = classifyFailure(collected);
  const failureClass = collected.timedOut
    ? "timeout"
    : classifiedFailure !== "protocol_error"
      ? classifiedFailure
      : collected.exitCode === 0 && payload
        ? "none"
        : classifiedFailure;
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
      schema_version: "2",
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

  const result = await runAttempt(inputPacket, 1, resolvedArtifactDir, spawnImpl);

  await writeFile(join(resolvedArtifactDir, "stdout.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stdout.log`)), "utf8");
  await writeFile(join(resolvedArtifactDir, "stderr.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stderr.log`)), "utf8");
  await writeFile(join(resolvedArtifactDir, "result.json"), JSON.stringify(result, null, 2), "utf8");
  return result;
}

export { redactText };
export { buildCommand, spawnSpec } from "./commands.mjs";
