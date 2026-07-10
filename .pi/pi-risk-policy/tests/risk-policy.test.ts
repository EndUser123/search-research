import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join as pathJoin } from "node:path";

import {
	classifyRisk,
	DEFAULT_CONFIG,
	isVerificationCommand,
	mergeConfig,
} from "../extensions/risk-classifier.ts";
import { extractCandidatePaths } from "../extensions/path-extractor.ts";
import { extractInstructionSegment } from "../extensions/prompt-splitter.ts";
import {
	canClaimDone,
	createEmptyVerificationState,
	missingRequirements,
} from "../extensions/verification-state.ts";
import { POLICY_BY_TIER } from "../extensions/risk-policy.ts";
import { RiskStateStore, type StoredFinding } from "../extensions/risk-state.ts";
import { extractBashExitCode } from "../extensions/bash-result.ts";
import { autoRecordPlanIfNeeded, evaluateAutoDiff, buildAutoDiffSummary, buildAutoDiffProbeLog } from "../extensions/auto-record.ts";
import { getSessionChangeSet, buildChangeSetPrompt, type ChangeSet } from "../extensions/session-changeset.ts";
import { suggestVerifyCommandsForPath } from "../extensions/verify-defaults.ts";
import riskPolicyExtensionFactory from "../extensions/risk-policy-extension.ts";
import { extractDeletionPaths } from "../extensions/risk-policy-extension.ts";
import { runReviewPass, type ReviewCallFn } from "../extensions/review-pass.ts";
import type { RiskAssessment, RiskStateSnapshot } from "../extensions/risk-types.ts";

// R11: find a registered handler by its function name. Avoids hardcoded
// indices like handlers.get("agent_end")![1] which break when handler
// registration order changes.
function findHandlerByName(
	handlers: Map<string, Array<(...args: unknown[]) => Promise<unknown>>>,
	event: string,
	name: string,
): ((...args: unknown[]) => Promise<unknown>) | undefined {
	const list = handlers.get(event) ?? [];
	for (const h of list) {
		if (h.name === name) return h;
	}
	return undefined;
}

// R12: exception-safe PI_DEBUG capture. The setter runs INSIDE the try
// R12: env assignment is now inside the try block in all 6 test
// occurrences. The helper is no longer needed.
function captureHandlers(): {
	handlers: Map<string, Array<(...args: unknown[]) => Promise<unknown>>>;
	pi: unknown;
} {
	const handlers = new Map<string, Array<(...args: unknown[]) => Promise<unknown>>>();
	const pi = {
		on: (event: string, handler: (...args: unknown[]) => Promise<unknown>) => {
			const list = handlers.get(event) ?? [];
			list.push(handler);
			handlers.set(event, list);
		},
		registerCommand: () => {},
		registerTool: () => {},
		registerShortcut: () => {},
		registerFlag: () => {},
		getFlag: () => undefined,
		sendMessage: () => {},
		sendUserMessage: () => {},
		appendEntry: () => {},
		setSessionName: () => {},
		getSessionName: () => undefined,
		setLabel: () => {},
		exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
		getActiveTools: () => [],
		getAllTools: () => [],
		setActiveTools: () => {},
		refreshTools: () => {},
		getCommands: () => [],
		setModel: async () => false,
		getThinkingLevel: () => "off" as const,
		setThinkingLevel: () => {},
		registerProvider: () => {},
		unregisterProvider: () => {},
		events: { on: () => {}, off: () => {}, emit: () => {} },
	};
	return { handlers, pi };
}

