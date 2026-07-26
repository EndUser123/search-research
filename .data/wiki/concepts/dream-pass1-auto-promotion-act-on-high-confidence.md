---
title: "/dream Pass 1 auto-promotion: act on high-confidence candidates, don't ask permission"
created: 2026-07-26
source: session-019f94c9
tags: [dream, wiki, auto-promotion, stated-default, harness-engineering, decision]
summary: >
  Pass 1 candidates in /dream that pass validate_wiki_entry.py AND have ≥2
  receipted instances are auto-promoted to wiki/concepts/ instead of being
  proposed for manual operator review. This inverts the default from "ask
  permission" to "ask forgiveness" — the operator sees what was promoted and
  deletes post-hoc if wrong. Follows the stated-default rule and the
  harness-engineering principle of making the right behavior the default.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
relations:
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: instance-of
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation
    type: instance-of
---

# /dream Pass 1 auto-promotion

## Decision context

**The problem:** in session 019f94c9, /dream produced 2 high-confidence wiki candidates. Both had ≥4 receipted instances. Both had clear existing-coverage gaps verified by filesystem grep. Both passed `validate_wiki_entry.py`. The model asked the operator "do you want me to promote these?" — wasting the operator's time on a decision the model had already made with high confidence and clear evidence.

The operator's response: "Why did you even ask me these questions??? This was a waste of my time. Did you have not high confidence in them?"

This is a specific instance of the stated-default rule from AGENTS.md: "When you have already stated a default, lead, or recommendation in your response, act on it rather than asking the user to confirm." The rule exists in prose. It did not fire. The fix is structural: make the skill auto-promote when the mechanical quality gate passes, removing the decision from the model entirely.

The deeper question is why the model asks when it shouldn't. The answer is the same pattern documented across 5+ sessions: under closure pressure, the model defaults to the safest-seeming action. "Ask the operator" feels safer than "act and risk being wrong" — but it's not safer for the operator, who pays the time cost of every unnecessary question. The structural fix is to remove the question entirely by making promotion the default when the quality gate passes.

## The decision

