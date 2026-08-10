---
title: "Enforcement and hooks: domain overview"
created: 2026-08-02
source: session-2026-08-02-wiki
tags: [enforcement, hooks, structural-fix, domain-overview]
summary: >
  Index of 78 wiki concepts related to agent enforcement, hooks, structural
  fixes, and verification gates. Grouped into 5 sub-themes: Enforcement
  Philosophy, Hook Implementation (Grok Build), Verification Gates, Skill
  Enforcement, and Close/Ship Enforcement. The core principle: prose rules
  are necessary but insufficient; hooks provide deterministic enforcement.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
---

# Enforcement and hooks: domain overview

## Decision context

This workspace's governance model (AGENTS.md rules, SKILL.md files, hook
scripts) represents a bet on structural enforcement over prose-only
instructions. The wiki accumulated 78 concepts tagged `enforcement`, `hooks`,
or `structural-fix` — this overview makes the domain navigable.

## Sub-theme 1: Enforcement Philosophy (code-over-prose, structural-fix, harness design)

| Concept | One-line summary |
|---|---|
| [[mandatory-step-enforcement-code-over-prose]] | The foundational principle: move control flow from prose to code |
| [[prose-rules-vs-structural-enforcement-research-2026]] | **NEW** — 2026 production evidence validating hooks > skills > prose |
| [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] | Harness design principle |
| [[mechanical-enforcement-over-behavioral-reminder]] | Mechanical > behavioral for preference capture |
| [[external-state-cross-check-as-structural-fix]] | Design heuristic for structural fixes |
| [[advisory-vs-mandatory-triggers]] | When to enforce structurally vs advisably |
| [[couple-triggers-to-events-that-actually-fire]] | Trigger coupling pattern |
| [[trusted-computing-base-for-agent-enforcement]] | Ring separation on a host with universal file access |
| [[fabrication-ceremony-tax-compounding-cost]] | The cost of structural defenses against lying |
| [[enforcement-hierarchy-and-compaction-strategy]] | Hierarchy and compaction for instruction files |

## Sub-theme 2: Hook Implementation (Grok Build specifics)

| Concept | One-line summary |
|---|---|
| [[grok-pretooluse-deny-contract-verified]] | PreToolUse deny contract verified end-to-end |
| [[grok-build-hook-exit-code-1-stderr-as-failure-signal]] | Exit code 1 + stderr as failure signal |
| [[grok-build-stop-hook-patterns-and-feedback-mechanism]] | Stop hook community implementations |
| [[grok-build-stop-hook-payload-lastassistantmessage]] | Payload field: lastAssistantMessage |
| [[grok-build-stop-hook-agent-text]] | Accessing agent text via chat_history.jsonl |
| [[grok-per-hook-disable-layer-silent-suppression]] | Disabled-hooks file silently suppresses |
| [[grok-build-disabled-hooks-per-hook-layer]] | Per-hook disable layer |
| [[grok-pretooluse-matcher-and-readonly-fastpath]] | What failed in canary tests |
| [[session-start-hooks-cannot-inject-visible-context-grok-build]] | SessionStart can't inject visible context |
| [[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]] | UserPromptSubmit can run Python, can't inject |
| [[hook-failure-mode-taxonomy]] | General, Grok-specific, exec-gate taxonomy |
| [[llm-judgment-hooks]] | Enforcement beyond regex |
| [[windows-gitbash-hook-invocation]] | Shebang line invocation on Git Bash |
| [[hook-script-capability-derivation-receipt-loop-fix]] | Receipt loop fix |
| [[quality-gate-hook-system-implementation]] | Working quality gate implementation |
| [[verify-before-write-hook-design]] | PreToolUse hook for external-sourced constants |

## Sub-theme 3: Verification Gates (maker-checker, receipts, verify-before-done)

| Concept | One-line summary |
|---|---|
| [[maker-checker-required-for-enforcement-work]] | Three-role conflict in agent-authored enforcement |
| [[execution-receipts-for-executable-artifacts]] | Test before trust |
| [[posttooluse-auto-verify-eliminates-stop-hook-stale-receipt-blocks]] | Auto-verify at edit time |
| [[posttooluse-fires-on-tool-call-completion-not-process-completion]] | Auto-backgrounded commands skip receipts |
| [[stop-hook-verification-receipt-capability-hierarchy]] | Capability hierarchy for receipt checks |
| [[skill-step-receipts-checked-by-hooks]] | Per-step evidence-gated lifecycle |
| [[verifier-false-confidence-receipt-claims-success-when-tool-absent]] | Receipts claiming success when verifier never ran |
| [[verify-against-existing-state-before-defensive-mechanisms]] | Check existing state before building defenses |
| [[verify-gate-enforcement-gap-document-vs-runtime]] | Documentation vs runtime invocation gap |
| [[lexical-vs-semantic-verification-gap]] | Gates that fire correctly on the wrong thing |
| [[test-coverage-gap-detection-structural-fix]] | Structural fix for shipping without tests |
| [[self-verifying-mutations-verification-tools-modify-files]] | When verification tools also modify files |
| [[inference-in-code-blind-spot]] | Writing guessed constants without verification |