describe("classifyRisk", () => {
	const base = {
		cwd: "/repo",
		candidatePaths: [],
		proposedCommands: [],
		config: DEFAULT_CONFIG,
	};

	it("classifies a docs/ task as LOW", () => {
		const a = classifyRisk({ ...base, prompt: "update the docs", candidatePaths: ["docs/readme.md"] });
		assert.equal(a.tier, "LOW");
		assert.ok(a.reasons.length > 0);
		assert.ok(a.matchedRules.includes("LOW_PATHS_ONLY"));
	});

	it("classifies a tests/ task as LOW", () => {
		const a = classifyRisk({ ...base, prompt: "fix the unit test", candidatePaths: ["tests/auth.test.ts"] });
		assert.equal(a.tier, "LOW");
	});

	it("classifies bare .md paths as LOW", () => {
		const a = classifyRisk({ ...base, prompt: "tidy README", candidatePaths: ["README.md"] });
		assert.equal(a.tier, "LOW");
	});

	it("classifies .md / .markdown / .txt anywhere as LOW", () => {
		const paths = ["~/.pi/agent/AGENTS.md", "CHANGELOG.markdown", "notes.txt"];
		for (const p of paths) {
			const a = classifyRisk({ ...base, prompt: "edit " + p, candidatePaths: [p] });
			assert.equal(a.tier, "LOW", `expected ${p} to classify as LOW`);
			assert.ok(a.matchedRules.includes("LOW_PATHS_ONLY"));
		}
	});

	it("does not let safe-text rule cover code extensions in agent home", () => {
		const a = classifyRisk({
			...base,
			prompt: "edit an extension",
			candidatePaths: ["~/.pi/agent/extensions/extra-search.ts"],
		});
		assert.equal(a.tier, "MED");
	});

	it("classifies a src/ feature change as MED", () => {
		const a = classifyRisk({ ...base, prompt: "add a feature", candidatePaths: ["src/feature.ts"] });
		assert.equal(a.tier, "MED");
		assert.ok(a.matchedRules.includes("DEFAULT_MED"));
		assert.ok(a.reasons.length > 0);
	});

	it("classifies an infra/ path as HIGH", () => {
		const a = classifyRisk({ ...base, prompt: "update infra", candidatePaths: ["infra/main.tf"] });
		assert.equal(a.tier, "HIGH");
		assert.ok(a.matchedRules.includes("HIGH_PATH"));
	});

	it("classifies an auth/ path as HIGH", () => {
		const a = classifyRisk({ ...base, prompt: "auth fix", candidatePaths: ["auth/login.ts"] });
		assert.equal(a.tier, "HIGH");
	});

	it("classifies a .github/workflows path as HIGH", () => {
		const a = classifyRisk({
			...base,
			prompt: "fix CI",
			candidatePaths: [".github/workflows/ci.yml"],
		});
		assert.equal(a.tier, "HIGH");
	});

	it("classifies a high-risk command as HIGH", () => {
		const a = classifyRisk({
			...base,
			prompt: "run something",
			proposedCommands: ["kubectl apply -f deployment.yaml"],
		});
		assert.equal(a.tier, "HIGH");
		assert.ok(a.matchedRules.includes("HIGH_COMMAND"));
	});

	it("classifies a destructive command as HIGH", () => {
		const a = classifyRisk({
			...base,
			prompt: "clean up",
			proposedCommands: ["rm -rf build/"],
		});
		assert.equal(a.tier, "HIGH");
	});

	it("does NOT fire HIGH_COMMAND on a pattern that is a substring of a larger token", () => {
		// Word-boundary regression guard (same bug class as PRODUCTION_KEYWORD):
		// 'kubectlen' contains 'kubectl' but is a different word. Before the fix,
		// unanchored String.includes matched it and escalated a benign command.
		const a = classifyRisk({ ...base, prompt: "x", proposedCommands: ["kubectlen get pods"] });
		assert.notEqual(a.tier, "HIGH");
		assert.ok(!a.matchedRules.includes("HIGH_COMMAND"));
		// Backward-compat: the real token still fires.
		const b = classifyRisk({ ...base, prompt: "x", proposedCommands: ["kubectl get pods"] });
		assert.ok(b.matchedRules.includes("HIGH_COMMAND"));
	});

	it("classifies a prompt with production keyword as HIGH", () => {
		const a = classifyRisk({
			...base,
			prompt: "deploy to production please",
			candidatePaths: ["src/app.ts"],
		});
		assert.equal(a.tier, "HIGH");
		assert.ok(a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});

	it("classifies a prompt with secret/credential keyword as HIGH", () => {
		const a = classifyRisk({ ...base, prompt: "rotate the credential" });
		assert.equal(a.tier, "HIGH");
	});

	it("does NOT fire PRODUCTION_KEYWORD on substring matches inside words", () => {
		// 'reprod' contains 'prod' but is not the word 'prod'. Word-boundary
		// matching must reject this, or any mention of reproducing a bug
		// escalates to HIGH. Regression guard for the unanchored-includes bug.
		const a = classifyRisk({ ...base, prompt: "reproduce the failing test", candidatePaths: ["src/app.ts"] });
		assert.notEqual(a.tier, "HIGH");
		assert.ok(!a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});

	it("still fires PRODUCTION_KEYWORD on a real word-boundary match", () => {
		// Backward-compat: a genuine 'deploy' or 'production' mention still
		// escalates. The word-boundary fix only rejects in-word substrings.
		const a = classifyRisk({ ...base, prompt: "ship the deploy now", candidatePaths: ["src/app.ts"] });
		assert.equal(a.tier, "HIGH");
		assert.ok(a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});

	// Safe-text downgrade: PRODUCTION_KEYWORD alone against a doc target is
	it("manual override returns that tier with overridden=true", () => {
		const a = classifyRisk({
			...base,
			prompt: "anything",
			candidatePaths: ["src/app.ts"],
			overrideTier: "HIGH",
		});
		assert.equal(a.tier, "HIGH");
		assert.equal(a.overridden, true);
		assert.ok(a.matchedRules.includes("MANUAL_OVERRIDE"));
	});

	it("manual override to LOW beats HIGH path signals", () => {
		const a = classifyRisk({
			...base,
			prompt: "deploy",
			candidatePaths: ["infra/main.tf"],
			overrideTier: "LOW",
		});
		assert.equal(a.tier, "LOW");
		assert.equal(a.overridden, true);
	});

	it("returns each reason at most once even when multiple inputs match the same rule", () => {
		const a = classifyRisk({
			...base,
			prompt: "deploy to production",
			candidatePaths: ["infra/x.tf", "infra/y.tf"],
			proposedCommands: ["kubectl apply", "kubectl delete"],
		});
		// HIGH_PATH rule fires once (not per path); HIGH_COMMAND fires once (not per command).
		assert.equal(a.reasons.filter((r) => r === "Touches high-risk path").length, 1);
		assert.equal(a.reasons.filter((r) => r === "Uses high-risk command").length, 1);
		assert.equal(a.matchedRules.filter((r) => r === "HIGH_PATH").length, 1);
		assert.equal(a.matchedRules.filter((r) => r === "HIGH_COMMAND").length, 1);
	});

	it("normalizes windows-style paths in candidatePaths", () => {
		const a = classifyRisk({ ...base, prompt: "edit", candidatePaths: ["infra\\x.tf"] });
		assert.equal(a.tier, "HIGH");
		assert.deepEqual(a.candidatePaths, ["infra/x.tf"]);
	});

	it("classifies a read-only query (no paths, no commands) as LOW", () => {
		const a = classifyRisk({
			...base,
			prompt: "does PI have a thinking mode like Claude Code?",
			candidatePaths: [],
			proposedCommands: [],
		});
		assert.equal(a.tier, "LOW");
		assert.ok(a.matchedRules.includes("QUERY_ONLY"));
		assert.ok(a.reasons.includes("Read-only query"));
	});

	it("never returns empty reasons", () => {
		const a = classifyRisk({ ...base, prompt: "", candidatePaths: [] });
		assert.ok(a.reasons.length > 0);
	it("normalizePath trims whitespace so padded paths match isSafeTextPath", () => {
		// "README.md  " with trailing spaces failed isSafeTextPath (ends with "  ", not ".md").
		// trim() in normalizePath fixes this.
		const a = classifyRisk({ ...base, prompt: "review", candidatePaths: ["  README.md  ", "  docs/notes.txt  "], proposedCommands: [] });
		assert.equal(a.tier, "LOW"); // safe-text extensions, correctly matched after trim
	});
	});
});

describe("extractCandidatePaths", () => {
	it("extracts slash-delimited paths", () => {
		assert.deepEqual(extractCandidatePaths("edit src/foo.ts please"), ["src/foo.ts"]);
	});

	it("extracts dotfile directory paths", () => {
		assert.deepEqual(extractCandidatePaths("see .github/workflows/ci.yml"), [".github/workflows/ci.yml"]);
	});

	it("extracts multiple paths", () => {
		const got = extractCandidatePaths("edit config/prod.yml and docs/readme.md");
		assert.deepEqual(got, ["config/prod.yml", "docs/readme.md"]);
	});

	it("ignores URLs", () => {
		const got = extractCandidatePaths("see https://example.com/foo.ts and bar.py");
		assert.deepEqual(got, ["bar.py"]);
	});

	it("returns empty for plain prose", () => {
		assert.deepEqual(extractCandidatePaths("no paths here"), []);
	});

	it("returns empty for empty input", () => {
		assert.deepEqual(extractCandidatePaths(""), []);
	});

	it("dedupes repeated paths", () => {
		const got = extractCandidatePaths("foo.ts and foo.ts again");
		assert.deepEqual(got, ["foo.ts"]);
	});

	it("does not double-emit bare filename when slash path is present", () => {
		const got = extractCandidatePaths("update src/foo.ts please");
		assert.deepEqual(got, ["src/foo.ts"]);
	});

	it("emits bare filename only when no slash path is present", () => {
		const got = extractCandidatePaths("rename foo.ts to bar.ts");
		assert.deepEqual(got, ["foo.ts", "bar.ts"]);
	});

	it("handles .json, .yml, .yaml, .sh, .tf, .sql extensions", () => {
		const got = extractCandidatePaths("scripts/deploy.sh config/db.sql infra/main.tf data.json schema.yaml");
		assert.ok(got.includes("scripts/deploy.sh"));
		assert.ok(got.includes("config/db.sql"));
		assert.ok(got.includes("infra/main.tf"));
		assert.ok(got.includes("data.json"));
		assert.ok(got.includes("schema.yaml"));
	});

	it("extracts scripting-language extensions the old allowlist missed (.ps1/.php/.lua/.dart)", () => {
		// Regression guard: the extension matcher is a SHAPE check
		// ([a-zA-Z][a-zA-Z0-9]{1,5}), not a hardcoded allowlist. Before this,
		// .ps1/.psm1/.bat/.cmd/.php/.lua/.dart/.ex/.zig/.pl/.r/.clj files were
		// invisible to the classifier — target files in those languages produced
		// no candidate paths, so highPaths/lowPaths silently couldn't match.
		const got = extractCandidatePaths("edit scripts/run.ps1 src/app.php and lib/util.lua");
		assert.ok(got.includes("scripts/run.ps1"), `got ${JSON.stringify(got)}`);
		assert.ok(got.includes("src/app.php"), `got ${JSON.stringify(got)}`);
		assert.ok(got.includes("lib/util.lua"), `got ${JSON.stringify(got)}`);
	});

	it("does not over-match prose with short or digit-first suffixes", () => {
		// "e.g" / "i.e" (1-char ext), "v1.2" (digit-first) must NOT be treated
		// as paths. This is the boundary that stops the denylist from matching
		// ordinary English. If this regresses, every sentence mentioning "e.g."
		// would inject phantom paths.
		assert.deepEqual(extractCandidatePaths("see e.g. the docs, use v1.2 or later"), []);
	});
});

describe("extractInstructionSegment", () => {
	it("returns the full prompt for a single-paragraph input", () => {
		assert.equal(extractInstructionSegment("just one paragraph"), "just one paragraph");
	});

	it("returns the last paragraph when context precedes it", () => {
		const prompt = "context paragraph 1\n\ncontext paragraph 2\n\nthe actual question?";
		assert.equal(extractInstructionSegment(prompt), "the actual question?");
	});

	it("skips trailing empty paragraphs", () => {
		const prompt = "real content\n\n\n\n";
		assert.equal(extractInstructionSegment(prompt), "real content");
	});

	it("skips a trailing code fence and returns the last prose paragraph", () => {
		const prompt = "first paragraph\n\n```\nsome code\n```\n\nwhat do you think?";
		assert.equal(extractInstructionSegment(prompt), "what do you think?");
	});

	it("returns empty string for empty input", () => {
		assert.equal(extractInstructionSegment(""), "");
	});

	it("returns empty string for whitespace-only input", () => {
		assert.equal(extractInstructionSegment("   \n\n   \n  "), "");
	});

	it("returns the last paragraph for a chat-transcript-style paste", () => {
		// Mirrors the session scenario: a long pasted transcript with the
		// user's actual question at the end. The instruction segment is the
		// last paragraph; the keyword scan then sees the question, not the
		// transcript, and the gate's false-positive is avoided.
		const prompt = "Previous LLM: deploy to production now.\n\nPrevious LLM: rotate the credential.\n\nPrevious LLM: yes please\n\nDo you see the principles the chat was exposing?";
		assert.equal(extractInstructionSegment(prompt), "Do you see the principles the chat was exposing?");
	});

	it("a session-paste prompt with phantom paths and a clean instruction classifies as MED, not HIGH", () => {
		// End-to-end: simulates the session's actual scenario through the
		// classifyNewTask split. The pasted transcript contains "production"
		// (PRODUCTION_KEYWORD trigger) and the path-extractor pulls phantom
		// paths from the transcript. With the instruction-segment split, the
		// keyword scan only sees the user's actual question (which has no
		// production keyword) and the gate falls through to MED instead of
		// HIGH.
		const pastedTranscript =
			"Previous LLM said: deploy to production now.\n\n" +
			"Previous LLM said: rotate the credential, then run snapshot_PreCompact.py.\n";
		const userQuestion = "Do you see the principles the chat was exposing?";
		const fullPrompt = pastedTranscript + "\n\n" + userQuestion;
		const instruction = extractInstructionSegment(fullPrompt);
		assert.equal(instruction, userQuestion);
		const phantomPaths = extractCandidatePaths(fullPrompt);
		assert.ok(phantomPaths.length > 0, `path-extractor should pull paths from full prompt; got ${JSON.stringify(phantomPaths)}`);
		const a = classifyRisk({
			cwd: "/repo",
			prompt: instruction,
			candidatePaths: phantomPaths,
			proposedCommands: [],
			config: DEFAULT_CONFIG,
		});
		assert.notEqual(a.tier, "HIGH", `expected MED, got ${a.tier} with reasons ${JSON.stringify(a.reasons)}`);
		assert.ok(!a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});

	it("LIMITATION: instruction-before-context returns the context, not the instruction", () => {
		// Known limitation: the splitter takes the last paragraph. When the
		// user puts their actual question BEFORE the context, the heuristic
		// returns the context. The classifier then scans the context (which
		// may contain production keywords from the chat paste) and may
		// false-positive. The user-side workaround is to put the instruction
		// at the end of the message.
		const prompt = "What do you think about this?\n\nThe previous LLM said: deploy to production now.";
		const instruction = extractInstructionSegment(prompt);
		assert.equal(instruction, "The previous LLM said: deploy to production now.");
	});

	it("LIMITATION: with instruction-before-context, the classifier still HIGH-fires on the context", () => {
		// Documents the end-to-end behavior for the known limitation. If
		// this test regresses (e.g., a future heuristic starts handling
		// instruction-before-context), update or remove this test.
		const prompt = "What do you think about this?\n\nThe previous LLM said: deploy to production now.";
		const instruction = extractInstructionSegment(prompt);
		const a = classifyRisk({
			cwd: "/repo",
			prompt: instruction,
			candidatePaths: [],
			proposedCommands: [],
			config: DEFAULT_CONFIG,
		});
		assert.equal(a.tier, "HIGH");
		assert.ok(a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});
});

describe("canClaimDone", () => {
	it("LOW can always claim done", () => {
		assert.equal(canClaimDone("LOW", createEmptyVerificationState()), true);
	});

	it("MED requires plan + verification ran + passed", () => {
		const v = createEmptyVerificationState();
		assert.equal(canClaimDone("MED", v), false);

		v.planned = true;
		assert.equal(canClaimDone("MED", v), false);

		v.verificationRan = true;
		v.verificationPassed = true;
		assert.equal(canClaimDone("MED", v), true);
	});

	it("MED still blocked when verification ran but failed", () => {
		const v = createEmptyVerificationState();
		v.planned = true;
		v.verificationRan = true;
		v.verificationPassed = false;
		assert.equal(canClaimDone("MED", v), false);
	});

	it("HIGH requires plan, verification, diff summary, manual approval", () => {
		const v = createEmptyVerificationState();
		v.planned = true;
		v.verificationRan = true;
		v.verificationPassed = true;
		v.diffSummarized = true;
		assert.equal(canClaimDone("HIGH", v), false);

		v.manualApprovalRecorded = true;
		assert.equal(canClaimDone("HIGH", v), true);
	});
});

describe("missingRequirements", () => {
	it("LOW has no missing", () => {
		assert.deepEqual(missingRequirements("LOW", createEmptyVerificationState()), []);
	});

	it("MED reports plan and verification until satisfied", () => {
		const v = createEmptyVerificationState();
		const m = missingRequirements("MED", v);
		assert.ok(m.includes("plan"));
		assert.ok(m.includes("verification command run"));
	});

	it("HIGH reports all four missing items at start", () => {
		const m = missingRequirements("HIGH", createEmptyVerificationState());
		assert.ok(m.includes("plan"));
		assert.ok(m.includes("verification command run"));
		assert.ok(m.includes("diff summary"));
		assert.ok(m.includes("manual approval (/risk-approve)"));
	});
});

describe("mergeConfig", () => {
	it("returns base when override is empty", () => {
		assert.deepEqual(mergeConfig(DEFAULT_CONFIG, {}), DEFAULT_CONFIG);
	});

	it("replaces arrays wholesale", () => {
		const merged = mergeConfig(DEFAULT_CONFIG, { highPaths: ["ops/"] });
		assert.deepEqual(merged.highPaths, ["ops/"]);
		assert.deepEqual(merged.lowPaths, DEFAULT_CONFIG.lowPaths);
	});

	it("merges verificationCommands additively", () => {
		const merged = mergeConfig(DEFAULT_CONFIG, {
			verificationCommands: { rust: ["cargo test"] },
		});
		assert.deepEqual(merged.verificationCommands.rust, ["cargo test"]);
		assert.deepEqual(merged.verificationCommands.default, DEFAULT_CONFIG.verificationCommands.default);
	});
});

describe("isVerificationCommand", () => {
	it("matches pytest", () => {
		assert.equal(isVerificationCommand("pytest -q", DEFAULT_CONFIG), true);
	});

	it("matches npm test", () => {
		assert.equal(isVerificationCommand("npm test", DEFAULT_CONFIG), true);
	});

	it("matches npm run lint", () => {
		assert.equal(isVerificationCommand("npm run lint", DEFAULT_CONFIG), true);
	});

	it("matches ruff", () => {
		assert.equal(isVerificationCommand("ruff check .", DEFAULT_CONFIG), true);
	});

	it("matches mypy", () => {
		assert.equal(isVerificationCommand("mypy .", DEFAULT_CONFIG), true);
	});

	it("matches cargo test via custom config", () => {
		const cfg = mergeConfig(DEFAULT_CONFIG, { verificationCommands: { rust: ["cargo test"] } });
		assert.equal(isVerificationCommand("cargo test", cfg), true);
	});

	it("does not match random commands", () => {
		assert.equal(isVerificationCommand("ls -la", DEFAULT_CONFIG), false);
		assert.equal(isVerificationCommand("echo hi", DEFAULT_CONFIG), false);
	});

	it("returns false for empty command", () => {
		assert.equal(isVerificationCommand("", DEFAULT_CONFIG), false);
	});

	it("matches npm test with cd prefix (compound command)", () => {
		// Real-world runs are `cd <repo> && npm test`; the split must reach the
		// `npm test` segment so the first-token check can match.
		assert.equal(isVerificationCommand("cd P:/.pi/pi-risk-policy && npm test", DEFAULT_CONFIG), true);
	});

	it("matches npm run typecheck + npm test in a compound command", () => {
		assert.equal(isVerificationCommand("cd P:/.pi/pi-risk-policy && npm run typecheck && npm test", DEFAULT_CONFIG), true);
	});

	it("matches npx tsc --noEmit with cd prefix", () => {
		assert.equal(isVerificationCommand("cd P:/.pi/pi-risk-policy && npx tsc --noEmit", DEFAULT_CONFIG), true);
	});

	it("does not match cd-only compound segment", () => {
		assert.equal(isVerificationCommand("cd P:/.pi/pi-risk-policy", DEFAULT_CONFIG), false);
	});
});

describe("checklist §2: exact-prompt cases", () => {
	const base = {
		cwd: "/repo",
		proposedCommands: [],
		config: DEFAULT_CONFIG,
	};

	it("Update docs/README.md → LOW", () => {
		const a = classifyRisk({
			...base,
			prompt: "Update docs/README.md",
			candidatePaths: extractCandidatePaths("Update docs/README.md"),
		});
		assert.equal(a.tier, "LOW");
	});

	it("Refactor src/auth.ts → MED", () => {
		// "auth" is intentionally NOT in DEFAULT_CONFIG.productionKeywords.
		// The path is src/auth.ts (which doesn't end with / so does not
		// match the highPaths prefix "auth/"), and the prompt contains no
		// remaining HIGH signal. Classification is MED.
		const a = classifyRisk({
			...base,
			prompt: "Refactor src/auth.ts",
			candidatePaths: extractCandidatePaths("Refactor src/auth.ts"),
		});
		assert.equal(a.tier, "MED");
	});

	it("Modify infra/deploy.yml for production → HIGH", () => {
		const a = classifyRisk({
			...base,
			prompt: "Modify infra/deploy.yml for production",
			candidatePaths: extractCandidatePaths("Modify infra/deploy.yml for production"),
		});
		assert.equal(a.tier, "HIGH");
		// Two signals should fire: HIGH_PATH (infra/) + PRODUCTION_KEYWORD
		assert.ok(a.matchedRules.includes("HIGH_PATH"));
		assert.ok(a.matchedRules.includes("PRODUCTION_KEYWORD"));
	});

	it("re-running the same prompt produces the same tier", () => {
		const prompt = "Refactor src/auth.ts";
		const paths = extractCandidatePaths(prompt);
		const a1 = classifyRisk({ ...base, prompt, candidatePaths: paths });
		const a2 = classifyRisk({ ...base, prompt, candidatePaths: paths });
		assert.equal(a1.tier, a2.tier);
		assert.deepEqual(a1.matchedRules, a2.matchedRules);
	});
});

describe("POLICY_BY_TIER", () => {
	it("LOW does not require plan or verification", () => {
		assert.equal(POLICY_BY_TIER.LOW.requirePlan, false);
		assert.equal(POLICY_BY_TIER.LOW.requireVerification, false);
	});

	it("MED requires plan and verification", () => {
		assert.equal(POLICY_BY_TIER.MED.requirePlan, true);
		assert.equal(POLICY_BY_TIER.MED.requireVerification, true);
		assert.equal(POLICY_BY_TIER.MED.manualApplyOnly, false);
	});

	it("HIGH is manual-apply only and allows infra changes", () => {
		assert.equal(POLICY_BY_TIER.HIGH.manualApplyOnly, true);
		assert.equal(POLICY_BY_TIER.HIGH.allowInfraChanges, true);
	});

	it("all tiers disallow destructive shell", () => {
		assert.equal(POLICY_BY_TIER.LOW.allowDestructiveShell, false);
		assert.equal(POLICY_BY_TIER.MED.allowDestructiveShell, false);
		assert.equal(POLICY_BY_TIER.HIGH.allowDestructiveShell, false);
	});
});

/**
 * Integration tests: drive the state store and classifier through the
 * transitions the event handlers would trigger (input, tool_result,
 * agent_end). These verify the wiring logic without needing a fake
 * ExtensionContext / ExtensionAPI.
 */
describe("integration: full task flow", () => {
	it("MED task: classify -> plan -> verify passes -> canClaimDone", () => {
		const store = new RiskStateStore();
		const config = DEFAULT_CONFIG;

		// Simulate input handler
		const prompt = "fix bug in src/app.ts";
		const paths = extractCandidatePaths(prompt);
		const assessment = classifyRisk({
			prompt,
			cwd: "/repo",
			candidatePaths: paths,
			proposedCommands: [],
			config,
		});
		store.setAssessment(assessment, POLICY_BY_TIER[assessment.tier]);
		store.resetVerification(); // input handler resets for new task

		assert.equal(assessment.tier, "MED");
		assert.equal(canClaimDone("MED", store.getSnapshot()!.verification), false);

		// Simulate risk_progress(action="plan")
		store.updateVerification({ planned: true });
		assert.equal(canClaimDone("MED", store.getSnapshot()!.verification), false);

		// Simulate tool_result: pytest passed (exit 0)
		store.updateVerification({
			verificationRan: true,
			verificationPassed: true,
			lastVerificationCommand: "pytest -q",
			lastVerificationExitCode: 0,
		});
		assert.equal(canClaimDone("MED", store.getSnapshot()!.verification), true);
	});

	it("HIGH task: cannot claim done without manual approval", () => {
		const store = new RiskStateStore();
		const config = DEFAULT_CONFIG;

		const prompt = "deploy to production";
		const paths = extractCandidatePaths(prompt);
		const assessment = classifyRisk({
			prompt,
			cwd: "/repo",
			candidatePaths: paths,
			proposedCommands: [],
			config,
		});
		store.setAssessment(assessment, POLICY_BY_TIER[assessment.tier]);
		store.resetVerification();

		assert.equal(assessment.tier, "HIGH");

		// Plan + verify + diff summary, but no manual approval yet
		store.updateVerification({
			planned: true,
			verificationRan: true,
			verificationPassed: true,
			diffSummarized: true,
		});
		assert.equal(canClaimDone("HIGH", store.getSnapshot()!.verification), false);

		// /risk-approve
		store.updateVerification({ manualApprovalRecorded: true });
		assert.equal(canClaimDone("HIGH", store.getSnapshot()!.verification), true);
	});

	it("MED task: failing verification keeps canClaimDone false", () => {
		const store = new RiskStateStore();
		const a = classifyRisk({
			prompt: "fix bug in src/app.ts",
			cwd: "/repo",
			candidatePaths: ["src/app.ts"],
			proposedCommands: [],
			config: DEFAULT_CONFIG,
		});
		store.setAssessment(a, POLICY_BY_TIER[a.tier]);
		store.updateVerification({ planned: true });
		store.updateVerification({
			verificationRan: true,
			verificationPassed: false,
			lastVerificationExitCode: 1,
		});
		assert.equal(canClaimDone("MED", store.getSnapshot()!.verification), false);
	});
});

describe("integration: override preserves verification", () => {
	it("/risk-override mid-task does NOT reset verification", () => {
		const store = new RiskStateStore();
		const config = DEFAULT_CONFIG;

		// Simulate first task: MED, plan recorded, verification passed
		const prompt1 = "fix bug in src/app.ts";
		const paths1 = extractCandidatePaths(prompt1);
		const a1 = classifyRisk({
			prompt: prompt1,
			cwd: "/repo",
			candidatePaths: paths1,
			proposedCommands: [],
			config,
		});
		store.setAssessment(a1, POLICY_BY_TIER[a1.tier]);
		store.resetVerification();
		store.updateVerification({
			planned: true,
			verificationRan: true,
			verificationPassed: true,
		});
		assert.equal(canClaimDone("MED", store.getSnapshot()!.verification), true);

		// Simulate /risk-override high: should re-tier but keep verification
		store.setOverride("HIGH");
		const reAssess = classifyRisk({
			prompt: prompt1,
			cwd: "/repo",
			candidatePaths: paths1,
			proposedCommands: [],
			config,
			overrideTier: "HIGH",
		});
		store.setAssessment(reAssess, POLICY_BY_TIER[reAssess.tier]);
		// NOTE: reclassifyCurrent must NOT call resetVerification()

		assert.equal(store.getSnapshot()!.assessment.tier, "HIGH");
		assert.equal(store.getSnapshot()!.verification.planned, true, "plan should survive override");
		assert.equal(store.getSnapshot()!.verification.verificationPassed, true, "verification should survive override");
		// HIGH needs diff + manual approval too
		assert.equal(canClaimDone("HIGH", store.getSnapshot()!.verification), false);
	});

	it("/risk-reset clears override without resetting verification", () => {
		const store = new RiskStateStore();
		const a = classifyRisk({
			prompt: "fix bug in src/app.ts",
			cwd: "/repo",
			candidatePaths: ["src/app.ts"],
			proposedCommands: [],
			config: DEFAULT_CONFIG,
		});
		store.setAssessment(a, POLICY_BY_TIER[a.tier]);
		store.setOverride("HIGH");
		store.updateVerification({
			planned: true,
			verificationRan: true,
			verificationPassed: true,
		});

		store.setOverride(null);
		// Verification stays
		assert.equal(store.getSnapshot()!.verification.planned, true);
		assert.equal(store.getSnapshot()!.verification.verificationPassed, true);
	});
});

describe("integration: agent_end mitigation", () => {
	it("fires warning when canClaimDone is false", () => {
		const store = new RiskStateStore();
		const config = DEFAULT_CONFIG;
		const a = classifyRisk({
			prompt: "fix bug in src/app.ts",
			cwd: "/repo",
			candidatePaths: ["src/app.ts"],
			proposedCommands: [],
			config,
		});
		store.setAssessment(a, POLICY_BY_TIER[a.tier]);
		store.resetVerification();

		const snap = store.getSnapshot()!;
		const missing = missingRequirements(snap.assessment.tier, snap.verification);
		assert.ok(missing.length > 0);
		assert.equal(canClaimDone(snap.assessment.tier, snap.verification), false);
	});

	it("does not fire when canClaimDone is true", () => {
		const store = new RiskStateStore();
		const a = classifyRisk({
			prompt: "fix bug in src/app.ts",
			cwd: "/repo",
			candidatePaths: ["src/app.ts"],
			proposedCommands: [],
			config: DEFAULT_CONFIG,
		});
		store.setAssessment(a, POLICY_BY_TIER[a.tier]);
		store.updateVerification({
			planned: true,
			verificationRan: true,
			verificationPassed: true,
		});
		const snap = store.getSnapshot()!;
		const missing = missingRequirements(snap.assessment.tier, snap.verification);
		assert.equal(missing.length, 0);
		assert.equal(canClaimDone(snap.assessment.tier, snap.verification), true);
	});
});

/**
 * Write-gate policy enforcement tests.
 *
 * Verify that the tool_call handler blocks writes correctly per tier:
 * - MED: auto-plan allows writes
 * - HIGH: auto-plan NOT sufficient; manual approval required
 * - Read-only tools never block
 */
describe("integration: write-gate policy", () => {

	it("MED + auto-plan + write => allowed", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const ctx = {
			cwd: "/repo",
			sessionManager: undefined,
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};

		// Classify as MED and auto-record plan
		await handlers.get("input")![0]!({ source: "interactive", text: "edit src/app.ts" }, ctx);
		// tool_call should NOT block (auto-plan set planned=true for MED)
		const result = await handlers.get("tool_call")![0]!({
			type: "tool_call",
			toolName: "write",
			toolCallId: "tc1",
			input: { path: "src/app.ts" },
		}, ctx);
		assert.equal(result, undefined, "MED write with auto-plan should be allowed");
	});

	it("HIGH + auto-plan + no approval + write => blocked", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const ctx = {
			cwd: "/repo",
			sessionManager: undefined,
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};

		// Classify as HIGH (production keyword triggers HIGH)
		await handlers.get("input")![0]!({ source: "interactive", text: "deploy to production" }, ctx);
		// tool_call should BLOCK: HIGH has planned=true (auto-plan) but no manual approval
		const result = await handlers.get("tool_call")![0]!({
			type: "tool_call",
			toolName: "write",
			toolCallId: "tc1",
			input: { path: "infra/deploy.yml" },
		}, ctx);
		assert.deepEqual(result, {
			block: true,
			reason: "HIGH risk: record manual approval via /risk-approve before editing.",
		});
	});

	it("HIGH + approval + write => allowed", async () => {
		// Create an enhanced pi mock that captures commands
		const handlers = new Map<string, Array<(...args: unknown[]) => Promise<unknown>>>();
		const commands = new Map<string, { handler: (args: string, ctx: unknown) => Promise<void> }>();
		const pi = {
			on: (event: string, handler: (...args: unknown[]) => Promise<unknown>) => {
				const list = handlers.get(event) ?? [];
				list.push(handler);
				handlers.set(event, list);
			},
			registerCommand: (name: string, cmd: { handler: (args: string, ctx: unknown) => Promise<void> }) => {
				commands.set(name, cmd);
			},
			registerTool: () => {},
			registerShortcut: () => {},
			registerFlag: () => {},
			getFlag: () => undefined,
			sendMessage: () => {},
			sendUserMessage: () => {},
			appendEntry: () => {},
			setSessionName: () => {},
			getSessionName: () => undefined,
			setLabel: () => {},
			exec: async () => ({ stdout: "", stderr: "", exitCode: 0 }),
			getActiveTools: () => [],
			getAllTools: () => [],
			setActiveTools: () => {},
			refreshTools: () => {},
			getCommands: () => [],
			setModel: async () => false,
			getThinkingLevel: () => "off" as const,
			setThinkingLevel: () => {},
			registerProvider: () => {},
			unregisterProvider: () => {},
			events: { on: () => {}, off: () => {}, emit: () => {} },
		};
		await riskPolicyExtensionFactory(pi as never);
		const ctx = {
			cwd: "/repo",
			sessionManager: undefined,
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};

		// Fire session_start to register commands
		await handlers.get("session_start")![0]!({}, ctx);

		// Classify as HIGH
		await handlers.get("input")![0]!({ source: "interactive", text: "deploy to production" }, ctx);
		// Simulate /risk-approve via the registered command handler
		const approveCmd = commands.get("risk-approve");
		assert.ok(approveCmd, "risk-approve command should be registered");
		await approveCmd!.handler("", ctx);
		// tool_call should NOT block now: HIGH has manualApprovalRecorded=true
		const result = await handlers.get("tool_call")![0]!({
			type: "tool_call",
			toolName: "write",
			toolCallId: "tc1",
			input: { path: "infra/deploy.yml" },
		}, ctx);
		assert.equal(result, undefined, "HIGH write with manual approval should be allowed");
	});

	it("read-only tools never block (HIGH tier)", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const ctx = {
			cwd: "/repo",
			sessionManager: undefined,
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};

		// Classify as HIGH
		await handlers.get("input")![0]!({ source: "interactive", text: "deploy to production" }, ctx);
		// read tool should NOT block (not write-like)
		const result = await handlers.get("tool_call")![0]!({
			type: "tool_call",
			toolName: "read",
			toolCallId: "tc1",
			input: { path: "infra/deploy.yml" },
		}, ctx);
		assert.equal(result, undefined, "read-only tool should not block even on HIGH tier");
	});
});

/**
 * Checklist §7: failure recording.
 *
 * Verifies that extractBashExitCode reports the real exit code from a
 * tool_result event, including when the traceback appears late in the
 * output. The extension's tool_result handler routes this through to
 * `verificationPassed` (false for non-zero exit), so these are the
 * underlying signal tests.
 */
describe("checklist §7: failure recording (extractBashExitCode)", () => {
	it("successful command: returns 0", () => {
		assert.equal(
			extractBashExitCode({
				isError: false,
				content: [{ type: "text", text: "5 passed in 0.42s" }],
			}),
			0,
		);
	});

	it("failing command with traceback + 'Command exited with code 1' footer", () => {
		assert.equal(
			extractBashExitCode({
				isError: true,
				content: [
					{
						type: "text",
						text: "Traceback (most recent call last):\n  File \"test.py\", line 3\n    assert False\nAssertionError\n\nCommand exited with code 1",
					},
				],
			}),
			1,
		);
	});

	it("late traceback: exit code line after >100 chars of output is still parsed", () => {
		const longOutput = "x".repeat(200) + "Failure details\n\nCommand exited with code 139";
		assert.equal(
			extractBashExitCode({
				isError: true,
				content: [{ type: "text", text: longOutput }],
			}),
			139,
		);
	});

	it("aborted/timeout (no 'exited with code' line): falls back to 1", () => {
		assert.equal(
			extractBashExitCode({
				isError: true,
				content: [{ type: "text", text: "Command aborted" }],
			}),
			1,
		);
	});

	it("empty content + isError: returns 1 (unknown failure)", () => {
		assert.equal(extractBashExitCode({ isError: true, content: [] }), 1);
	});

	it("isError false with non-zero-looking content still returns 0", () => {
		assert.equal(
			extractBashExitCode({
				isError: false,
				content: [{ type: "text", text: "exited with code 1 (this is in the output, not the actual error)" }],
			}),
			0,
		);
	});
});

// ---------------------------------------------------------------------------
// Auto-record: structural plan / verification / diff-summary recording.
// These tests pin the behavior that plan/diff/verify state is recorded
// automatically when the gate activates, not only when the model remembers.
// ---------------------------------------------------------------------------

describe("autoRecordPlanIfNeeded", () => {

	const baseAssessment = {
		tier: "MED" as const,
		reasons: ["touches code"],
		matchedRules: ["CODE_PATH"],
		candidatePaths: ["extensions/foo.ts"],
		proposedCommands: [],
		promptSummary: "edit foo.ts",
		overridden: false,
	};
	const emptyV = {
		planned: false,
		verificationRan: false,
		verificationPassed: false,
		diffSummarized: false,
		manualApprovalRecorded: false,
	};

	it("records plan on MED when nothing exists", () => {
		const result = autoRecordPlanIfNeeded(emptyV, baseAssessment);
		assert.equal(result.changed, true);
		assert.equal(result.next.planned, true);
		assert.match(result.next.planText ?? "", /^AUTO-RECORDED PLAN:/);
		assert.equal(result.next.planSource, "auto");
		assert.match(result.next.planText ?? "", /MED/);
		assert.match(result.next.planText ?? "", /foo\.ts/);
	});

	it("records plan on HIGH when nothing exists", () => {
		const result = autoRecordPlanIfNeeded(emptyV, { ...baseAssessment, tier: "HIGH" });
		assert.equal(result.changed, true);
		assert.equal(result.next.planned, true);
		assert.match(result.next.planText ?? "", /^AUTO-RECORDED PLAN:/);
		assert.match(result.next.planText ?? "", /HIGH/);
	});

	it("does NOT record on LOW", () => {
		const result = autoRecordPlanIfNeeded(emptyV, { ...baseAssessment, tier: "LOW" });
		assert.equal(result.changed, false);
		assert.equal(result.next.planned, false);
	});

	it("does NOT overwrite an existing explicit plan", () => {
		const existing = {
			...emptyV,
			planned: true,
			planText: "USER PLAN: my hand-written plan",
			planSource: "user" as const,
		};
		const result = autoRecordPlanIfNeeded(existing, baseAssessment);
		assert.equal(result.changed, false);
		assert.equal(result.next.planText, "USER PLAN: my hand-written plan");
	});
});

describe("evaluateAutoDiff", () => {
	const baseProbe = {
		tier: "MED" as const,
		planned: true,
		diffSummarized: false,
		hasSessionManager: true,
		hasBranch: true,
		changeSetEntryCount: 1,
		verificationRan: true,
		verificationPassed: true,
		lastVerificationExitCode: 0,
	};

	it("records when MED, branch present, changeset non-empty", () => {
		const r = evaluateAutoDiff(baseProbe);
		assert.equal(r.willRecord, true);
		assert.equal(r.skipReason, undefined);
	});

	it("skips on LOW tier", () => {
		const r = evaluateAutoDiff({ ...baseProbe, tier: "LOW" });
		assert.equal(r.willRecord, false);
		assert.equal(r.skipReason, "skip_low_tier");
	});

	it("records on HIGH tier", () => {
		const r = evaluateAutoDiff({ ...baseProbe, tier: "HIGH" });
		assert.equal(r.willRecord, true);
	});

	it("skips when already summarized", () => {
		const r = evaluateAutoDiff({ ...baseProbe, diffSummarized: true });
		assert.equal(r.willRecord, false);
		assert.equal(r.skipReason, "skip_already_summarized");
	});

	it("skips when no sessionManager", () => {
		const r = evaluateAutoDiff({ ...baseProbe, hasSessionManager: false });
		assert.equal(r.willRecord, false);
		assert.equal(r.skipReason, "skip_no_session_manager");
	});

	it("skips when no branch", () => {
		const r = evaluateAutoDiff({ ...baseProbe, hasBranch: false });
		assert.equal(r.willRecord, false);
		assert.equal(r.skipReason, "skip_no_branch");
	});

	it("skips when changeset is empty", () => {
		const r = evaluateAutoDiff({ ...baseProbe, changeSetEntryCount: 0 });
		assert.equal(r.willRecord, false);
		assert.equal(r.skipReason, "skip_empty_changeset");
	});

	it("guard order: LOW tier is checked before summarized", () => {
		const r = evaluateAutoDiff({ ...baseProbe, tier: "LOW", diffSummarized: true });
		assert.equal(r.skipReason, "skip_low_tier");
	});

	it("R8: does NOT filter on planned=false — auto-diff records regardless of plan state", () => {
		const r = evaluateAutoDiff({ ...baseProbe, planned: false });
		assert.equal(r.willRecord, true);
		assert.equal(r.skipReason, undefined);
	});
});

describe("buildAutoDiffSummary", () => {
	const baseRecord = {
		tier: "MED" as const,
		planned: true,
		diffSummarized: false,
		hasSessionManager: true,
		hasBranch: true,
		changeSetEntryCount: 2,
		verificationRan: true,
		verificationPassed: true,
		lastVerificationExitCode: 0,
		fileList: "src/a.ts, src/b.ts",
	};

	it("includes the AUTO-RECORDED DIFF SUMMARY prefix", () => {
		const s = buildAutoDiffSummary(baseRecord);
		assert.match(s, /^AUTO-RECORDED DIFF SUMMARY:/);
	});

	it("names the touched files from the fileList", () => {
		const s = buildAutoDiffSummary(baseRecord);
		assert.match(s, /src\/a\.ts/);
		assert.match(s, /src\/b\.ts/);
	});

	it("includes the file count", () => {
		const s = buildAutoDiffSummary(baseRecord);
		assert.match(s, /2 file\(s\) changed in session/);
	});

	it("reports verification passed when verificationRan=true and exitCode=0", () => {
		const s = buildAutoDiffSummary(baseRecord);
		assert.match(s, /verification passed \(exit 0\)/);
	});

	it("reports verification failed when exitCode != 0", () => {
		const s = buildAutoDiffSummary({ ...baseRecord, verificationPassed: false, lastVerificationExitCode: 1 });
		assert.match(s, /verification failed \(exit 1\)/);
	});

	it("reports no verification captured yet when verificationRan=false", () => {
		const s = buildAutoDiffSummary({ ...baseRecord, verificationRan: false });
		assert.match(s, /no verification captured yet/);
	});

	it("uses ? for exit code when lastVerificationExitCode is undefined", () => {
		const s = buildAutoDiffSummary({ ...baseRecord, lastVerificationExitCode: undefined });
		assert.match(s, /exit \?/);
	});
});

describe("buildAutoDiffProbeLog", () => {
	const baseProbe = {
		cwd: "/repo",
		tier: "MED" as const,
		planned: true,
		verificationRan: true,
		verificationPassed: true,
		diffSummarized: false,
		hasSessionManager: true,
		hasBranch: true,
		changeSetEntryCount: 2,
		willRecord: true,
	};

	it("emits event=auto_diff_probe with the expected fields", () => {
		const entry = buildAutoDiffProbeLog(baseProbe);
		assert.equal(entry.event, "auto_diff_probe");
		assert.equal(entry.cwd, "/repo");
		assert.equal(entry.tier, "MED");
		assert.equal(entry.planned, true);
		assert.equal(entry.changeSetEntryCount, 2);
		assert.equal(entry.willRecord, true);
		assert.equal(entry.skipReason, undefined);
	});

	it("includes skipReason only when provided", () => {
		const withReason = buildAutoDiffProbeLog({ ...baseProbe, skipReason: "skip_empty_changeset" });
		assert.equal(withReason.skipReason, "skip_empty_changeset");
		const without = buildAutoDiffProbeLog(baseProbe);
		assert.equal(Object.prototype.hasOwnProperty.call(without, "skipReason"), false);
	});

	it("supports HIGH tier", () => {
		const entry = buildAutoDiffProbeLog({ ...baseProbe, tier: "HIGH" });
		assert.equal(entry.tier, "HIGH");
	});
});

describe("extension factory — live handler wiring", () => {

	it("registers tool_result and agent_end handlers", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		assert.ok(handlers.has("tool_result"), "tool_result handler should be registered");
		assert.ok(handlers.has("agent_end"), "agent_end handler should be registered");
		assert.equal(handlers.get("tool_result")!.length >= 1, true);
		assert.equal(handlers.get("agent_end")!.length >= 1, true);
	});

	it("tool_result handler does not throw on synthetic bash event", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const handler = handlers.get("tool_result")![0]!;
		// Synthetic bash tool_result event with successful npm test
		const event = {
			type: "tool_result" as const,
			toolName: "bash" as const,
			toolCallId: "tc1",
			input: { command: "npm test" },
			content: [{ type: "text" as const, text: "Tests: 83 passed\n" }],
			details: undefined,
			isError: false,
		};
		// Should not throw — hooks are wrapped in try/catch / no-throw paths.
		await handler(event, {} as never);
	});

	it("tool_result handler records verification for live compound `cd ... && npm test` payload", async () => {
		// Reproduces the exact live tool_result shape observed in the event probe:
		// keys [type, toolName, toolCallId, input, content, details, isError],
		// toolName "bash", input.command = "cd <repo> && npm test". This previously
		// failed because isVerificationCommand rejected the `cd ... &&` prefix.
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "rptest-live-payload-"));
		try {
			const { handlers, pi } = captureHandlers();
			await riskPolicyExtensionFactory(pi as never);
			const ctx = {
				cwd: tempDir,
				sessionManager: { getBranch: () => [] },
				ui: { notify: () => {} },
				mode: "rpc" as const,
				hasUI: false,
				modelRegistry: {} as never,
				model: undefined,
				isIdle: () => true,
				isProjectTrusted: () => true,
				getSignal: () => undefined,
				abort: () => {},
				hasPendingMessages: () => false,
				shutdown: () => {},
				getContextUsage: () => undefined,
				compact: () => {},
				getSystemPrompt: () => "",
			};
			const handler = handlers.get("tool_result")![0]!;
			// SUCCESS path: isError=false → exitCode 0 (inferred), passed=true.
			await handler(
				{
					type: "tool_result",
					toolName: "bash",
					toolCallId: "tc-ok",
					input: { command: "cd P:/.pi/pi-risk-policy && npm test" },
					content: [{ type: "text", text: "127 passed\n" }],
					details: undefined,
					isError: false,
				},
				ctx,
			);
			let logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			let lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const ok = lines.find((e: { event?: string }) => e.event === "verification_update") as
				| { exitCode?: number; exitCodeInferred?: boolean; passed?: boolean }
				| undefined;
			assert.ok(ok, "verification_update must appear for compound npm test");
			assert.equal(ok!.passed, true);
			assert.equal(ok!.exitCode, 0);
			assert.equal(ok!.exitCodeInferred, true, "success exit code is inferred from isError=false");
			// FAILURE path: isError=true → passed=false.
			await handler(
				{
					type: "tool_result",
					toolName: "bash",
					toolCallId: "tc-fail",
					input: { command: "cd P:/.pi/pi-risk-policy && npm test" },
					content: [{ type: "text", text: "Error: Command exited with code 1\n" }],
					details: undefined,
					isError: true,
				},
				ctx,
			);
			logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const updates = lines.filter((e: { event?: string }) => e.event === "verification_update");
			const fail = updates[updates.length - 1] as
				| { exitCode?: number; exitCodeInferred?: boolean; passed?: boolean }
				| undefined;
			assert.ok(fail, "verification_update must appear for failed npm test");
			assert.equal(fail!.passed, false);
			assert.equal(fail!.exitCode, 1);
			assert.equal(fail!.exitCodeInferred, false, "numeric exit parsed from content is not inferred");
		} finally {
			await rm(tempDir, { recursive: true, force: true });
		}
	});

	it("agent_end handler does not throw with minimal ctx", async () => {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const handler = findHandlerByName(handlers, "agent_end", "agentEndAutoDiffHandler")!;
		const ctx = {
			cwd: "/tmp",
			sessionManager: { getBranch: () => [] },
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};
		await handler({ type: "agent_end", messages: [] }, ctx);
	});

	it("full flow: input -> tool_result -> agent_end records auto-diff for MED task", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "rptest-full-"));
		try {
			process.env.PI_DEBUG = "1";
			const { handlers, pi } = captureHandlers();
			await riskPolicyExtensionFactory(pi as never);
			// Build a fake ctx with a session branch that has one write entry.
			const fakeBranch = [
				{
					type: "message",
					id: "m1",
					timestamp: 1700000000000,
					message: {
						role: "assistant",
						content: [
							{
								type: "toolCall",
								name: "write",
								arguments: { path: "tmp/agent-end-live-test.ts", content: "export const x = 'ok';\n" },
							},
						],
					},
				},
			];
			const ctx = {
				cwd: tempDir,
				sessionManager: { getBranch: () => fakeBranch },
				ui: { notify: () => {} },
				mode: "rpc" as const,
				hasUI: false,
				modelRegistry: {} as never,
				model: undefined,
				isIdle: () => true,
				isProjectTrusted: () => true,
				getSignal: () => undefined,
				abort: () => {},
				hasPendingMessages: () => false,
				shutdown: () => {},
				getContextUsage: () => undefined,
				compact: () => {},
				getSystemPrompt: () => "",
			};
			// 1. input handler classifies the task and resets verification.
			const inputHandler = handlers.get("input")![0]!;
			await inputHandler({ source: "interactive", text: "edit tmp/agent-end-live-test.ts" }, ctx);
			// 2. tool_result handler for npm test.
			const trHandler = handlers.get("tool_result")![0]!;
			await trHandler(
				{
					type: "tool_result",
					toolName: "bash",
					toolCallId: "tc1",
					input: { command: "npm test" },
					content: [{ type: "text", text: "Tests: 83 passed\n" }],
					details: undefined,
					isError: false,
				},
				ctx,
			);
			// 3. agent_end handler should now record the auto-diff.
			const aeHandler = findHandlerByName(handlers, "agent_end", "agentEndAutoDiffHandler")!;
			await aeHandler({ type: "agent_end", messages: [] }, ctx);
			// R11: assert observable side effects in risk-log.jsonl.
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const classified = lines.find((e: { event?: string }) => e.event === "classified");
			assert.ok(classified, "classified event must appear");
			assert.equal((classified as { tier?: string }).tier, "MED");
			const verify = lines.find((e: { event?: string }) => e.event === "verification_update");
			assert.ok(verify, "verification_update event must appear");
			assert.equal((verify as { passed?: boolean }).passed, true);
			const recorded = lines.find((e: { event?: string }) => e.event === "auto_diff_summary_recorded");
			assert.ok(recorded, "auto_diff_summary_recorded event must appear");
			assert.equal((recorded as { fileCount?: number }).fileCount, 1);
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});

	it("agent_end auto-diff branch writes auto_diff_summary_recorded to risk-log.jsonl when gate passes", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "rptest-"));
		try {
			process.env.PI_DEBUG = "1";
			const { handlers, pi } = captureHandlers();
			await riskPolicyExtensionFactory(pi as never);
			const fakeBranch = [
				{
					type: "message",
					id: "m1",
					timestamp: 1700000000000,
					message: {
						role: "assistant",
						content: [
							{
								type: "toolCall",
								name: "write",
								arguments: { path: "tmp/x.ts", content: "export const x = 1;\n" },
							},
						],
					},
				},
			];
			const ctx = {
				cwd: tempDir,
				sessionManager: { getBranch: () => fakeBranch },
				ui: { notify: () => {} },
				mode: "rpc" as const,
				hasUI: false,
				modelRegistry: {} as never,
				model: undefined,
				isIdle: () => true,
				isProjectTrusted: () => true,
				getSignal: () => undefined,
				abort: () => {},
				hasPendingMessages: () => false,
				shutdown: () => {},
				getContextUsage: () => undefined,
				compact: () => {},
				getSystemPrompt: () => "",
			};
			// Classify via input to set tier=MED, planned=true.
			await handlers.get("input")![0]!(
				{ source: "interactive", text: "edit tmp/x.ts" },
				ctx,
			);
			// Record verification via tool_result so verifyNote is "passed".
			await handlers.get("tool_result")![0]!(
				{
					type: "tool_result",
					toolName: "bash",
					toolCallId: "tc1",
					input: { command: "npm test" },
					content: [{ type: "text", text: "ok\n" }],
					details: undefined,
					isError: false,
				},
				ctx,
			);
			// Fire agent_end — should auto-record the diff summary.
			await findHandlerByName(handlers, "agent_end", "agentEndAutoDiffHandler")!({ type: "agent_end", messages: [] }, ctx);
			// Read the log file written to the temp cwd.
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const recorded = lines.find((e: { event?: string }) => e.event === "auto_diff_summary_recorded");
			assert.ok(recorded, "auto_diff_summary_recorded event must appear in risk-log.jsonl");
			assert.equal((recorded as { fileCount?: number }).fileCount, 1);
			const probe = lines.find((e: { event?: string }) => e.event === "auto_diff_probe");
			assert.ok(probe, "auto_diff_probe event must appear in risk-log.jsonl");
			assert.equal((probe as { willRecord?: boolean }).willRecord, true);
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});
});

