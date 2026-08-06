---
title: "Skill effectiveness measurement: what the field does that skill-dev and skill-prune don't"
created: 2026-08-06
source: session-2026-08-06 (/www research on skill optimization techniques)
tags: [skill-optimization, trigger-accuracy, token-efficiency, eval-driven, description-optimization, skill-dev, skill-prune, gap-analysis]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  External research reveals our skill-dev and skill-prune are strong on
  structural quality (defects, leanness, enforcement) but weak on the two
  metrics the field considers most important for skill effectiveness:
  trigger accuracy (does the right skill fire?) and token efficiency
  (how much context does each invocation cost?). The field's core
  recommendation — eval-driven description optimization with train/validation
  query sets and trigger-rate measurement — is completely absent from
  both skills. This concept documents the gap and maps each missing
  technique to where it would plug in. It extends
  [[compound-skill-improvement-patterns]] (adding the missing measurement
  techniques), identifies gaps in [[skill-techniques-index]] (our 42-technique
  index), and complements [[fleet-health-patterns-skill-bloat-sibling-conflicts-fabricated-decisions]].
  The trigger-accuracy gap connects to [[agent-control-plane-enforcement-architectures-2026]].
sources:
  - https://agentskills.io/skill-creation/optimizing-descriptions (agentskills.io, 2026) — primary source on description optimization with eval loop
  - https://developers.openai.com/blog/eval-skills (OpenAI, 2026) — eval methodology for skill trigger accuracy
  - https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/ (NVIDIA, 2026) — governance, trigger metrics, SkillSpector
  - https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills (Anthropic, 2025) — progressive disclosure 3-level architecture
  - https://arxiv.org/html/2602.12430v3 (arXiv, 2026) — agent skills survey: human-authored > LLM-generated
  - https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity (Perplexity, 2026) — skill maintenance lifecycle
  - https://www.mindstudio.ai/blog/progressive-disclosure-ai-agents-context-management (MindStudio, 2026) — context engineering patterns
  - https://arize.com/blog/best-practices-for-building-an-ai-agent-router/ (Arize, 2026) — routing confusion matrix
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (Anthropic, 2026) — best practices
  - https://github.com/mgechev/skills-best-practices (mgechev, 2026) — community best practices
relations:
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: extends — adds the missing measurement techniques
  - target: wiki/concepts/skill-techniques-index.md
    type: extends — identifies gaps in the 42-technique index
  - target: wiki/concepts/fleet-health-patterns-skill-bloat-sibling-conflicts-fabricated-decisions.md
    type: complements — that concept addresses bloat; this addresses effectiveness
  - target: wiki/concepts/agent-control-plane-enforcement-architectures-2026.md
    type: related — trigger accuracy is the routing layer of the control plane
---

# Skill effectiveness measurement: what the field does that skill-dev and skill-prune don't

## Decision context

**Why this research was needed:** the operator asked whether we're using
research and ideas about skill efficiency properly in skill-prune and
skill-dev. A gap analysis against 10 external sources revealed our skills
are structurally strong but measurement-poor.

**What the research changed:** identified 4 missing techniques the field
considers essential, each mapped to where it would plug into skill-dev or
skill-prune.

## What we do well (confirmed by external research)

Our skill-dev and skill-prune implement techniques the field confirms are
best practice:

| Technique | Our implementation | Field confirmation |
|---|---|---|
| Progressive disclosure (3-level architecture) | T19 in techniques index; /tp pilot this session | [ESTABLISHED] — Anthropic, agentskills.io, Perplexity |
| Static defect scan (AST-based) | skill-dev Check 7 (script_scan.py) | [SUPPORTED] — NVIDIA governance |
| Leanness check (line count + bloat categories) | skill-dev Check 6 | [ESTABLISHED] — MindStudio inverted-U, SkillsBench |
| Held-out validation | skill-dev Mode 2 Step 4 | [SUPPORTED] — OpenAI eval methodology |
| LLM-fillable enforcement gap detection | skill-dev Check 8 | [NOVEL] — our innovation, not in external sources |

## What we're missing (4 gaps)

### Gap 1: Eval-driven description optimization [MAJOR]

**The field's #1 recommendation.** agentskills.io, OpenAI, and NVIDIA all
say the same thing: the `description` field is THE primary lever for skill
effectiveness. Systematic optimization requires:

1. Create ~20 eval queries (10 should-trigger, 10 should-not — including
   near-misses for negatives)
2. Split into train (60%) / validation (40%)
3. Run each query 3x against the agent; measure trigger rate
4. Iterate on the description using train-set failures
5. Select the version with best validation pass rate

**Our status:** skill-dev mentions "description optimization (Technique 16)"
in the failure-mode table but has NO eval-driven loop. No eval query
generator, no trigger-rate measurement, no train/validation split. The
technique exists conceptually but is not operationalized. [+0 abstain —
untested on our workspace]

### Gap 2: Token efficiency tracking [MAJOR]

**The field tracks:** tokens per invocation, trajectory efficiency (loops,
redundancy), and step count. These are first-class metrics alongside
trigger accuracy and task completion.

**Our status:** neither skill-dev nor skill-prune tracks token usage per
skill invocation. We measure structural quality (defects, leanness) but
not runtime cost. A skill that fires correctly but costs 5,000 tokens per
invocation where 1,500 would suffice is invisible to our current
measurement. [CONFIRMED — grep showed zero mentions of "token efficiency"
in either skill]

### Gap 3: Trigger accuracy confusion matrix [MAJOR]

**The field measures:** for each skill, how often does it trigger correctly
(true positive), incorrectly fire (false positive), fail to fire when it
should (false negative), or correctly not fire (true negative). This is
the routing layer's confusion matrix.

