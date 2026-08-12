/**
 * risk-policy-extension — package runtime entrypoint.
 *
 * Wires together: classifier + policy table, in-memory state, UI,
 * commands, tools, JSONL logging, and an in-memory session log ring
 * buffer for /risk-why.
 *
 * Hook mapping vs. the implementation spec:
 *   beforeUserTurn            -> input event (raw prompt, pre-skill/template)
 *   onObservedVerification    -> tool_result for the bash tool
 *   beforeAssistantCompletion -> agent_end (MITIGATION only — see note below)
 *                                + before_agent_start (inject policy reminder)
 *   repo-local config         -> ctx.isProjectTrusted() + read .pi/risk-policy.json
 *
 * NOTE on "prevent false completion": agent_end fires AFTER the assistant
 * message is finalized, so it cannot prevent the model from saying "done"
 * in the current turn. What we do is (a) notify the user that verification
 * is incomplete, and (b) inject a reminder into the next turn's system
 * prompt. This is mitigation, not enforcement. The spec's literal
 * requirement is not achievable through pi's lifecycle hooks.
 */

import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { createHash } from "node:crypto";

/**
 * Extract file paths from a deletion command.
 *
 * Handles: rm <paths>, git rm <paths>, git checkout -- <paths>,
 * git restore -- <paths>, git clean -fd <paths>,
 * Remove-Item <paths> (PowerShell, incl. -Recurse/-Force),
 * del/erase <paths> (cmd), and the PowerShell alias `ri`.
 *
 * Cross-platform: the original Unix-only matcher (rm/git rm/git checkout/
 * git restore) silently missed every Windows/PowerShell deletion, so deleted
 * files kept producing stale review findings. Removing a file via Remove-Item
 * on Windows now tracks the same way `rm` does on Unix.
 *
 * ponytail: simple argument extraction. Ignores flags. Handles quoted args.
 * Does not validate that paths exist — any path-looking argument after the
 * delete verb is treated as potentially deleted. Upgrade path: call
 * fs.existsSync if the runtime supports it.
 */