describe("getSessionChangeSet — live ctx integration", () => {
	function fakeCtx(branch: unknown[]): { sessionManager: { getBranch: () => unknown[] } } {
		return { sessionManager: { getBranch: () => branch } };
	}

	it("returns empty ChangeSet when sessionManager is missing", () => {
		const cs = getSessionChangeSet({} as never);
		assert.deepEqual(cs.entries, []);
		assert.deepEqual(cs.distinctPaths, []);
		assert.equal(cs.source, "session-ledger");
	});

	it("returns empty ChangeSet when getBranch returns null", () => {
		const ctx = { sessionManager: { getBranch: () => null } };
		const cs = getSessionChangeSet(ctx as never);
		assert.equal(cs.entries.length, 0);
	});

	it("extracts write entries from the branch", () => {
		const branch = [
			{
				type: "message",
				id: "m1",
				timestamp: 1700000000000,
				message: {
					role: "assistant",
					content: [
						{
							type: "toolCall",
							name: "write",
							arguments: { path: "src/foo.ts", content: "export const x = 1;\n" },
						},
					],
				},
			},
		];
		const cs = getSessionChangeSet(fakeCtx(branch) as never);
		assert.equal(cs.entries.length, 1);
		assert.equal(cs.entries[0]?.path, "src/foo.ts");
		assert.equal(cs.entries[0]?.toolName, "write");
		assert.equal(cs.entries[0]?.after, "export const x = 1;\n");
		assert.deepEqual(cs.distinctPaths, ["src/foo.ts"]);
		assert.equal(cs.source, "session-ledger");
	});

	it("extracts edit entries with merged before/after", () => {
		const branch = [
			{
				type: "message",
				id: "m1",
				timestamp: 1700000000000,
				message: {
					role: "assistant",
					content: [
						{
							type: "toolCall",
							name: "edit",
							arguments: {
								path: "src/bar.ts",
								edits: [
									{ oldText: "const x = 1;", newText: "const x = 2;" },
									{ oldText: "const y = 9;", newText: "const y = 10;" },
								],
							},
						},
					],
				},
			},
		];
		const cs = getSessionChangeSet(fakeCtx(branch) as never);
		assert.equal(cs.entries.length, 1);
		assert.equal(cs.entries[0]?.path, "src/bar.ts");
		assert.match(cs.entries[0]?.after ?? "", /const x = 2;/);
		assert.match(cs.entries[0]?.after ?? "", /const y = 10;/);
	});

	it("skips non-message entries", () => {
		const branch = [{ type: "label", id: "l1" }];
		const cs = getSessionChangeSet(fakeCtx(branch) as never);
		assert.equal(cs.entries.length, 0);
	});

	it("R18: drops toolCall entries whose tool is not write or edit (grep/find/bash results don't appear in diff)", () => {
		const branch = [
			{
				type: "message", id: "m1", timestamp: 1700000000000,
				message: { role: "assistant", content: [
					{ type: "toolCall", name: "grep", arguments: { pattern: "x", path: "." } },
					{ type: "toolCall", name: "bash", arguments: { command: "ls" } },
					{ type: "toolCall", name: "read", arguments: { path: "src/a.ts" } },
					{ type: "toolCall", name: "find", arguments: { pattern: "*.ts" } },
				] },
			},
		];
		const cs = getSessionChangeSet(fakeCtx(branch) as never);
		assert.equal(cs.entries.length, 0);
		assert.equal(cs.distinctPaths.length, 0);
	});
});

