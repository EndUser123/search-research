---
title: "i-have-adhd skill — implementation decision and evidence audit"
id: i-have-adhd-skill-implementation-research
category: decision
created: 2026-08-06
verified: 2026-08-06
accurate_as_of_head: f7c57bd
tags: [adhd, skill, output-style, instruction-budget, system-prompt, evidence-audit, decision]
host: grok
agent: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Decision to install ayghri/i-have-adhd as an opt-in skill (/adhd) rather than
  AGENTS.md rules or a SessionStart hook. Research validated: (1) AGENTS.md is
  already past IFScale's instruction budget (~200+ rules, 30K tokens); (2) Grok
  Build SessionStart hooks are passive (stdout ignored) so can't inject behavioral
  rules; (3) 5 of 10 ADHD rules are evidence-supported, Rule 9 is contradicted
  (ADHD working memory is 3-4 items not 5). Rule 7 ("make wins visible")
  propagated into /close, /handoff, and /go as the one genuinely missing element.
sources:
  - title: "IFScale: How Many Instructions Can LLMs Follow at Once?"
    url: https://arxiv.org/abs/2507.11538
    quality: 9
    primary_source: true
  - title: "LLMs Get Lost In Multi-Turn Conversation"
    url: https://arxiv.org/abs/2505.06120
    quality: 9
    primary_source: true
  - title: "A Closer Look at System Prompt Robustness"
    url: https://arxiv.org/abs/2502.12197
    quality: 8
    primary_source: true
  - title: "Lost in the Middle (Liu et al.)"
    url: https://arxiv.org/abs/2307.03172
    quality: 10
    primary_source: true
relations:
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: related
  - target: wiki/concepts/prose-rules-vs-structural-enforcement-research-2026.md
    type: related
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: related
---

# i-have-adhd skill — implementation decision and evidence audit

## Decision context

**The problem:** the operator found `ayghri/i-have-adhd` (17.6K stars) — a 10-rule output-style skill for ADHD-friendly LLM output — and wanted it implemented on Grok Build. Three implementation paths were proposed: (A) skill-only opt-in, (B) AGENTS.md always-on block, (C) SessionStart hook + file-write + read-directive (mirroring the Claude Code always-on pattern).

