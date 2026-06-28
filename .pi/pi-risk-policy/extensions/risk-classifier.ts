/**
 * Deterministic risk classifier.
 *
 * No probabilistic scoring, no hidden weights. Every tier decision has
 * at least one human-readable reason.
 */

import type { RiskAssessment, RiskConfig, RiskTier } from "./risk-types.ts";

export const DEFAULT_CONFIG: RiskConfig = {
	lowPaths: ["docs/", "tests/", "examples/", "fixtures/"],
	highPaths: [
		"infra/",
		"deploy/",
		"config/prod/",
		"auth/",
		"security/",
		"secrets/",
		".github/workflows/",
	],
	highCommandPatterns: [
		"kubectl",
		"terraform apply",
		"pulumi up",
		"helm upgrade",
		"git push --force",
		"rm -rf",
		"docker push",
	],
	productionKeywords: ["prod", "production", "deploy", "secret", "credential"],
	verificationCommands: {
		default: ["pytest -q"],
		typescript: ["npm run test", "npm run lint"],
		python: ["pytest -q", "ruff check .", "mypy ."],
	},
};

/** Build a short, deterministic summary of a prompt for logging/UI. */
export function summarizePrompt(prompt: string): string {
	const cleaned = (prompt ?? "").replace(/\s+/g, " ").trim();
	if (cleaned.length <= 120) return cleaned;
	return cleaned.slice(0, 117) + "...";
}