export function extractDeletionPaths(command: string): string[] {
	// Strip known delete verbs + their flags to get to the path args.
	// "rm -rf src/foo bar/" -> tail = "src/foo bar/"
	// "git rm src/foo.ts" -> tail = "src/foo.ts"
	// "git checkout -- src/foo.ts" -> tail = "src/foo.ts"
	// "git clean -fd src/" -> tail = "src/"
	// "Remove-Item -Recurse -Force foo.ps1" -> tail = "foo.ps1"
	// "del foo.ps1" -> tail = "foo.ps1"
	let tail = command
		.replace(
			/^(?:rm|ri|del|erase|Remove-Item|git\s+(?:rm|checkout|restore|clean))(?:\s+-[A-Za-z]+)*\s*(?:--(?:recursive|dry-run|force))?/i,
			"",
		)
		.replace(/^\s*--\S*/i, "")
		.trimStart();

	// Split on whitespace, strip trailing slashes (dir → "src/", stored as "src" for child matching).
	const paths: string[] = [];
	for (const token of tail.split(/\s+/)) {
		if (!token || token === "--") continue;
		// Remove surrounding quotes.
		const cleaned = token.replace(/^['"]|['"]$/g, "");
		if (!cleaned || cleaned.startsWith("-")) continue;
		// Skip common non-path args that rm/git rm sometimes carry.
		if (/^(.*\/)?\.[a-z]+$/i.test(cleaned)) continue; // e.g. ".gitignore"
		// Normalize: backslash → slash, strip leading ./, collapse leading slashes.
		const normalized = cleaned.replace(/\\/g, "/").replace(/^\.\//, "").replace(/^\/+/, "").replace(/\/+$/, "");
		if (normalized) paths.push(normalized);
	}

	// For directory deletions (rm -r dir/), store both "dir/" and "dir" so that
	// "dir/foo.ts" matches under both forms.
	return paths.flatMap((p) => {
		const noSlash = p.endsWith("/") ? p.slice(0, -1) : p;
		return p.endsWith("/") ? [noSlash, p] : [noSlash];
	});
}

// R12: tiny helper so non-Node runtimes (e.g. Deno workers, Bun edge) where
// process.env access throws don't crash the extension. The check is also
// done once at factory load via the IIFE below, but the helper is used in
// inline checks that fire after that.
function isPiDebugEnabled(): boolean {
	try {
		const v = process.env.PI_DEBUG;
		return v === "1" || v === "true";
	} catch {
		return false;
	}
}

import type { ExtensionAPI, ExtensionContext, ToolResultEvent } from "@earendil-works/pi-coding-agent";
import { isBashToolResult } from "@earendil-works/pi-coding-agent";

import {
	classifyRisk,
	isVerificationCommand,
	mergeConfig,
	DEFAULT_CONFIG,
	type DeepPartial,
} from "./risk-classifier.ts";
import { extractCandidatePaths } from "./path-extractor.ts";
import { extractInstructionSegment } from "./prompt-splitter.ts";
import { POLICY_BY_TIER } from "./risk-policy.ts";
import { RiskStateStore, type StoredFinding } from "./risk-state.ts";
import { getSessionChangeSet } from "./session-changeset.ts";
import { clearRiskUI, showRiskBanner, showRiskWarning } from "./risk-ui.ts";
import { suggestVerifyCommands } from "./verify-defaults.ts";
import { runReviewPass } from "./review-pass.ts";
import { detectWorktree } from "./worktree-detect.ts";
import { registerRiskCommands, type RiskLogEntry } from "./risk-commands.ts";
import { registerRiskTools } from "./risk-tools.ts";
import { appendRiskLog } from "./risk-log.ts";
import { canClaimDone, missingRequirements } from "./verification-state.ts";
import { extractBashExitCode } from "./bash-result.ts";
import { autoRecordPlanIfNeeded, evaluateAutoDiff, buildAutoDiffSummary, buildAutoDiffProbeLog } from "./auto-record.ts";
import type { RiskAssessment, RiskConfig, RiskPolicy, RiskTier } from "./risk-types.ts";

const REPO_CONFIG_NAME = "risk-policy.json";
const MAX_SESSION_LOG = 50;

async function loadRepoConfig(ctx: ExtensionContext): Promise<RiskConfig | null> {
	const path = join(ctx.cwd, ".pi", REPO_CONFIG_NAME);
	try {
		const raw = await readFile(path, "utf8");
		const parsed = JSON.parse(raw) as DeepPartial<RiskConfig>;
		return mergeConfig(DEFAULT_CONFIG, parsed);
	} catch (err) {
		const code = (err as NodeJS.ErrnoException)?.code;
		if (code === "ENOENT") return null;
		const msg = `risk-policy: failed to load ${path} (${err instanceof Error ? err.message : String(err)}), using defaults`;
		if (ctx.hasUI) ctx.ui.notify(msg, "warning");
		if (isPiDebugEnabled()) console.error(msg);
		return null;
	}
}

function buildPolicyReminder(tier: RiskTier, reasons: string[], missing: string[]): string {
	const reasonStr = reasons.length ? `Reasons: ${reasons.join("; ")}.` : "";
	if (tier === "LOW") {
		return `[risk-policy] Active tier: LOW. ${reasonStr} Fast path.`;
	}
	if (missing.length === 0) {
		return `[risk-policy] Active tier: ${tier}. ${reasonStr} All verification requirements met.`;
	}
	return `[risk-policy] Active tier: ${tier}. ${reasonStr} Still required before claiming done: ${missing.join(", ")}.`;
}

/**
 * Best-effort extraction of a bash command's exit code from a tool_result
 * event. See extensions/bash-result.ts for behavior. (The function lives
 * in its own module so it can be unit-tested without an extension
 * runtime.)
 */

export default function riskPolicyExtension(pi: ExtensionAPI) {
	const store = new RiskStateStore();
	let config: RiskConfig = DEFAULT_CONFIG;

	// R18: hoist debug-only computation to the top so it is computed once
	// before any handler is registered. The IIFE pattern protects against
	// process.env being absent in non-Node runtimes.
	const debugProbesEnabled = isPiDebugEnabled();

	// R11: named handler factories so the registered handlers have stable
	// names for stack traces, logs, and inspection. Each closure captures
	// only what it needs from the outer scope.
	async function agentEndAutoDiffHandler(_event: unknown, ctx: ExtensionContext): Promise<void> {
		if (debugProbesEnabled) {
			await safeProbeLog({ event: "hook_seen", cwd: ctx.cwd, hook: "agent_end", at: new Date().toISOString(), phase: "auto_diff" });
		}
		const snap = store.getSnapshot();
		if (!snap) return;

		// Structural auto-diff summary: at agent_end, for MED/HIGH, if the
		// session ledger has changes and diffSummarized is false, record a
		// machine summary. Never reads git diff. Never crashes on errors.
		const tier = snap.assessment.tier;
		const diffSummarized = snap.verification.diffSummarized;

		// Derive probe inputs once. The changeSet is cached for the record step
		// so we never call getSessionChangeSet(ctx) twice for the same turn.
		let changeSetEntryCount = 0;
		let hasSessionManager = false;
		let hasBranch = false;
		let changeSet: ReturnType<typeof getSessionChangeSet> | undefined;
		let probeError: string | undefined;
		try {
			const sm = (ctx as { sessionManager?: unknown }).sessionManager;
			hasSessionManager = sm !== undefined && sm !== null;
			if (hasSessionManager) {
				const branch = typeof (sm as { getBranch?: () => unknown }).getBranch === "function"
					? (sm as { getBranch: () => unknown }).getBranch()
					: null;
				hasBranch = Array.isArray(branch);
				if (hasBranch) {
					changeSet = getSessionChangeSet(ctx);
					changeSetEntryCount = changeSet.entries ? changeSet.entries.length : 0;
				}
			}
		} catch (err) {
			probeError = err instanceof Error ? err.message : String(err);
		}

		const probeInput = {
			tier,
			planned: snap.verification.planned,
			diffSummarized,
			hasSessionManager,
			hasBranch,
			changeSetEntryCount,
			verificationRan: snap.verification.verificationRan,
			verificationPassed: snap.verification.verificationPassed,
			lastVerificationExitCode: snap.verification.lastVerificationExitCode,
		};
		const verdict = evaluateAutoDiff(probeInput);
		const willRecord = verdict.willRecord;
		const skipReason = probeError ? `skip_error:${probeError}` : verdict.skipReason;
		if (debugProbesEnabled) {
			await safeProbeLog(buildAutoDiffProbeLog({
				cwd: ctx.cwd,
				tier,
				planned: snap.verification.planned,
				verificationRan: snap.verification.verificationRan,
				verificationPassed: snap.verification.verificationPassed,
				diffSummarized,
				hasSessionManager,
				hasBranch,
				changeSetEntryCount,
				willRecord,
				...(skipReason ? { skipReason } : {}),
			}));
		}
		if (willRecord && changeSet) {
			try {
				const fileList = changeSet.entries.map((e) => e.path).join(", ");
				const summary = buildAutoDiffSummary({ ...probeInput, fileList });
				store.updateVerification({ diffSummarized: true, diffSummary: summary });
				await logEvent({ event: "auto_diff_summary_recorded", cwd: ctx.cwd, fileCount: changeSet.entries.length });
			} catch (err) {
				// R1: never let a malformed record step crash the hook. Log and move on.
				await logEvent({
					event: "auto_diff_summary_failed",
					cwd: ctx.cwd,
					details: [err instanceof Error ? err.message : String(err)],
				});
			}
		}

		// Re-read snap after potential auto-record above.
		const updated = store.getSnapshot();
		if (!updated) return;
		const unaddressed = store.getUnaddressedHigh();
		if (canClaimDone(updated.assessment.tier, updated.verification) && unaddressed.length === 0) return;

		const missing = missingRequirements(updated.assessment.tier, updated.verification);
		const reviewBlock = unaddressed.length > 0
			? ` [risk-policy] ${unaddressed.length} unaddressed high-severity review finding(s): ${unaddressed.map((f) => `${f.id} ${f.path}: ${f.message}`).join(" | ")}. Record disposition via risk_progress action=disposition finding=<id> status=addressed|dismissed_with_reason|accepted_as_followup.`
			: "";
		const editedPaths = lastCandidatePaths.length > 0
			? lastCandidatePaths.filter((p) => /\.[a-z0-9]+$/i.test(p))
			: (snap?.assessment?.candidatePaths ?? []).filter((p) => /\.[a-z0-9]+$/i.test(p));
		const suggestedCommands = new Set<string>();
		for (const p of editedPaths) {
			const dot = p.lastIndexOf(".");
			if (dot < 0) continue;
			const ext = p.slice(dot);
			const cmds = suggestVerifyCommands(ext);
			if (cmds) for (const c of cmds) suggestedCommands.add(c);
		}
		const verifyHint = suggestedCommands.size > 0
			? ` Suggested verify commands: ${[...suggestedCommands].join(" | ")}`
			: "";
		const message = `[risk-policy] BLOCKED: ${updated.assessment.tier} cannot claim done. Missing: ${missing.join(", ")}.${verifyHint}${reviewBlock} Record via risk_progress action=verification.`;
		await showRiskWarning(ctx, message);
		await logEvent({
			event: "verification_block",
			cwd: ctx.cwd,
			tier: updated.assessment.tier,
			missing,
		});
	}

	// Last classification inputs, so override/reset can re-tier without
	// losing the candidate paths or resetting verification.
	let lastPrompt = "";
	let lastCandidatePaths: string[] = [];

	// In-memory ring buffer of recent log entries for /risk-why.
	const sessionLog: RiskLogEntry[] = [];

	const logEvent = async (entry: Record<string, unknown>): Promise<void> => {
		const record = { timestamp: new Date().toISOString(), ...entry } as RiskLogEntry;
		sessionLog.push(record);
		if (sessionLog.length > MAX_SESSION_LOG) sessionLog.shift();
		await appendRiskLog(record);
	};

	// R3: probe logs are diagnostic-only and must never crash the hook.
	// Wrap each probe log so a logging failure (full disk, bad permissions,
	// hash crash) cannot break auto-verification or auto-diff.
	const safeProbeLog = async (entry: Record<string, unknown>): Promise<void> => {
		try {
			await logEvent(entry);
		} catch {
			// probe logs are advisory — swallow.
		}
	};

	const publish = async (
		ctx: ExtensionContext,
		assessment: RiskAssessment,
		policy: RiskPolicy,
	): Promise<void> => {
		store.setAssessment(assessment, policy);
		// Structural auto-plan: the moment the gate activates MED/HIGH, record
		// a basic machine plan. No model call. Doesn't overwrite an explicit
		// user/model plan if one already exists.
		const snap = store.getSnapshot();
		if (snap) {
			const plan = autoRecordPlanIfNeeded(snap.verification, assessment);
			if (plan.changed) {
				store.updateVerification({ planned: true, planText: plan.next.planText, planSource: "auto" });
				await logEvent({ event: "auto_plan_recorded", cwd: ctx.cwd, tier: assessment.tier });
			}
		}
		await showRiskBanner(ctx, assessment, policy);
	};

	const getPolicy = (tier: RiskTier): RiskPolicy => POLICY_BY_TIER[tier];

	// R16: cap the stored prompt so an unbounded user message can't bloat
	// the in-memory store or the reclassify payload. 2000 chars matches
	// buildChangeSetPrompt's truncation budget.
	const MAX_PROMPT_CHARS = 2000;

	/** Classify a new top-level user task. Resets verification state. */
	const classifyNewTask = async (ctx: ExtensionContext, prompt: string): Promise<void> => {
		const capped = prompt.length > MAX_PROMPT_CHARS
			? `${prompt.slice(0, MAX_PROMPT_CHARS)}\n... [truncated ${prompt.length - MAX_PROMPT_CHARS} chars]`
			: prompt;
		lastPrompt = capped;
		lastCandidatePaths = extractCandidatePaths(capped);
		store.setLastPrompt(capped);
		store.resetVerification();
		// Scan only the user's actual instruction for production keywords.
		// Pasted context (chat transcripts, file dumps) goes into lastPrompt
		// and candidatePaths but not into input.prompt — the path-extractor
		// still sees the full text by design, but the keyword scan targets
		// the intent segment so production mentions in pasted context don't
		// false-positive the gate. Falls back to the full prompt when the
		// instruction segment is empty (e.g., a code-only paste).
		const instructionSegment = extractInstructionSegment(prompt) || prompt;
		const assessment = classifyRisk({
			prompt: instructionSegment,
			cwd: ctx.cwd,
			candidatePaths: lastCandidatePaths,
			proposedCommands: [],
			config,
			overrideTier: store.getOverride(),
		});
		await publish(ctx, assessment, getPolicy(assessment.tier));
		await logEvent({
			event: "classified",
			cwd: ctx.cwd,
			tier: assessment.tier,
			reasons: assessment.reasons,
			matchedRules: assessment.matchedRules,
			candidatePaths: assessment.candidatePaths,
			proposedCommands: assessment.proposedCommands,
			override: assessment.overridden,
			verification: store.getSnapshot()?.verification,
		});
	};

	/** Re-tier the current task (override changed). Does NOT reset verification. */
	const reclassifyCurrent = async (ctx: ExtensionContext): Promise<void> => {
		const assessment = classifyRisk({
			prompt: store.getLastPrompt(),
			cwd: ctx.cwd,
			candidatePaths: lastCandidatePaths,
			proposedCommands: [],
			config,
			overrideTier: store.getOverride(),
		});
		await publish(ctx, assessment, getPolicy(assessment.tier));
		await logEvent({
			event: store.getOverride() ? "override" : "classified",
			cwd: ctx.cwd,
			tier: assessment.tier,
			reasons: assessment.reasons,
			matchedRules: assessment.matchedRules,
			override: assessment.overridden,
		});
	};

	pi.on("session_start", async (_event, ctx) => {
		store.clearDeletedPaths();
		if (debugProbesEnabled) {
			await safeProbeLog({ event: "hook_seen", cwd: ctx.cwd, hook: "session_start", at: new Date().toISOString() });
		}
		store.setWorktree(detectWorktree(ctx.cwd));

		if (ctx.isProjectTrusted()) {
			const repo = await loadRepoConfig(ctx);
			if (repo) {
				config = repo;
				if (ctx.hasUI) ctx.ui.notify("risk-policy: loaded repo-local config", "info");
			}
		} else if (ctx.hasUI) {
			ctx.ui.notify("risk-policy: project not trusted, using default config", "info");
		}

		registerRiskCommands(
			pi,
			store,
			(ctx) => reclassifyCurrent(ctx),
			() => [...sessionLog],
		);
		registerRiskTools(pi, store, () => config, () => lastPrompt, ctx);

		await logEvent({
			event: "session_start",
			cwd: ctx.cwd,
			configSource: ctx.isProjectTrusted()
				? config === DEFAULT_CONFIG
					? "default"
					: "repo+default"
				: "default",
		});
	});

	// Spec hook: beforeUserTurn. The `input` event fires for the raw prompt.
	pi.on("input", async (event, ctx) => {
		if (debugProbesEnabled) {
			await safeProbeLog({
				event: "hook_seen",
				cwd: ctx.cwd,
				hook: "input",
				at: new Date().toISOString(),
				source: event.source,
				promptPreview: (event.text ?? "").slice(0, 80),
			});
		}
		if (event.source === "extension") return;
		const text = (event.text ?? "").trim();
		if (!text) return;
		// Slash commands are handled by pi before the agent loop; skip them.
		if (text.startsWith("/")) return;
		try {
			await classifyNewTask(ctx, text);
		} catch (err) {
			if (ctx.hasUI) ctx.ui.notify(`risk-policy: classify failed (${(err as Error).message})`, "warning");
		}
		return;
	});

	// Inject unaddressed review findings into the LLM message array via the
	// `context` event. Per the brief's correction: "inject findings via the
	// context event (rewrites the message array before the next LLM call),
	// NOT by instructing the model to look." A synthetic user message
	// carries the findings; the model sees them without being told to look.
	//
	// Dedup: the context event fires before every LLM call (possibly multiple
	// times per turn during tool-call loops). We only inject when the findings
	// fingerprint changes — same findings + same dispositions = skip. This
	// prevents context flooding (inject-every-turn DEFECT).
	let lastInjectedFindingsKey = "";
	const findingsKey = (findings: readonly { id: string; disposition?: string; message?: string; severity?: string }[]): string =>
		findings.map((f) => {
			// R5: hash the message so a long message doesn't bloat the dedup key.
			const msgHash = f.message ? createHash("sha256").update(f.message).digest("hex").slice(0, 8) : "";
			return `${f.id}:${f.severity ?? "?"}:${f.disposition ?? "?"}:${msgHash}`;
		}).join("|");

	pi.on("context", async (event) => {
		const findings = store.getFindings();
		if (findings.length === 0) {
			lastInjectedFindingsKey = "";
			return;
		}
		const key = findingsKey(findings);
		if (key === lastInjectedFindingsKey) return; // already injected for this state
		lastInjectedFindingsKey = key;

		const lines: string[] = [
			"[risk-policy] Review findings pending disposition. Address each with `risk_progress action=disposition finding=<id> status=<addressed|dismissed_with_reason|accepted_as_followup> [note=<reason>]`. High-severity review findings BLOCK completion until disposed.",
		];
		for (const f of findings) {
			const disp = f.disposition ? ` [${f.disposition}${f.dispositionNote ? `: ${f.dispositionNote}` : ""}]` : " [unaddressed]";
			lines.push(`  - ${f.id} (${f.kind}/${f.severity}) ${f.path}: ${f.message}${disp}`);
		}
		const synthetic: { role: "user"; content: string; timestamp: number } = {
			role: "user",
			content: lines.join("\n"),
			timestamp: Date.now(),
		};
		return { messages: [...event.messages, synthetic] };
	});

	// Spec hook: onObservedVerification. Inspect bash tool results.
	pi.on("tool_result", async (event: ToolResultEvent, ctx: ExtensionContext) => {
		// Audit: hook_seen fires before any guard. Distinguishes "handler ran"
		// R18: debug-only vars are computed only when the debug gate is open,
		// so production runs don't pay for the parse or hash.
		if (debugProbesEnabled) {
			const _auditInput = event.input;
			const _auditInputObj = (_auditInput && typeof _auditInput === "object" ? _auditInput : {}) as Record<string, unknown>;
			const _auditCommand = typeof _auditInputObj.command === "string" ? _auditInputObj.command : "";
			await safeProbeLog({
				event: "hook_seen",
				cwd: ctx.cwd,
				hook: "tool_result",
				at: new Date().toISOString(),
				toolName: event.toolName,
				hasCommand: _auditCommand.length > 0,
				hasExitCode: event.details?.exitCode !== undefined,
			});
		}
		// R18: probe-specific vars are computed only when the debug gate is open,
		// so production runs don't pay for the hash.
		if (debugProbesEnabled) {
			const probeInput = event.input;
			const probeInputObj = (probeInput && typeof probeInput === "object" ? probeInput : {}) as Record<string, unknown>;
			const probeCommand = typeof probeInputObj.command === "string" ? probeInputObj.command : "";
			const probeDetails = event.details;
			// R2: never log raw command text. Hash the command so distinct commands
			// stay distinguishable for debugging without leaking file paths or
			// env values to the JSONL audit log.
			const commandFingerprint = probeCommand.length > 0
				? createHash("sha256").update(probeCommand).digest("hex").slice(0, 12)
				: "";
			await safeProbeLog({
				event: "tool_result_seen",
				cwd: ctx.cwd,
				commandFingerprint,
				detailsType: probeDetails === undefined ? "undefined" : typeof probeDetails,
				isBashToolResult: isBashToolResult(event),
				isVerificationCommand: probeCommand.length > 0 && isVerificationCommand(probeCommand, config),
			});
		}
		if (!isBashToolResult(event)) return;
		const command = (event.input?.command as string | undefined) ?? "";
		if (!command) return;

		// Detect file deletions across shells: Unix (rm/git rm/git checkout/git
		// restore/git clean) and Windows (Remove-Item, del, erase, the `ri` alias).
		// Deleted paths are excluded from findings in the next agent_end merge so
		// that findings for a deleted file don't persist forever without a
		// disposition. Windows support matters: a Remove-Item deletion that isn't
		// matched here leaves stale findings (regression seen this session).
		const isDeleteCommand = /^\s*rm\b/i.test(command)
			|| /^\s*(?:ri|del|erase|Remove-Item)\b/i.test(command)
			|| /^\s*git\s+(?:rm|checkout|restore|clean)\b/i.test(command);
		if (isDeleteCommand && !event.isError) {
			const deleted = extractDeletionPaths(command);
			for (const p of deleted) {
				store.addDeletedPath(p);
			}
			if (deleted.length > 0) {
				await logEvent({ event: "deleted_paths_detected", cwd: ctx.cwd, paths: deleted });
			}
		}

		if (!isVerificationCommand(command, config)) return;

		try {
			const exitCode = extractBashExitCode(event);
			const isError = event.isError === true;
			// extractBashExitCode returns 0 on success (isError===false) without a
			// numeric code in the payload; only a parsed "exited with code N" is a
			// real numeric exit. Mark inferred honestly for auditability.
			const hasNumericExit = isError && (() => {
				const c = event.content;
				if (!Array.isArray(c)) return false;
				return /exited with code (-?\d+)/.test(c.map((x) => (x && typeof x === "object" && "type" in x && x.type === "text" ? String(x.text) : "")).join(" "));
			})();
			store.updateVerification({
				verificationRan: true,
				verificationPassed: exitCode === 0,
				lastVerificationCommand: command,
				lastVerificationExitCode: exitCode,
				verificationSource: "auto",
			});
			await logEvent({
				event: "verification_update",
				cwd: ctx.cwd,
				exitCode,
				exitCodeInferred: !hasNumericExit,
				passed: exitCode === 0,
			});
		} catch (err) {
			// R3: never let a malformed bash result crash the hook. Log and move on.
			await logEvent({
				event: "auto_verification_failed",
				cwd: ctx.cwd,
				command,
				details: [err instanceof Error ? err.message : String(err)],
			});
		}
	});

	// Spec hook: beforeAssistantCompletion (mitigation — see file header).
	pi.on("tool_call", async (event, ctx) => {
		// R18: debug-only vars are computed only when the debug gate is open.
		if (debugProbesEnabled) {
			const _tcInput = (event as { input?: unknown }).input;
			const _tcInputObj = (_tcInput && typeof _tcInput === "object" ? _tcInput : {}) as Record<string, unknown>;
			const _tcPath = typeof _tcInputObj.path === "string" ? _tcInputObj.path : "";
			await safeProbeLog({
				event: "hook_seen",
				cwd: ctx.cwd,
				hook: "tool_call",
				at: new Date().toISOString(),
				toolName: (event as { toolName?: string }).toolName ?? "?",
				pathPreview: _tcPath.slice(0, 80),
			});
		}
		const snap = store.getSnapshot();
		if (!snap) return;
		if (snap.assessment.tier === "LOW") return;
		const toolName = (event as { toolName?: string }).toolName ?? "";
		const input = (event as { input?: unknown }).input;
		const cmd = typeof input === "object" && input !== null && "command" in input
			? String((input as { command?: unknown }).command ?? "")
			: "";

		const isWriteLike = toolName === "write" || toolName === "edit" ||
			(toolName === "bash" && /\b(rm|mv|cp|mkdir|touch|git\s+commit|git\s+push|npm\s+(i|install)|pnpm\s+add|yarn\s+add|sudo)\b/.test(cmd));
		if (!isWriteLike) return;
		if (snap.verification.planned) {
			// HIGH requires manual approval for write/apply actions, even with a plan.
			if (snap.assessment.tier === "HIGH" && !snap.verification.manualApprovalRecorded) {
				await logEvent({
					event: "write_gate_block",
					cwd: ctx.cwd,
					tier: snap.assessment.tier,
					toolName,
					command: cmd || undefined,
					reason: "manual_approval_required",
				});
				return { block: true, reason: `${snap.assessment.tier} risk: record manual approval via /risk-approve before editing.` };
			}
			return;
		}
		await logEvent({
			event: "write_gate_block",
			cwd: ctx.cwd,
			tier: snap.assessment.tier,
			toolName,
			command: cmd || undefined,
		});
		return { block: true, reason: `${snap.assessment.tier} risk: record a plan via risk_progress before editing.` };
	});

	// Review/simplify pass: runs on every agent_end, MED+ only. Sources input
	// from the in-memory SessionChangeSet — NEVER from `git diff`. Bypasses
	// the pi-simplify/pi-review packages' hard-coded git step.
	pi.on("agent_end", async (_event, ctx) => {
		if (debugProbesEnabled) {
			await safeProbeLog({ event: "hook_seen", cwd: ctx.cwd, hook: "agent_end", at: new Date().toISOString(), phase: "review" });
		}
		const snap = store.getSnapshot();
		if (!snap) return;
		// R1 invariant: the caller must guard on tier !== LOW before registering this
		// handler. This assert documents the invariant and crashes loudly if violated
		// rather than silently no-oping — a removed guard is a latent bug.
		if (snap.assessment.tier === "LOW") {
			await logEvent({ event: "invariant_violation", cwd: ctx.cwd, hook: "agent_end", detail: "review handler reached with LOW tier" });
			return;
		}
		const changeSet = getSessionChangeSet(ctx);
		const verdict = await runReviewPass(ctx, changeSet, snap, snap.timestamp);
		const newFindings = [
			...verdict.simplify.map((f) => ({ ...f, storedAt: verdict.ranAt })),
			...verdict.review.map((f) => ({ ...f, storedAt: verdict.ranAt })),
		];
		// Merge: keep existing (possibly dispositioned) findings, add new ones from this run.
		// Dedup key: path:severity:kind:message. "kind" is included so simplify and review
		// findings on the same content are kept separate. runReviewPass resets its counter
		// each turn, so "S1" in turn 1 and "S1" in turn 2 are different ids for the same
		// finding — using id as the dedup key would never catch cross-turn duplicates.
		const keyOf = (f: StoredFinding) => `${f.path}:${f.severity}:${f.kind}:${f.message}`;
		const existing = store.getFindings();
		const existingKeys = new Set(existing.map(keyOf));
		// ponytail: filter out findings for deleted files so they don't persist forever.
		// Upgrade: validate deletions against the filesystem instead of inferring from
		// command patterns (rm/git rm don't always delete, e.g. "rm --help").
		const toAdd = newFindings.filter(
			(f) => !existingKeys.has(keyOf(f as StoredFinding)) && !store.isDeletedPath(f.path),
		);
		const filteredExisting = existing.filter((f) => !store.isDeletedPath(f.path));
		store.setFindings([...filteredExisting, ...toAdd]);
		// Notify on findings. For skipped runs, only notify on non-standard skip reasons —
		// "no-session-changes" is normal for non-writing turns and would spam every time.
		// "tier=LOW" never reaches this handler (wrapped at the call site above).
		const shouldNotify =
			verdict.simplify.length > 0 ||
			verdict.review.length > 0 ||
			(verdict.skippedReason !== undefined && verdict.skippedReason !== "no-session-changes");
		if (ctx.hasUI && shouldNotify) {
			const note = verdict.skippedReason
				? `Review pass skipped: ${verdict.skippedReason}`
				: `Review pass: simplify=${verdict.simplify.length} review=${verdict.review.length}`;
			ctx.ui.notify(note, verdict.review.some((f) => f.severity === "high") ? "warning" : "info");
		}
	});

	pi.on("agent_end", agentEndAutoDiffHandler);

	pi.on("session_shutdown", async (_event, ctx) => {
		if (debugProbesEnabled) {
			await safeProbeLog({ event: "hook_seen", cwd: ctx.cwd, hook: "session_shutdown", at: new Date().toISOString() });
		}
		// Ponytail: swallow but log so silent cleanup failures stay observable.
		try {
			clearRiskUI(ctx);
		} catch (err) {
			// R6: wrap the failure log in its own try/catch so a logging
			// crash doesn't prevent session_shutdown from completing.
			try {
				await logEvent({
					event: "session_shutdown_cleanup_failed",
					cwd: ctx.cwd,
					details: [err instanceof Error ? err.message : String(err)],
				});
			} catch {
				// Last resort: nothing else to do.
			}
		}
	});
}