describe("buildChangeSetPrompt — privacy regression", () => {
	it("returns the empty-marker for a no-change set", () => {
		const prompt = buildChangeSetPrompt({ entries: [], distinctPaths: [], source: "session-ledger", note: "" });
		assert.equal(prompt, "(no changes recorded in this session)");
	});

	it("truncates long before/after fields so secrets don't leak to the LLM", () => {
		const long = "x".repeat(5000);
		const cs = {
			entries: [{
				toolName: "write" as const,
				path: "src/secrets.ts",
				before: undefined,
				after: long,
				entryId: "e1",
				entryTimestamp: 1700000000000,
			}],
			distinctPaths: ["src/secrets.ts"],
			source: "session-ledger" as const,
			note: "",
		};
		const prompt = buildChangeSetPrompt(cs);
		assert.match(prompt, /\.\.\. \[truncated \d+ chars\]/);
		assert.ok(prompt.length < 4000, "truncated prompt should be under 4000 chars");
	});

	it("does NOT include raw 5000-char secret in the rendered prompt", () => {
		const secret = "API_KEY=" + "Z".repeat(4900);
		const cs = {
			entries: [{
				toolName: "write" as const,
				path: "creds.txt",
				before: undefined,
				after: secret,
				entryId: "e1",
				entryTimestamp: 1700000000000,
			}],
			distinctPaths: ["creds.txt"],
			source: "session-ledger" as const,
			note: "",
		};
		const prompt = buildChangeSetPrompt(cs);
		assert.equal(prompt.includes("Z".repeat(4900)), false);
	});

	it("preserves short fields verbatim", () => {
		const cs = {
			entries: [{
				toolName: "edit" as const,
				path: "src/x.ts",
				before: "const a = 1;",
				after: "const a = 2;",
				entryId: "e1",
				entryTimestamp: 1700000000000,
			}],
			distinctPaths: ["src/x.ts"],
			source: "session-ledger" as const,
			note: "",
		};
		const prompt = buildChangeSetPrompt(cs);
		assert.match(prompt, /const a = 1;/);
		assert.match(prompt, /const a = 2;/);
		assert.equal(prompt.includes("truncated"), false);
	});
});

