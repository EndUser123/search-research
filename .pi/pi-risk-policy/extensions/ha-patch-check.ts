// One-shot session-start check that verifies the pi-high-availability patch
// is active. Inline (no shell-out) so it's fast and dependency-free.
//
// Returns:
//   "pass" — patched classifier present + synthetic MiniMax 2056 classifies as quota
//   "fail" — patched classifier missing OR patterns not loaded
//
// Never logs secrets. Never throws — failures degrade gracefully to "fail".

import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export type HaPatchStatus = "pass" | "fail";

export interface HaPatchCheckResult {
	status: HaPatchStatus;
	details: string[];
}

export function checkHaPatch(): HaPatchCheckResult {
	const details: string[] = [];

	// 1. Verify the patched file is present and contains the patched markers.
	const indexPath = join(homedir(), ".pi", "agent", "npm", "node_modules", "pi-high-availability", "extensions", "index.ts");
	if (!existsSync(indexPath)) {
		details.push("index.ts missing at " + indexPath);
		return { status: "fail", details };
	}
	const src = readFileSync(indexPath, "utf-8");
	const readsQuota = /quotaErrorPatterns/.test(src);
	const readsCapacity = /capacityErrorPatterns/.test(src);
	const readsTransient = /transientErrorPatterns/.test(src);
	const hasPriorityFirst = /turn_start[\s\S]{0,800}priority-first selection/.test(src);
	if (!readsQuota || !readsCapacity || !readsTransient || !hasPriorityFirst) {
		details.push(
			`patched markers missing: quota=${readsQuota} capacity=${readsCapacity} transient=${readsTransient} priorityFirst=${hasPriorityFirst}`,
		);
		return { status: "fail", details };
	}

	// 2. Load ha.json quota patterns and verify MiniMax 2056 → quota.
	const haPath = join(homedir(), ".pi", "agent", "ha.json");
	if (!existsSync(haPath)) {
		details.push("ha.json missing");
		return { status: "fail", details };
	}
	const ha = JSON.parse(readFileSync(haPath, "utf-8"));
	const quotaPatterns: string[] = ha.quotaErrorPatterns || [];

	const minmax2056 = JSON.stringify({ status: 500, error: { code: 2056, message: "usage limit exceeded" } });
	const isQuota = quotaPatterns.some((p: string) =>
		minmax2056.toLowerCase().includes(p.toLowerCase()) || minmax2056.includes(p),
	);
	if (!isQuota) {
		details.push("MiniMax 2056 payload does NOT match any quotaErrorPatterns");
		return { status: "fail", details };
	}

	// 3. Negative test: "context length exceeded" must NOT classify as quota.
	const ctxLength = "context length exceeded";
	const falsePositive = quotaPatterns.some((p: string) =>
		ctxLength.toLowerCase().includes(p.toLowerCase()) || ctxLength.includes(p),
	);
	if (falsePositive) {
		details.push("overly broad quota pattern matches 'context length exceeded'");
		return { status: "fail", details };
	}

	details.push("patched classifier present");
	details.push("MiniMax 2056 → quota");
	details.push("context length excluded");
	return { status: "pass", details };
}

export function formatHaPatchWarning(): string {
	return [
		"[ha-patch] BLOCKING WARNING: pi-high-availability patch is missing or inactive.",
		"",
		"MiniMax/Z.ai quota failover is NOT trusted.",
		"MiniMax 2056 / 1008 and z.ai quota errors may not switch to GLM/Mistral.",
		"",
		"Stop and reapply before serious MiniMax-heavy work:",
		"",
		"  patch -p0 < ~/.pi/agent/patches/pi-high-availability-error-patterns.patch",
		"",
		"Then verify:",
		"",
		"  node ~/.pi/agent/patches/check-pi-high-availability-patch.mjs",
	].join("\n");
}
