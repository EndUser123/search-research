/**
 * Custom tools exposed to the LLM.
 *
 *   get_active_risk_policy  — current assessment, policy, verification
 *   evaluate_change_risk    — read-only: classify a proposed change
 *   risk_progress           — record plan / diff summary / verification
 *
 * evaluate_change_risk is deliberately read-only: it reports the honest
 * tier for the given inputs without mutating the active assessment. The
 * active tier only changes via a new user task or /risk-override.
 */

import { StringEnum } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { Type, Literal, Union } from "typebox";
import type { RiskAssessment, RiskConfig, RiskPolicy } from "./risk-types.ts";
import { classifyRisk } from "./risk-classifier.ts";
import type { RiskStateStore } from "./risk-state.ts";
import { getSessionChangeSet } from "./session-changeset.ts";
import { POLICY_BY_TIER } from "./risk-policy.ts";

const EvaluateChangeRiskInput = Type.Object({
	paths: Type.Optional(Type.Array(Type.String(), { description: "Candidate file paths" })),
	commands: Type.Optional(Type.Array(Type.String(), { description: "Candidate commands" })),
	prompt: Type.Optional(Type.String({ description: "Prompt text to scan for production keywords" })),
});

const RiskProgressInput = Type.Object({
	action: StringEnum(["plan", "diff_summary", "verification", "disposition"] as const),
	text: Type.Optional(Type.String({ description: "Optional accompanying text" })),
	passed: Type.Optional(Type.Boolean({ description: "For verification: did it pass?" })),
	command: Type.Optional(Type.String({ description: "For verification: the command run" })),
	exitCode: Type.Optional(Type.Number({ description: "For verification: command exit code" })),
	finding: Type.Optional(Type.String({ description: "For disposition: finding id (e.g. R1, S2)" })),
	status: Type.Optional(Union([Literal("addressed"), Literal("dismissed_with_reason"), Literal("accepted_as_followup")], {
		description: "For disposition: status of the finding",
	})),
	note: Type.Optional(Type.String({ description: "For disposition: optional note explaining dismissal or followup" })),
});

type EvaluateChangeRiskArgs = {
	paths?: string[];
	commands?: string[];
	prompt?: string;
};

type RiskProgressArgs = {
	action: "plan" | "diff_summary" | "verification" | "disposition";
	text?: string;
	passed?: boolean;
	command?: string;
	exitCode?: number;
	finding?: string;
	status?: "addressed" | "dismissed_with_reason" | "accepted_as_followup";
	note?: string;
};

