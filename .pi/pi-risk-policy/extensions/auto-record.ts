// Helpers for structural auto-recording of plan / verification / diff state.
// All auto-recorded state is labelled so the model and the user can see it
// was machine-generated, not a user-shown normalization block.

import { suggestVerifyCommandsForPath } from "./verify-defaults.ts";
import type { RiskAssessment, RiskTier, VerificationState } from "./risk-types.ts";

const AUTO_PLAN_PREFIX = "AUTO-RECORDED PLAN:";
const AUTO_VERIFY_PREFIX = "AUTO-CAPTURED VERIFICATION";
const AUTO_DIFF_PREFIX = "AUTO-RECORDED DIFF SUMMARY:";

/**
 * Build a one-line plan string for structural auto-plan recording.
 * The classifier-provided `promptSummary` and `candidatePaths` are the
 * primary inputs. The expected-verify hint is per-filetype.
 */
export function synthesizePlanText(assessment: RiskAssessment): string {
	const paths = assessment.candidatePaths.length > 0
		? assessment.candidatePaths.slice(0, 5).join(", ")
		: "(no candidate paths)";
	let verifyHint = "(none)";
	if (assessment.candidatePaths.length > 0) {
		const first = assessment.candidatePaths[0]!;
		const cmds = suggestVerifyCommandsForPath(first);
		if (cmds && cmds.length > 0) verifyHint = cmds[0]!;
	}
	const prompt = (assessment.promptSummary || "").slice(0, 200);
	return `${AUTO_PLAN_PREFIX} ${assessment.tier} task touching ${paths}. Prompt: ${prompt} Expected verification: ${verifyHint}.`;
}

/** True if verification state is empty (never recorded). */
export function isUnplanned(v: VerificationState): boolean {
	return !v.planned;
}

/** Auto-record a plan if MED/HIGH and not already planned. Returns true if it set planned=true. */
export function autoRecordPlanIfNeeded(
	current: VerificationState,
	assessment: RiskAssessment,
): { changed: boolean; next: VerificationState } {
	if (assessment.tier !== "MED" && assessment.tier !== "HIGH") return { changed: false, next: current };
	if (current.planned) return { changed: false, next: current };
	return {
		changed: true,
		next: {
			...current,
			planned: true,
			planText: synthesizePlanText(assessment),
			planSource: "auto",
		},
	};
}

export interface AutoDiffProbeInput {
	readonly tier: "LOW" | "MED" | "HIGH";
	readonly planned: boolean;
	readonly diffSummarized: boolean;
	readonly hasSessionManager: boolean;
	readonly hasBranch: boolean;
	readonly changeSetEntryCount: number;
	readonly verificationRan: boolean;
	readonly verificationPassed: boolean;
	readonly lastVerificationExitCode: number | undefined;
}

export interface AutoDiffProbeResult {
	readonly willRecord: boolean;
	readonly skipReason?: string;
}

export interface AutoDiffRecordInput extends AutoDiffProbeInput {
	readonly fileList: string;
}

export interface AutoDiffRecordResult extends AutoDiffProbeResult {
	readonly summary?: string;
}

/**
 * Evaluate whether the auto-diff branch should record. Pure function for
 * unit testing. The live handler reads inputs from the snapshot + ctx and
 * passes them in; this decides what the result and (optional) summary would be.
 */
export function evaluateAutoDiff(input: AutoDiffProbeInput): AutoDiffProbeResult {
	if (input.tier !== "MED" && input.tier !== "HIGH") {
		return { willRecord: false, skipReason: "skip_low_tier" };
	}
	if (input.diffSummarized) {
		return { willRecord: false, skipReason: "skip_already_summarized" };
	}
	if (!input.hasSessionManager) {
		return { willRecord: false, skipReason: "skip_no_session_manager" };
	}
	if (!input.hasBranch) {
		return { willRecord: false, skipReason: "skip_no_branch" };
	}
	if (input.changeSetEntryCount === 0) {
		return { willRecord: false, skipReason: "skip_empty_changeset" };
	}
	return { willRecord: true };
}

/**
 * Pure builder for the auto-diff summary text. Kept separate from
 * evaluateAutoDiff so the live handler can call it AFTER the gate passes
 * without re-deriving the skip-reason order.
 */
export function buildAutoDiffSummary(input: AutoDiffRecordInput): string {
	const verifyNote = input.verificationRan
		? `verification ${input.verificationPassed ? "passed" : "failed"} (exit ${input.lastVerificationExitCode ?? "?"})`
		: "no verification captured yet";
	return `${AUTO_DIFF_PREFIX} ${input.changeSetEntryCount} file(s) changed in session: ${input.fileList}. ${verifyNote}.`;
}

// R6: typed wire format for the auto_diff_probe log entry. Keys are part
// of the contract with consumers of risk-log.jsonl.
export interface AutoDiffProbeLogEntry {
	readonly event: "auto_diff_probe";
	readonly cwd: string;
	readonly tier: RiskTier;
	readonly planned: boolean;
	readonly verificationRan: boolean;
	readonly verificationPassed: boolean;
	readonly diffSummarized: boolean;
	readonly hasSessionManager: boolean;
	readonly hasBranch: boolean;
	readonly changeSetEntryCount: number;
	readonly willRecord: boolean;
	readonly skipReason?: string;
}

/**
 * Pure formatter for the auto_diff_probe log entry. Keeps the live handler
 * free of inline payload construction so the wire format is unit-testable
 * and centralized.
 */
export function buildAutoDiffProbeLog(input: Omit<AutoDiffProbeLogEntry, "event" | "skipReason"> & { skipReason?: string }): AutoDiffProbeLogEntry {
	return {
		event: "auto_diff_probe",
		cwd: input.cwd,
		tier: input.tier,
		planned: input.planned,
		verificationRan: input.verificationRan,
		verificationPassed: input.verificationPassed,
		diffSummarized: input.diffSummarized,
		hasSessionManager: input.hasSessionManager,
		hasBranch: input.hasBranch,
		changeSetEntryCount: input.changeSetEntryCount,
		willRecord: input.willRecord,
		...(input.skipReason ? { skipReason: input.skipReason } : {}),
	};
}

export { AUTO_PLAN_PREFIX, AUTO_VERIFY_PREFIX, AUTO_DIFF_PREFIX };
