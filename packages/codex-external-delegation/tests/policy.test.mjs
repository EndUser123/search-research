import test from "node:test";
import assert from "node:assert/strict";
import { classifyTask } from "../src/policy.mjs";
import { compilePacket, hashPacket } from "../src/packet.mjs";

const bounded = {
  objective: "List callers of module X.",
  model: "opencode-go/deepseek-v4-flash",
  cwd: "P:/repo",
  allowed_paths: ["src/", "tests/"],
  verification_commands: ["rg -n module src tests"],
};

test("classifies a bounded mechanical task for automatic OpenCode execution", () => {
  const result = classifyTask(bounded);
  assert.deepEqual(result, {
    role: "BOUNDED_EXECUTION",
    lane: "opencode",
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

test("represents agy, MMX, and PI as explicit non-automatic roles", () => {
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).lane, "agy");
  assert.equal(classifyTask({ requested_role: "SEARCH_DISCOVERY" }).lane, "mmx");
  assert.equal(classifyTask({ requested_role: "SPECIALIST_EXPLICIT" }).lane, "pi");
  assert.equal(classifyTask({ requested_role: "ADVISORY_REVIEW" }).eligible, false);
});

test("compiles a complete versioned packet and hashes authoritative inputs", () => {
  const { packet } = compilePacket({ ...bounded, task_id: "packet-001", invocation_id: "invoke-001" });
  assert.equal(packet.schema_version, "2");
  assert.equal(packet.role, "BOUNDED_EXECUTION");
  assert.equal(packet.selected_lane, "opencode");
  assert.equal(packet.mode, "read_only");
  assert.equal(packet.requested_agent, "external-readonly-primary");
  assert.equal(packet.agent, "external-readonly-primary");
  assert.equal(packet.failure_policy, "halt_no_automatic_fallback");
  assert.equal(packet.packet_hash, hashPacket(packet));
  const changed = { ...packet, objective: "List exports of module X." };
  assert.notEqual(packet.packet_hash, hashPacket(changed));
});
