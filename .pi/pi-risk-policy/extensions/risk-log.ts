/**
 * JSONL audit log for risk-policy events.
 *
 * Appends to `.pi/risk-log.jsonl` in the project when project trust allows.
 * Falls back silently when the directory is not writable. Logging must
 * never crash the session.
 *
 * Caching: the resolved path is cached per-cwd so repeated appends are
 * cheap. Failures are NOT cached — a transient permission error today
 * does not permanently disable logging for the session.
 */

import { appendFile, mkdir } from "node:fs/promises";
import { join } from "node:path";

const resolvedPaths = new Map<string, string>();

async function resolveLogPath(cwd: string): Promise<string | null> {
	const cached = resolvedPaths.get(cwd);
	if (cached) return cached;

	const dir = join(cwd, ".pi");
	const file = join(dir, "risk-log.jsonl");
	try {
		await mkdir(dir, { recursive: true });
		// Probe writability with an empty append.
		await appendFile(file, "", { encoding: "utf8" });
		resolvedPaths.set(cwd, file);
		return file;
	} catch {
		return null;
	}
}

export async function appendRiskLog(entry: Record<string, unknown>): Promise<void> {
	const cwd = (entry.cwd as string | undefined) ?? process.cwd();
	const file = await resolveLogPath(cwd);
	if (!file) return;

	const line =
		JSON.stringify({
			timestamp: new Date().toISOString(),
			...entry,
		}) + "\n";

	try {
		await appendFile(file, line, { encoding: "utf8" });
	} catch {
		// Don't cache the failure; next call will re-resolve and retry.
	}
}

// R6: expose a way to reset the per-cwd path cache so tests that run in
// the same process across multiple cwd values don't see a stale mapping.
export function _resetRiskLogPathCacheForTests(): void {
	resolvedPaths.clear();
}