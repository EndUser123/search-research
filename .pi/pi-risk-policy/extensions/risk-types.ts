/**
 * Core types for the risk-policy extension.
 *
 * Three discrete tiers (LOW / MED / HIGH) with deterministic attached
 * controls. No probabilistic scoring, no hidden weights.
 */

export type RiskTier = "LOW" | "MED" | "HIGH";

export interface RiskConfig {
	lowPaths: string[];
	highPaths: string[];
	highCommandPatterns: string[];
	productionKeywords: string[];
	verificationCommands: {
		default: string[];
		typescript?: string[];
		python?: string[];
		[key: string]: string[] | undefined;
	};
}

export interface RiskAssessment {
	tier: RiskTier;
	reasons: string[];
	matchedRules: string[];
	candidatePaths: string[];
	proposedCommands: string[];
	promptSummary: string;
	overridden: boolean;
}

export interface RiskPolicy {
	requirePlan: boolean;
	requireVerification: boolean;
	manualApplyOnly: boolean;
	allowDestructiveShell: boolean;
	allowInfraChanges: boolean;
	uiLabel: string;
}

export interface VerificationState {
	planned: boolean;
	verificationRan: boolean;
	verificationPassed: boolean;
	diffSummarized: boolean;
	manualApprovalRecorded: boolean;
	lastVerificationCommand?: string;
	lastVerificationExitCode?: number;
	planText?: string;
	planSource?: "user" | "auto";
	diffSummary?: string;
	verificationSource?: "user" | "auto";
}

export interface WorktreeSnapshot {
	inWorktree: boolean;
	worktreeName: string | null;
	mainGitDir: string | null;
	cwd: string;
	checkedAt: string;
}

export type HaPatchStatus = "active" | "missing" | "unchecked";

export interface HaPatchSnapshot {
	status: HaPatchStatus;
	checkedAt: string;
	details: string[];
}

export interface RiskStateSnapshot {
	assessment: RiskAssessment;
	policy: RiskPolicy;
	verification: VerificationState;
	timestamp: string;
	worktree?: WorktreeSnapshot;
	haPatch?: HaPatchSnapshot;
}