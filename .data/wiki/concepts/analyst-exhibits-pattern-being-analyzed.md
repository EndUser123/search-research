---
title: "The analyst exhibits the pattern being analyzed"
created: 2026-07-21
last_verified: 2026-08-02
source: AAR report 11 (console_ec84a662, 20260721-220000)
tags: [meta-pattern, self-reference, analyst-bias, blind-spot, calibration]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 2
summary: >
  When an agent analyzes a failure pattern (e.g., "the model fabricates
  under uncertainty"), the agent is itself subject to the same pattern
  during the analysis. The analyst is not exempt from the failure mode
  being analyzed. This creates a self-referential blind spot where the
  analysis report itself contains instances of the pattern it documents.
---

# The analyst exhibits the pattern being analyzed

## The pattern

An agent produces an AAR report documenting that "the model fabricates causal claims without verification." The AAR report itself contains a causal claim without verification. The agent who diagnosed fabrication fabricated during the diagnosis.

This is not hypocrisy — it's the same cognitive pressure operating at both levels. The helpfulness bias that causes fabrication under uncertainty also causes fabrication during the analysis of fabrication.

## Why it happens

1. **The analyst and the analyzed share the same training.** The AAR orchestrator is the same model that produced the failures. The bias is architectural, not situational.
2. **Analysis feels like a different task.** "Describing a pattern" feels different from "making a claim about the world." But causal assertions in the analysis ARE claims about the world and need the same receipts.
3. **The calibration gate catches the analyzed instances but not the analyst's.** The AAR's Lesson Calibration Gate checks lessons for evidence backing — but the analysis between the lessons is not gated.

## The fix

- **Apply the same standard to the analysis as to the analyzed.** Every causal claim in the AAR report (not just the headline lessons) should cite evidence.
- **Use a fresh-subagent verifier on the AAR report itself.** A different context reading the report can catch analyst-level instances that the original context cannot see.
- **Label the meta-level explicitly.** If the AAR documents "narrativization without verification," add a check: "Did this AAR narrativize anything without verification?"

## Extension: applies to fix sets, not just analysis claims (refined 2026-07-26c)

The pattern generalizes beyond the analysis *narrative* to the analysis *output* — specifically, the recommended fixes. A `/why` (or `/aar`, or any RCA) investigation that documents "closure pressure caused unverified claims" and then recommends four prose rules as fixes is exhibiting the pattern at the fix level: the fixes are themselves unverified claims (no test that they'll work, no competing-fix analysis, no falsifier). The analyst's recommendation set is subject to the same closure pressure that produced the original failure.

**Concrete instance (2026-07-26, session 019f9f48):** a `/why` run on the symlink-recommendation failure correctly diagnosed "receipt misattribution" and recommended four fixes — all prose rules. The recommendation set exhibited the exact pattern the analysis documented: prose rules are the mitigation class the workspace's own pattern library (`[[mandatory-step-enforcement-code-over-prose]]`, 2026-07-20) flags as decaying under closure pressure. The operator caught it by asking "did you critically review these fixes?" — the same question that catches the original pattern.

**Fix at the skill level:** `/why` Step 14 should run the `[[external-state-cross-check-as-structural-fix]]` design heuristic on its own fix set. The wiki already has the test: *"When you catch yourself proposing 'add a rule'...run the test: (1) what external state would have flagged this failure? (2) Can the actor manipulate that state?"* The skill needs to invoke it — not re-derive it.

**Naming convention:** the field calls this **self-referential agent improvement** (Gödel Agent, arxiv 2410.04444, Oct 2024). The workspace calls it "the analyst exhibits the pattern being analyzed." Same pattern, different vocabulary.

## Evidence

Three independent instances documented across sessions:

1. **R11 L4** (session ec84a662, 2026-07-21): The AAR report documented fabrication patterns while itself containing unverified causal claims about those patterns.
2. **Session 019f8507** (2026-07-21): The AAR documented "narrativization without verification" (P2, 3 episodes) while the AAR report itself contained narrativized claims ("nobody closes handoffs," "drift-endemic problem") that the operator corrected.
3. **Session 019f9f48** (2026-07-26): `/why` run on the symlink-recommendation failure recommended four prose fixes; operator's "did you critically review these?" question surfaced that all four were the decaying-mitigation class the wiki already documents.

The pattern also maps to the academic literature: Gödel Agent (arxiv 2410.04444) documents self-referential agent improvement as a recognized pattern class.

## What this means for our workspace

1. **Every RCA and AAR must pass its own fix-set through the same evidence standard as the findings.** This is now structurally enforced by `/why` Step 14's external-state-cross-check heuristic, but only if the skill actually invokes it. The gap between "the wiki has the test" and "the skill runs the test" is where this pattern hides.

2. **Fresh-subagent verification on analysis artifacts.** When `/aar` or `/why` produces a report, a fresh subagent (different context) should scan the report for instances of the pattern being documented. This is the `/check` and `/review` composition: the reviewer is not the analyst.

3. **The epistemic debt scanner now catches this pattern at the concept level.** A wiki concept with `verification: inferred` that documents a verification failure pattern is itself an instance of the pattern — the concept should be upgraded to `verified` with receipts before it's cited as authoritative. This concept was itself `inferred` until 2026-08-02; the upgrade to `multi-source-verified` with 3 receipted instances closes the self-referential loop.

## Falsifier

This concept is wrong if:
- Future AAR/RCA reports consistently pass the same evidence standard they apply to their subjects (the pattern stops appearing in practice).
- The Gödel Agent framing (arxiv 2410.04444) is shown to be a different phenomenon than what's documented here (if self-referential improvement is structurally distinct from analyst-level bias).
- A structural fix (e.g., mandatory fresh-subagent verification on all analysis artifacts) eliminates the pattern entirely — at which point this concept becomes a historical reference rather than an active warning.

## Related

- [[writing-discipline-not-enforced]] — the analyst writing "verify" without verifying is the same gap
- [[plausible-narratives-substitute-for-verification]] — the specific pattern the analyst exhibits
- [[mandatory-step-enforcement-code-over-prose]] — prose rules decay; the fix-level pattern is recommending prose rules
- [[external-state-cross-check-as-structural-fix]] — the heuristic that catches fix-level instances

## Auto-related

- [[skill-graph]]
- [[agent-reliability-patterns-and-production-validation]]
- [[skill-authoring-patterns-dos-and-donts]]
- [[model-fit-and-post-hoc-behavioral-detection]]
- [[circuit-breaker-pattern]]

