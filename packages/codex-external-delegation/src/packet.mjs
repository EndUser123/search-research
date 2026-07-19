import { createHash, randomUUID } from "node:crypto";
import { classifyTask } from "./policy.mjs";

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

export function compilePacket(input = {}) {
  const classification = input.classification || classifyTask(input);
  const invocationId = input.invocation_id || randomUUID();
  const effectiveMode = input.mode || "read_only";
  const requestedAgent = input.requested_agent || (classification.lane === "opencode" ? (effectiveMode === "read_only" ? "external-readonly-primary" : "external-writer") : null);
  const packet = {
    schema_version: "2",
    invocation_id: invocationId,
    parent_run_id: input.parent_run_id || null,
    task_id: input.task_id || invocationId,
    role: classification.role,
    selected_lane: classification.lane,
    requested_worker: input.requested_worker || (classification.lane === "opencode" ? "opencode" : null),
    requested_provider: input.requested_provider || (classification.lane === "opencode" ? "opencode" : null),
    requested_model: input.requested_model || input.model || null,
    requested_agent: requestedAgent,
    worker: classification.lane === "opencode" ? "opencode" : null,
    model: input.model || input.requested_model || null,
    agent: input.agent || requestedAgent,
    objective: input.objective || "",
    relevant_context: input.relevant_context || [],
    cwd: input.cwd || "",
    allowed_paths: input.allowed_paths || [],
    forbidden_paths: input.forbidden_paths || [],
    forbidden_actions: input.forbidden_actions || ["invoke another lane", "commit", "push"],
    mode: effectiveMode,
    output_schema: input.output_schema || { required: ["observations"] },
    timeout_seconds: input.timeout_seconds || 120,
    timeout_ms: input.timeout_ms || (input.timeout_seconds || 120) * 1000,
    containment: input.containment || (input.mode === "write" ? "isolated_worktree_required" : "read_only"),
    isolated_cwd: input.isolated_cwd || null,
    verification: { commands: input.verification_commands || input.verification?.commands || [] },
    evidence_requirements: input.evidence_requirements || ["raw_stdout", "raw_stderr", "result_json"],
    failure_policy: input.failure_policy || "halt_no_automatic_fallback",
    acceptance_criteria: input.acceptance_criteria || ["codex_independent_verification"],
    classification_reason: classification.reason,
  };
  packet.packet_hash = hashPacket(packet);
  return { classification, packet };
}
