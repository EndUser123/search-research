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
 *
 * Failure surfacing: a model/parse failure is reported as an explicit
 * `skippedReason: "review-failed: ..."` so the UI says "review skipped"
 * rather than silently reporting an unreviewed change-set as clean. The
 * prior `catch { return null }` swallowed truncated-JSON / throw / no-model
 * identically, which made the first multi-file refactor look clean when it
 * was never actually reviewed. `no-model` stays silent (nothing the user
 * can fix mid-session); `model-error` and `parse-failed` surface.
 */

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

/**
 * The actual model call, swappable for tests. Production wraps `completeSimple`.
 * Returns raw model text; the JSON-parse + failure-classification logic lives
 * in `callModel`. Tests inject a fn that returns truncated JSON or throws to
 * exercise the failure-propagation path — without this seam that path is
 * untestable (`completeSimple` is a direct import that hits the network).
 */
export type ReviewCallFn = (
	model: { provider: string },
	userPrompt: string,
	systemPrompt: string,
	maxTokens: number,
	apiKey: string,
) => Promise<string>;

const defaultCallFn: ReviewCallFn = async (model, userPrompt, systemPrompt, maxTokens, apiKey) => {
	const result = await completeSimple(model, {
		systemPrompt,
		messages: [{ role: "user" as const, content: [{ type: "text" as const, text: userPrompt }], timestamp: Date.now() }],
	}, { apiKey, maxTokens });
	let text = "";
	for (const block of result.content) {
		if ((block as { type?: string }).type === "text") {
			text += (block as { text?: string }).text ?? "";
		}
	}
	return text;
};

type CallResult =
	| { ok: true; findings: Array<{ path: string; severity: "low" | "med" | "high"; message: string }> }
	| { ok: false; reason: "no-model" | "model-error" | "parse-failed"; detail?: string };

async function callModel(
	ctx: ExtensionContext,
	systemPrompt: string,
	userPrompt: string,
	maxTokens: number,
	callFn: ReviewCallFn = defaultCallFn,
): Promise<CallResult> {
	const model = ctx.model;
	if (!model) return { ok: false, reason: "no-model" };
	const apiKey = await ctx.modelRegistry.getApiKeyForProvider(model.provider);
	if (!apiKey) return { ok: false, reason: "no-model" };
	try {
		const text = await callFn(model, userPrompt, systemPrompt, maxTokens, apiKey);
		const jsonMatch = text.match(/\{[\s\S]*\}/);
		if (!jsonMatch) return { ok: false, reason: "parse-failed", detail: "no JSON object in model output" };
		// Greedy \{[\s\S]*\} on a truncated response matches a dangling fragment;
		// JSON.parse then throws -> caught below as parse-failed (the message is
		// "Unexpected token" or similar). Both paths now surface instead of null.
		const parsed = JSON.parse(jsonMatch[0]);
		return { ok: true, findings: parsed.findings ?? [] };
	} catch (err) {
		// Distinguish a JSON parse throw from a model/network throw by message shape.
		const msg = err instanceof Error ? err.message : String(err);
		const isParseError = msg.startsWith("Unexpected") || msg.includes("is not valid JSON") || msg.includes("JSON");
		return { ok: false, reason: isParseError ? "parse-failed" : "model-error", detail: msg };
	}
}

export async function runReviewPass(
	ctx: ExtensionContext,
	changeSet: ChangeSet,
	snap: RiskStateSnapshot,
	turnId: string,
	callFn: ReviewCallFn = defaultCallFn,
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
	// Scale maxTokens to the change-set size so the prompt itself doesn't eat
	// the entire budget and force the findings JSON to truncate (which
	// previously surfaced as a silent "clean" verdict via a swallowed throw).
	// Floor 4096, cap 16384 — findings are terse JSON, this is headroom only.
	const maxTokens = Math.min(16384, Math.max(4096, userPrompt.length));

	const simplify = await callModel(ctx, SIMPLIFY_SYSTEM, userPrompt, maxTokens, callFn);
	// Surface model/parse failures explicitly. `no-model` stays silent (nothing
	// the user can fix mid-session, preserves prior behavior + existing tests).
	if (!simplify.ok && simplify.reason !== "no-model") {
		return {
			simplify: [],
			review: [],
			ranAt,
			skippedReason: `review-failed: ${simplify.reason}${simplify.detail ? ` (${simplify.detail.slice(0, 120)})` : ""}`,
		};
	}
	let simplifyCounter = 0;
	const simplifyFindings: ReviewFinding[] = (simplify.ok ? simplify.findings : []).map((f) => ({
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
	let reviewSkipReason: string | undefined;
	if (reviewEligible) {
		const review = await callModel(ctx, REVIEW_SYSTEM, userPrompt, maxTokens, callFn);
		if (!review.ok && review.reason !== "no-model") {
			// Review pass failed but simplify succeeded: report the simplify
			// findings we have plus the failure reason so the user knows the
			// deeper review didn't complete.
			reviewSkipReason = `review-failed: ${review.reason}${review.detail ? ` (${review.detail.slice(0, 120)})` : ""}`;
		} else {
			let reviewCounter = 0;
			reviewFindings = (review.ok ? review.findings : []).map((f) => ({
				id: `R${++reviewCounter}`,
				kind: "review",
				path: f.path,
				severity: f.severity,
				message: f.message,
				turnId,
			}));
		}
	}

	return {
		simplify: simplifyFindings,
		review: reviewFindings,
		ranAt,
		skippedReason: reviewSkipReason ?? (reviewEligible ? undefined : `turnCount=${turnCount} fileCount=${fileCount} (<2 files and <5 turns)`),
	};
}
