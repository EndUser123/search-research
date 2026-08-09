import { mkdir, readFile, writeFile } from "node:fs/promises";
import { spawn as defaultSpawn } from "node:child_process";
import { dirname, join } from "node:path";
import { validatePacket, validateResult, validateResultPayloadSchema } from "./contract.mjs";
import { buildCommand, spawnSpec } from "./commands.mjs";
import { classifyFailure } from "./failures.mjs";
import { extractJsonEventText, extractResultPayload, renderPrompt } from "./prompt.mjs";
import { hashPacket } from "./packet.mjs";
import { buildHistoryEntry, historyRootForArtifact, writeHistoryEntry } from "./memory.mjs";
import { changedPaths, cleanupEmptyWorktree, pathsRelativeToCwd, pathsWithinScope, preserveWorktree, provisionWorktree, validateWorktree } from "./worktree.mjs";

const DEFAULT_TIMEOUT_MS = 120_000;
function redactText(value) {
  return String(value)
    .replace(/\bsk-[A-Za-z0-9_-]{16,}\b/g, "[REDACTED_API_KEY]")
    .replace(/((?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*["']?)([^\s,;"'}]+)/gi, "$1[REDACTED]")
    .replace(/("(?:apiKey|api_key|accessToken|access_token|secret|password)"\s*:\s*")[^"]*(")/gi, "$1[REDACTED]$2")
    .replace(/("authorization"\s*:\s*"Bearer\s+)[^"]*(")/gi, "$1[REDACTED]$2")
    .replace(/(authorization\s*[:=]\s*bearer\s+)[^\s,;"'}]+/gi, "$1[REDACTED]");
}

function workerEnvironment(packet) {
  // Packets do not get to inject arbitrary process configuration. Provider
  // credentials and model registries belong to the operator environment;
  // allowing packet.env would permit NODE_OPTIONS or Pi config redirection to
  // change the harness independently of the requested identity.
  const env = { ...process.env };
  if (["pi", "opencode"].includes(packet.worker) && process.platform === "win32") {
    const pathKey = Object.keys(env).find((key) => key.toLowerCase() === "path") || "Path";
    const nodeDirectory = dirname(process.execPath);
    env[pathKey] = `${nodeDirectory};${env[pathKey] || ""}`;
  }
  return env;
}

function redactedPacket(packet) {
  return JSON.parse(redactText(JSON.stringify(packet)));
}

function runtimeIdentities(text) {
  const identities = [];
  for (const line of String(text).split(/\r?\n/)) {
    try {
      const event = JSON.parse(line);
      const messages = [event.message, event.assistantMessageEvent?.partial, event.partial, event];
      for (const message of messages) {
        if (message?.provider && message?.model) {
          identities.push({ provider: message.provider, model: message.model });
        }
      }
    } catch { /* non-JSON output is handled by the protocol parser */ }
  }
  return identities;
}

function modelMatches(provider, requestedModel, runtimeModel) {
  if (requestedModel === runtimeModel) return true;
  const qualifiedPrefix = provider ? `${provider}/` : null;
  return Boolean(qualifiedPrefix
    && requestedModel.startsWith(qualifiedPrefix)
    && requestedModel.slice(qualifiedPrefix.length) === runtimeModel);
}

function identityMismatch(packet, stdout) {
  if (packet.worker !== "pi") return null;
  const identities = runtimeIdentities(stdout);
  if (!identities.length) return "runtime_identity_missing";
  const expected = { provider: packet.requested_provider, model: packet.model };
  return identities.some((identity) => identity.provider !== expected.provider
    || !modelMatches(expected.provider, expected.model, identity.model))
    ? "runtime_identity_mismatch"
    : null;
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
    provider: packet.requested_provider || null,
    model: packet.model,
    invocation_method: packet.invocation_method || (packet.worker === "pi" ? "pi" : packet.worker),
    orchestrator: packet.orchestrator || "codex",
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
  if (result.status === "ok") {
    const required = packet.output_schema?.required || [];
    const missing = required.filter((key) => !Object.prototype.hasOwnProperty.call(result.result_payload, key));
    if (missing.length) {
      return {
        ...result,
        status: "failed",
        failure_class: "contract_error",
        contract_errors: ["missing_required_result_fields"],
        missing_result_fields: missing,
        result_payload: null,
      };
    }
    const schemaErrors = validateResultPayloadSchema(result.result_payload, packet.output_schema);
    if (schemaErrors.length) {
      return {
        ...result,
        status: "failed",
        failure_class: "contract_error",
        contract_errors: ["result_payload_schema_mismatch"],
        schema_errors: schemaErrors,
        result_payload: null,
      };
    }
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
    env: workerEnvironment(packet),
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
  const classifiedFailure = classifyFailure({ ...collected, payload });
  const runtimeIdentityError = collected.exitCode === 0 && payload ? identityMismatch(packet, collected.stdout) : null;
  const failureClass = runtimeIdentityError
    ? "identity_mismatch"
    : collected.timedOut
    ? "timeout"
    : classifiedFailure !== "protocol_error"
      ? classifiedFailure
      : collected.exitCode === 0 && payload
        ? "none"
        : classifiedFailure;
  const details = { ...collected, payload, failureClass, artifactDir };

  await writeFile(join(artifactDir, `attempt-${attempt}.stdout.log`), redactText(collected.stdout), "utf8");
  await writeFile(join(artifactDir, `attempt-${attempt}.stderr.log`), redactText(collected.stderr), "utf8");
  await writeFile(join(artifactDir, `attempt-${attempt}.json`), redactText(JSON.stringify({ ...details, error: collected.error?.message || null }, null, 2)), "utf8");

  return createResult(packet, attempt, details);
}

async function finalizeResult(packet, result, { startedAt, artifactDir, historyDir, memoryWriter = writeHistoryEntry } = {}) {
  try {
    const entry = buildHistoryEntry(packet, result, { startedAt, endedAt: Date.now(), artifactDir });
    const receipt = await memoryWriter(entry, historyDir || historyRootForArtifact(artifactDir));
    result.telemetry = { status: "recorded", entry_id: entry.entry_id, path: receipt.path };
  } catch (error) {
    result.telemetry = { status: "failed", failure_class: "telemetry_error", message: error.message };
  }
  await writeFile(join(artifactDir, "result.json"), JSON.stringify(result, null, 2), "utf8");
  return result;
}

export async function runPacket(packet, { artifactDir, spawnImpl = defaultSpawn, historyDir, memoryWriter = writeHistoryEntry } = {}) {
  let inputPacket = packet && typeof packet === "object" ? packet : {};
  const resolvedArtifactDir = artifactDir || join(inputPacket.cwd || process.cwd(), ".codex", "state", "external-delegation", inputPacket.task_id || "invalid-packet");
  const startedAt = Date.now();
  await mkdir(resolvedArtifactDir, { recursive: true });

  if (inputPacket.model_selection?.confidence === "unverified") {
    const result = { schema_version: "2", task_id: inputPacket.task_id, session_id: inputPacket.session_id || null, run_id: inputPacket.run_id || null, request_id: inputPacket.request_id || null, invocation_id: inputPacket.invocation_id || null, status: "blocked", failure_class: "unverified_model_selection", worker: inputPacket.worker, provider: inputPacket.requested_provider || null, model: inputPacket.model, attempt: 0, exit_code: null, timed_out: false, result_payload: null, artifact_dir: resolvedArtifactDir };
    return finalizeResult(inputPacket, result, { startedAt, artifactDir: resolvedArtifactDir, historyDir, memoryWriter });
  }

  let worktree = null;
  if (inputPacket.mode === "write" && !inputPacket.isolated_cwd && inputPacket.worktree_request) {
    try {
      worktree = await provisionWorktree({
        ...inputPacket.worktree_request,
        taskId: inputPacket.task_id,
        repoRoot: inputPacket.cwd,
        stateDir: join(resolvedArtifactDir, "lifecycle"),
        ownerSession: inputPacket.session_id
          || inputPacket.worktree_request.ownerSession
          || inputPacket.worktree_request.owner_session
          || "codex",
      });
      inputPacket = { ...inputPacket, isolated_cwd: worktree.isolated_cwd, worktree, packet_hash: undefined };
      inputPacket.packet_hash = hashPacket(inputPacket);
    } catch (error) {
      const result = { schema_version: "2", task_id: inputPacket.task_id || "unknown", session_id: inputPacket.session_id || null, run_id: inputPacket.run_id || null, request_id: inputPacket.request_id || null, invocation_id: inputPacket.invocation_id || null, status: "blocked", failure_class: "worktree_error", worker: inputPacket.worker || null, provider: inputPacket.requested_provider || null, model: inputPacket.model || null, attempt: 0, exit_code: null, timed_out: false, result_payload: null, message: error.message, artifact_dir: resolvedArtifactDir };
      return finalizeResult(inputPacket, result, { startedAt, artifactDir: resolvedArtifactDir, historyDir, memoryWriter });
    }
  }

  const validation = validatePacket(inputPacket);
  await writeFile(join(resolvedArtifactDir, "packet.json"), JSON.stringify(redactedPacket(inputPacket), null, 2), "utf8");

  if (!validation.ok) {
    const result = {
      schema_version: "2",
      task_id: inputPacket.task_id || "unknown",
      session_id: inputPacket.session_id || null,
      run_id: inputPacket.run_id || null,
      request_id: inputPacket.request_id || null,
      invocation_id: inputPacket.invocation_id || null,
      status: "blocked",
      failure_class: "contract_error",
      worker: inputPacket.worker || null,
      provider: inputPacket.requested_provider || null,
      model: inputPacket.model || null,
      attempt: 0,
      exit_code: null,
      timed_out: false,
      result_payload: null,
      contract_errors: validation.errors,
      artifact_dir: resolvedArtifactDir,
    };
    if (worktree) {
      try {
        const changed = await changedPaths(worktree.worktree_path);
        result.worktree_lifecycle = await preserveWorktree({
          worktree,
          taskId: inputPacket.task_id,
          disposition: changed.length ? "quarantined_pre_spawn_block" : "preserved_pre_spawn_block",
          reason: "packet_validation_failed_before_worker_start",
          changed,
        });
        await writeFile(join(resolvedArtifactDir, "worktree-lifecycle.json"), JSON.stringify(result.worktree_lifecycle, null, 2), "utf8");
      } catch (error) {
        result.worktree_lifecycle = { status: "error", disposition: "lifecycle_record_failed", reason: error.message };
      }
    }
    return finalizeResult(inputPacket, result, { startedAt, artifactDir: resolvedArtifactDir, historyDir, memoryWriter });
  }

  if (inputPacket.mode === "write") {
    const stateDir = worktree?.metadata_file ? dirname(dirname(worktree.metadata_file)) : join(resolvedArtifactDir, "lifecycle");
    const identity = await validateWorktree({ isolatedCwd: inputPacket.isolated_cwd, repoRoot: inputPacket.cwd, taskId: inputPacket.task_id, stateDir });
    if (!identity.ok) {
      const result = { schema_version: "2", task_id: inputPacket.task_id, session_id: inputPacket.session_id || null, run_id: inputPacket.run_id || null, request_id: inputPacket.request_id || null, invocation_id: inputPacket.invocation_id || null, status: "blocked", failure_class: "worktree_error", worker: inputPacket.worker, provider: inputPacket.requested_provider || null, model: inputPacket.model, attempt: 0, exit_code: null, timed_out: false, result_payload: null, message: identity.reason, artifact_dir: resolvedArtifactDir };
      if (worktree) {
        try {
          const changed = await changedPaths(worktree.worktree_path);
          result.worktree_lifecycle = await preserveWorktree({
            worktree,
            taskId: inputPacket.task_id,
            disposition: changed.length ? "quarantined_identity_block" : "preserved_identity_block",
            reason: identity.reason,
            changed,
          });
          await writeFile(join(resolvedArtifactDir, "worktree-lifecycle.json"), JSON.stringify(result.worktree_lifecycle, null, 2), "utf8");
        } catch (error) {
          result.worktree_lifecycle = { status: "error", disposition: "lifecycle_record_failed", reason: error.message };
        }
      }
      return finalizeResult(inputPacket, result, { startedAt, artifactDir: resolvedArtifactDir, historyDir, memoryWriter });
    }
  }

  const result = await runAttempt(inputPacket, 1, resolvedArtifactDir, spawnImpl);
  let observedPaths = null;
  let lifecyclePaths = null;
  let outOfScope = [];

  if (inputPacket.mode === "write" && inputPacket.isolated_cwd) {
    try {
      lifecyclePaths = worktree?.worktree_path
        ? await changedPaths(worktree.worktree_path)
        : await changedPaths(inputPacket.isolated_cwd);
      observedPaths = worktree?.logical_relative
        ? pathsRelativeToCwd(lifecyclePaths, worktree.logical_relative)
        : lifecyclePaths;
      outOfScope = pathsWithinScope(observedPaths, inputPacket.write_scope || []);
      if (outOfScope.length) {
        result.status = "failed";
        result.failure_class = "scope_violation";
        result.result_payload = null;
        result.scope_violation = { changed_paths: observedPaths, worktree_changed_paths: lifecyclePaths, out_of_scope: outOfScope };
      }
    } catch (error) {
      result.status = "failed";
      result.failure_class = "scope_verification_error";
      result.result_payload = null;
      result.scope_verification_error = error.message;
    }
  }

  if (worktree && observedPaths !== null) {
    try {
      let lifecycle;
      if (outOfScope.length) {
        lifecycle = await preserveWorktree({
          worktree,
          taskId: inputPacket.task_id,
          disposition: "quarantined_scope_violation",
          reason: "worker changed paths outside write_scope",
          changed: lifecyclePaths || observedPaths,
        });
      } else if (inputPacket.worktree_cleanup === "clean_if_empty") {
        lifecycle = await cleanupEmptyWorktree({
          worktree,
          taskId: inputPacket.task_id,
          isolatedCwd: inputPacket.isolated_cwd,
          repoRoot: worktree.repo_root || inputPacket.cwd,
        });
      } else {
        lifecycle = await preserveWorktree({
          worktree,
          taskId: inputPacket.task_id,
          disposition: observedPaths.length ? "preserved_for_parent_review" : "preserved_clean",
          reason: observedPaths.length ? "parent must independently inspect and integrate changes" : "no worker changes detected",
          changed: lifecyclePaths || observedPaths,
        });
      }
      result.worktree_lifecycle = lifecycle;
      await writeFile(join(resolvedArtifactDir, "worktree-lifecycle.json"), JSON.stringify(lifecycle, null, 2), "utf8");
      if (lifecycle.status === "error") {
        result.status = "failed";
        result.failure_class = "cleanup_error";
        result.result_payload = null;
        result.cleanup_error = lifecycle.reason;
      }
    } catch (error) {
      result.status = "failed";
      result.failure_class = "cleanup_error";
      result.result_payload = null;
      result.cleanup_error = error.message;
      result.worktree_lifecycle = { status: "error", disposition: "lifecycle_record_failed", reason: error.message };
      await writeFile(join(resolvedArtifactDir, "worktree-lifecycle.json"), JSON.stringify(result.worktree_lifecycle, null, 2), "utf8");
    }
  }

  await writeFile(join(resolvedArtifactDir, "stdout.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stdout.log`)), "utf8");
  await writeFile(join(resolvedArtifactDir, "stderr.log"), await readFile(join(resolvedArtifactDir, `attempt-${result.attempt}.stderr.log`)), "utf8");
  return finalizeResult(inputPacket, result, { startedAt, artifactDir: resolvedArtifactDir, historyDir, memoryWriter });
}

export { redactText };
export { workerEnvironment };
export { buildCommand, spawnSpec } from "./commands.mjs";
