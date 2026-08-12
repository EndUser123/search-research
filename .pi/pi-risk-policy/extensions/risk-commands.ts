/**
 * Slash commands for risk-policy.
 *
 *   /risk                  — current tier, reasons, rules, policy, verification
 *   /risk-why              — latest assessment + recent session log entries
 *   /risk-override <tier>  — force LOW | MED | HIGH until /risk-reset
 *   /risk-reset            — clear manual override, return to automatic
 *   /risk-approve          — HIGH only, mark manual approval recorded
 *   /risk-plan [text]      — record plan
 *   /risk-diff [text]      — record diff summary
 */

import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import type { RiskStateSnapshot, RiskTier } from "./risk-types.ts";
import type { RiskStateStore } from "./risk-state.ts";

interface AutocompleteItem {
	value: string;
	label: string;
	description?: string;
}

// R15: typed union of known event names so the wire format is grep-friendly
// and typo-resistant. The set is enforced where the entry is constructed;
// the `event: string` index below remains for forward-compat with external
// log writers.
export type RiskLogEventName =
	| "hook_seen"
	| "auto_diff_summary_recorded"
	| "auto_diff_summary_failed"
	| "auto_diff_probe"
	| "verification_block"
	| "auto_plan_recorded"
	| "classified"
	| "override"
	| "session_start"
	| "tool_result_seen"
	| "verification_update"
	| "auto_verification_failed"
	| "write_gate_block"
	| "session_shutdown_cleanup_failed";

export interface RiskLogEntry {
	timestamp: string;
	event: RiskLogEventName | string;
	[key: string]: unknown;
}

const VALID_TIERS = new Set<RiskTier>(["LOW", "MED", "HIGH"]);

function isValidTier(s: string): s is RiskTier {
	return VALID_TIERS.has(s.toUpperCase() as RiskTier);
}

function renderSnapshot(snap: RiskStateSnapshot | null): string {
	if (!snap) return "Risk: (no assessment yet — send a prompt)";
	const a = snap.assessment;
	const p = snap.policy;
	const v = snap.verification;
	const lines: string[] = [];
	lines.push(`Risk: ${a.tier}${a.overridden ? " (manual override)" : ""}`);
	lines.push(`Policy: ${p.uiLabel}`);
	if (a.reasons.length) lines.push(`Reasons: ${a.reasons.join(", ")}`);
	if (a.matchedRules.length) lines.push(`Rules: ${a.matchedRules.join(", ")}`);
	lines.push(`Paths: ${a.candidatePaths.length ? a.candidatePaths.join(", ") : "(none)"}`);
	lines.push(`Verification:`);
	lines.push(`  planned: ${v.planned}`);
	lines.push(`  verificationRan: ${v.verificationRan}`);
	lines.push(`  verificationPassed: ${v.verificationPassed}`);
	lines.push(`  diffSummarized: ${v.diffSummarized}`);
	lines.push(`  manualApprovalRecorded: ${v.manualApprovalRecorded}`);
	return lines.join("\n");
}

function renderRecentLog(entries: RiskLogEntry[]): string {
	if (entries.length === 0) return "(no session log entries yet)";
	return entries
		.slice(-5)
		.map((e) => {
			const ts = e.timestamp.slice(11, 19);
			const tier = e.tier ? ` [${e.tier}]` : "";
			const detail = e.command
				? ` ${e.command} (exit ${e.exitCode ?? "?"})`
				: e.missing
					? ` missing: ${(e.missing as string[]).join(", ")}`
					: "";
			return `${ts}${tier} ${e.event}${detail}`;
		})
		.join("\n");
}

export function registerRiskCommands(
	pi: ExtensionAPI,
	store: RiskStateStore,
	reclassifyCurrent: (ctx: ExtensionContext) => Promise<void>,
	getRecentLogEntries: () => RiskLogEntry[],
): void {
	pi.registerCommand("risk", {
		description: "Show current risk tier, reasons, rules, and policy",
		handler: async (_args, ctx) => {
			ctx.ui.notify(renderSnapshot(store.getSnapshot()), "info");
		},
	});

	pi.registerCommand("risk-why", {
		description: "Show latest assessment and recent session log entries",
		handler: async (_args, ctx) => {
			const snap = renderSnapshot(store.getSnapshot());
			const log = renderRecentLog(getRecentLogEntries());
			ctx.ui.notify(`${snap}\n\nRecent log:\n${log}`, "info");
		},
	});

	pi.registerCommand("risk-override", {
		description: "Set manual override tier: /risk-override low|med|high",
		getArgumentCompletions: (prefix: string): AutocompleteItem[] | null => {
			const items: AutocompleteItem[] = ["low", "med", "high"].map((v) => ({ value: v, label: v }));
			const filtered = items.filter((i) => i.value.startsWith(prefix.toLowerCase()));
			return filtered.length ? filtered : null;
		},
		handler: async (args, ctx) => {
			const arg = (args ?? "").trim().toUpperCase();
			if (!isValidTier(arg)) {
				ctx.ui.notify("Usage: /risk-override low|med|high", "warning");
				return;
			}
			store.setOverride(arg);
			await reclassifyCurrent(ctx);
			ctx.ui.notify(`Manual override set to ${arg}`, "info");
		},
	});

	pi.registerCommand("risk-reset", {
		description: "Clear manual risk override",
		handler: async (_args, ctx) => {
			store.setOverride(null);
			await reclassifyCurrent(ctx);
			ctx.ui.notify("Risk override cleared", "info");
		},
	});

	pi.registerCommand("risk-approve", {
		description: "HIGH only — record manual approval for the current task",
		handler: async (_args, ctx) => {
			const snap = store.getSnapshot();
			const tier = snap?.assessment.tier ?? "LOW";
			if (tier !== "HIGH") {
				ctx.ui.notify("/risk-approve is only meaningful for HIGH risk", "warning");
				return;
			}
			store.updateVerification({ manualApprovalRecorded: true });
			ctx.ui.notify("Manual approval recorded", "info");
		},
	});

	pi.registerCommand("risk-plan", {
		description: "Record a plan for the current MED/HIGH task",
		handler: async (args, ctx) => {
			const text = (args ?? "").trim();
			store.updateVerification({ planned: true });
			ctx.ui.notify(text ? `Plan recorded (${text.length} chars)` : "Plan recorded", "info");
		},
	});

	pi.registerCommand("risk-diff", {
		description: "Record a diff summary for the current HIGH task",
		handler: async (args, ctx) => {
			const text = (args ?? "").trim();
			store.updateVerification({ diffSummarized: true });
			ctx.ui.notify(text ? `Diff summary recorded (${text.length} chars)` : "Diff summary recorded", "info");
		},
	});
}