describe("isVerificationCommand — generic script patterns", () => {
	it("matches `node test-foo.mjs`", () => {
		assert.equal(isVerificationCommand("node test-foo.mjs", DEFAULT_CONFIG), true);
	});
	it("matches `node check-x.mjs`", () => {
		assert.equal(isVerificationCommand("node check-x.mjs", DEFAULT_CONFIG), true);
	});
	it("matches `node foo.test.mjs`", () => {
		assert.equal(isVerificationCommand("node foo.test.mjs", DEFAULT_CONFIG), true);
	});
	it("matches `node foo.spec.ts`", () => {
		assert.equal(isVerificationCommand("node foo.spec.ts", DEFAULT_CONFIG), true);
	});
	it("does NOT match bare `node script.js`", () => {
		assert.equal(isVerificationCommand("node script.js", DEFAULT_CONFIG), false);
	});
	it("still matches `tsc --noEmit`", () => {
		assert.equal(isVerificationCommand("tsc --noEmit", DEFAULT_CONFIG), true);
	});
	it("still matches `npm test`", () => {
		assert.equal(isVerificationCommand("npm test", DEFAULT_CONFIG), true);
	});
});

describe("suggestVerifyCommandsForPath", () => {
	it("returns TypeScript verify for .ts paths", () => {
		const cmds = suggestVerifyCommandsForPath("src/foo.ts");
		assert.ok(cmds);
		assert.ok(cmds!.some((c) => c.includes("tsc") || c.includes("npm")));
	});

	it("returns Python verify for .py paths", () => {
		const cmds = suggestVerifyCommandsForPath("src/foo.py");
		assert.ok(cmds);
		assert.ok(cmds!.some((c) => c.includes("pytest") || c.includes("ruff")));
	});

	it("returns empty array for .md paths (no-op probes removed)", () => {
		const cmds = suggestVerifyCommandsForPath("README.md");
		assert.deepEqual(cmds, []);
	});

	it("returns empty array for .txt paths (no-op probes removed)", () => {
		const cmds = suggestVerifyCommandsForPath("notes.txt");
		assert.deepEqual(cmds, []);
	});

	it("returns null for unknown extensions", () => {
		assert.equal(suggestVerifyCommandsForPath("data.xyz"), null);
	});
});