**Pass 1 candidates in `/dream` are auto-promoted** to `P:/.data/wiki/concepts/<slug>.md` when ALL of:
1. ≥2 independent receipted instances (not single-source observations)
2. Pass `validate_wiki_entry.py` (the workspace's mechanical quality gate)
3. No existing wiki concept covers the same pattern (verified by filesystem grep)

Auto-promoted concepts are logged via `append_log.py` and surfaced in the dream output as "PROMOTED: <slug>." The operator reviews what was promoted and deletes post-hoc if wrong.

**What stays propose-only:** Pass 2 (contradictions — require operator judgment on which side wins, because both sides may be valid in different scopes), Pass 3 (retirements — dormant in v1, but when activated will require operator approval because deletion is harder to reverse than addition), Pass 4 (operator profile — safety boundary: changes to the operator's documented collaboration style always require human approval, because the model has a sycophancy incentive to flatter the profile and auto-promotion would amplify that bias).

## Steelman of the rejected alternative

**Rejected: keep all passes as propose-only.** The argument for manual promotion: the operator has final authority over what enters the wiki; auto-promotion risks flooding the wiki with low-quality entries that the operator then has to review and delete; the operator's delete-after-the-fact workload is higher than the approve-before-the-fact workload because deletes require finding the entry first.

**Why rejected:** the quality gate (`validate_wiki_entry.py` + ≥2 receipts + no-duplicate check) already filters out the low-quality entries the steelman worries about. The operator's actual experience (this session) was that asking permission for high-confidence decisions was more costly than reviewing promoted entries would be — because the ask interrupts the operator's flow and forces a decision they would have made identically anyway. The delete-after-the-fact path is only exercised when the model is wrong, which the quality gate makes rare. This mirrors the pattern documented in [[close-auto-invokes-aar]] where a prose boundary ("never auto: run /aar") was treated as design intent but was actually a regression that blocked correct behavior. The lesson: defaults that require human action to proceed correctly will be skipped under pressure; defaults that proceed correctly and allow human override afterward are more reliable. The cost asymmetry also favors auto-promotion: deleting a wrong entry takes 10 seconds; asking permission for a right entry costs the operator's attention and flow — which is worth far more than 10 seconds. When the quality gate is mechanical and the action is reversible, "ask forgiveness" is structurally superior to "ask permission."

A counter-consideration: auto-promotion could flood the wiki if the quality gate is misconfigured (too permissive). The defense is the falsifier (monitor delete rate after 10 runs) and the fact that the validator has been tested across 50+ real entries this month.
If the delete rate exceeds 20%, the threshold tightens (increase instance count, add cross-model review).

## Connection to this session's other findings

Session 019f94c9 produced several related decisions and findings that form a cluster around the theme of "make good behavior the path of least resistance through structural enforcement":

- [[trusted-exit-status-fallacy-pipeline-ground-truth]] — downstream tools should grep artifacts, not trust exit codes. The /dream auto-promotion is an instance: the validator IS the artifact check, not a summary-field trust.
- [[validator-script-closure-pressure-backstop]] — post-hoc validator scripts catch closure-pressure minimization. The validator that gates auto-promotion (`validate_wiki_entry.py`) is itself one of these scripts.
- [[close-auto-invokes-aar]] — the 5th documented instance of skipping mandatory work under closure pressure. The /dream auto-promotion removes one such decision point (the "should I promote?" question) from the model's closure-pressure surface.

The meta-pattern: every place where the model makes a judgment call that could be replaced by a mechanical check + post-hoc review, the mechanical check should win. The model's judgment is valuable for deciding WHAT to write; it's unreliable for deciding WHETHER to ask permission for things it already decided to do. The workspace has documented this failure class across 5+ sessions — each time a rule existed in prose ("act on defaults"), each time it didn't fire under pressure, each time the fix was structural (remove the decision point). This concept records one more instance of that structural fix and the principle it instantiates.

## Falsifier

This decision is wrong if: the operator frequently deletes auto-promoted concepts (the quality gate is too permissive, flooding the wiki with noise), OR the auto-promotion causes a duplicate/stale concept that the no-duplicate check misses. Test: after 10 /dream runs, check the delete rate of auto-promoted concepts. If >20%, tighten the gate (increase instance threshold, add a cross-model review step).

## What this means for our workspace

- `/dream` now writes directly to `wiki/concepts/` for qualifying Pass 1 candidates — no more "operator reviews and promotes" step for high-confidence findings
- The mechanical quality gate (`validate_wiki_entry.py`) is the structural enforcement; the model's judgment is removed from the promotion decision for qualifying candidates
- This is the same pattern as [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]: make the right behavior the default, not a decision the model chooses under pressure
- Other skills that produce high-confidence outputs with mechanical quality gates should consider the same pattern (e.g., `/www` Phase 3 wiki writes that pass the validator)
- This connects to [[evidence-first-default-and-needless-confirmation]] (the broader rule this structurally enforces) and [[mandatory-step-enforcement-code-over-prose]] (moving from prose rule to code-enforced behavior)
- The [[llm-dreaming-memory-consolidation]] concept's "non-destructive consolidation" principle is preserved — auto-promotion writes new concepts but never modifies existing ones or procedural memory

## Receipts

- `~/.grok/skills/dream/SKILL.md` — 4 locations changed from "propose only" to "auto-promote when validator passes + ≥2 receipted instances" (Stance, Hard rules, Non-goals, Step 6)
- `~/.grok/skills/wiki/scripts/validate_wiki_entry.py` — the mechanical quality gate that controls auto-promotion
- Session 019f94c9: operator feedback "Why did you even ask me these questions???" — the incident that motivated the change
- `~/.grok/AGENTS.md` § "Stated-default rule — act, don't ask" — the prose rule this structurally enforces

## Broader pattern: the ask-permission-vs-ask-forgiveness axis

This decision is one instance of a broader architectural pattern in this workspace. The same axis appears in:

1. **Auto-commit authority** (`[[auto-commit-authority-isolation]]`): the workspace shifted from "ask before committing" to "commit automatically, operator can revert." The rationale was identical: asking wastes operator time on decisions they would have made identically.
2. **`/close` auto-invoking `/aar`** (`[[close-auto-invokes-aar]]`): the workspace shifted from "recommend /aar" to "auto-invoke /aar." Same rationale.
3. **`/wiki` default mode** (this skill): `/wiki` already writes concepts directly by default. The operator reviews post-hoc. `/dream` was the holdout — it proposed instead of writing.

The unifying principle: **when the model has high confidence + mechanical quality gate + post-hoc review path, the default should be to act, not to ask.** The ask-permission default belongs in contexts where the action is irreversible (destructive git, publishing, sending) or where the quality gate is absent (judgment-only decisions). Wiki promotion is reversible (delete the file) and quality-gated (validator). Therefore: auto-promote.

The failure mode this prevents is documented across [[code-orchestrates-model-judges-skill-scale]] (4 rationalizations to skip mandatory work) and [[reactive-pattern-matching-and-closure-pressure]] (pattern-completion overrides rule-following). The model generates plausible reasons to ask instead of act — "the operator might disagree," "I should confirm," "this is a decision the operator should make" — all of which are the same closure-pressure pattern wearing a helpful-looking mask. The structural fix removes the decision point entirely.

## Sources

- `~/.grok/skills/dream/SKILL.md` (commit c773ad0 in ~/.grok)
- `~/.grok/AGENTS.md` § "Evidence-first default" and § "Stated-default rule"
- `P:/.data/wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md`
- Session 019f94c9 operator feedback (2026-07-26)
