import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const packageRoot = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const cli = join(packageRoot, "bin", "external-delegation.mjs");

async function packetFile(packet) {
  const dir = await mkdtemp(join(tmpdir(), "codex-delegation-cli-"));
  const path = join(dir, "packet.json");
  await writeFile(path, JSON.stringify(packet), "utf8");
  return path;
}

const validPacket = {
  schema_version: "2",
  task_id: "cli-001",
  worker: "pi",
  model: "minimax/MiniMax-M3",
  objective: "Return a structured file list.",
  cwd: "P:/repo",
  mode: "read_only",
  output_schema: { required: ["files"] },
  verification: { commands: ["node --version"] },
};

test("classify returns structured success for a valid packet", async () => {
  const path = await packetFile(validPacket);
  const result = spawnSync(process.execPath, [cli, "classify", "--packet", path], { encoding: "utf8" });
  assert.equal(result.status, 0);
  assert.equal(JSON.parse(result.stdout).status, "ok");
});

test("dry-run returns the selected worker command without spawning it", async () => {
  const path = await packetFile(validPacket);
  const result = spawnSync(process.execPath, [cli, "run", "--packet", path, "--dry-run"], { encoding: "utf8" });
  assert.equal(result.status, 0);
  const output = JSON.parse(result.stdout);
  assert.equal(output.status, "dry_run");
  assert.equal(output.command, process.platform === "win32" ? "pi.cmd" : "pi");
});

test("invalid packet returns the blocked exit code", async () => {
  const path = await packetFile({ task_id: "invalid" });
  const result = spawnSync(process.execPath, [cli, "classify", "--packet", path], { encoding: "utf8" });
  assert.equal(result.status, 30);
  assert.equal(JSON.parse(result.stdout).failure_class, "contract_error");
});

test("classify accepts a packet from stdin", () => {
  const result = spawnSync(process.execPath, [cli, "classify", "--packet", "-"], {
    input: JSON.stringify(validPacket),
    encoding: "utf8",
  });
  assert.equal(result.status, 0);
  assert.equal(JSON.parse(result.stdout).status, "ok");
});

test("classify accepts a UTF-8 BOM on stdin", () => {
  const result = spawnSync(process.execPath, [cli, "classify", "--packet", "-"], {
    input: `\uFEFF${JSON.stringify(validPacket)}`,
    encoding: "utf8",
  });
  assert.equal(result.status, 0);
  assert.equal(JSON.parse(result.stdout).status, "ok");
});