describe("RiskStateStore — lastPrompt accessor (R17)", () => {
	it("getLastPrompt returns empty string by default", () => {
		const store = new RiskStateStore();
		assert.equal(store.getLastPrompt(), "");
	});

	it("setLastPrompt then getLastPrompt returns the stored value", () => {
		const store = new RiskStateStore();
		store.setLastPrompt("edit tmp/foo.ts");
		assert.equal(store.getLastPrompt(), "edit tmp/foo.ts");
	});

	it("setLastPrompt overwrites previous value", () => {
		const store = new RiskStateStore();
		store.setLastPrompt("first");
		store.setLastPrompt("second");
		assert.equal(store.getLastPrompt(), "second");
	});
});

describe("RiskStateStore \u2014 deleted paths", () => {
	it("isDeletedPath: exact file match", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		assert.equal(store.isDeletedPath("src/bar.ts"), false);
	});

	it("isDeletedPath: nested child of deleted directory", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		assert.equal(store.isDeletedPath("src/deep/nested.ts"), true);
		assert.equal(store.isDeletedPath("other/foo.ts"), false);
	});

	it("isDeletedPath: normalizes backslashes", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src\\foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
	});

	it("isDeletedPath: strips leading ./", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("./src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
	});

	it("clearDeletedPaths: resets all tracked deletions", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		store.clearDeletedPaths();
		assert.equal(store.isDeletedPath("src/foo.ts"), false);
	});
});

