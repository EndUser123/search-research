import { createHash, randomUUID } from "node:crypto";
import { classifyTask } from "./policy.mjs";
import { selectModel } from "./model-selector.mjs";

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

export function hashPacket(packet) {
  const withoutHash = { ...packet };
  delete withoutHash.packet_hash;
  return createHash("sha256").update(canonical(withoutHash)).digest("hex");
}

function inferMode(input) {
  if (input.mode !== undefined && input.mode !== null) return input.mode;
  const declaredWriteScope = Array.isArray(input.write_scope) && input.write_scope.length > 0;
  const requestedWorktree = input.worktree_request !== undefined && input.worktree_request !== null;
  const providedIsolation = typeof input.isolated_cwd === "string" && input.isolated_cwd.trim().length > 0;
  return declaredWriteScope || requestedWorktree || providedIsolation ? "write" : "read_only";
}

export function compilePacket(input = {}) {
  const classification = input.classification || classifyTask(input);
  const invocationId = input.invocation_id || randomUUID();
  const effectiveMode = inferMode(input);
  const hasExplicitModel = Boolean(input.model || input.requested_model);
  const selection = !hasExplicitModel && classification.lane === "pi"
    ? selectModel({ ...input, classification })
    : null;
  const selectedWorker = input.requested_worker || selection?.worker || (classification.lane === "pi" || classification.lane === "opencode" ? classification.lane : null);
  const selectedProvider = input.requested_provider || selection?.provider || selectedWorker;
  const selectedModel = input.model || input.requested_model || selection?.model || null;
  const requestedAgent = input.requested_agent || (classification.lane === "opencode" ? (effectiveMode === "read_only" ? "external-readonly-primary" : "external-writer") : null);
  const packet = {
    schema_version: "2",
    session_id: input.session_id || null,
    run_id: input.run_id || null,
    request_id: input.request_id || null,
    invocation_id: invocationId,
    parent_run_id: input.parent_run_id || null,
    task_id: input.task_id || invocationId,
    role: classification.role,
    selected_lane: classification.lane,
    task_type: input.task_type || classification.role || null,
    task_class: input.task_class || classification.lane || null,
    requested_worker: selectedWorker,
    requested_provider: selectedProvider,
    requested_model: selectedModel,
    requested_agent: requestedAgent,
    worker: selectedWorker,
    invocation_method: input.invocation_method || selection?.invocation_method || (selectedWorker === "pi" ? "pi" : selectedWorker),
    orchestrator: input.orchestrator || selection?.orchestrator || "codex",
    model: selectedModel,
    agent: input.agent || requestedAgent,
    objective: input.objective || "",
    relevant_context: input.relevant_context || [],
    cwd: input.cwd || "",
    allowed_paths: input.allowed_paths || [],
    forbidden_paths: input.forbidden_paths || [],
    forbidden_actions: input.forbidden_actions || ["invoke another lane", "commit", "push"],
    mode: effectiveMode,
    write_scope: input.write_scope || [],
    output_schema: input.output_schema || { required: ["observations"] },
    timeout_seconds: input.timeout_seconds || 120,
    timeout_ms: input.timeout_ms || (input.timeout_seconds || 120) * 1000,
    containment: input.containment || (effectiveMode === "write" ? "isolated_worktree_required" : "read_only"),
    isolated_cwd: input.isolated_cwd || null,
    worktree_request: input.worktree_request || null,
    worktree_cleanup: input.worktree_cleanup || "preserve",
    verification: { commands: input.verification_commands || input.verification?.commands || [] },
    evidence_requirements: input.evidence_requirements || ["raw_stdout", "raw_stderr", "result_json"],
    failure_policy: input.failure_policy || "halt_no_automatic_fallback",
    acceptance_criteria: input.acceptance_criteria || ["codex_independent_verification"],
    classification_reason: classification.reason,
    model_selection: selection,
  };
  packet.packet_hash = hashPacket(packet);
  return { classification, packet };
}
