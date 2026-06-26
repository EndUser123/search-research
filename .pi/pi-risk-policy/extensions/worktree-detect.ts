/**
 * Worktree detection.
 *
 * Detects whether the current cwd is a linked git worktree (Option B tier).
 * In a main checkout, `.git` is a directory. In a linked worktree, `.git` is
 * a FILE containing `gitdir: <main>/.git/worktrees/<name>`. This is the
 * filesystem signal per the handoff.
 *
 * Pure read-only detection. Does NOT change gate behavior; just records the
 * tier so /risk-why can surface it.
 */

import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

export interface WorktreeInfo {
	readonly inWorktree: boolean;
	readonly worktreeName: string | null;
	readonly mainGitDir: string | null;
	readonly cwd: string;
	readonly checkedAt: string;
}

const GIT_FILE_MARKER = "gitdir: ";

export function detectWorktree(cwd: string): WorktreeInfo {
	const checkedAt = new Date().toISOString();
	const gitPath = join(cwd, ".git");
	let stat;
	try {
		stat = statSync(gitPath);
	} catch {
		return { inWorktree: false, worktreeName: null, mainGitDir: null, cwd, checkedAt };
	}
	if (!stat.isFile()) {
		return { inWorktree: false, worktreeName: null, mainGitDir: null, cwd, checkedAt };
	}
	let raw: string;
	try {
		raw = readFileSync(gitPath, "utf8");
	} catch {
		return { inWorktree: false, worktreeName: null, mainGitDir: null, cwd, checkedAt };
	}
	const trimmed = raw.trim();
	if (!trimmed.startsWith(GIT_FILE_MARKER)) {
		return { inWorktree: false, worktreeName: null, mainGitDir: null, cwd, checkedAt };
	}
	const gitdir = trimmed.slice(GIT_FILE_MARKER.length).trim();
	// gitdir format: "P:/.git/worktrees/<name>" or "P:/.git/worktrees/<name>/".
	const segments = gitdir.split(/[\\/]+/).filter(Boolean);
	const wtIdx = segments.lastIndexOf("worktrees");
	let worktreeName: string | null = null;
	if (wtIdx >= 0 && wtIdx + 1 < segments.length) {
		worktreeName = segments[wtIdx + 1];
	}
	const mainGitDir = gitdir.replace(/[\\/]+worktrees[\\/].*$/, "");
	return { inWorktree: true, worktreeName, mainGitDir, cwd, checkedAt };
}
