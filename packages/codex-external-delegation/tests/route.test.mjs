import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const cli = join(process.cwd(), "bin", "external-delegation.mjs");

test("route emits a packet for bounded work and no packet for agy advisory review", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-route-test-"));
  const boundedPath = join(dir, "bounded.json");
  const agyPath = join(dir, "agy.json");
  await writeFile(boundedPath, JSON.stringify({
    objective: "List callers of module X.",
    model: "opencode-go/deepseek-v4-flash",
    cwd: "P:/repo",
    allowed_paths: ["src/"],
    verification_commands: ["rg -n module src"],
  }));
  await writeFile(agyPath, JSON.stringify({ requested_role: "ADVISORY_REVIEW" }));

  const bounded = spawnSync(process.execPath, [cli, "route", "--input", boundedPath], { encoding: "utf8" });
  const boundedOutput = JSON.parse(bounded.stdout);
  assert.equal(bounded.status, 0);
  assert.equal(boundedOutput.classification.lane, "opencode");
  assert.equal(boundedOutput.packet.failure_policy, "halt_no_automatic_fallback");
  assert.equal(typeof boundedOutput.packet.packet_hash, "string");

  const agy = spawnSync(process.execPath, [cli, "route", "--input", agyPath], { encoding: "utf8" });
  const agyOutput = JSON.parse(agy.stdout);
  assert.equal(agy.status, 0);
  assert.equal(agyOutput.classification.lane, "agy");
  assert.equal(agyOutput.classification.eligible, false);
  assert.equal(agyOutput.lane.status, "advisory_manual_identity_unproven");
  assert.equal(agyOutput.packet, undefined);
});