// ponytail: trim first so isSafeTextPath can match "  README.md  " correctly.
// Without trim, a trailing-space suffix would break the .endsWith('.md') check.
function normalizePath(p: string): string {
	return p.trim().replace(/\\/g, "/").replace(/^\.\//, "").replace(/^\/+/, "");
}

export function classifyRisk(input: {
	prompt: string;
	cwd: string;
	candidatePaths: string[];
	proposedCommands: string[];
	config: RiskConfig;
	overrideTier?: RiskTier | null;
}): RiskAssessment {
	const normalizedPaths = [...new Set(input.candidatePaths.map(normalizePath))].filter(Boolean);
	const normalizedCommands = [...new Set(input.proposedCommands.map((v) => v.trim()))].filter(Boolean);
	if (input.overrideTier) {
		return {
			tier: input.overrideTier,
			reasons: ["Manual override"],
			matchedRules: ["MANUAL_OVERRIDE"],
			candidatePaths: normalizedPaths,
			proposedCommands: normalizedCommands,
			promptSummary: summarizePrompt(input.prompt ?? ""),
			overridden: true,
		};
	}

	const reasons = new Set<string>();
	const matchedRules = new Set<string>();

	if (
		normalizedPaths.some((path) =>
			input.config.highPaths.some((prefix) => path.includes(prefix)),
		)
	) {
		reasons.add("Touches high-risk path");
		matchedRules.add("HIGH_PATH");
	}

	if (
		normalizedCommands.some((cmd) =>
			// Word-boundary match (same remedy as PRODUCTION_KEYWORD): 'kubectl' must
			// not fire on 'kubectlen', 'helm upgrade' must not fire inside a larger
			// token. Patterns are lowercased and matched case-insensitively.
			input.config.highCommandPatterns.some((pattern) =>
				new RegExp(`\\b${pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(cmd)
			)
		)
	) {
		reasons.add("Uses high-risk command");
		matchedRules.add("HIGH_COMMAND");
	}

	if (input.config.productionKeywords.some((keyword) =>
		// Word-boundary match so "prod" no longer fires on "reproduce"/"reprod",
		// and "deploy" doesn't fire on substrings inside other words. Keywords
		// are matched case-insensitively against the original prompt.
		new RegExp(`\\b${keyword.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i").test(input.prompt ?? "")
	)) {
		reasons.add("Prompt mentions production or sensitive operations");
		matchedRules.add("PRODUCTION_KEYWORD");
	}

	if (matchedRules.size > 0) {
		return {
			tier: "HIGH",
			reasons: [...reasons],
			matchedRules: [...matchedRules],
			candidatePaths: normalizedPaths,
			proposedCommands: normalizedCommands,
			promptSummary: summarizePrompt(input.prompt ?? ""),
			overridden: false,
		};
	}

	// Text files cannot be executed, sourced, or imported. Treating them
	// as LOW regardless of path matches user intent (edit README / AGENTS.md /
	// notes) without forcing every prompt to name the path. Code-bearing
	// extensions (.ts, .sh, ...) still default to MED, so this is not a footgun.
	const SAFE_TEXT_EXTENSIONS = [".md", ".markdown", ".txt"];
	const isSafeTextPath = (path: string) =>
		SAFE_TEXT_EXTENSIONS.some((ext) => path.toLowerCase().endsWith(ext));

	const allLow =
		normalizedPaths.length > 0 &&
		normalizedPaths.every(
			(path) =>
				isSafeTextPath(path) ||
				input.config.lowPaths.some((prefix) => path.includes(prefix)),
		);

	if (allLow) {
		return {
			tier: "LOW",
			reasons: ["Only low-risk paths targeted"],
			matchedRules: ["LOW_PATHS_ONLY"],
			candidatePaths: normalizedPaths,
			proposedCommands: normalizedCommands,
			promptSummary: summarizePrompt(input.prompt ?? ""),
			overridden: false,
		};
	}

	// Fallback for queries with no extracted paths and no proposed commands.
	// Placed after LOW_PATHS_ONLY so that any future path-inference step
	// (e.g. extracting paths from a screenshot or file content) gets caught by
	// the safe-path check before this fires.
	if (normalizedPaths.length === 0 && normalizedCommands.length === 0) {
		return {
			tier: "LOW",
			reasons: ["Read-only query"],
			matchedRules: ["QUERY_ONLY"],
			candidatePaths: normalizedPaths,
			proposedCommands: normalizedCommands,
			promptSummary: summarizePrompt(input.prompt ?? ""),
			overridden: false,
		};
	}

	return {
		tier: "MED",
		reasons: ["Application code change or unknown scope"],
		matchedRules: ["DEFAULT_MED"],
		candidatePaths: normalizedPaths,
		proposedCommands: normalizedCommands,
		promptSummary: summarizePrompt(input.prompt ?? ""),
		overridden: false,
	};
}

/**
 * Recursive partial type for config overrides. Arrays stay whole
 * (`T[] | undefined`) rather than being partially-tupelized.
 */
export type DeepPartial<T> = T extends (infer U)[]
	? U[] | undefined
	: T extends object
		? { [P in keyof T]?: DeepPartial<T[P]> }
		: T;

/**
 * Merge a partial config over a base config. Top-level arrays are replaced
 * wholesale (override semantics). `verificationCommands` is merged key-by-key
 * so a repo can add a language without redeclaring the defaults.
 */
export function mergeConfig(
	base: RiskConfig,
	override: DeepPartial<RiskConfig> | null | undefined,
): RiskConfig {
	if (!override || typeof override !== "object") return base;
	return {
		lowPaths: override.lowPaths ?? base.lowPaths,
		highPaths: override.highPaths ?? base.highPaths,
		highCommandPatterns: override.highCommandPatterns ?? base.highCommandPatterns,
		productionKeywords: override.productionKeywords ?? base.productionKeywords,
		verificationCommands: {
			...base.verificationCommands,
			...(override.verificationCommands ?? {}),
		},
	};
}

const KNOWN_VERIFICATION_BINARIES = new Set([
	"pytest",
	"mypy",
	"ruff",
	"go",
	"cargo",
	"rustc",
	"npm",
	"pnpm",
	"yarn",
	"bun",
	"jest",
	"vitest",
	"mocha",
	"tsc",
	"eslint",
	"prettier",
	"make",
	"cmake",
	"tox",
	"nox",
]);

const VERIFICATION_VERBS = /^(test|tests|run|run-script|check|lint|build|verify)$/;

function gatherConfiguredPatterns(config: RiskConfig): string[] {
	const out: string[] = [];
	const vc = config.verificationCommands ?? {};
	for (const cmds of Object.values(vc)) {
		if (Array.isArray(cmds)) out.push(...cmds);
	}
	return out;
}

/**
 * Decide whether a command is a verification command under the current config.
 *
 * Two signals, either suffices:
 *   1. The command contains a configured pattern as a substring.
 *   2. The command's first token is a known test/runner binary and the
 *      second token (if any) is a verification verb (test, lint, check, ...).
 */
export function isVerificationCommand(command: string, config: RiskConfig): boolean {
	const cmd = (command ?? "").trim();
	if (!cmd) return false;
	// Compound commands (`cd <dir> && npm test`) are common in real runs but
	// defeat both detection paths: the first token is `cd` (not a known
	// verify binary), and substring patterns don't survive the `cd ... && `
	// prefix. Split on shell separators and accept if ANY segment matches.
	const segments = cmd.split(/\s*(?:&&|\|\||;)\s*/).filter(Boolean);
	if (segments.length === 0) return false;
	if (segments.length === 1) return isVerificationCommandSegment(segments[0], config);
	return segments.some((seg) => isVerificationCommandSegment(seg, config));
}

function isVerificationCommandSegment(command: string, config: RiskConfig): boolean {
	const cmd = (command ?? "").trim();
	if (!cmd) return false;
	const lower = cmd.toLowerCase();

	const patterns = gatherConfiguredPatterns(config);
	if (patterns.some((p) => p && lower.includes(p.toLowerCase()))) return true;

	const tokens = lower.split(/\s+/);
	const first = tokens[0] ?? "";
	const second = tokens[1] ?? "";
	if (KNOWN_VERIFICATION_BINARIES.has(first)) {
		if (!second || VERIFICATION_VERBS.test(second)) return true;
		// Typecheck-only invocations: `tsc --noEmit` and similar.
		if (tokens.slice(1).some((t) => t === "--noemit" || t === "--no-emit")) return true;
	}

	// `npx <known-binary>` is treated the same as the binary directly.
	if (first === "npx" && KNOWN_VERIFICATION_BINARIES.has(second)) {
		const rest = tokens.slice(2);
		if (rest.length === 0 || rest.some((t) => VERIFICATION_VERBS.test(t) || t === "--noemit" || t === "--no-emit")) return true;
	}

	// `node <script>` runner — treat as verify-shaped when the script name
	// indicates a test or check (e.g. `node test-foo.mjs`, `node check-x.mjs`,
	// `node foo.test.mjs`). Bare `node script.js` does not match.
	if (first === "node" && second) {
		if (/(^|[\/\\])test[-_.]/.test(second)) return true;
		if (/(^|[\/\\])check[-_.]/.test(second)) return true;
		if (/\.test\.[a-z]+$/.test(second)) return true;
		if (/\.spec\.[a-z]+$/.test(second)) return true;
	}

	return false;
}