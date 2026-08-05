import { readFile, rename, writeFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { dirname, join, relative, resolve } from "node:path";

const execFileAsync = promisify(execFile);
const DEFAULT_HELPER = "P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/go/scripts/worktree_safety.py";

function helperPath() { return process.env.CODEX_PI_WORKTREE_HELPER || DEFAULT_HELPER; }
function pythonCommand() { return process.env.CODEX_PI_PYTHON || "python"; }
function cleanupScriptPath() { return process.env.CODEX_PI_WORKTREE_CLEANUP || join(dirname(helperPath()), "worktree_cleanup.py"); }
function metadataPath(stateDir, taskId) { return join(stateDir, "worktree-tasks", `${taskId}.json`); }
function samePath(left, right) { return resolve(left).toLowerCase() === resolve(right).toLowerCase(); }

async function gitWorktrees(repoRoot) {
  const { stdout } = await execFileAsync("git", ["-C", repoRoot, "worktree", "list", "--porcelain"], { windowsHide: true, maxBuffer: 1024 * 1024 });
  return stdout.split(/\r?\n(?=worktree )/).filter(Boolean).map((block) => ({
    path: block.match(/^worktree (.+)$/m)?.[1] || "",
    branch: block.match(/^branch (.+)$/m)?.[1] || null,
    head: block.match(/^HEAD (.+)$/m)?.[1] || null,
  }));
}

export async function provisionWorktree({ taskId, title, objective = "", repoRoot, stateDir, canonicalBranch = "main", worktreeRoot, intendedFiles = [], ownerSession = "codex" } = {}) {
  if (!taskId || !repoRoot || !stateDir) throw new Error("taskId, repoRoot, and stateDir are required");
  const { stdout: gitRootOutput } = await execFileAsync("git", ["-C", repoRoot, "rev-parse", "--show-toplevel"], { windowsHide: true, maxBuffer: 1024 * 1024 });
  const gitRepoRoot = resolve(gitRootOutput.trim());
  const logicalCwd = resolve(repoRoot);
  const logicalRelative = relative(gitRepoRoot, logicalCwd).replaceAll("\\", "/");
  if (logicalRelative.startsWith("../") || logicalRelative === ".." || /^[A-Za-z]:\//.test(logicalRelative)) {
    throw new Error("logical delegation cwd is outside the Git repository root");
  }
  const args = [helperPath(), "--state-dir", stateDir, "start", "--task-id", taskId, "--title", title || taskId, "--objective", objective, "--repo-root", gitRepoRoot, "--canonical-branch", canonicalBranch, "--owner-session", ownerSession];
  if (worktreeRoot) args.push("--worktree-root", worktreeRoot);
  if (intendedFiles.length) args.push("--intended-files", intendedFiles.join(","));
  try { await execFileAsync(pythonCommand(), args, { windowsHide: true, maxBuffer: 1024 * 1024 }); }
  catch (error) { throw new Error(`worktree provisioning failed: ${error.stderr || error.message}`); }
  const metadataFile = metadataPath(stateDir, taskId);
  const metadata = JSON.parse(await readFile(metadataFile, "utf8"));
  if (metadata.schema !== "worktree-task.v1" || metadata.task_id !== taskId) throw new Error("worktree metadata contract mismatch");
  if (!samePath(metadata.repo_root, gitRepoRoot) || samePath(metadata.worktree_path, gitRepoRoot)) throw new Error("worktree metadata repository identity mismatch");
  const isolatedCwd = logicalRelative ? join(metadata.worktree_path, logicalRelative) : metadata.worktree_path;
  const updated = await updateMetadata(metadataFile, {
    task_id: taskId,
    logical_cwd: logicalCwd,
    logical_relative: logicalRelative,
    isolated_cwd: isolatedCwd,
  });
  const git = (await gitWorktrees(gitRepoRoot)).find((entry) => samePath(entry.path, metadata.worktree_path));
  if (!git) throw new Error("provisioned worktree is not registered with Git");
  return { ...updated, git, metadata_file: metadataFile, isolated_cwd: isolatedCwd };
}

export async function validateWorktree({ isolatedCwd, repoRoot, taskId, stateDir } = {}) {
  if (!isolatedCwd || !repoRoot || !taskId || !stateDir) return { ok: false, reason: "missing_worktree_identity" };
  try {
    const metadata = JSON.parse(await readFile(metadataPath(stateDir, taskId), "utf8"));
    const logicalRelative = metadata.logical_relative || "";
    const expectedIsolatedCwd = logicalRelative ? join(metadata.worktree_path, logicalRelative) : metadata.worktree_path;
    const git = (await gitWorktrees(metadata.repo_root)).find((entry) => samePath(entry.path, metadata.worktree_path));
    if (!git || !samePath(expectedIsolatedCwd, isolatedCwd) || !samePath(metadata.logical_cwd || metadata.repo_root, repoRoot)) return { ok: false, reason: "worktree_identity_mismatch" };
    return { ok: true, metadata, git };
  } catch (error) { return { ok: false, reason: "worktree_validation_failed", detail: error.message }; }
}

async function updateMetadata(metadataFile, updates) {
  const metadata = JSON.parse(await readFile(metadataFile, "utf8"));
  if (metadata.schema !== "worktree-task.v1" || metadata.task_id !== updates.task_id) {
    throw new Error("worktree metadata contract mismatch during lifecycle update");
  }
  const next = { ...metadata, ...updates, updated_at: new Date().toISOString() };
  const temporary = `${metadataFile}.tmp-${process.pid}`;
  await writeFile(temporary, JSON.stringify(next, null, 2), "utf8");
  await rename(temporary, metadataFile);
  return next;
}

export async function preserveWorktree({ worktree, taskId, disposition, reason, changed = [] } = {}) {
  if (!worktree?.metadata_file) return { status: "not_managed", disposition };
  const terminal = changed.length === 0 && disposition === "preserved_clean";
  const metadata = await updateMetadata(worktree.metadata_file, {
    task_id: taskId,
    status: terminal ? "terminal" : disposition.startsWith("quarantined") ? "quarantined" : "active",
    cleanup_state: disposition,
    lifecycle_reason: reason || "",
    changed_paths: changed,
  });
  return {
    status: "preserved",
    disposition,
    reason: reason || "",
    changed_paths: changed,
    worktree_path: metadata.worktree_path,
    branch: metadata.branch,
  };
}

export async function cleanupEmptyWorktree({ worktree, taskId, isolatedCwd, repoRoot } = {}) {
  if (!worktree?.metadata_file) return { status: "not_managed", disposition: "not_managed" };
  const worktreePath = worktree.worktree_path || isolatedCwd;
  const changed = await changedPaths(worktreePath);
  if (changed.length) {
    return preserveWorktree({
      worktree,
      taskId,
      disposition: "quarantined_dirty",
      reason: "cleanup_requested_but_worktree_contains_changes",
      changed,
    });
  }

  const branch = worktree.branch || "";
  try {
    const preflightScript = [
      "import json, sys",
      "from pathlib import Path",
      "sys.path.insert(0, sys.argv[3])",
      "import preflight",
      "report = preflight.preflight_run(Path(sys.argv[1]), Path(sys.argv[2]), branch_name=sys.argv[4])",
      "print(json.dumps({'blocked': report.blocked, 'findings': [{'severity': f.severity.value, 'code': f.code, 'message': f.message} for f in report.findings]}))",
    ].join("; ");
    const preflight = await execFileAsync(pythonCommand(), [
      "-c",
      preflightScript,
      worktreePath,
      repoRoot,
      dirname(cleanupScriptPath()),
      branch,
    ], {
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    const report = JSON.parse(preflight.stdout);
    const blocking = report.findings.filter((finding) => finding.severity === "block");
    const unexpectedBlocks = blocking.filter((finding) => {
      if (finding.code !== "BRANCH_IN_USE") return true;
      const normalizedMessage = String(finding.message).replaceAll("\\", "/").toLowerCase();
      return !normalizedMessage.includes(String(worktreePath).replaceAll("\\", "/").toLowerCase());
    });
    const warnings = report.findings.filter((finding) => finding.severity === "warn");
    const unexpectedProcessWarnings = warnings.filter((finding) => finding.code === "PROC_REFERENCES_WT" && !/(python|powershell|pwsh)\.exe/i.test(finding.message));
    const nonProcessWarnings = warnings.filter((finding) => finding.code !== "PROC_REFERENCES_WT");
    if (unexpectedBlocks.length) throw new Error(`shared preflight blocked cleanup: ${unexpectedBlocks.map((finding) => finding.code).join(",")}`);
    if (unexpectedProcessWarnings.length || nonProcessWarnings.length) {
      throw new Error(`shared preflight returned actionable warnings: ${[...unexpectedProcessWarnings, ...nonProcessWarnings].map((finding) => finding.code).join(",")}`);
    }

    await execFileAsync("git", ["-C", repoRoot, "worktree", "remove", worktreePath], {
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });
    const stillRegistered = (await gitWorktrees(repoRoot)).some((entry) => samePath(entry.path, worktreePath));
    if (stillRegistered) throw new Error("clean worktree removal returned success but Git still registers the worktree");

    let branchDisposition = "branch_preserved";
    if (branch) {
      try {
        await execFileAsync("git", ["-C", repoRoot, "branch", "-d", branch], { windowsHide: true, maxBuffer: 1024 * 1024 });
        branchDisposition = "branch_deleted";
      } catch (error) {
        const detail = `${error.stderr || ""} ${error.message || ""}`;
        if (/not fully merged|not an ancestor|contains work/i.test(detail)) {
          branchDisposition = "branch_preserved_unmerged";
        } else {
          throw new Error(`safe branch deletion failed: ${detail}`);
        }
      }
    }
    const metadata = await updateMetadata(worktree.metadata_file, {
      task_id: taskId,
      status: "terminal",
      cleanup_state: branchDisposition === "branch_deleted" ? "cleaned" : "cleaned_worktree_branch_preserved",
      lifecycle_reason: "explicit_clean_if_empty_policy",
      changed_paths: [],
    });
    return {
      status: "cleaned",
      disposition: branchDisposition === "branch_deleted" ? "cleaned" : "cleaned_worktree_branch_preserved",
      preflight_findings: report.findings,
      worktree_path: metadata.worktree_path,
      branch: metadata.branch,
    };
  } catch (error) {
    try {
      await updateMetadata(worktree.metadata_file, {
        task_id: taskId,
        status: "quarantined",
        cleanup_state: "cleanup_failed",
        lifecycle_reason: error.stderr || error.message,
        changed_paths: [],
      });
    } catch { /* preserve the original cleanup failure */ }
    return {
      status: "error",
      disposition: "cleanup_failed",
      reason: error.stderr || error.message,
      worktree_path: worktreePath,
      branch,
    };
  }
}

export async function changedPaths(worktreePath) {
  const { stdout } = await execFileAsync("git", ["-C", worktreePath, "status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"], { windowsHide: true, maxBuffer: 1024 * 1024 });
  return stdout.split(/\r?\n/).filter(Boolean).map((line) => line.slice(3).trim()).map((path) => path.includes(" -> ") ? path.split(" -> ").at(-1) : path);
}

export function pathsWithinScope(paths, scope) {
  const normalized = scope.map((entry) => entry.replaceAll("\\", "/").replace(/^\.\//, "").replace(/\/$/, ""))
    .map((root) => root === "." ? "" : root);
  return paths.filter((path) => {
    const value = path.replaceAll("\\", "/").replace(/^\.\//, "");
    return !normalized.some((root) => root === ""
      ? value !== ".." && !value.startsWith("../")
      : value === root || value.startsWith(`${root}/`));
  });
}

export function pathsRelativeToCwd(paths, logicalRelative = "") {
  const prefix = logicalRelative.replaceAll("\\", "/").replace(/^\.\//, "").replace(/\/$/, "");
  if (!prefix) return paths;
  return paths.map((path) => {
    const value = path.replaceAll("\\", "/").replace(/^\.\//, "");
    if (value === prefix) return ".";
    if (value.startsWith(`${prefix}/`)) return value.slice(prefix.length + 1);
    return `../${value}`;
  });
}

export { metadataPath };
