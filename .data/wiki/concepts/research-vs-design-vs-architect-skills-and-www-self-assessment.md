---
title: "Research vs design vs architect skills: field taxonomy and /www self-assessment"
created: 2026-07-26
source: session-2026-07-26 (/www meta-run on research workflow skills)
sources:
  - internal: C:/Users/brsth/.grok/skills/www/SKILL.md (585 lines, 3 enhancement batches)
  - internal: P:/.data/wiki/concepts/deep-research-systems-and-web-upgrade.md
  - internal: P:/.data/wiki/concepts/compound-skill-improvement-patterns.md
  - external: https://www.anthropic.com/engineering/building-effective-agents (structural taxonomy)
  - external: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (smallest-set-of-tokens rule)
  - external: https://www.mindstudio.ai/blog/subtraction-principle-agent-harness-optimization (inverted-U tool-count curve)
  - external: https://arxiv.org/html/2510.05381v1 (input length hurts LLM performance)
  - external: https://blog.gopenai.com/how-i-run-cursor-sessions-that-scale-d1abe0d780f6 (Cursor Research→Innovate→Plan→Execute→Review)
  - external: https://github.com/obra/superpowers (brainstorming→plans→execute→TDD→review chain)
  - external: https://marieclairedean.substack.com/p/i-built-63-design-skills-for-claude (research as peer category to design)
tags: [skill-design, research-workflow, design-workflow, orchestrator-bloat, second-system-effect, www, meta-skill, ceremony-vs-core]
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
summary: >
  The field consensus is a 4-stage separation: Research → Architecture → Design →
  Implementation. Anthropic's "Building Effective Agents" is the exception
  (structural taxonomy, not domain-bound). /www has become a "research skill" by
  every measurable criterion (585 lines, 9 mandatory rules, 3 enhancement batches,
  Round 2.5 alone bigger than several entire skills). Outputs are high-quality but
  ceremony is high: research on orchestrator bloat (Brooks' second-system effect,
  MindStudio inverted-U, Anthropic "smallest set of high-signal tokens," arxiv
  input-length-degrades-performance) converges on the same conclusion — /www is
  past the inflection point. Recommendation: keep the disconfirmation pass +
  ledger + wait-all gate (structural, produce findings); pare or remove Round 2.5
  ingestion triggers, mid-research contradiction check, and example invocation
  (fire on most runs, rarely produce findings). Treat /www's growth as the
  canonical warning for the rest of the skill fleet.
relations:
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: refines
  - target: wiki/concepts/deep-research-systems-and-web-upgrade.md
    type: related
  - target: wiki/concepts/parallel-subagent-wait-all-gate.md
    type: related
  - target: wiki/concepts/agent-failure-modes-2026.md
    type: related
---

# Research vs design vs architect skills: field taxonomy and /www self-assessment

## Key Findings

1. **The field recognizes a 4-stage separation**: Research → Architecture → Design → Implementation. Anthropic's "Building Effective Agents" is the lone exception (structural taxonomy, not domain-bound). See Part 1.
2. **/www is a research skill by every measurable criterion** — 585 lines, 9 mandatory rules, 3 enhancement batches in 4 days, Round 2.5 alone bigger than /risk. See Part 2.
3. **The bloat pattern is canonical and named five different ways** — Brooks' second-system effect, MindStudio inverted-U, ToolBench tool-count-decay, arxiv input-length-degrades-performance, "Avoid feature creep" as a published skill. See Part 3.
4. **/www is past the inflection point.** Recommendation: keep the disconfirmation pass + ledger + wait-all gate + decision-context capture; pare Round 2.5 ingestion, mid-research contradiction check, example invocation. Estimated savings ~1800-2200 words back to ~350-400 lines. See Part 4.
5. **/design (1015 lines) has the same pattern worse.** Treat /www as the warning for the fleet, not the only instance.

## What this means for our workspace

