/**
 * UI helpers for risk-policy.
 *
 *   ctx.ui.setStatus()  — persistent footer marker ("R:LOW/MED/HIGH")
 *   ctx.ui.notify()     — non-blocking toast (HIGH, warnings)
 *
 * ponytail: dropped the above-editor widget. The footer "R:LOW/MED/HIGH"
 * already conveys the tier; the per-turn "Reason:" line cluttered the
 * screen and duplicated the footer. Details are in /risk-log.jsonl and
 * via /risk-review if you need them.
 */

import type { ExtensionContext, Theme } from "@earendil-works/pi-coding-agent";
import type { RiskAssessment, RiskPolicy, RiskTier } from "./risk-types.ts";

// ponytail: RiskAssessment and RiskPolicy are still used in the showRiskBanner
// signature (callers in risk-policy-extension.ts pass them); kept despite
// most of their fields no longer being rendered, because changing the
// signature would ripple into every caller.

const STATUS_KEY = "risk-policy";
// ponytail: WIDGET_KEY removed — widget no longer rendered.

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

	if (tier === "HIGH" && !assessment.overridden) {
		ctx.ui.notify(`HIGH risk: ${assessment.reasons.join(", ")}`, "warning");
	}

	// ponytail: was ctx.ui.setWidget(WIDGET_KEY, [banner, reasonLine]).
	// Removed because the widget duplicated the footer marker and cluttered
	// the area above the editor where pi's working spinner also renders.
	void policy; // kept in signature for callers that pass it
}

export async function showRiskWarning(ctx: ExtensionContext, message: string): Promise<void> {
	if (!ctx.hasUI) return;
	ctx.ui.notify(message, "warning");
}

export function clearRiskUI(ctx: ExtensionContext): void {
	if (!ctx.hasUI) return;
	ctx.ui.setStatus(STATUS_KEY, undefined);
	// ponytail: was ctx.ui.setWidget(WIDGET_KEY, undefined). No widget now.
}

// Re-export so callers don't need to import Theme separately if they just
// want the color mapping.
export { tierThemeColor };
export type { Theme };