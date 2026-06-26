/**
 * Review / simplify pass.
 *
 * Runs on `agent_end` for MED+ tasks. Sources its input exclusively from
 * the session-scoped SessionChangeSet — NEVER from `git diff` of the
 * working tree, NEVER from a shared aggregator. The model is called
 * directly via `completeSimple` with a prompt that contains the session
 * change-set inline; the pi-simplify / pi-review packages (which hard-code
 * `git diff` internally) are bypassed.
 *
 * - `simplify`: any MED+ change. Advisory only. Findings are stored in
 *   the in-memory `reviewFindings` and re-injected on the next turn via
 *   `before_agent_start` as a system-prompt suffix.
 * - `review`: MED+ with `>=2` files touched OR `>=5` user turns. BLOCKS
 *   the next MED+ write until findings are resolved. Resolved by calling
 *   `risk_progress action=verification` with `passed=true` (or by manually
 *   recording a `diff_summary` for HIGH tasks; see canClaimDone()).
 */

import type { Model } from "@earendil-works/pi-ai";
import { completeSimple } from "@earendil-works/pi-ai";
import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import type { ChangeSet } from "./session-changeset.ts";
import { buildChangeSetPrompt } from "./session-changeset.ts";
import type { RiskStateSnapshot } from "./risk-types.ts";

export interface ReviewFinding {
	readonly id: string;
	readonly kind: "simplify" | "review";
	readonly path: string;
	readonly severity: "low" | "med" | "high";
	readonly message: string;
	readonly turnId: string;
}

export interface ReviewVerdict {
	readonly simplify: ReviewFinding[];
	readonly review: ReviewFinding[];
	readonly ranAt: string;
	readonly skippedReason?: string;
}

const SIMPLIFY_SYSTEM =
	"You are a code quality reviewer. The user gave you the EXACT session-scoped change-set. Do not infer changes from anything else. Output JSON only: {\"findings\":[{\"path\":...,\"severity\":\"low|med|high\",\"message\":...}]}. If the change is clean, output {\"findings\":[]}.";

const REVIEW_SYSTEM =
	"You are a maintainer-style reviewer. The user gave you the EXACT session-scoped change-set. Verify correctness, security, performance, operability, maintainability. Output JSON only: {\"findings\":[{\"path\":...,\"severity\":\"low|med|high\",\"message\":...}]}.";

async function callModel(
	ctx: ExtensionContext,
	systemPrompt: string,
	userPrompt: string,
): Promise<{ findings: Array<{ path: string; severity: "low" | "med" | "high"; message: string }> } | null> {
	const model = ctx.model;
	if (!model) return null;
	const apiKey = await ctx.modelRegistry.getApiKeyForProvider(model.provider);
	if (!apiKey) return null;
	try {
		const result = await completeSimple(model, {
			systemPrompt,
			messages: [{ role: "user" as const, content: [{ type: "text" as const, text: userPrompt }], timestamp: Date.now() }],
		}, { apiKey, maxTokens: 4096 });
		let text = "";
		for (const block of result.content) {
			if ((block as { type?: string }).type === "text") {
				text += (block as { text?: string }).text ?? "";
			}
		}
		const jsonMatch = text.match(/\{[\s\S]*\}/);
		if (!jsonMatch) return null;
		return JSON.parse(jsonMatch[0]);
	} catch {
		return null;
	}
}

export async function runReviewPass(
	ctx: ExtensionContext,
	changeSet: ChangeSet,
	snap: RiskStateSnapshot,
	turnId: string,
): Promise<ReviewVerdict> {
	const ranAt = new Date().toISOString();
	if (snap.assessment.tier === "LOW") {
		return { simplify: [], review: [], ranAt, skippedReason: "tier=LOW" };
	}

	if (changeSet.entries.length === 0) {
		return { simplify: [], review: [], ranAt, skippedReason: "no-session-changes" };
	}

	const turnCount = (() => {
		// ReadonlySessionManager exposes getBranch(): SessionEntry[] but not a
		// getUserMessages() helper. Count user-typed message entries on the
		// branch directly. getBranch() may be absent in non-TUI contexts;
		// fall back to 0 turns.
		const sm = (ctx as { sessionManager?: { getBranch?: () => unknown[] } }).sessionManager;
		if (!sm || typeof sm.getBranch !== "function") return 0;
		const branch = sm.getBranch();
		if (!Array.isArray(branch)) return 0;
		return branch.filter((e) => {
			const entry = e as { type?: string; message?: { role?: string } };
			return entry?.type === "message" && entry.message?.role === "user";
		}).length;
	})();

	const userPrompt = buildChangeSetPrompt(changeSet);

	const simplify = await callModel(ctx, SIMPLIFY_SYSTEM, userPrompt);
	let simplifyCounter = 0;
	const simplifyFindings: ReviewFinding[] = (simplify?.findings ?? []).map((f) => ({
		id: `S${++simplifyCounter}`,
		kind: "simplify",
		path: f.path,
		severity: f.severity,
		message: f.message,
		turnId,
	}));

	const fileCount = changeSet.distinctPaths.length;
	const reviewEligible = fileCount >= 2 || turnCount >= 5;
	let reviewFindings: ReviewFinding[] = [];
	if (reviewEligible) {
		const review = await callModel(ctx, REVIEW_SYSTEM, userPrompt);
		let reviewCounter = 0;
		reviewFindings = (review?.findings ?? []).map((f) => ({
			id: `R${++reviewCounter}`,
			kind: "review",
			path: f.path,
			severity: f.severity,
			message: f.message,
			turnId,
		}));
	}

	return {
		simplify: simplifyFindings,
		review: reviewFindings,
		ranAt,
		skippedReason: reviewEligible ? undefined : `turnCount=${turnCount} fileCount=${fileCount} (<2 files and <5 turns)`,
	};
}
