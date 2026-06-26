/**
 * In-memory state holder for the risk-policy extension.
 *
 * Per the spec: only current-session state. No persistence across
 * restarts. Manual override is tracked separately from computed
 * assessment. Verification resets on each new top-level user task
 * (the caller decides what counts as "new" — see the entrypoint).
 */

import { createEmptyVerificationState } from "./verification-state.ts";
import { POLICY_BY_TIER } from "./risk-policy.ts";
import type {
	HaPatchSnapshot,
	HaPatchStatus,
	RiskAssessment,
	RiskPolicy,
	RiskStateSnapshot,
	RiskTier,
	VerificationState,
	WorktreeSnapshot,
} from "./risk-types.ts";

export interface StoredFinding {
	readonly kind: "simplify" | "review";
	readonly path: string;
	readonly severity: "low" | "med" | "high";
	readonly message: string;
	readonly turnId: string;
	readonly storedAt: string;
	readonly disposition?: "addressed" | "dismissed_with_reason" | "accepted_as_followup";
	readonly dispositionNote?: string;
	readonly disposedAt?: string;
	readonly id: string;
}

export class RiskStateStore {
	private assessment: RiskAssessment | null = null;
	private policy: RiskPolicy = POLICY_BY_TIER.LOW;
	private verification: VerificationState = createEmptyVerificationState();
	private override: RiskTier | null = null;
	private findings: StoredFinding[] = [];
	private worktree: WorktreeSnapshot | null = null;
	private haPatch: HaPatchSnapshot = { status: "unchecked", checkedAt: "", details: [] };
	private lastPrompt: string = "";

	getSnapshot(): RiskStateSnapshot | null {
		if (!this.assessment) return null;
		return {
			assessment: this.assessment,
			policy: this.policy,
			verification: this.verification,
			timestamp: new Date().toISOString(),
			worktree: this.worktree ?? undefined,
			haPatch: this.haPatch,
		};
	}

	setAssessment(assessment: RiskAssessment, policy: RiskPolicy): void {
		this.assessment = assessment;
		this.policy = policy;
	}

	setLastPrompt(prompt: string): void {
		this.lastPrompt = prompt;
	}

	getLastPrompt(): string {
		return this.lastPrompt;
	}

	updateVerification(partial: Partial<VerificationState>): void {
		this.verification = { ...this.verification, ...partial };
	}

	resetVerification(): void {
		this.verification = createEmptyVerificationState();
	}

	setOverride(tier: RiskTier | null): void {
		this.override = tier;
	}

	getOverride(): RiskTier | null {
		return this.override;
	}

	setFindings(findings: StoredFinding[]): void {
		this.findings = findings.slice();
	}

	getFindings(): readonly StoredFinding[] {
		return this.findings.slice();
	}

	clearFindings(): void {
		this.findings = [];
	}

	recordDisposition(input: {
		id: string;
		disposition: "addressed" | "dismissed_with_reason" | "accepted_as_followup";
		note?: string;
	}): { ok: boolean; remainingHigh: number } {
		const idx = this.findings.findIndex((f) => f.id === input.id);
		if (idx < 0) return { ok: false, remainingHigh: 0 };
		const existing = this.findings[idx]!;
		this.findings[idx] = {
			...existing,
			disposition: input.disposition,
			dispositionNote: input.note,
			disposedAt: new Date().toISOString(),
		};
		const remainingHigh = this.findings.filter(
			(f) => f.kind === "review" && f.severity === "high" && !f.disposition,
		).length;
		return { ok: true, remainingHigh };
	}

	getUnaddressedHigh(): readonly StoredFinding[] {
		return this.findings.filter(
			(f) => f.kind === "review" && f.severity === "high" && !f.disposition,
		);
	}

	setWorktree(wt: WorktreeSnapshot): void {
		this.worktree = wt;
	}

	getWorktree(): WorktreeSnapshot | null {
		return this.worktree;
	}

	setHaPatch(status: HaPatchStatus, details: string[]): void {
		this.haPatch = { status, checkedAt: new Date().toISOString(), details };
	}

	getHaPatch(): HaPatchSnapshot {
		return this.haPatch;
	}
}