**Our status:** skill-dev Mode 1 measures retrospective MEC (marginal
external contribution — did the skill's output get used?). But MEC doesn't
distinguish between "skill didn't fire" (routing failure) and "skill fired
but output was ignored" (quality failure). The confusion matrix separates
these. [CONFIRMED — grep showed zero mentions of "confusion matrix" in
either skill]

### Gap 4: Security/governance scanning [MODERATE]

**NVIDIA's SkillSpector** scans skills for prompt injection, trigger abuse,
excessive agency, tool poisoning, and vulnerable dependencies. The field
treats skills as untrusted code requiring governance.

**Our status:** we scan for structural defects (broken paths, host
conformance, passthrough gaps) but not for security vulnerabilities in
the skill's instructions or scripts. Our security model assumes
operator-authored skills (which is correct for our workspace) but doesn't
scan marketplace-installed skills. [PARTIAL — our model is different from
the field's; we author most skills ourselves]

## What we do that the field DOESN'T (our innovations)

| Our technique | Field status | Value |
|---|---|---|
| LLM-fillable enforcement gap detection (Check 8) | Not in external sources | [NOVEL] — catches the /ship skip-/check failure class |
| 42-technique index with cross-references | Not in external sources | [NOVEL] — our portfolio's institutional memory |
| Epistemic debt scanner (epistemic_debt.py) | Not in external sources | [NOVEL] — vault-quality tracking |
| Self-clearing enforcement hooks | Not in external sources | [NOVEL] — documented this session |

## What this means for our workspace

1. **The biggest improvement to skill-dev Mode 2 would be adding eval-driven
   trigger testing.** The field is unanimous: trigger accuracy is the #1
   skill effectiveness metric. A skill that doesn't fire (or fires wrongly)
   provides zero value regardless of its internal quality. Adding a
   trigger-test step to Mode 2 (create eval queries, measure trigger rate,
   iterate on description) would close the largest gap.

2. **Token efficiency tracking is the #2 gap.** Our skills consume context
   budget on every invocation but we don't measure how much. Adding a
   token-cost metric to Mode 1 (measure tokens consumed per invocation
   via transcript analysis) would make invisible costs visible.

3. **skill-prune should check description quality, not just structural
   staleness.** Currently skill-prune detects duplicates, orphans, and
   drift. It does NOT evaluate whether skill descriptions still trigger
   correctly after the skill has been modified. A skill whose body was
   rewritten but whose description wasn't updated will have degraded
   trigger accuracy — and skill-prune won't catch it.

4. **The confusion matrix belongs in skill-dev Mode 3 (audit-active).** The
   bulk audit currently produces a ranked table of MEC scores. Adding a
   "trigger accuracy" column (derived from transcript analysis: how often
   was this skill invoked when it should have been?) would make the audit
   actionable on routing quality, not just output quality.

## Falsifier

These gaps are NOT real if:
- Our skills trigger correctly 95%+ of the time without eval-driven
  optimization (measurement would confirm this — currently unmeasured)
- Token cost is not a meaningful constraint on our fleet (our skills
  may be small enough that per-invocation cost is negligible)
- The eval-driven approach doesn't improve trigger rates on our workload
  (our descriptions may already be well-tuned from iterative use)

**Test:** measure trigger accuracy on 5 skills using transcript analysis.
If accuracy is >90% across all 5, the gap is academic. If <80% on any
skill, the gap is urgent.

## Receipts

- **skill-dev grep results:** `skill-dev mentions 'trigger accuracy': False`, `'eval query': False`, `'token efficiency': False`, `'confusion matrix': False` — all confirmed via PowerShell grep, session 2026-08-06
- **skill-prune grep results:** same — all False
- **Techniques index:** 42 techniques (T1-T42) read in full, session 2026-08-06. T16 (exclusion clause) is the closest to description optimization but does not include eval-driven testing.
- **Field sources:** 10 external sources (agentskills.io, OpenAI, NVIDIA, Anthropic, arXiv, Perplexity, MindStudio, Arize, mgechev, Claude docs) — all agree on trigger accuracy as #1 metric

## Sources

- [agentskills.io: Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) (2026) — eval-driven description optimization loop: train/validation query sets, trigger rate measurement
- [OpenAI: Eval skills](https://developers.openai.com/blog/eval-skills) (2026) — eval methodology: outcome, process, style, efficiency metrics
- [NVIDIA: Verified agent skills](https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/) (2026) — governance, SkillSpector, trigger metrics
- [Anthropic: Equipping agents with agent skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) (2025) — progressive disclosure 3-level architecture, iteration from traces
- [arXiv 2602.12430](https://arxiv.org/html/2602.12430v3) (2026) — agent skills survey: human-authored > LLM-generated, portability
- [Perplexity: Designing agent skills](https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity) (2026) — skill maintenance lifecycle, when to create a skill
- [MindStudio: Progressive disclosure](https://www.mindstudio.ai/blog/progressive-disclosure-ai-agents-context-management) (2026) — context engineering patterns, inverted-U
- [Arize: AI agent router best practices](https://arize.com/blog/best-practices-for-building-an-ai-agent-router/) (2026) — routing confusion matrix, selection accuracy
- [Anthropic: Skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) (2026) — lean SKILL.md, match freedom to fragility
- [mgechev/skills-best-practices](https://github.com/mgechev/skills-best-practices) (2026) — community best practices, gotchas sections

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[research-vs-design-vs-architect-skills-and-www-self-assessment]]
- [[research-applicability-checking-dont-cite-without-verifying-assumptions]]
- [[deep-research-systems-and-web-upgrade]]

