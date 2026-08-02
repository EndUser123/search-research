---
title: "Prose rules vs structural enforcement: what 2026 production evidence says about agent governance"
created: 2026-08-02
source: session-2026-08-02-www
tags: [skill-design, enforcement, hooks, anti-pattern, harness-engineering, practitioner-signal, best-practices]
summary: >
  The 2026 production consensus is clear: prose rules (AGENTS.md, CLAUDE.md)
  are a necessary but insufficient layer for agent governance. Hooks are the
  only deterministic enforcement; skills provide routing + verification;
  few-shot examples pin format better than prose. System prompts are now
  treated as "software, not prose" — conditionally assembled, versioned,
  tested. Multi-turn coherence degrades from 90%+ single-turn to 10-15%
  across full conversations, making structural enforcement mandatory.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

# Prose rules vs structural enforcement

## Decision context

**Why this research was needed:** the workspace's entire governance model
(AGENTS.md rules, SKILL.md files, hook scripts) represents a bet on
structural enforcement over prose-only instructions. The wiki has 22 concepts
tagged `enforcement` and 27 tagged `hooks`, all internally derived. The
question: does the external field agree with this architectural choice, or
are we over-engineering?

## Key Findings

### Finding 1: "If it must never happen, make it a hook" — community consensus [PRACTITIONER]