export function registerRiskTools(
	pi: ExtensionAPI,
	store: RiskStateStore,
	getConfig: () => RiskConfig,
	getLastPrompt: () => string,
	ctx: ExtensionContext,
): void {
	pi.registerTool({
		name: "get_active_risk_policy",
		label: "Get active risk policy",
		description:
			"Returns the current risk tier, assessment reasons, matched rules, policy controls, and verification state for the active task.",
		parameters: Type.Object({}),
		async execute() {
			const snap = store.getSnapshot();
			const tier = snap?.assessment.tier ?? null;
			const assessment = snap?.assessment ?? null;
			const policy = snap?.policy ?? null;
			const verification = snap?.verification ?? null;
			const text = snap
				? [
						`Tier: ${snap.assessment.tier}${snap.assessment.overridden ? " (manual)" : ""}`,
						`Policy: ${snap.policy.uiLabel}`,
						`Reasons: ${snap.assessment.reasons.join("; ")}`,
						`Rules: ${snap.assessment.matchedRules.join(", ")}`,
						`Paths: ${snap.assessment.candidatePaths.join(", ") || "(none)"}`,
						`Verification: planned=${snap.verification.planned} ran=${snap.verification.verificationRan} passed=${snap.verification.verificationPassed} diff=${snap.verification.diffSummarized} approved=${snap.verification.manualApprovalRecorded}`,
						`Worktree: ${snap.worktree ? (snap.worktree.inWorktree ? `yes (name=${snap.worktree.worktreeName ?? "?"}, main=${snap.worktree.mainGitDir ?? "?"})` : "no") : "unknown"}`,
					].join("\n")
				: "No risk assessment yet. Send a prompt first.";
			return {
				content: [{ type: "text" as const, text }],
				details: { tier, assessment, policy, verification },
			};
		},
	});

	pi.registerTool({
		name: "evaluate_change_risk",
		label: "Evaluate change risk",
		description:
			"Read-only: classify a proposed change given optional paths, commands, and prompt text. Returns tier, reasons, matched rules, and policy. Does NOT change the active task tier.",
		parameters: EvaluateChangeRiskInput,
		async execute(_id, params, _signal, _onUpdate, ctx) {
			const args = params as unknown as EvaluateChangeRiskArgs;
			const config = getConfig();
			const current = store.getSnapshot();
			const existingPaths = current?.assessment.candidatePaths ?? [];
			const prompt = args.prompt ?? getLastPrompt();

			// Read-only: classify but do not store.
			// candidatePaths merges the active snapshot's paths so the user can call
			// evaluate_change_risk with additional paths without re-specifying the current ones.
			// proposedCommands is always [] in the active snapshot (nothing populates it), so
			// we pass args.commands directly rather than merging a dead empty array.
			const assessment: RiskAssessment = classifyRisk({
				prompt,
				cwd: ctx.cwd,
				candidatePaths: [...existingPaths, ...(args.paths ?? [])],
				proposedCommands: args.commands ?? [],
				config,
				overrideTier: null, // evaluation is independent of active override
			});
			const policy: RiskPolicy = POLICY_BY_TIER[assessment.tier];

			const text =
				`Tier: ${assessment.tier}\n` +
				`Reasons: ${assessment.reasons.join("; ")}\n` +
				`Rules: ${assessment.matchedRules.join(", ")}\n` +
				`Policy: ${policy.uiLabel}`;
			return {
				content: [{ type: "text" as const, text }],
				details: {
					tier: assessment.tier,
					reasons: assessment.reasons,
					matchedRules: assessment.matchedRules,
					policy,
				},
			};
		},
	});

	pi.registerTool({
		name: "risk_progress",
		label: "Record risk progress",
		description:
			"Record progress on risk-required items: action=plan records a plan, action=diff_summary records a diff summary, action=verification records a verification command result.",
		parameters: RiskProgressInput,
		async execute(_id, params) {
			const args = params as unknown as RiskProgressArgs;
			const baseDetails = {
				action: args.action,
				planned: false as boolean,
				diffSummarized: false as boolean,
				verificationRan: false as boolean,
				verificationPassed: false as boolean,
				lastVerificationCommand: undefined as string | undefined,
				lastVerificationExitCode: undefined as number | undefined,
			};
			switch (args.action) {
				case "plan":
					store.updateVerification({ planned: true });
					return {
						content: [{ type: "text" as const, text: args.text ? `Plan recorded: ${args.text}` : "Plan recorded" }],
						details: { ...baseDetails, action: "plan", planned: true },
					};
				case "diff_summary":
					store.updateVerification({ diffSummarized: true });
					return {
						content: [
							{ type: "text" as const, text: args.text ? `Diff summary recorded: ${args.text}` : "Diff summary recorded" },
						],
						details: { ...baseDetails, action: "diff_summary", diffSummarized: true },
					};
				case "verification": {
					const passed = args.passed ?? (args.exitCode === 0);
					store.updateVerification({
						verificationRan: true,
						verificationPassed: passed,
						lastVerificationCommand: args.command,
						lastVerificationExitCode: args.exitCode,
					});
					// Verification clears any outstanding review findings — the
					// model has satisfied the gate, the findings are addressed.
					if (passed) store.clearFindings();
					return {
						content: [
							{
								type: "text" as const,
								text: `Verification recorded: passed=${passed} command=${args.command ?? "(none)"} exit=${args.exitCode ?? "?"}`,
							},
						],
						details: {
							...baseDetails,
							action: "verification",
							verificationRan: true,
							verificationPassed: passed,
							lastVerificationCommand: args.command,
							lastVerificationExitCode: args.exitCode,
						},
					};
				}
				case "disposition": {
					if (typeof args.finding !== "string" || typeof args.status !== "string") {
						throw new Error("disposition requires `finding` and `status`");
					}
					const result = store.recordDisposition({
						id: args.finding,
						disposition: args.status as "addressed" | "dismissed_with_reason" | "accepted_as_followup",
						note: typeof args.note === "string" ? args.note : undefined,
					});
					return {
						content: [
							{
								type: "text" as const,
								text: result.ok
									? `Disposition recorded for ${args.finding}: ${args.status}${args.note ? ` (note: ${args.note})` : ""}. Remaining unaddressed high-severity review findings: ${result.remainingHigh}.`
									: `Disposition failed: finding ${args.finding} not found.`,
							},
						],
						details: {
							...baseDetails,
							action: "disposition",
							finding: args.finding,
							status: args.status,
							ok: result.ok,
							remainingHigh: result.remainingHigh,
						},
					};
				}
				default:
					throw new Error(`unknown action: ${(args as { action: string }).action}`);
			}
		},
	});

	// Session-scoped change-set. NEVER read from the working tree. The only
	// source of truth is the in-memory record populated by the tool_call
	// hook when edit/write fires. This is the isolation boundary for
	// multi-terminal environments.
	pi.registerTool({
		name: "get_session_changeset",
		label: "Get session change-set",
		description:
			"Returns the session-scoped change-set for THIS session only, sourced from the session ledger (ctx.sessionManager.getBranch()). NEVER reads the working tree. NEVER aggregates across sessions.",
		parameters: Type.Object({}),
		async execute() {
			const cs = getSessionChangeSet(ctx);
			const text = cs.entries.length === 0
				? "No write/edit changes recorded in this session's branch."
				: cs.entries
						.map(
							(e, i) =>
								`[${i}] ${e.toolName} @ ${new Date(e.entryTimestamp).toISOString()} -> ${e.path}\n` +
								`    before: ${e.before ?? "(none)"}\n` +
								`    after: ${e.after}`,
						)
						.join("\n");
			return {
				content: [{ type: "text" as const, text: `${text}\n\nsource: ${cs.source} — ${cs.note}` }],
				details: {
					count: cs.entries.length,
					paths: cs.distinctPaths,
					source: cs.source,
				},
			};
		},
	});
}