**What the research changed:** the /www research disproved option C (hook can't inject context — SessionStart stdout is ignored on Grok Build), showed option B is actively harmful (AGENTS.md is already past the instruction budget), and validated option A as the optimal long-term path.

## The decision: skill-only (Option A)

Installed at `~/.grok/skills/adhd/SKILL.md`. Invocable as `/adhd`. Opt-in — off until invoked, matching the upstream `disable-model-invocation: true` design intent. A SessionStart hook at `~/.grok/hooks/adhd-skill-reminder.json` reminds the operator that `/adhd` is available at each new session.

**Name collision note:** `UditAkhourii/adhd` is a completely different project (parallel divergent ideation for coding agents). See [[adhd-parallel-frame-divergent-ideation-integration]] for that project.

**Rule 7 propagation (2026-08-06):** the one genuinely missing ADHD element — "make wins visible" — was propagated into three skills:
- `/close`: Completed items lead with "What now works" framing
- `/handoff`: body stance leads with concrete outcome, not background
- `/go`: phase progress lines show what each phase produced that now works

**Review fixes (2026-08-06, /review session 019fd8b0):**
- Hook matcher expanded from `startup` to `startup|resume` — reminder now fires on resumed sessions
- H1 heading fixed from `# i-have-adhd` to `# adhd` to match frontmatter
- Rule 9 workspace override added inline: "AGENTS.md completeness-over-curation wins; chunk instead of capping"
- Handoff stance bullet de-bolded for consistency
- Hook inline `python -c` extracted to `hooks/scripts/adhd_skill_reminder.py` (Class C quoting hazard eliminated)

**Upstream-skill + workspace-override pattern:** when installing a third-party skill that partially conflicts with workspace rules, keep the upstream content clean and add an inline override note at the conflict point. This preserves update-ability (git pull from upstream) while resolving the conflict at runtime.

**Rejected alternatives and why:**

| Option | Rejected because | Evidence |
|--------|-----------------|----------|
| C (hook + file-write) | Grok Build SessionStart hooks are passive (stdout ignored). File-read ≠ behavioral shaping — a file the model reads once has no enforcement mechanism. | 10-hooks.md:303; arXiv:2502.12197 (system prompts have trained priority over user-injected content) |
| B (AGENTS.md always-on) | AGENTS.md is 122K bytes (~30K tokens, ~200+ rules) — already in IFScale's "uniform abandonment" regime. Adding rules degrades compliance with ALL existing rules. | arXiv:2507.11538 (IFScale); [[agents-md-construction-best-practices]] |
| E (selective merge) | Same instruction-budget problem as B. Every line moved INTO AGENTS.md degrades every line already there. | Same |

## Evidence: system prompt instruction budget

The IFScale benchmark (arXiv:2507.11538, Distyl AI) tested 20 frontier models with 10–500 instructions in a single prompt. Key findings:

- Even the best model (gemini-2.5-pro) only achieved 68.9% accuracy at 500 instructions
- Degradation is **uniform** at high density (not position-selective) — every additional rule weakens ALL rules proportionally
- At 150–250 instructions, models transition from "lost in the middle" (position bias) to "uniform abandonment" (all rules degrade equally)
- Claude-sonnet-4: 94.4% at 100 instructions → 42.9% at 500

**Implication for this host:** `~/.grok/AGENTS.md` at ~30K tokens (~200+ rules) is already in the uniform-abandonment regime. Adding even 4 more rules measurably degrades compliance with the existing ruleset. This is the structural reason to keep new rules OUT of AGENTS.md.

## Evidence: opt-in vs always-on for output-style rules

Three independent findings converge:

1. **System prompts have trained priority** (arXiv:2502.12197) — models are trained to prioritize system-channel instructions over user-message-injected content. Skill-invoked rules arrive in the user/tool channel, not the system channel.
2. **Multi-turn instruction decay** (arXiv:2505.06120) — performance drops 39% across multi-turn conversations. Rules injected mid-conversation decay as the conversation grows.
3. **But system-prompt budget is fixed** — every always-on rule competes with every other always-on rule. Opt-in rules don't compete.

**Resolution:** don't pick a default — pick per-rule. Output-style rules that are domain-specific and tolerable to occasionally miss belong in a skill (opt-in). Load-bearing rules that must fire every session belong in the system prompt — but only if there's budget.

## Evidence: ADHD rule audit

The skill's README credits Ramsay & Rostain's *The Adult ADHD Tool Kit* as "loosely based on." Research validation of the 10 rules:

| Rule | Evidence | Source |
|------|----------|--------|
| 1. Lead with next action | **Strong** — task initiation is the most replicated ADHD executive function deficit | CHADD; lifestack.ai |
| 2. Number multi-step tasks | **Strong** — working memory deficits are large-magnitude in ADHD meta-analysis | Kasper et al. (APA) |
| 3. End with next action (<2 min) | **Mixed** — principle supported; "2-min" framing is GTD, not ADHD research | brainchildstartups.com |
| 4. Suppress tangents | **Strong** — working memory load reduction | attncenter.nyc |
| 5. Restate state every turn | **Strong** — working memory deficit; chunking improves recall ~63% | understood.org; Applied Cognitive Psychology |
| 6. Specific time estimates | **Supported** — Barkley's time-blindness research | Known but not in search results |
| 7. Make wins visible | **Partial** — dopamine mechanism real; "visible progress" is extrapolation | Inference from reward literature |
| 8. Matter-of-fact errors | **No ADHD-specific evidence** — UX preference | None found |
| 9. Cap lists at 5 | **Contradicted** — ADHD working memory is 3-4 items, not 5 | learntothrivewithadhd.com |
| 10. No preamble/closer | **No ADHD-specific evidence** — style preference | None found |

**Rule 9 conflict:** "Cap at 5" is wrong on two axes. ADHD research says 3-4 items (not 5). And the workspace's `~/.grok/AGENTS.md` says "Completeness over curation — list every item with positive ROI. Do not filter to a top N." The resolution: don't cap — **chunk**. Present top 3-4 as "do now," then the rest as "additional items."

## What this means for our workspace

- `/adhd` is available as an opt-in skill — type `/adhd` to activate ADHD-friendly output for a session
- Rule 7 ("make wins visible") is now embedded in `/close`, `/handoff`, and `/go` — these always surface wins regardless of whether `/adhd` is active
- Rule 9 ("cap at 5") was rejected — it conflicts with AGENTS.md "completeness over curation." When `/adhd` is active, lists should be chunked (top 3-4 as "do now"), not capped
- The SessionStart hook reminds the operator that `/adhd` exists — it does NOT inject rules into model context (that doesn't work on Grok Build)
- Do NOT add more rules to AGENTS.md for ADHD-friendly output — the instruction budget is exhausted. Use `/adhd` opt-in instead

## Falsifier

This decision is wrong if:
- Grok Build adds a SessionStart context-injection mechanism (not stdout) — the hook approach becomes viable and always-on could work
- The operator trims AGENTS.md below ~150 rules, creating instruction budget for a selective merge
- A future /www run finds controlled evidence that persona-framing ("you are an ADHD-friendly agent") outperforms rule enumeration for output-style compliance

## Related

- [[agents-md-construction-best-practices]] — the instruction budget principle this decision follows
- [[prose-rules-vs-structural-enforcement-research-2026]] — hooks > skills > prose hierarchy
- [[enforcement-hierarchy-and-compaction-strategy]] — why system-prompt rules are the strongest enforcement form
- [[adhd-parallel-frame-divergent-ideation-integration]] — different project with same name (divergent ideation, not output formatting)

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[internal-adhd-experiences-and-hidden-manifestations]]
- [[wiki-captures-decisions-by-default]]
- [[adhd-parallel-frame-divergent-ideation-integration]]

