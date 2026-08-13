import test from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { cp, mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { checkCase } from "../benchmarks/capability-difficulty/src/checkers.mjs";
import { fixtureRoot } from "../benchmarks/capability-difficulty/src/fixtures.mjs";

async function worktree(base = tmpdir()) {
  const root = await mkdtemp(join(base, "codex-pi-checker-test-"));
  const destination = join(root, "benchmarks", "capability-difficulty", "fixtures");
  await mkdir(join(root, "benchmarks", "capability-difficulty"), { recursive: true });
  await cp(fixtureRoot(), destination, { recursive: true });
  return root;
}

async function edit(root, directory, file, content) {
  await writeFile(join(root, "benchmarks", "capability-difficulty", "fixtures", directory, file), content, "utf8");
}

async function partialWorktree(directory) {
  const root = await mkdtemp(join(tmpdir(), "codex-pi-checker-partial-"));
  const destination = join(root, "benchmarks", "capability-difficulty", "fixtures", directory);
  await mkdir(join(root, "benchmarks", "capability-difficulty", "fixtures"), { recursive: true });
  await cp(join(fixtureRoot(), directory), destination, { recursive: true });
  return root;
}

test("mechanical and reasoning checkers score payload evidence, not receipt shape alone", async () => {
  const mechanical = await checkCase({
    caseId: "capability.contract_following.easy.001",
    payload: { response: JSON.stringify({ answer: 7, confidence: "high" }) },
  });
  const reasoning = await checkCase({
    caseId: "capability.context_retrieval.easy.001",
    payload: { response: JSON.stringify({ answer: "the quota window is five hours", record_id: "record-001" }) },
  });
  assert.equal(mechanical.status, "verification_passed");
  assert.equal(reasoning.status, "verification_passed");
  assert.equal((await checkCase({
    caseId: "capability.context_retrieval.easy.001",
    payload: { response: "The quota window is five hours; record-001" },
  })).status, "verification_failed");
  assert.equal((await checkCase({
    caseId: "capability.contract_following.easy.001",
    payload: { response: JSON.stringify({ answer: 8, confidence: "high" }) },
  })).status, "verification_failed");
});

test("coding checker rejects the seeded localized bug and accepts a scoped fix", async () => {
  const root = await worktree();
  try {
    const baseline = await checkCase({ caseId: "code_pool.localized_patch.easy.001", worktreePath: root });
    assert.equal(baseline.status, "verification_failed");
    await edit(root, "localized-patch", "normalize.mjs", `export function normalizeItems(values) {\n  if (values.length === 0) return [];\n  return values.map((value) => String(value).trim());\n}\n`);
    const fixed = await checkCase({ caseId: "code_pool.localized_patch.easy.001", worktreePath: root });
    assert.equal(fixed.status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("coding checker accepts a scoped fix in a partial materialized fixture worktree", async () => {
  const root = await partialWorktree("localized-patch");
  try {
    await edit(root, "localized-patch", "normalize.mjs", `export function normalizeItems(values) {\n  return values.map((value) => String(value).trim());\n}\n`);
    assert.equal((await checkCase({ caseId: "code_pool.localized_patch.easy.001", worktreePath: root })).status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("multi-file and compatibility checkers require behavioral invariants", async () => {
  const root = await worktree();
  try {
    await edit(root, "multi-file-invariant", "serializer.mjs", `export function serializeRecord(record) {\n  return JSON.stringify({ version: 2, id: record.id, name: record.name, priority: record.priority ?? 0 });\n}\n`);
    await edit(root, "multi-file-invariant", "deserializer.mjs", `export function deserializeRecord(serialized) {\n  const record = JSON.parse(serialized);\n  return { id: record.id, name: record.name, priority: record.priority ?? 0 };\n}\n`);
    assert.equal((await checkCase({ caseId: "code_pool.multi_file_invariant.hard.001", worktreePath: root })).status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }

  const apiRoot = await worktree();
  try {
    await edit(apiRoot, "api-compatibility", "api.mjs", `export function createRequest(path, options = {}) {\n  if (typeof path !== "string" || path.length === 0) throw new TypeError("path must be non-empty");\n  const timeoutMs = options.timeoutMs ?? 5000;\n  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0) throw new RangeError("timeoutMs must be a positive integer");\n  return { path, timeoutMs };\n}\n`);
    assert.equal((await checkCase({ caseId: "code_pool.api_compatibility.expert.001", worktreePath: apiRoot })).status, "verification_passed");
  } finally {
    await rm(apiRoot, { recursive: true, force: true });
  }
});

test("test-authoring checker requires a concrete scoped test file", async () => {
  const root = await worktree();
  try {
    const missing = await checkCase({ caseId: "code_pool.test_authoring.medium.001", worktreePath: root });
    assert.equal(missing.status, "verification_failed");
    await edit(root, "test-authoring", "parser.test.mjs", `import test from "node:test";\nimport assert from "node:assert/strict";\nimport { parseList } from "./parser.mjs";\ntest("boundary cases", () => {\n  assert.deepEqual(parseList(" a , b "), ["a", "b"]);\n  assert.deepEqual(parseList(""), [""]);\n  assert.deepEqual(parseList("x,,y"), ["x", "", "y"]);\n});\n`);
    const result = await checkCase({ caseId: "code_pool.test_authoring.medium.001", worktreePath: root });
    assert.equal(result.status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("test-authoring checker runs absolute tests from a mapped P drive", { skip: !existsSync("P:/tmp") }, async () => {
  const root = await worktree("P:/tmp");
  try {
    await edit(root, "test-authoring", "parser.test.mjs", `import test from "node:test";\nimport assert from "node:assert/strict";\nimport { parseList } from "./parser.mjs";\ntest("boundary cases", () => {\n  assert.deepEqual(parseList(" a , b "), ["a", "b"]);\n  assert.deepEqual(parseList(""), [""]);\n  assert.deepEqual(parseList("x,,y"), ["x", "", "y"]);\n});\n`);
    const result = await checkCase({ caseId: "code_pool.test_authoring.medium.001", worktreePath: root });
    assert.equal(result.status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("debugging and lifecycle checkers distinguish race/error behavior from shape", async () => {
  const root = await worktree();
  try {
    await edit(root, "debugging-and-edge-cases", "cache.mjs", `export class AsyncCache {\n  constructor() { this.values = new Map(); this.inFlight = new Map(); }\n  async get(key, loader, { signal } = {}) {\n    if (signal?.aborted) throw Object.assign(new Error("aborted"), { name: "AbortError" });\n    if (this.values.has(key)) return this.values.get(key);\n    if (this.inFlight.has(key)) return this.inFlight.get(key);\n    const pending = (async () => {\n      const value = await loader({ signal });\n      if (signal?.aborted) throw Object.assign(new Error("aborted"), { name: "AbortError" });\n      this.values.set(key, value);\n      return value;\n    })();\n    this.inFlight.set(key, pending);\n    try { return await pending; } finally { if (this.inFlight.get(key) === pending) this.inFlight.delete(key); }\n  }\n}\n`);
    assert.equal((await checkCase({ caseId: "code_pool.debugging_and_edge_cases.hard.001", worktreePath: root })).status, "verification_passed");
  } finally {
    await rm(root, { recursive: true, force: true });
  }

  const lifecycleRoot = await worktree();
  try {
    await edit(lifecycleRoot, "regression-fix", "lifecycle.mjs", `export async function executeRequest(send) {\n  try { return { status: "ok", attempt: 1, response: await send() }; }\n  catch (error) { return { status: "error", attempt: 1, error: { name: error.name, message: error.message, code: error.code } }; }\n}\n`);
    assert.equal((await checkCase({ caseId: "code_pool.regression_fix.expert.001", worktreePath: lifecycleRoot })).status, "verification_passed");
  } finally {
    await rm(lifecycleRoot, { recursive: true, force: true });
  }
});
