/**
 * Policy table: tier -> controls.
 *
 * Higher-risk changes require stronger controls, stronger verification,
 * and explicit oversight.
 */

import type { RiskPolicy, RiskTier } from "./risk-types.ts";

export const POLICY_BY_TIER: Record<RiskTier, RiskPolicy> = {
	LOW: {
		requirePlan: false,
		requireVerification: false,
		manualApplyOnly: false,
		allowDestructiveShell: false,
		allowInfraChanges: false,
		uiLabel: "LOW — fast path",
	},
	MED: {
		requirePlan: true,
		requireVerification: true,
		manualApplyOnly: false,
		allowDestructiveShell: false,
		allowInfraChanges: false,
		uiLabel: "MED — plan + verify required",
	},
	HIGH: {
		requirePlan: true,
		requireVerification: true,
		manualApplyOnly: true,
		allowDestructiveShell: false,
		allowInfraChanges: true,
		uiLabel: "HIGH — plan + verify + manual apply",
	},
};