describe("extractDeletionPaths \u2014 from risk-policy-extension.ts", () => {
	it("rm single file", () => {
		assert.deepEqual(extractDeletionPaths("rm src/foo.ts"), ["src/foo.ts"]);
	});

	it("rm multiple files", () => {
		assert.deepEqual(extractDeletionPaths("rm src/foo.ts src/bar.ts"), ["src/foo.ts", "src/bar.ts"]);
	});

	it("rm -rf directory", () => {
		assert.deepEqual(extractDeletionPaths("rm -rf src/"), ["src"]);
	});

	it("rm -r with glob", () => {
		assert.deepEqual(extractDeletionPaths("rm -r src/*.ts"), ["src/*.ts"]);
	});

	it("git rm file", () => {
		assert.deepEqual(extractDeletionPaths("git rm src/foo.ts"), ["src/foo.ts"]);
	});

	it("git rm --cached", () => {
		assert.deepEqual(extractDeletionPaths("git rm --cached src/foo.ts"), ["src/foo.ts"]);
	});

	it("git checkout -- file", () => {
		assert.deepEqual(extractDeletionPaths("git checkout -- src/foo.ts"), ["src/foo.ts"]);
	});

	it("git restore -- file", () => {
		assert.deepEqual(extractDeletionPaths("git restore -- src/foo.ts"), ["src/foo.ts"]);
	});

	it("ignores flags and non-path args", () => {
		assert.deepEqual(extractDeletionPaths("rm -rf -- src/foo.ts"), ["src/foo.ts"]);
		assert.deepEqual(extractDeletionPaths("rm -r -f src/foo.ts"), ["src/foo.ts"]);
		assert.deepEqual(extractDeletionPaths("rm --help"), []);
		assert.deepEqual(extractDeletionPaths("git rm -f src/foo.ts"), ["src/foo.ts"]);
	});

	it("handles quoted paths", () => {
		assert.deepEqual(extractDeletionPaths('"src/foo.ts"'), ["src/foo.ts"]);
		assert.deepEqual(extractDeletionPaths("'src/foo.ts'"), ["src/foo.ts"]);
	});

	it("normalizes backslashes and leading dots", () => {
		assert.deepEqual(extractDeletionPaths("rm src\\foo.ts"), ["src/foo.ts"]);
		assert.deepEqual(extractDeletionPaths("rm ./src/foo.ts"), ["src/foo.ts"]);
	});
});


describe("extractDeletionPaths — cross-shell / Windows support", () => {
	// Regression guard: the original Unix-only matcher (rm/git rm/git checkout/
	// git restore) silently missed every Windows/PowerShell deletion, so files
	// deleted via Remove-Item kept producing stale review findings. These cases
	// lock in that Remove-Item, del, erase, git clean, and the `ri` alias all
	// track deletions the same way `rm` does.

	it("extracts paths from PowerShell Remove-Item with flags", () => {
		assert.deepEqual(extractDeletionPaths("Remove-Item -Recurse -Force scripts/run.ps1"), ["scripts/run.ps1"]);
		assert.deepEqual(extractDeletionPaths("Remove-Item src/foo.ts"), ["src/foo.ts"]);
	});

	it("extracts paths from cmd del / erase", () => {
		assert.deepEqual(extractDeletionPaths("del src/foo.ts"), ["src/foo.ts"]);
		assert.deepEqual(extractDeletionPaths("erase src/foo.ts"), ["src/foo.ts"]);
	});

	it("extracts paths from git clean", () => {
		assert.deepEqual(extractDeletionPaths("git clean -fd src/"), ["src"]);
	});

	it("extracts paths from the PowerShell ri alias", () => {
		assert.deepEqual(extractDeletionPaths("ri src/foo.ts"), ["src/foo.ts"]);
	});
});


describe("RiskStateStore \u2014 deleted paths", () => {
	it("isDeletedPath: exact file match", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		assert.equal(store.isDeletedPath("src/bar.ts"), false);
	});

	it("isDeletedPath: nested child of deleted directory", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		assert.equal(store.isDeletedPath("src/deep/nested.ts"), true);
		assert.equal(store.isDeletedPath("other/foo.ts"), false);
	});

	it("isDeletedPath: normalizes backslashes", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src\\foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
	});

	it("isDeletedPath: strips leading ./", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("./src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
	});

	it("clearDeletedPaths: resets all tracked deletions", () => {
		const store = new RiskStateStore();
		store.addDeletedPath("src/foo.ts");
		assert.equal(store.isDeletedPath("src/foo.ts"), true);
		store.clearDeletedPaths();
		assert.equal(store.isDeletedPath("src/foo.ts"), false);
	});
});

describe("Findings dedup across turns", () => {
	// Mirror the keyOf + merge logic from risk-policy-extension.ts.
	// Dedup key: path:severity:kind:message. runReviewPass resets its counter each
	// turn, so "S1" in turn 1 and "S1" in turn 2 are different ids for the same
	// finding — using id as the dedup key would never catch cross-turn duplicates.
	const keyOf = (f: { path: string; severity: string; kind: string; message: string }) =>
		`${f.path}:${f.severity}:${f.kind}:${f.message}`;

	const mkFinding = (id: string, path: string, kind: "simplify" | "review" = "review", severity = "med", message = "test") =>
		({ id, path, kind, severity, message });

	it("same content, different id: filtered by path+severity+message", () => {
		// Counter resets each turn: "S1" in turn 1, "S1" in turn 2.
		// Dedup must catch this using content key, not id.
		const existing = [mkFinding("S1", "src/a.ts", "review", "med", "unused var")];
		const newFindings = [mkFinding("S2", "src/a.ts", "review", "med", "unused var")];
		const existingKeys = new Set(existing.map(keyOf));
		const toAdd = newFindings.filter((f) => !existingKeys.has(keyOf(f)));
		assert.equal(toAdd.length, 0);
	});

	it("same path+severity but different message: treated as different finding", () => {
		const existing = [mkFinding("S1", "src/a.ts", "review", "med", "unused var")];
		const newFindings = [mkFinding("S2", "src/a.ts", "review", "med", "different msg")];
		const existingKeys = new Set(existing.map(keyOf));
		const toAdd = newFindings.filter((f) => !existingKeys.has(keyOf(f)));
		assert.equal(toAdd.length, 1);
	});

	it("RiskStateStore: disposition persists across setFindings calls", () => {
		const store = new RiskStateStore();
		const f = { kind: "review" as const, path: "src/a.ts", severity: "med" as const, message: "x", turnId: "t1", id: "R1", storedAt: "2024-01-01" };
		store.setFindings([f]);
		store.recordDisposition({ id: "R1", disposition: "addressed" });
		assert.equal(store.getFindings().length, 1);
		assert.equal(store.getFindings()[0]?.disposition, "addressed");
		// Next turn with no new findings: merge is a no-op
		store.setFindings([...store.getFindings()]);
		assert.equal(store.getFindings().length, 1);
		assert.equal(store.getFindings()[0]?.disposition, "addressed");
	});

	it("RiskStateStore: dispositioned finding is not re-added by merge on next turn", () => {
		const store = new RiskStateStore();
		const f = { kind: "review" as const, path: "src/a.ts", severity: "med" as const, message: "x", turnId: "t1", id: "R1", storedAt: "2024-01-01" };
		store.setFindings([f]);
		store.recordDisposition({ id: "R1", disposition: "addressed" });
		// Simulate next turn: review generates the same finding (new id)
		const existing = store.getFindings();
		const newFindings = [{ ...f, storedAt: "2024-01-02" }];
		const existingKeys = new Set(existing.map(keyOf));
		const toAdd = newFindings.filter((f) => !existingKeys.has(keyOf(f)));
		store.setFindings([...existing, ...toAdd]);
		assert.equal(store.getFindings().length, 1); // no re-add
		assert.equal(store.getFindings()[0]?.disposition, "addressed"); // disposition preserved
	});
});

