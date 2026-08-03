---
title: "Subagent output token exhaustion — decomposition by output volume, not prompt tightening"
created: 2026-08-02
source: session-019fb177
tags: [subagent-decomposition, max-tokens, review-specialists, output-volume, model-limitations]
summary: >
  When a subagent hits max_tokens_truncation, the instinct is to tighten the
  prompt or switch to a more expensive model. Both fail. The ceiling is about
  output generation volume, not prompt size. The fix is task decomposition:
  shrink the task (per-file, per-check) so each subagent's output fits within
  the model's output ceiling.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: related
  - target: wiki/concepts/subagent-shell-quoting-durable-fix.md
    type: related
---

# Subagent output token exhaustion

## Decision context

During a /review session (2026-08-02), a correctness specialist reviewing 3
files with 6 verification commands hit `max_tokens_truncation` on MiniMax-M3
(~30K output ceiling). The retry with a tighter prompt ("under 2000 words")
also failed — the analysis itself (edge-case testing + evidence-backed findings)
requires ~25K tokens of output regardless of prompt size.

## The pattern

The `max_tokens` ceiling constrains **output generation volume**, not input
prompt size. A shorter prompt does not reduce output. The analysis produces
the same number of findings with the same evidence depth regardless of how
concisely the instructions are worded.

**Common high-output task shapes (decompose these):**
- Correctness review of N files with M edge-case tests each → decompose per-file
- Full-package audit with multiple lenses → decompose per-lens × per-file-group
- Any task that asks "run tests + analyze output + write detailed findings with evidence"

**What does NOT help:**
- Tightening the prompt ("keep under 2000 words") — the analysis volume is constant
- Switching to a more expensive model — same ceiling, more cost
- Retrying with the same task — same truncation

**What DOES help:**
- Per-file decomposition: N specialists × ~8K output each, instead of 1 specialist × 25K
- Two-pass findings: first pass writes short findings (ID + title + severity), second pass fills detail
- Per-lens × per-file-group: when both lens diversity AND file count are high

## What this means for our workspace

The /review SKILL.md already has rule 23 (task decomposition) and the
output-size estimation heuristic. This concept documents the underlying
principle so other skills ([[check-vs-review-complementary-not-redundant]],
/tp parallel panel, [[coding-model-pool-tier-1-tier-2]]) can apply the same
pattern. It also relates to [[subagent-shell-quoting-durable-fix]] — both
are failure modes where the agent's instinct (retry harder) is the wrong
response, and the structural fix (change the task shape) is the right one.

**Output estimation heuristic:** expected findings × ~500 tokens/finding
(with evidence + verification receipts). If estimated output > 50% of the
model's output ceiling, decompose before spawning. This applies to
[[model-pool-selection-policy-speed-quota-diversity]] decisions: when
choosing between one expensive model and N cheap models, the N cheap models
may be the only option that fits within output ceilings.

**Output estimation heuristic:** expected findings × ~500 tokens/finding
(with evidence + verification receipts). If estimated output > 50% of the
model's output ceiling, decompose before spawning.

**Model output ceilings (approximate, 2026-08):**
- MiniMax-M3: ~30K output tokens
- Parent Grok (GLM-5.2): higher but variable
- DeepSeek V4 Flash: similar to M3

## Silent zero-output resume (distinct from truncation)

**Finding (2026-08-02, session 019fc30c):** A resumed writer subagent (MiniMax-M3, `/design` Step 4 revision round 2) produced **exit 0 with 103 tool calls in 6.15 seconds, but zero effective edits** — all 14 review findings remained `Status: open` in the review file. This is NOT `max_tokens_truncation` (no error was raised). The resumed agent's accumulated transcript from prior rounds (draft + round 1 revision + consistency sweep) was so large that the agent exhausted its reasoning budget just processing the context, leaving nothing for actual editing.

**Why this is more dangerous than truncation:**
- Truncation produces an explicit error (`max_tokens_truncation`) — the orchestrator knows it failed
- Silent zero-output produces exit 0 — the orchestrator thinks the revision succeeded
- Detection requires comparing the review file's Status fields before and after the resume
- If undetected, the design loop spins: re-review finds the same issues, re-revision produces no edits, indefinitely

**Detection heuristic:** after any `resume_from` revision, check whether the number of `Status: open` findings actually decreased. If it stayed the same or increased despite the agent claiming completion, the resume was a silent no-op. Fall back to a fresh agent with a focused prompt.

**Root cause is the same as truncation:** accumulated transcript context. The difference is whether the model fails loudly (truncation) or silently (processes context but produces no actionable output). Both share the same fix: fresh agent instead of resume when context is large.

**Related:** [[multi-subagent-orchestration-workflow-failure-patterns]] § "Generalization: Any skill using resume_from across ≥2 rounds is at risk" — this finding extends that generalization from "may truncate" to "may also silently no-op."

## Falsifier

This concept is wrong if, within 6 months:
- Prompt tightening is found to reliably prevent max_tokens_truncation (it doesn't)
- A model appears with effectively unlimited output (eliminating the need for decomposition)
- Task decomposition produces lower-quality findings than a single large specialist
- The silent zero-output variant is found to be model-specific (only MiniMax-M3) rather than a general property of context-saturated resumes

## Receipts

- Session 019fb177 (2026-08-02): correctness specialist failed on MiniMax-M3, 3 files, 30K ceiling
- Retry with "under 2000 words" also failed
- Fix: per-file decomposition (3 specialists × ~8K output each) — all succeeded
- /review SKILL.md rule 23 + output-size estimation heuristic (commit `f494cf4`)
- Session 019fc30c (2026-08-02): resumed writer `/design` round 2, 6.15s, 103 tool calls, 0 effective edits — all 14 findings remained Status: open. Receipt: `get_command_or_subagent_output` showed exit 0; review file grep confirmed 0 findings changed to Status: addressed. Fix: fresh writer with focused prompt produced all 14 addressed in 457s.

## Auto-related

- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[parallel-subagent-wait-all-gate]]
- [[skill-catalog]]

