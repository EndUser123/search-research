import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, readdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathsWithinScope, preserveWorktree, validateWorktree } from "../src/worktree.mjs";

test("identifies changed paths outside the declared write scope", () => {
  assert.deepEqual(
    pathsWithinScope(["src/a.mjs", "tests/a.test.mjs", "package.json"], ["src/", "tests/"]),
    ["package.json"],
  );
});

test("treats dot scope as the logical cwd while retaining parent escapes", () => {
  assert.deepEqual(
    pathsWithinScope(["src/a.mjs", "../other-package/file.mjs"], ["."]),
    ["../other-package/file.mjs"],
  );
});

test("fails closed when worktree identity is incomplete", async () => {
  const result = await validateWorktree({ isolatedCwd: "P:/tmp/worktree" });
  assert.deepEqual(result, { ok: false, reason: "missing_worktree_identity" });
});

test("concurrent lifecycle metadata updates use isolated staging files", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-worktree-test-"));
  const metadataFile = join(dir, "task.json");
  await writeFile(metadataFile, JSON.stringify({
    schema: "worktree-task.v1",
    task_id: "task-1",
    repo_root: "P:/repo",
    worktree_path: "P:/worktree",
    branch: "codex/task-1",
  }), "utf8");
  await Promise.all([
    preserveWorktree({
      worktree: { metadata_file: metadataFile, worktree_path: "P:/worktree", branch: "codex/task-1" },
      taskId: "task-1",
      disposition: "preserved_clean",
      changed: [],
    }),
    preserveWorktree({
      worktree: { metadata_file: metadataFile, worktree_path: "P:/worktree", branch: "codex/task-1" },
      taskId: "task-1",
      disposition: "preserved_clean",
      changed: [],
    }),
  ]);
  const metadata = JSON.parse(await readFile(metadataFile, "utf8"));
  assert.equal(metadata.schema, "worktree-task.v1");
  assert.equal(metadata.task_id, "task-1");
  assert.deepEqual((await readdir(dir)).filter((name) => name.includes(".tmp-")), []);
});

test("recovers a valid staged metadata file after an interrupted replacement", async () => {
  const dir = await mkdtemp(join(tmpdir(), "codex-worktree-recovery-"));
  const metadataFile = join(dir, "task.json");
  await writeFile(`${metadataFile}.tmp-crashed-run`, JSON.stringify({
    schema: "worktree-task.v1",
    task_id: "task-recovery",
    repo_root: "P:/repo",
    worktree_path: "P:/worktree",
    branch: "codex/task-recovery",
  }), "utf8");
  await preserveWorktree({
    worktree: { metadata_file: metadataFile, worktree_path: "P:/worktree", branch: "codex/task-recovery" },
    taskId: "task-recovery",
    disposition: "preserved_clean",
    changed: [],
  });
  const metadata = JSON.parse(await readFile(metadataFile, "utf8"));
  assert.equal(metadata.task_id, "task-recovery");
  assert.equal(metadata.cleanup_state, "preserved_clean");
  assert.deepEqual((await readdir(dir)).filter((name) => name.includes(".tmp-") || name.includes(".bak-")), []);
});