describe("R8: hook_seen probes fire unconditionally when PI_DEBUG=1", () => {
	async function runHandlerSuite(tempDir: string) {
		const { handlers, pi } = captureHandlers();
		await riskPolicyExtensionFactory(pi as never);
		const fakeBranch = [{
			type: "message",
			id: "m1",
			timestamp: 1700000000000,
			message: { role: "assistant", content: [{
				type: "toolCall", name: "write",
				arguments: { path: "tmp/r8.ts", content: "export const r = 1;\n" },
			}] },
		}];
		const ctx = {
			cwd: tempDir,
			sessionManager: { getBranch: () => fakeBranch },
			ui: { notify: () => {} },
			mode: "rpc" as const,
			hasUI: false,
			modelRegistry: {} as never,
			model: undefined,
			isIdle: () => true,
			isProjectTrusted: () => true,
			getSignal: () => undefined,
			abort: () => {},
			hasPendingMessages: () => false,
			shutdown: () => {},
			getContextUsage: () => undefined,
			compact: () => {},
			getSystemPrompt: () => "",
		};
		await handlers.get("input")![0]!({ source: "interactive", text: "edit tmp/r8.ts" }, ctx);
		await handlers.get("tool_call")![0]!({
			type: "tool_call", toolName: "write", toolCallId: "tc1",
			input: { path: "tmp/r8.ts" },
		}, ctx);
		await handlers.get("tool_result")![0]!({
			type: "tool_result", toolName: "bash", toolCallId: "tc2",
			input: { command: "npm test" },
			content: [{ type: "text", text: "ok\n" }],
			details: undefined,
			isError: false,
		}, ctx);
		await findHandlerByName(handlers, "agent_end", "agentEndAutoDiffHandler")!({ type: "agent_end", messages: [] }, ctx);
	}

	it("input hook_seen fires for interactive prompts", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "r8-probe-"));
		try {
			process.env.PI_DEBUG = "1";
			await runHandlerSuite(tempDir);
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const inputHook = lines.find((e: { event?: string }) => e.event === "hook_seen" && (e as { hook?: string }).hook === "input");
			assert.ok(inputHook, "input hook_seen must appear when PI_DEBUG=1");
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});

	it("tool_call hook_seen fires for write/edit tool calls", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "r8-probe-"));
		try {
			process.env.PI_DEBUG = "1";
			await runHandlerSuite(tempDir);
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const tcHook = lines.find((e: { event?: string }) => e.event === "hook_seen" && (e as { hook?: string }).hook === "tool_call");
			assert.ok(tcHook, "tool_call hook_seen must appear when PI_DEBUG=1");
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});

	it("tool_result hook_seen fires for bash tool results", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "r8-probe-"));
		try {
			process.env.PI_DEBUG = "1";
			await runHandlerSuite(tempDir);
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const trHook = lines.find((e: { event?: string }) => e.event === "hook_seen" && (e as { hook?: string }).hook === "tool_result");
			assert.ok(trHook, "tool_result hook_seen must appear when PI_DEBUG=1");
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});

	it("agent_end hook_seen fires at end of turn", async () => {
		const prevDebug = process.env.PI_DEBUG;
		const tempDir = await mkdtemp(pathJoin(tmpdir(), "r8-probe-"));
		try {
			process.env.PI_DEBUG = "1";
			await runHandlerSuite(tempDir);
			const logText = await readFile(`${tempDir}/.pi/risk-log.jsonl`, "utf8");
			const lines = logText.split("\n").filter(Boolean).map((l) => JSON.parse(l));
			const aeHook = lines.find((e: { event?: string }) => e.event === "hook_seen" && (e as { hook?: string }).hook === "agent_end");
			assert.ok(aeHook, "agent_end hook_seen must appear when PI_DEBUG=1");
		} finally {
			if (prevDebug === undefined) delete process.env.PI_DEBUG;
			else process.env.PI_DEBUG = prevDebug;
			await rm(tempDir, { recursive: true, force: true });
		}
	});
});

describe("runReviewPass — turn-count derivation", () => {
	function makeSnapshot(): RiskStateSnapshot {
		const assessment: RiskAssessment = {
			tier: "MED",
			reasons: ["test"],
			matchedRules: ["TEST"],
			candidatePaths: ["tmp/foo.ts"],
			proposedCommands: [],
			promptSummary: "test",
			overridden: false,
		};
		return {
			assessment,
			policy: { requirePlan: true, requireVerification: true, manualApplyOnly: false, allowDestructiveShell: false, allowInfraChanges: false, uiLabel: "MED" },
			verification: { planned: true, verificationRan: false, verificationPassed: false, diffSummarized: false, manualApprovalRecorded: false },
			timestamp: new Date().toISOString(),
		};
	}

	function makeCtxWithBranch(branch: unknown[]): { sessionManager: { getBranch: () => unknown[] }; model: undefined; modelRegistry: { getApiKeyForProvider: () => Promise<string> } } {
		return {
			sessionManager: { getBranch: () => branch },
			model: undefined,
			modelRegistry: { getApiKeyForProvider: async () => "fake-key" },
		};
	}

	it("returns skippedReason='no-session-changes' when branch is empty (turn count falls back to 0)", async () => {
		const cs = getSessionChangeSet(makeCtxWithBranch([]) as never);
		const snap = makeSnapshot();
		const verdict = await runReviewPass(makeCtxWithBranch([]) as never, cs, snap, "turn-1");
		assert.deepEqual(verdict.simplify, []);
		assert.deepEqual(verdict.review, []);
		assert.match(verdict.skippedReason ?? "", /no-session-changes/);
	});

	it("returns skippedReason containing '<2 files and <5 turns' when changes < 2 and branch < 5 user messages", async () => {
		const branch = [
			{ type: "message", id: "m1", message: { role: "user", content: [{ type: "text", text: "hi" }] } },
		];
		const cs = getSessionChangeSet(makeCtxWithBranch(branch) as never);
		// force distinctPaths to length 1 by passing empty branch but a fake single-entry changeset via direct construction
		cs.entries.push({ toolName: "write", path: "tmp/x.ts", before: undefined, after: "x", entryId: "e1", entryTimestamp: 1 } as never);
		const snap = makeSnapshot();
		const verdict = await runReviewPass(makeCtxWithBranch(branch) as never, cs, snap, "turn-1");
		assert.match(verdict.skippedReason ?? "", /<2 files and <5 turns/);
	});

	it("R9: gracefully degrades when sessionManager.getBranch is absent (returns 0 turns, no throw)", async () => {
		const ctx = { model: undefined, modelRegistry: { getApiKeyForProvider: async () => "fake-key" } };
		const cs = getSessionChangeSet(ctx as never);
		const snap = makeSnapshot();
		// changeSet is empty so verdict is skippedReason='no-session-changes'.
		const verdict = await runReviewPass(ctx as never, cs, snap, "turn-1");
		assert.match(verdict.skippedReason ?? "", /no-session-changes/);
	});
});

describe("runReviewPass — failure propagation (no silent \"clean\" on model/parse failure)", () => {
	// Regression guard: callModel previously returned null on EVERY failure mode
	// (throw, truncated JSON, no-model) and the caller treated null as "clean."
	// The first multi-file refactor would silently produce an unreviewed verdict.
	// These cases inject a callFn that fails and assert the verdict surfaces a
	// review-failed skip reason with zero findings, instead of looking clean.

	function makeSnapshot(): RiskStateSnapshot {
		const assessment: RiskAssessment = {
			tier: "MED",
			reasons: ["test"],
			matchedRules: ["TEST"],
			candidatePaths: ["tmp/foo.ts"],
			proposedCommands: [],
			promptSummary: "test",
			overridden: false,
		};
		return {
			assessment,
			policy: { requirePlan: true, requireVerification: true, manualApplyOnly: false, allowDestructiveShell: false, allowInfraChanges: false, uiLabel: "MED" },
			verification: { planned: true, verificationRan: false, verificationPassed: false, diffSummarized: false, manualApprovalRecorded: false },
			timestamp: new Date().toISOString(),
		};
	}

	// ctx WITH a model + apikey so callModel gets past the no-model guard and
	// reaches the callFn. The injected callFn is what produces the failure.
	function makeCtxWithModel(): { sessionManager: { getBranch: () => unknown[] }; model: { provider: string }; modelRegistry: { getApiKeyForProvider: () => Promise<string> } } {
		return {
			sessionManager: { getBranch: () => [] },
			model: { provider: "fake" },
			modelRegistry: { getApiKeyForProvider: async () => "fake-key" },
		};
	}

	// A single-entry changeset with content so buildChangeSetPrompt is non-empty
	// and the review pass actually invokes callFn.
	function singleEntryChangeSet(): ChangeSet {
		return {
			entries: [{ toolName: "write", path: "tmp/foo.ts", before: undefined, after: "x", entryId: "e1", entryTimestamp: 1 }],
			distinctPaths: ["tmp/foo.ts"],
			source: "session-ledger",
			note: "test",
		};
	}

	it("surfaces review-failed when the model returns truncated/unparseable JSON", async () => {
		// Simulates the original bug: maxTokens too small, model output truncated
		// mid-JSON. Greedy \{[\s\S]*\} matches a dangling fragment, JSON.parse
		// throws -> must surface as review-failed, NOT zero findings + clean.
		const truncatedCallFn: ReviewCallFn = async () => '{"findings":[{"path":"tmp/foo.ts","severity":"med","mes';
		const verdict = await runReviewPass(makeCtxWithModel() as never, singleEntryChangeSet(), makeSnapshot(), "turn-1", truncatedCallFn);
		assert.match(verdict.skippedReason ?? "", /review-failed/);
		assert.deepEqual(verdict.simplify, []);
		assert.deepEqual(verdict.review, []);
	});

	it("surfaces review-failed when the model call throws", async () => {
		// Network/provider failure mid-call. Previously swallowed by catch -> null
		// -> clean verdict. Must now surface as review-failed.
		const throwingCallFn: ReviewCallFn = async () => { throw new Error("connect ECONNREFUSED"); };
		const verdict = await runReviewPass(makeCtxWithModel() as never, singleEntryChangeSet(), makeSnapshot(), "turn-1", throwingCallFn);
		assert.match(verdict.skippedReason ?? "", /review-failed/);
		assert.deepEqual(verdict.simplify, []);
		assert.deepEqual(verdict.review, []);
	});

	it("still reports clean when the model returns valid empty findings", async () => {
		// Backward-compat: a genuinely clean change-set still produces no findings
		// and no review-failed signal. (With a single-file changeset the review
		// pass is separately skipped as not-eligible — that's correct behavior,
		// not a failure. The assertion is specifically that we don't surface
		// review-failed, which would mean a healthy model call was misclassified.)
		const cleanCallFn: ReviewCallFn = async () => '{"findings":[]}';
		const verdict = await runReviewPass(makeCtxWithModel() as never, singleEntryChangeSet(), makeSnapshot(), "turn-1", cleanCallFn);
		assert.doesNotMatch(verdict.skippedReason ?? "", /review-failed/);
		assert.deepEqual(verdict.simplify, []);
		assert.deepEqual(verdict.review, []);
	});
});