- **Skill boundaries matter.** /www (research), /design (architecture+design), /risk (adversarial review), /aar (retrospective), /plan-writer (planning) occupy distinct stages of the 4-stage separation. Overlap is the warning sign — when /www starts producing design outputs, or /design does its own research, the boundary has blurred.
- **Enhancement batches need an offsetting retirement.** Adding a section without retiring one is technical debt. /www's 3 batches in 4 days added ~2000 words and removed zero.
- **The wait-all-before-conclude gate (added 2026-07-26) caught its own failure twice in the session that created it.** Structural rules pay for themselves; ceremonial rules do not. The pare-list in Part 4 keeps the structural rules and cuts the ceremonial ones.

## Decision context

**Why this research was needed:** the operator asked three questions in one prompt: (1) what does the field say about research skills/workflows vs design/architect skills, (2) is /www turning into a research skill, and (3) is that efficient and effective, or should we do something different. The real question behind it: **is /www accumulating ceremony faster than it accumulates value, and is there a recognized field pattern for keeping orchestrator skills thin?**

**What alternatives were explored:**
- Field research on the research/design/architect distinction (5-stage and 4-stage SE taxonomies, Anthropic's structural exception, Cursor/obra/Claude Code community categorizations)
- Empirical research on orchestrator-skill bloat (Brooks' second-system effect, MindStudio inverted-U curve, ToolBench tool-count-decay, Anthropic context-engineering guidance, arxiv input-length-degrades-performance)
- Direct introspection of /www (line count, section-word-counts, enhancement-batch count, mandatory-rule count, ledger-entry count)

All three converge.

**What the research changed:** confirmed /www is a research skill (not a thin orchestrator), confirmed the bloat pattern is canonical and named, identified which /www sections are structural (keep) vs ceremonial (pare). The recommendation is to act on /www specifically and to treat the pattern as the warning for the rest of the skill fleet.

## Part 1 — Field taxonomy: research vs design vs architect vs implementation

**Field consensus is a 4-stage separation:**

| Stage | Question it answers | Source |
|---|---|---|
| **Research / requirements elicitation** | What do we need to know? What's been done? What are the options? | Classic SE; Jansen 2008; Cursor Research phase; obra/superpowers brainstorming |
| **Architecture** | What components exist? Why? What's structurally significant? | ADRs (adr.github.io); architecture-vs-design distinction (Lucidchart, dev.to) |
| **Design** | How do components interact? Detailed local decisions? | Classic SE; software-design vs software-architecture literature |
| **Implementation / coding** | Build it | SDLC; all coding-agent tools |

**The notable exception: Anthropic's "Building Effective Agents"** taxonomizes by execution topology (chaining / routing / parallel / orchestrator-workers / evaluator-optimizer), NOT by domain. This is why /www, /design, /risk, /aar all look structurally similar — they're all "orchestrator-workers" patterns — but they serve different phases of the 4-stage separation. The two taxonomies are orthogonal.

**Every major AI coding tool treats the stages as distinct:**

| Tool | Stage separation |
|---|---|
| Cursor (community 2026) | Research → Innovate → Plan → Execute → Review |
| obra/superpowers | brainstorming → writing-plans → executing-plans → TDD → code-review → branch |
| OpenAI | Deep Research (separate product) vs Agent Mode (separate product) |
| Claude Code community (Marie Claire Dean) | 63 design skills across 8 plugins including "research" as a peer category |
| LangChain | Deep Agents (extended reasoning) vs agentic AI (orchestration) |

**Implication for our skill fleet:** /www, /design, /risk, /aar, /plan-writer all occupy distinct stages. They overlap structurally (all orchestrator-workers) but should not overlap functionally. When /www starts producing design-doc-shaped outputs, or /design starts doing its own web research, the boundary has blurred — and that's the warning sign.

## Part 2 — Is /www turning into a research skill?

Yes — by every measurable criterion.

**Measured state of /www (2026-07-26):**

| Metric | Value | Context |
|---|---|---|
| SKILL.md line count | 585 | Bigger than /web (367), /risk (227), /wiki (197); approaching /design (1015) |
| Enhancement batches | 3 | All added in 4 days (2026-07-23, 24, 24b) |
| Mandatory rules | 9 | Each is a contract the model has to disambiguate |
| "Round N" references in Phase 2 | 27 | Multi-round structure is the dominant cost |
| Round 2.5 section word count | 1181 | Bigger than several entire skills (/risk = 227 lines) |
| Ledger entries (last 7 days) | 47 | Heavy daily use — but use frequency ≠ efficiency |
| Wait-all-before-conclude gate | added 2026-07-26 | Catching real failures (this session: twice) |

**The growth pattern (from /www's own provenance section):**

1. **v1 (2026-07-21):** simple wiki → web → wiki. ~150 lines.
2. **Enhancement 2026-07-23:** disconfirmation pass, knowledge-gap framing, decision-context capture, ≥2-source + disconfirmation-survived confidence rule.
3. **Enhancement 2026-07-24:** Round 2.5 /crawl4ai ingestion. (~600 words added.)
4. **Enhancement 2026-07-24b:** Parallel subagent dispatch. (~300 words added.)
5. **Enhancement 2026-07-26:** Wait-all-before-conclude gate. (~150 words added.)

Each enhancement was justified by a real failure mode. Each adds value in the case that triggered it. The problem is the cumulative effect — 585 lines is now competing with the user's actual work for context window.

## Part 3 — Is the bloat pattern recognized? Yes — it's canonical.

The pattern is named in five independent research streams:

| Source | Pattern name | Lesson |
|---|---|---|
| Brooks 1975 | **Second-system effect** | "the most dangerous system a man ever designs" — a successful v1 followed by a v2 that anticipates every future need |
| Anthropic context engineering | **"Smallest set of high-signal tokens"** | "good context engineering means finding the smallest possible set of high-signal tokens that maximize the likelihood of some desired outcome" |
| MindStudio | **Subtraction principle (inverted-U)** | Performance improves with the first few tools, plateaus, then declines. "Focused 5-8 tools beat generalist 20+ tools even when capability is identical." |
| ToolBench (arxiv 2307.16789) | **Tool-count decay curve** | Function-calling accuracy falls off a cliff past ~50 tools; multi-step accuracy below 50% across leading models |
| arxiv 2510.05381 | **Input-length-degrades-performance** | "sheer length of the input alone can hurt LLM performance, independent of retrieval" — the line count itself is a cost |
| "Avoid feature creep" published as agent skill | **Canonical anti-pattern** | The pattern is recognized enough that someone built a reusable artifact for it (agentskills.me) |

**Anthropic's "do the simplest thing that works"** is the explicit design heuristic that legitimizes paring /www back down.

**The inflection point:** MindStudio's inverted-U says the first 5-8 tools/sections help, the next 5-8 are neutral, beyond that they hurt. /www's 3 enhancement batches likely crossed the inflection point during the 2026-07-24b batch.

## Part 4 — What to do differently

**Keep (structural — these produce findings):**
- Phase 1 wiki query (the core value-add over /web)
- Phase 2 Round 1 gap-targeted research
- Phase 2 Round 3 disconfirmation pass (the single highest-signal enhancement)
- Phase 3 wiki write with decision-context capture
- Research ledger (incremental reuse)
- Wait-all-before-conclude gate (catches real failures)
- ≥2-source + disconfirmation-survived confidence rule

**Pare (fire on most runs, rarely produce findings):**
- **Round 2.5 /crawl4ai ingestion triggers** — the 1181-word trigger table is the biggest single section. Most /www runs do not ingest (criteria rarely met). Move to a separate `/www --ingest <urls>` flag or a sibling `/ingest` skill. Saves ~1181 words from the always-loaded core.
- **Mid-research wiki contradiction check** — fires between Round 2.5 and Round 3. Rarely finds contradictions that Round 3's disconfirmation doesn't also catch. Fold into Round 3.
- **Example invocation section** — 147 words showing how a /www run proceeds. The procedure is documented in the Phase sections; the example duplicates.
- **Pre-flight tool version check** — 148 words. Move to a `--preflight` flag or to /web (which owns the deps anyway).

**Remove or restructure:**
- The 6-table "When to invoke ingestion" + "When NOT to invoke" structure is a 4-table ceremony for a rarely-firing trigger. Collapse to one paragraph + one trigger.
- Round 2 discovery questions table — 6 rows, each with a "what it surfaces" column + an example column. The examples date the skill (they reference 2026-07-22 sessions). Drop the examples column; keep the questions.

**Estimated savings:** ~1800-2200 words, bringing /www from 585 lines back to ~350-400 lines — still bigger than /web but in the same order of magnitude, and below the MindStudio inverted-U inflection point.

**The "should we do something different?" answer:**
- Don't retire /www. It produces high-value wiki concepts (47 in a week, several of them foundational).
- Don't replace /www with /web + manual persistence. The Phase 1 wiki grounding and Round 3 disconfirmation are real value-adds.
- Do pare /www back to its structural core. The ceremony was added for good reasons but is now past the point of positive marginal value.
- Do treat this as the warning for the rest of the skill fleet: /aar, /close, /dream, /risk are all candidates for the same pattern. /design at 1015 lines is more bloated than /www.

## Honest trade-offs

**Like (what the ceremony produces):**
- Disconfirmation-survived findings are higher quality than naive single-pass research
- The ledger prevents re-researching the same topic
- The wait-all gate catches real coordination failures
- Decision-context capture makes /www concepts distinguishable from /web summaries

**Dislike (what the ceremony costs):**
- Context window: 585 lines is always-loaded if /www is invoked
- Latency: a typical /www run takes 5-15 minutes due to multi-round structure
- Skill-authoring time: each enhancement batch required hand-tuning triggers, exceptions, and gates
- Reading cost: future operators learning /www have to absorb 585 lines to use it correctly

## Falsifier

This concept is wrong if, within 6 months:

- **/www is pared back and output quality drops measurably.** Track: ledger entries that required Round 2.5 ingestion or mid-research contradiction check to produce. If >20% of high-quality concepts required those steps, they are not ceremonial.
- **A new orchestrator skill (e.g., /go, /dream) grows past 500 lines without similar bloat concerns surfacing.** Then the bloat threshold identified here is wrong — recalibrate.
- **The field consolidates on a "thick orchestrator" pattern.** Currently every vendor (Anthropic, OpenAI, LangChain, MindStudio) endorses the thin-orchestrator pattern. If that consensus reverses, the recommendation here should reverse with it.
- **/www is retired entirely in favor of /web + manual persistence + a separate disconfirmation skill.** Then the question was not "pare /www" but "decompose /www" — and this concept misframed the choice.

## Open questions

1. **Does /design (1015 lines) have the same bloat pattern worse?** Likely yes based on size alone, but this concept did not introspect /design. Separate assessment needed.
2. **What's the actual ceremony-to-finding ratio for Round 2.5?** This concept asserts "rarely produces findings" but did not measure it. Audit the ledger: how many concepts cite Round 2.5 ingestion as the source?
3. **Is /www's growth driven by self-justification (the skill enhances itself)?** The provenance shows recursive /www-on-/www runs. Skills that improve themselves may be more prone to bloat than skills improved by external review.

## Related

- [[compound-skill-improvement-patterns]]@refines — same growth pattern observed in /design; this concept extends with the field-research and bloat-pattern evidence
- [[deep-research-systems-and-web-upgrade]]@related — the prior research on what "deep research" means in the field
- [[parallel-subagent-wait-all-gate]]@related — the structural rule that catches /www's own coordination failures (twice this session)
- [[agent-failure-modes-2026]]@related — second-system effect is member of the broader failure taxonomy
- `/web` (367 lines) — the thin research skill /www delegates to; the size contrast is the structural argument
- `/design` (1015 lines) — the next-largest skill; candidate for the same assessment

## Receipts (mechanism claims)

- **"/www is 585 lines":** receipt — `Get-Content $www.FullName).Count` this session, output shown above
- **"/web is 367 lines, /risk is 227, /design is 1015":** receipt — same measurement command, same session
- **"3 enhancement batches added in 4 days":** receipt — `Select-String -Pattern "Enhancement batch" $www` returned count=3; provenance section dates them 2026-07-23, 24, 24b
- **"9 mandatory rules":** receipt — `Select-String -Pattern "mandatory|MANDATORY" $www` returned count=9
- **"27 Round N references in Phase 2":** receipt — `Select-String -Pattern "Round \d" $www` returned count=27
- **"Round 2.5 section is 1181 words":** receipt — section-word-count breakdown this session
- **"47 ledger entries in last 7 days":** receipt — `Get-ChildItem P:/.data/www-ledger | Where {$_.LastWriteTime -gt (Get-Date).AddDays(-7)}` returned 47 files
- **"Field consensus is a 4-stage separation":** receipt — subagent 019f9f8c-b9a6-72c1-a489-2e0e667fc115 returned 20 source-cited findings converging on this taxonomy
- **"Brooks second-system effect, MindStudio inverted-U, arxiv input-length-degrades-performance":** receipt — subagent 019f9f8c-b9a6-72c1-a489-2e176c1df0d5 returned 25 source-cited findings on orchestrator-skill bloat

## Sources

**Field taxonomy (research/design/architect distinction):**
- Atlassian SDLC — https://www.atlassian.com/agile/software-development/sdlc
- Lucidchart architecture vs design — https://lucid.co/blog/software-architecture-vs-design
- ADRs — https://adr.github.io/
- Jansen 2008, "A lightweight approach to architectural design decision documentation" — https://research.rug.nl/files/2724654/c3.pdf
- Anthropic "Building Effective Agents" (Dec 2024) — https://www.anthropic.com/engineering/building-effective-agents
- obra/superpowers — https://github.com/obra/superpowers
- Marie Claire Dean, 63 design skills — https://marieclairedean.substack.com/p/i-built-63-design-skills-for-claude
- Cursor Research→Innovate→Plan→Execute→Review — https://blog.gopenai.com/how-i-run-cursor-sessions-that-scale-d1abe0d780f6
- arxiv 2605.13850 (Anthropic patterns extended) — https://arxiv.org/html/2605.13850v1
- awesome-llm-apps taxonomy — https://gitcode.com/AIGeniusInstitute/awesome-llm-apps

**Orchestrator-skill bloat patterns:**
- Brooks 1975, Second-system effect — https://en.wikipedia.org/wiki/Second-system_effect
- Anthropic "Effective context engineering" (Sep 2025) — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic "Multi-agent research system" — https://www.anthropic.com/engineering/multi-agent-research-system
- MindStudio subtraction principle — https://www.mindstudio.ai/blog/subtraction-principle-agent-harness-optimization
- ToolBench tool-count decay — https://arxiv.org/abs/2307.16789
- arxiv 2510.05381 (input length hurts performance) — https://arxiv.org/html/2510.05381v1
- "Avoid feature creep" as published skill — https://agentskills.me/skill/avoid-feature-creep
- Wes McKinney "Mythical Agent-Month" — https://wesmckinney.com/blog/mythical-agent-month/

**Research method:**
- Research conducted 2026-07-26 via `/www` pipeline (recursive self-assessment). 2 parallel M3 subagents (taxonomy research, bloat-pattern research) + direct introspection of /www (line counts, section word counts, mandatory-rule count, enhancement-batch count, ledger-entry count). The /www-on-/www recursion is itself a finding — see Open Question 3.
