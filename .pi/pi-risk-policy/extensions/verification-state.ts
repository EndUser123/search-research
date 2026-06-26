/**
 * Verification state helpers.
 *
 * Verification is the deterministic gate that decides whether a task may
 * claim "done". Each tier has a stricter bar than the last.
 */

import type { RiskTier, VerificationState } from "./risk-types.ts";

export function createEmptyVerificationState(): VerificationState {
	return {
		planned: false,
		verificationRan: false,
		verificationPassed: false,
		diffSummarized: false,
		manualApprovalRecorded: false,
	};
}

export function canClaimDone(tier: RiskTier, verification: VerificationState): boolean {
	if (tier === "LOW") return true;

	if (tier === "MED") {
		return verification.planned && verification.verificationRan && verification.verificationPassed;
	}

	// HIGH
	return (
		verification.planned &&
		verification.verificationRan &&
		verification.verificationPassed &&
		verification.diffSummarized &&
		verification.manualApprovalRecorded
	);
}

export function missingRequirements(tier: RiskTier, verification: VerificationState): string[] {
	const missing: string[] = [];
	if (tier === "LOW") return missing;
	if (!verification.planned) missing.push("plan");
	if (!verification.verificationRan) missing.push("verification command run");
	else if (!verification.verificationPassed) missing.push("verification passed");
	if (tier === "HIGH") {
		if (!verification.diffSummarized) missing.push("diff summary");
		if (!verification.manualApprovalRecorded) missing.push("manual approval (/risk-approve)");
	}
	return missing;
}