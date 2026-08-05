import test from "node:test";
import assert from "node:assert/strict";
import { classifyTask } from "../src/policy.mjs";
import { compilePacket, hashPacket } from "../src/packet.mjs";

const bounded = {
  objective: "List callers of module X.",
  model: "minimax/MiniMax-M3",
  cwd: "P:/repo",
  allowed_paths: ["src/", "tests/"],
  verification_commands: ["rg -n module src tests"],
};

test("classifies a bounded mechanical task for automatic Pi execution", () => {
  const result = classifyTask(bounded);
  assert.deepEqual(result, {
    role: "BOUNDED_EXECUTION",
    lane: "pi",
    eligible: true,
    selection_mode: "automatic",
    reason: "bounded_low_ambiguity_task_with_deterministic_verification",
  });
});

test("keeps ambiguous and judgment-heavy tasks with Codex", () => {
  assert.equal(classifyTask({ ...bounded, ambiguity: "high" }).lane, "codex_native");
  assert.equal(classifyTask({ ...bounded, needs_architecture: true }).lane, "codex_native");
  assert.equal(classifyTask({ ...bounded, verification_commands: [] }).reason, "independent_verification_missing");
});

test("represents agy, MMX, and explicit specialist work as non-automatic roles", () => {
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).lane, "agy");
  assert.equal(classifyTask({ requested_role: "SEARCH_DISCOVERY" }).lane, "mmx");
  assert.equal(classifyTask({ requested_role: "SPECIALIST_EXPLICIT" }).lane, "pi");
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).eligible, false);
});

test("compiles a complete versioned packet and hashes authoritative inputs", () => {
  const { packet } = compilePacket({ ...bounded, task_id: "packet-001", invocation_id: "invoke-001" });
  assert.equal(packet.schema_version, "2");
  assert.equal(packet.role, "BOUNDED_EXECUTION");
  assert.equal(packet.selected_lane, "pi");
  assert.equal(packet.mode, "read_only");
  assert.equal(packet.requested_agent, null);
  assert.equal(packet.agent, null);
  assert.equal(packet.failure_policy, "halt_no_automatic_fallback");
  assert.equal(packet.packet_hash, hashPacket(packet));
  const changed = { ...packet, objective: "List exports of module X." };
  assert.notEqual(packet.packet_hash, hashPacket(changed));
});

test("uses authoritative provider state when the caller leaves model selection open", () => {
  const { packet } = compilePacket({
    objective: "Read the package manifest and report its name.",
    cwd: "P:/repo",
    allowed_paths: ["package.json"],
    verification_commands: ["node -e \"JSON.parse(require('fs').readFileSync('package.json'))\""],
    task_domain: "mechanical",
    provider_health: {
      "opencode-go": { available: true, quota_available: true, reliability: 0.99, p90_latency_ms: 4000, evidence_count: 8 },
    },
  });
  assert.equal(packet.worker, "pi");
  assert.equal(packet.requested_provider, "nvidia-nim");
  assert.equal(packet.model, "deepseek-ai/deepseek-v4-flash");
  assert.equal(packet.model_selection.status, "selected");
  assert.notEqual(packet.model_selection.health_source, "caller_input");
});

test("preserves explicit OpenCode identity when a caller selects that lane", () => {
  const { packet } = compilePacket({
    ...bounded,
    task_id: "packet-opencode-001",
    requested_worker: "opencode",
    requested_provider: "opencode",
    classification: {
      role: "BOUNDED_EXECUTION",
      lane: "opencode",
      eligible: false,
      selection_mode: "explicit",
      reason: "explicit_alternative",
    },
  });
  assert.equal(packet.selected_lane, "opencode");
  assert.equal(packet.worker, "opencode");
  assert.equal(packet.requested_agent, "external-readonly-primary");
});