## Sub-theme 4: Skill Enforcement (auto-invocation, compliance, performance)

| Concept | One-line summary |
|---|---|
| [[skill-auto-invocation-reliability]] | Does auto-invocation work? Does host matter? |
| [[skill-performance-and-reliability]] | Maximizing value while preventing bypass |
| [[llm-instruction-non-compliance-activation-gap-2026]] | Why agents read skills but don't follow them |
| [[langgraph-vs-wrapper-scripts-skill-enforcement]] | Decision and rationale |
| [[enforcing-kb-consultation-before-action-methods]] | Methods practitioners like/dislike |
| [[rule-not-fired-vs-rule-doesnt-exist]] | Distinguish non-firing from non-existence |
| [[intg2-resolved-gate-state-set-needs-llm-check]] | needs_llm_check as valid terminal state |
| [[cognitive-enforcement-patterns-for-ai-coding-agents]] | Mandatory self-checks, epistemic discipline |
| [[dual-path-hazard-delete-manual-when-adding-mechanical]] | Delete manual when replacing with mechanical |

## Sub-theme 5: Close/Ship Enforcement (authority, logs, process compliance)

| Concept | One-line summary |
|---|---|
| [[close-authority-state-machine-design]] | Design rationale and known flaws |
| [[close-single-authority-renderer]] | Single rendering authority for close reports |
| [[ship-phase-log-enforcement-design]] | Phase-log enforcement for compliance |
| [[ship-receipt-mechanical-generation-from-per-check-results]] | Mechanically generated receipts |
| [[list-before-claim-for-destructive-proposal-actions]] | List before claim pattern |
| [[validator-script-closure-pressure-backstop]] | Validator as closure-pressure backstop |
| [[optimal-vs-blanket-rule-application]] | When to split a default rule per-instance |
| [[symptom-to-abstraction-escalation]] | Generalize session fixes to workspace abstractions |
| [[exemption-logic-as-conflict-signal]] | Exemption logic as conflict signal |

## Behavioral enforcement (sycophancy, defensiveness, honesty)

| Concept | One-line summary |
|---|---|
| [[llm-sycophancy-calibration-failure-research-2026]] | **NEW** — Stanford/MASK/AbstentionBench evidence |
| [[llm-defensiveness-under-pushback-structural-fix]] | Skill-level fixes for defensiveness |
| [[theatrical-contrition-and-over-apologetic-response-patterns]] | UX optimization for correction flows |
| [[mechanisms-for-thought-partner-behavior]] | Hooks, skills, agents for thought-partner behavior |
| [[model-fit-and-post-hoc-behavioral-detection]] | Matching models to operator style |
| [[behavioral-detection-approaches-practitioner-survey]] | Practitioner approaches to behavioral detection |

## Sub-theme 6: Knowledge-artifact consistency (revision invalidation, state consistency)

| Concept | One-line summary |
|---|---|
| [[research-artifact-revision-invalidation]] | Research artifacts need state consistency like software systems — changed premises invalidate downstream derived claims |

## What this means for our workspace

The enforcement domain is the wiki's second-largest (78 concepts). The 2026
external research confirms the core architectural bet: "if it must never
happen, make it a hook." The highest-ROI improvement opportunity is
**tool-description quality** (33%→100% accuracy jump from better schemas).
The multi-turn coherence degradation (90%→10-15%) validates the compaction
recovery and handoff format investments.

## Evidence

This is a reference/index document — no mechanism claims about local code.
Concept counts derived from tag scan (`P:/tmp/concept_enumerate.py`, 2026-08-02).
External validation cited from research linked in [[prose-rules-vs-structural-enforcement-research-2026]].

## Falsifier

This overview is stale when new enforcement concepts are added without
updating it. Run `/wiki enforcement-domain-overview` to regenerate.

## Related

- [[multi-agent-fleet-domain-overview]] — the companion fleet domain overview
- [[design-patterns-domain-overview]] — the trigger/skill pattern overview
- [[mandatory-step-enforcement-code-over-prose]] — the foundational principle

## Auto-related

- [[skill-graph]]
- [[portable-ai-brain-pattern]]
- [[skill-catalog]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]

