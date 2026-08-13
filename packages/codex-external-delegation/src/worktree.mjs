import { randomUUID } from "node:crypto";
import { lstat, mkdir, readdir, readFile, rename, stat, unlink, writeFile } from "node:fs/promises";
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

async function replaceFile(temporary, destination) {
  let lastError;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      await rename(temporary, destination);
      return;
    } catch (error) {
      lastError = error;
      // Windows rename does not replace an existing destination. Move the
      // completed destination aside before retrying. The backup makes the
      // short replacement window recoverable after a process crash.
      if (!(["EPERM", "EEXIST"].includes(error.code))) throw error;
      const backup = `${destination}.bak-${process.pid}-${randomUUID()}`;
      let backedUp = false;
      try {
        await rename(destination, backup);
        backedUp = true;
      } catch (renameError) {
        if (renameError.code !== "ENOENT") throw renameError;
      }
      try {
        await rename(temporary, destination);
        if (backedUp) await unlink(backup).catch(() => {});
        return;
      } catch (replaceError) {
        lastError = replaceError;
        if (backedUp) {
          // Restore only when the destination is still absent. If another
          // updater won, leave its newer result in place and retry ours.
          try {
            await rename(backup, destination);
          } catch (restoreError) {
            if (restoreError.code !== "EEXIST" && restoreError.code !== "EPERM") throw restoreError;
          }
        }
        await new Promise((resolveDelay) => setTimeout(resolveDelay, 2));
      }
    }
  }
  throw lastError;
}

async function readMetadata(metadataFile) {
  try {
    return JSON.parse(await readFile(metadataFile, "utf8"));
  } catch (error) {
    if (error.code !== "ENOENT" && !(error instanceof SyntaxError)) throw error;
    const directory = dirname(metadataFile);
    const basename = metadataFile.split(/[\\/]/).at(-1);
    let names;
    try {
      names = await readdir(directory);
    } catch {
      throw error;
    }
    const candidates = [];
    for (const name of names) {
      if (!name.startsWith(`${basename}.tmp-`) && !name.startsWith(`${basename}.bak-`)) continue;
      const path = join(directory, name);
      try {
        const value = JSON.parse(await readFile(path, "utf8"));
        if (value?.schema === "worktree-task.v1" && value.task_id) {
          candidates.push({
            path,
            value,
            priority: name.startsWith(`${basename}.tmp-`) ? 2 : 1,
            mtime: (await stat(path)).mtimeMs,
          });
        }
      } catch { /* ignore incomplete staging files */ }
    }
    candidates.sort((left, right) => right.priority - left.priority || right.mtime - left.mtime);
    if (!candidates.length) throw error;
    await replaceFile(candidates[0].path, metadataFile);
    return candidates[0].value;
  }
}

async function gitWorktrees(repoRoot) {
  const { stdout } = await execFileAsync("git", ["-C", repoRoot, "worktree", "list", "--porcelain"], { windowsHide: true, maxBuffer: 1024 * 1024 });
  return stdout.split(/\r?\n(?=worktree )/).filter(Boolean).map((block) => ({
    path: block.match(/^worktree (.+)$/m)?.[1] || "",
    branch: block.match(/^branch (.+)$/m)?.[1] || null,
    head: block.match(/^HEAD (.+)$/m)?.[1] || null,
  }));
}

function isWithin(root, candidate) {
  const rootPath = resolve(root);
  const candidatePath = resolve(candidate);
  const relativePath = relative(rootPath, candidatePath);
  return relativePath === "" || (relativePath !== ".." && !relativePath.startsWith(`..${process.platform === "win32" ? "\\" : "/"}`) && !/^[A-Za-z]:[\\/]/.test(relativePath));
}

