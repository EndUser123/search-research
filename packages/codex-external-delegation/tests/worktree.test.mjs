import test from "node:test";
import assert from "node:assert/strict";
import { pathsWithinScope, validateWorktree } from "../src/worktree.mjs";

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