Reddit r/ClaudeCode community discussion (2026) established the enforcement
taxonomy: CLAUDE.md/AGENTS.md are **suggestions** the model reads; hooks are
**deterministic enforcement** (format on save, block dangerous writes);
skills are **on-demand workflow loading**. The rule of thumb: "if a human
would tell every new teammate once, put it in CLAUDE.md; if it's a repeatable
workflow, make it a skill; **if it must never happen, make it a hook**."
(Source: [r/ClaudeCode](https://reddit.com/r/ClaudeCode/comments/1tmq9kz/))

### Finding 2: System prompts are now "software, not prose" (arXiv 2512.08769)

The 2026 practitioner consensus treats the system prompt as a conditionally
assembled "constitutional document" — persona, behavioral constraints, tool
policy, and output contracts — not prose. Claude Code's system prompt is
**110+ separate instruction strings** totaling 16K–25K tokens, assembled
dynamically at runtime. The strongest lever is **tool description quality**:
unoptimized schemas score 33% accuracy; user-centered schemas hit **100%** on
the same Composio benchmark. (Source: [Swarmsignal](https://swarmsignal.net/agent-prompt-engineering-production-guide/))

### Finding 3: Skills are a context management strategy, not a capability upgrade

Skills' value comes from **routing and progressive disclosure** — the model
sees only a name/description at startup, loads full instructions on demand,
and proves work via scripts. The most common failure mode is **routing
ambiguity** (overlapping descriptions), not bad instructions. A skill without
verification is a skill that "occasionally works and silently fails."
(Source: [Steve Kinney](https://stevekinney.com/writing/agent-skills))

### Finding 4: Multi-turn coherence degrades catastrophically without enforcement

90%+ single-turn accuracy degrades to **10-15% across full multi-step
conversations**. Multi-turn coherence is the central unsolved problem.
Instruction hierarchy (system > user > tool output) is trained into models,
achieving +63% defense against prompt extraction — but RL-based attacks still
achieve **98% bypass rates**. The hierarchy must be both trained AND enforced
at runtime. (Source: [Zylos.ai](https://zylos.ai/research/2026-03-30-prompt-engineering-ai-agent-systems-instruction-hierarchies/))

### Finding 5: Few-shot examples are structural enforcement for pipelines [PRACTITIONER]

"Zero-shot is for the chat window; few-shot is for the pipeline." Zero-shot
is sufficient for generic tasks on frontier models. Few-shot (2–5 examples)
wins for custom formats, proprietary classifications, and structured-output
pipelines. The first 1–2 examples produce the biggest accuracy jump; beyond
4-5, diminishing returns. This validates our examples-over-rules concept —
but with the corrected corpus size (2-8, not 10-30). (Source:
[Prompt Architects](https://prompt-architects.com/blog/44-few-shot-vs-zero-shot-prompting))

### Finding 6: "The first few thousand lines determine everything" [PRACTITIONER]

Reddit r/ClaudeCode (843 pts): "When I start a new project, I obsess over
getting the process, guidelines, and guardrails right from the start. Whenever
something is being done for the first time, I make sure it's done clean."
Those early decisions compound — they become the model's default behavior for
the entire project. (Source: [r/ClaudeCode](https://reddit.com/r/ClaudeCode/comments/1qxvobt/))

## What this means for our workspace

1. **Our architectural bet (hooks > skills > prose) is externally validated.**
   The community consensus ("if it must never happen, make it a hook") matches
   exactly what we've built: PreToolUse hooks for verify-before-write,
   spawn-model-gate, skill-staleness; skills for workflow routing; AGENTS.md
   for always-on context.

2. **The verify-before-write hook is the right pattern.** The "skill without
   verification is a skill that occasionally works and silently fails" finding
   directly justifies the verify-before-write hook design. The hook IS the
   verification mechanism that turns a prose rule into deterministic
   enforcement.

3. **Tool description quality is an underinvested lever.** The 33%→100%
   accuracy jump from better tool descriptions is a finding we haven't
   acted on. Our SKILL.md descriptions could be audited for clarity. This is
   the highest-ROI improvement opportunity surfaced by this research.

4. **The 10-15% multi-turn coherence floor means context management is
   survival-critical.** Our compaction recovery, handoff format, and
   /recap-grok skills are not luxuries — they're the structural mitigation
   for a known 85-90% degradation rate. The research validates the investment.

5. **AGENTS.md bloat is a real risk.** If Claude Code's system prompt is
   110+ separate strings totaling 16K-25K tokens, and our AGENTS.md is
   ~103KB (~26K tokens), we're at the upper bound. The research suggests
   conditionally assembled prompts (load sections on demand) over monolithic
   always-on files. This is a future improvement direction.

## Falsifier

These findings are wrong if: (a) a future model generation solves multi-turn
coherence without external enforcement (making hooks unnecessary), (b)
prose-only governance is shown to match hook-enforced governance in
production deployments (the structural advantage disappears), or (c) the
tool-description-quality finding (33%→100%) fails to replicate on different
benchmarks or task types.

## Evidence

All findings are externally sourced from published research (arXiv 2512.08769,
Composio benchmark, Zylos.ai) and Reddit practitioner discussions. No local
code inspection was performed. The workspace-implications are [INFERENCE]
derived from applying external findings to our hook/skill/AGENTS.md stack.
The tool-description-quality recommendation (33%→100%) is a proposed audit,
not yet executed.

## Sources

- [r/ClaudeCode: "Difference between Hooks, Skills, CLAUDE.md"](https://reddit.com/r/ClaudeCode/comments/1tmq9kz/) (2026) [PRACTITIONER]
- [Swarmsignal: Production Agent Prompt Engineering](https://swarmsignal.net/agent-prompt-engineering-production-guide/) (2026, arXiv 2512.08769)
- [Steve Kinney: Agent Skills, Stripped of Hype](https://stevekinney.com/writing/agent-skills) (2026)
- [Zylos.ai: Instruction Hierarchies](https://zylos.ai/research/2026-03-30-prompt-engineering-ai-agent-systems-instruction-hierarchies/) (2026)
- [Prompt Architects: Few-Shot vs Zero-Shot](https://prompt-architects.com/blog/44-few-shot-vs-zero-shot-prompting) (2026)
- [r/ClaudeCode: "100% AI code for 1+ year"](https://reddit.com/r/ClaudeCode/comments/1qxvobt/) (843 pts, 2026) [PRACTITIONER]

## Related

- [[examples-over-rules-escape-hatch]] — when to switch from rules to examples
- [[mandatory-step-enforcement-code-over-prose]] — the enforcement principle
- [[verify-before-write-hook-design]] — the structural fix
- [[skill-enforcement-layers]] — enforcement taxonomy
- [[couple-triggers-to-events-that-actually-fire]] — trigger design

## Auto-related

- [[enforcing-kb-consultation-before-action-methods]]
- [[structural-enforcement-for-skipped-rules-grok-build-2026]]
- [[skill-catalog]]
- [[verify-gate-enforcement-gap-document-vs-runtime]]
- [[theatrical-contrition-and-over-apologetic-response-patterns]]