function safeRelativePath(value, field) {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be a non-empty relative path`);
  const normalized = value.replaceAll("\\", "/");
  if (normalized.startsWith("/") || /^[A-Za-z]:\//.test(normalized)) throw new Error(`${field} must be relative`);
  const parts = normalized.split("/").filter(Boolean);
  if (!parts.length || parts.includes("..")) throw new Error(`${field} escapes its root`);
  return parts.join("/");
}

async function copyMaterializedEntry(source, destination) {
  const sourceStat = await lstat(source);
  if (sourceStat.isSymbolicLink()) throw new Error(`materialization source symlink is not allowed: ${source}`);
  if (sourceStat.isDirectory()) {
    await mkdir(destination, { recursive: true });
    for (const entry of await readdir(source, { withFileTypes: true })) {
      await copyMaterializedEntry(join(source, entry.name), join(destination, entry.name));
    }
    return;
  }
  if (!sourceStat.isFile()) throw new Error(`materialization source is not a regular file or directory: ${source}`);
  await mkdir(dirname(destination), { recursive: true });
  const contents = await readFile(source);
  try {
    await writeFile(destination, contents, { flag: "wx" });
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    const existing = await readFile(destination);
    if (!existing.equals(contents)) throw new Error(`materialization destination already exists with different content: ${destination}`);
  }
}

async function rejectDestinationSymlinks(destinationRoot, destination) {
  const rootPath = resolve(destinationRoot);
  const candidatePath = resolve(destination);
  const rootStat = await lstat(rootPath).catch((error) => {
    if (error.code === "ENOENT") return null;
    throw error;
  });
  if (!rootStat) return;
  if (rootStat.isSymbolicLink()) throw new Error(`materialization destination root symlink is not allowed: ${rootPath}`);
  let current = rootPath;
  const parts = relative(rootPath, candidatePath).split(/[\\/]/).filter(Boolean);
  for (const part of parts) {
    current = join(current, part);
    const entry = await lstat(current).catch((error) => {
      if (error.code === "ENOENT") return null;
      throw error;
    });
    if (entry?.isSymbolicLink()) throw new Error(`materialization destination symlink is not allowed: ${current}`);
    if (!entry) break;
  }
}

/**
 * Copy benchmark-owned, untracked inputs into a disposable worktree.
 * Sources must be relative to the logical repository cwd and destinations
 * must be relative to the isolated cwd. This keeps the parent checker and
 * the main checkout out of the worker's write surface.
 */
export async function materializeWorktreePaths({ paths = [], sourceRoot, destinationRoot } = {}) {
  if (!Array.isArray(paths) || paths.length === 0) return [];
  if (!sourceRoot || !destinationRoot) throw new Error("materialization roots are required");
  const materialized = [];
  for (const value of paths) {
    if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("materialization entries must be objects");
    const sourceRelative = safeRelativePath(value.source, "materialization source");
    const destinationRelative = safeRelativePath(value.destination, "materialization destination");
    const source = resolve(sourceRoot, sourceRelative);
    const destination = resolve(destinationRoot, destinationRelative);
    if (!isWithin(sourceRoot, source)) throw new Error("materialization source escapes the logical cwd");
    if (!isWithin(destinationRoot, destination)) throw new Error("materialization destination escapes the isolated cwd");
    await rejectDestinationSymlinks(destinationRoot, destination);
    await copyMaterializedEntry(source, destination);
    materialized.push({ source: sourceRelative, destination: destinationRelative });
  }
  return materialized;
}

function timeoutEvidence(error) {
  return /timed out|timeoutexpired|timeout/i.test(`${error?.stderr || ""}\n${error?.message || ""}`);
}

async function recoverTimedOutProvision({ taskId, title, objective, gitRepoRoot, stateDir, canonicalBranch, worktreeRoot, intendedFiles, ownerSession } = {}) {
  if (!worktreeRoot) return null;
  const expectedPath = resolve(join(worktreeRoot, taskId));
  let git = null;
  for (let attempt = 0; attempt < 5; attempt += 1) {
    const registrations = await gitWorktrees(gitRepoRoot);
    git = registrations.find((entry) => samePath(entry.path, expectedPath));
    if (git?.branch && await stat(expectedPath).catch(() => null)) break;
    git = null;
    if (attempt < 4) await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
  }
  if (!git) return null;
  const metadataFile = metadataPath(stateDir, taskId);
  try {
    const existing = await readMetadata(metadataFile);
    if (existing?.schema === "worktree-task.v1" && existing.task_id === taskId) return existing;
  } catch { /* helper timed out before writing metadata */ }
  const now = new Date().toISOString();
  const metadata = {
    schema: "worktree-task.v1",
    task_id: taskId,
    title: title || taskId,
    objective: objective || "",
    branch: git.branch.replace(/^refs\/heads\//, ""),
    worktree_path: expectedPath,
    base_commit: git.head || "",
    canonical_branch: canonicalBranch,
    repo_root: gitRepoRoot,
    owner_session: ownerSession || "",
    owner_run_id: "",
    intended_files: intendedFiles,
    integration_sensitive_files_touched: [],
    status: "active",
    created_at: now,
    updated_at: now,
    tests_run: null,
    cache_version_decision: null,
    cleanup_state: "recovered_after_helper_timeout",
    provisioning_recovery: "git_worktree_registered_without_helper_metadata",
  };
  await mkdir(dirname(metadataFile), { recursive: true });
  try {
    await writeFile(metadataFile, JSON.stringify(metadata, null, 2), { encoding: "utf8", flag: "wx" });
    return metadata;
  } catch (error) {
    if (error.code !== "EEXIST") throw error;
    const existing = await readMetadata(metadataFile);
    if (existing?.schema === "worktree-task.v1" && existing.task_id === taskId) return existing;
    throw error;
  }
}

export async function provisionWorktree({ taskId, title, objective = "", repoRoot, stateDir, canonicalBranch = "main", worktreeRoot, intendedFiles = [], materializePaths = [], ownerSession = "codex" } = {}) {
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
  let metadata;
  try {
    await execFileAsync(pythonCommand(), args, { windowsHide: true, maxBuffer: 1024 * 1024 });
  } catch (error) {
    if (timeoutEvidence(error)) {
      metadata = await recoverTimedOutProvision({ taskId, title, objective, gitRepoRoot, stateDir, canonicalBranch, worktreeRoot, intendedFiles, ownerSession });
    }
    if (!metadata) throw new Error(`worktree provisioning failed: ${error.stderr || error.message}`);
  }
  const metadataFile = metadataPath(stateDir, taskId);
  metadata ||= await readMetadata(metadataFile);
  if (metadata.schema !== "worktree-task.v1" || metadata.task_id !== taskId) throw new Error("worktree metadata contract mismatch");
  if (!samePath(metadata.repo_root, gitRepoRoot) || samePath(metadata.worktree_path, gitRepoRoot)) throw new Error("worktree metadata repository identity mismatch");
  const isolatedCwd = logicalRelative ? join(metadata.worktree_path, logicalRelative) : metadata.worktree_path;
  const updated = await updateMetadata(metadataFile, {
    task_id: taskId,
    logical_cwd: logicalCwd,
    logical_relative: logicalRelative,
    isolated_cwd: isolatedCwd,
  });
  const materialized = await materializeWorktreePaths({ paths: materializePaths, sourceRoot: logicalCwd, destinationRoot: isolatedCwd });
  const finalMetadata = materialized.length
    ? await updateMetadata(metadataFile, { task_id: taskId, materialized_paths: materialized })
    : updated;
  const git = (await gitWorktrees(gitRepoRoot)).find((entry) => samePath(entry.path, metadata.worktree_path));
  if (!git) throw new Error("provisioned worktree is not registered with Git");
  return { ...finalMetadata, git, metadata_file: metadataFile, isolated_cwd: isolatedCwd };
}

export async function validateWorktree({ isolatedCwd, repoRoot, taskId, stateDir } = {}) {
  if (!isolatedCwd || !repoRoot || !taskId || !stateDir) return { ok: false, reason: "missing_worktree_identity" };
  try {
    const metadata = await readMetadata(metadataPath(stateDir, taskId));
    const logicalRelative = metadata.logical_relative || "";
    const expectedIsolatedCwd = logicalRelative ? join(metadata.worktree_path, logicalRelative) : metadata.worktree_path;
    const git = (await gitWorktrees(metadata.repo_root)).find((entry) => samePath(entry.path, metadata.worktree_path));
    if (!git || !samePath(expectedIsolatedCwd, isolatedCwd) || !samePath(metadata.logical_cwd || metadata.repo_root, repoRoot)) return { ok: false, reason: "worktree_identity_mismatch" };
    return { ok: true, metadata, git };
  } catch (error) { return { ok: false, reason: "worktree_validation_failed", detail: error.message }; }
}

async function updateMetadata(metadataFile, updates) {
  const metadata = await readMetadata(metadataFile);
  if (metadata.schema !== "worktree-task.v1" || metadata.task_id !== updates.task_id) {
    throw new Error("worktree metadata contract mismatch during lifecycle update");
  }
  const next = { ...metadata, ...updates, updated_at: new Date().toISOString() };
  // A process can update multiple worktree records concurrently. A PID-only
  // temp name lets those updates overwrite each other's staging file.
  const temporary = `${metadataFile}.tmp-${process.pid}-${randomUUID()}`;
  await writeFile(temporary, JSON.stringify(next, null, 2), { encoding: "utf8", flag: "wx" });
  try {
    await replaceFile(temporary, metadataFile);
  } catch (error) {
    try { await unlink(temporary); } catch { /* best effort cleanup */ }
    throw error;
  }
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
