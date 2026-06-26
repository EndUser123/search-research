/**
 * UI helpers for risk-policy.
 *
 *   ctx.ui.setStatus()  — persistent footer marker ("R:LOW/MED/HIGH")
 *   ctx.ui.setWidget()  — banner above the editor with policy + reasons
 *   ctx.ui.notify()     — non-blocking toast (HIGH, warnings)
 */

import type { ExtensionContext, Theme } from "@earendil-works/pi-coding-agent";
import type { RiskAssessment, RiskPolicy, RiskTier } from "./risk-types.ts";

const STATUS_KEY = "risk-policy";
const WIDGET_KEY = "risk-policy-banner";

function tierThemeColor(tier: RiskTier): "success" | "warning" | "error" {
	switch (tier) {
		case "HIGH":
			return "error";
		case "MED":
			return "warning";
		default:
			return "success";
	}
}

export async function showRiskBanner(
	ctx: ExtensionContext,
	assessment: RiskAssessment,
	policy: RiskPolicy,
): Promise<void> {
	if (!ctx.hasUI) return;

	const theme = ctx.ui.theme;
	const tier = assessment.tier;
	const tierText = theme.fg(tierThemeColor(tier), tier);
	const overrideMark = assessment.overridden ? theme.fg("muted", " (manual)") : "";

	ctx.ui.setStatus(STATUS_KEY, `${theme.fg("dim", "R:")}${tierText}${overrideMark}`);

	const policyDetail = policy.uiLabel.replace(/^[A-Z]+ — /, "");
	const banner = `${theme.fg("accent", "Risk: ")}${tierText}${overrideMark} ${theme.fg(
		"muted",
		"—",
	)} ${theme.fg("muted", policyDetail)}`;
	const reasonLine =
		assessment.reasons.length > 0
			? `${theme.fg("dim", "Reason: ")}${theme.fg("muted", assessment.reasons.join(", "))}`
			: "";
	ctx.ui.setWidget(WIDGET_KEY, reasonLine ? [banner, reasonLine] : [banner]);

	if (tier === "HIGH" && !assessment.overridden) {
		ctx.ui.notify(`HIGH risk: ${assessment.reasons.join(", ")}`, "warning");
	}
}

export async function showRiskWarning(ctx: ExtensionContext, message: string): Promise<void> {
	if (!ctx.hasUI) return;
	ctx.ui.notify(message, "warning");
}

export function clearRiskUI(ctx: ExtensionContext): void {
	if (!ctx.hasUI) return;
	ctx.ui.setStatus(STATUS_KEY, undefined);
	ctx.ui.setWidget(WIDGET_KEY, undefined);
}

// Re-export so callers don't need to import Theme separately if they just
// want the color mapping.
export { tierThemeColor };
export type { Theme };