---
title: "Skill authoring patterns: do's and don'ts for AI-agent skills"
created: 2026-07-21
source: session-2026-07-21 (/www compound research)
sources:
  - https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  - https://generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics
  - https://anthonytd.com/blog/building-skills-for-ai-agents/
  - https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff
  - P:/.data/wiki/concepts/multi-agent-correlated-errors.md
  - P:/.data/wiki/concepts/skill-enforcement-layers.md
  - P:/.data/wiki/concepts/deliberation-waste-re-deriving-same-answer.md
tags: [skill-design, skill-authoring, claude-code, grok-build, ai-agents, patterns, anti-patterns, do's-and-don'ts]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "Do's and don'ts for authoring AI-agent skills (SKILL.md), synthesized from Anthropic's official best practices, the 14-pattern breakdown by generativeprogrammer.com, anthonytd's field guide, and Graphite's incremental-review research. Covers description-as-firing-condition, exclusion clauses, context budget, progressive disclosure, control tuning, explain-the-why, A/B loop development, and incremental review reuse. Directly relevant to our /www, /tp, /aar, /handoff skills."
---

# Skill authoring patterns: do's and don'ts for AI-agent skills

Synthesized from four web sources researched via `/www` on 2026-07-21. Focuses on what's unique and non-obvious relative to our existing concepts. Our skill portfolio (`/tp`, `/aar`, `/handoff`, `/www`, `/design`, `/go`, `/review`, `/red-team`) is the implicit test surface — patterns here either confirm what those skills already do or flag what they miss.

## Do's

### 1. Treat the description as a firing condition, not a summary

Source: [generativeprogrammer.com Pattern 1](https://generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics), [Anthropic best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

The `description` field is the **only signal** the model sees at selection time (Level 1 of progressive disclosure). A skill that fails at selection never runs, no matter how good its body is. Write it as a firing condition with three parts: **what it does + when to trigger + key signal phrases or slash command**.

Anthropic's skill-creator recommends descriptions that are slightly "pushy" — Claude has a measured tendency to under-trigger skills. Example structure:
```
[What it does] + [When to trigger] + [Key signal phrases or slash command]
```

Target: ~90% of relevant natural-language queries should trigger the skill without the user knowing the slash command.

**Our conformance:** `/www`'s description follows this pattern. `/tp`'s description is strong. `/handoff`'s description is strong.

### 2. Add exclusion clauses to the description

Source: generativeprogrammer.com Pattern 2.

Positive triggers pull a skill in; **exclusions push it out**. Both are needed. A description that only says when to fire will hijack work that belongs to another skill or step in when bare Claude would suffice.

Ruben Hassid calls the exclusion line "the single most important line in the description," above the positive trigger.

Example: "Do NOT use for blog articles, newsletters, emails, tweets, or long-form content."

**Our gap:** several of our skills lack explicit exclusion clauses. `/tp` should exclude "code review of a specific diff (use /review)" — it currently does this in the "Adjacent skills" table but not in the description itself. `/aar` should exclude "live critique of a current question (use /tp)".

### 3. Default assumption: the model is already smart

Source: Anthropic best practices.

Only add context the model doesn't already have. Challenge each piece of information:
- "Does the model really need this explanation?"
- "Can I assume the model knows this?"
- "Does this paragraph justify its token cost?"

The context window is a **public good**. Every token in your skill competes with conversation history, other skills' metadata, and the user's actual request.

### 4. Use progressive disclosure (three levels)

Source: Anthropic best practices, generativeprogrammer.com Pattern 4.

| Level | What loads | When |
|---|---|---|
| 1. YAML metadata (name + description) | ~100 tokens per skill | Always in system prompt |
| 2. SKILL.md body | Full instructions | Only when skill fires |
| 3. Reference files / scripts | Detail content | Only when task references them |

**Rules:**
- Keep SKILL.md body **under 500 lines**; split beyond that
- Keep reference files **one level deep** from SKILL.md (no nested chains like SKILL.md → advanced.md → details.md)
- Long reference files (>100 lines) get a table of contents at the top
- Scripts in `scripts/` execute without loading into context

**Our conformance:** `/aar` follows this pattern well — lean core SKILL.md + `references/*.md` loaded on trigger. `/tp` has `protocol.md` as deep reference. `/www` delegates to `/wiki` and `/web` rather than reimplementing.

### 5. Match instruction freedom to task fragility (Control Tuning)

Source: generativeprogrammer.com Pattern 5, Anthropic best practices.

| Freedom level | When to use | Form |
|---|---|---|
| **High** (prose) | Multiple valid approaches; context-dependent | Text instructions, "use your judgement" |
| **Medium** (pseudocode) | Preferred pattern exists; some variation acceptable | Parameterized scripts |
| **Low** (exact scripts) | Operations are fragile; consistency is critical | Specific commands, no flags, "do not modify" |

**Analogy (Anthropic):** narrow bridge with cliffs → low freedom; open field → high freedom.

**Our conformance:** `/aar` uses low-freedom for Step 0 (exact Python script) and high-freedom for Phase 4 (pattern synthesis). `/www` uses medium-freedom (delegates to /wiki and /web with routing logic).

### 6. Explain the why, not just the rule

Source: generativeprogrammer.com Pattern 6.

All-caps `ALWAYS` / `NEVER` / `MUST` without reasoning gives the model rigid rules with no context. It follows the letter but misses edge cases the author didn't anticipate, or over-applies a rule where judgement was needed. Anthropic's skill-creator explicitly flags all-caps imperatives as a yellow flag.

**Better:** "Use constructor injection. Field injection breaks testability because we cannot mock the field without Spring context."

**Our conformance:** `/tp` explains *why* the fresh subagent matters (Costa & Kallick's "you cannot refocus your own glasses"). `/aar` explains *why* stale-data-immunity matters (per-run freshness contract). `/handoff`'s preflight step explains *why* it runs (prevents inaccurate handoffs).

### 7. Develop iteratively with the A/B loop

Source: [anthonytd.com](https://anthonytd.com/blog/building-skills-for-ai-agents/).

- **Agent A** helps you author/refine the skill
- **Agent B** (a fresh instance) uses it on real tasks — observes behavior
- **Agent C** (optional) critiques the skill itself — reviews SKILL.md for clarity, concision, gaps

Watch B's failures → bring specific issues back to A → refine. This is structurally the same pattern as `/tp`'s two-lens architecture, applied to skill development instead of critique.

**Our application:** when we ship a new skill (`/www`), we should have a fresh instance run it on a real topic and report friction. The `/tp` subagent-with-tools protocol is the right shape for Agent C.

### 8. Ship a copyable checklist for multi-step workflows

Source: generativeprogrammer.com Pattern 10, Anthropic best practices.

For workflows with >3 steps, provide a checklist the model pastes into its response and ticks off. The checklist lives in the conversation, so skipping a step is visible to both model and user.

**Our conformance:** `/aar` has a phase structure but no copyable checklist. `/handoff` has numbered steps but no checklist format. `/www` has three phases but no checklist. **Gap:** we could add checklists to `/aar`, `/handoff`, and `/www`.

### 9. Wire in self-correcting loops (validator → fix → repeat)

Source: generativeprogrammer.com Pattern 11, Anthropic best practices.

Produce output → run validator → if it fails, fix and revalidate → terminate only when validation passes.

**Our conformance:** `/aar` has the output validator (`output_validator.py`). `/handoff` has the preflight step (Step 5). `/www` has the lifecycle tracking gate (`exit_clean: true`). All three follow this pattern.

### 10. Maintain state/cache between reviews (incremental reuse)

Source: [Graphite guide](https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff).

> "Maintain state or cache between reviews; reuse prior context so you don't have to reprocess everything every time."

> "Caching / incremental updates: avoid reindexing the entire repo each time; use incremental updates as new commits land."

This directly validates the **AAR ledger** proposal from earlier this session. Graphite, SonarQube, PMD, and CodeQL all implement incremental analysis with cached prior results. The pattern is named and proven in static analysis; applying it to LLM-driven AAR is the novel step.

## Don'ts

### 1. Don't write a vague description

Source: generativeprogrammer.com Pattern 1.

**Anti-patterns:**
- "Helps with documents"
- "Processes data"
- "Does stuff with files"

A vague description fails at selection time. The model never invokes the skill, or invokes it on the wrong requests.

### 2. Don't re-explain what the model already knows

Source: Anthropic best practices, generativeprogrammer.com Pattern 3.

**Anti-pattern:**
> "PDF (Portable Document Format) files are a common file format that contains text, images, and other content. To extract text from a PDF, you'll need to use a library..."

The model knows what a PDF is. Every paragraph must justify its token cost.

### 3. Don't use all-caps imperatives without reasoning

Source: generativeprogrammer.com Pattern 6.

**Anti-pattern:**
> "MUST use constructor injection. NEVER use field injection."

This gives the model rules with no rubric for unanticipated cases. Explain *why* the rule exists so the model can generalize.

### 4. Don't use deeply nested references

Source: Anthropic best practices, generativeprogrammer.com Pattern 4.

**Anti-pattern:**
```
SKILL.md → advanced.md → details.md → actual_information.md
```

The model partially reads files when they're referenced from other referenced files. It may use `head -100` to preview, resulting in incomplete information.

**Fix:** keep all reference files **one level deep** from SKILL.md.

### 5. Don't include time-sensitive information inline

Source: Anthropic best practices.

**Anti-pattern:**
> "If you're doing this before August 2025, use the old API. After August 2025, use the new API."

This dates the skill and will become wrong. Put legacy information in an "old patterns" appendix or `<details>` block.

### 6. Don't use inconsistent terminology

Source: Anthropic best practices.

**Anti-pattern:** mixing "API endpoint", "URL", "API route", "path" for the same concept.

Pick one term and use it throughout. Consistency reduces cognitive load.

### 7. Don't over-constrain where judgement is needed

Source: generativeprogrammer.com Pattern 5.

Authors consistently err toward over-constraining because rigid instructions feel safer. They are not; they just fail differently. Match the freedom level to the task's actual fragility.

### 8. Don't build skills that duplicate other skills' failure modes

Source: anthonytd.com.

> "Split concerns into separate skills when they have their own failure modes. Ask: 'should this be one skill or two?'"

If two workflows share state and have the same failure modes, they belong in one skill. If they have different failure modes, they belong in separate skills.

**Our application:** `/tp` and `/red-team` have different failure modes (collaborative critique vs adversarial review) — correctly separate. `/aar` and `/debrief` have overlapping failure modes (retrospective analysis) — **candidate for consolidation review**.

### 9. Don't over-optimize skills that aren't frequently used

Source: anthonytd.com.

> "Don't over-optimize skills that aren't frequently used — match the effort to how often the skill actually runs."

A skill invoked once a month doesn't need the same rigor as one invoked daily. This is the [[deliberation-waste]] pattern applied to skill maintenance.

### 10. Don't declare "done" without eval

Source: anthonytd.com, Anthropic best practices.

**Evaluation-driven development:**
1. Identify gaps (run model on representative tasks without the skill)
2. Create evaluations (3 scenarios that test the gaps)
3. Establish baseline
4. Write minimal instructions
5. Iterate (execute evals, compare against baseline, refine)

**Anatomy of a test scenario:**

| Component | What to write |
|---|---|
| **Prompt** | Exact user input, using real data |
| **Expected output** | Ideal artifact (structure, not verbatim) |
| **Assertions** | 3-5 checkable facts |
| **Anti-assertions** | Things that should NOT appear |

**Our gap:** none of our skills (`/tp`, `/aar`, `/handoff`, `/www`) have formal eval scenarios. We test by running them on real work, which is Level 1 (manual). Upgrading to Level 2 (scripted) or Level 3 (programmatic) would catch regressions when we edit skills.

## Relationship to our skill portfolio

| Our skill | Conformance | Gaps flagged by this research |
|---|---|---|
| `/tp` | Strong description; explains the why; two-lens architecture = A/B loop | Missing exclusion clause in description; no formal eval scenarios |
| `/aar` | Progressive disclosure; self-correcting loop (validator); lean core + references | No copyable phase checklist; no formal eval scenarios |
| `/handoff` | Numbered steps; preflight validator | No copyable checklist format; no exclusion clause |
| `/www` | Delegates rather than reimplements; lifecycle gate | Just shipped — needs A/B loop testing with a fresh instance |
| `/design` | Context firewall (Step 0.5); writer/reviewer loop | Not assessed in this research pass |
| `/go` | Not assessed | Not assessed in this research pass |
| `/review` | Not assessed | Not assessed in this research pass |
| `/red-team` | Not assessed | Not assessed in this research pass |

## Open questions

- Should we add formal eval scenarios to our skills? (anthonytd Level 2/3)
- Should `/aar` and `/debrief` be consolidated given overlapping failure modes?
- Should we add copyable checklists to `/aar`, `/handoff`, `/www`?
- Does the AAR ledger proposal map cleanly to Graphite's incremental-review-cache pattern?

## Sources (full list)

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Anthropic official. Source for: concision principle, three degrees of freedom, progressive disclosure, gerund naming, description in third person, avoid time-sensitive info, consistent terminology, workflows with checklists, feedback loops, build evaluations first.
- [Skill Authoring Patterns from Anthropic's Best Practices](https://generativeprogrammer.com/p/skill-authoring-patterns-from-anthropics) — generativeprogrammer.com, 2026-04-18. Source for: 14 patterns across 5 categories (discovery, context economy, instruction calibration, workflow control, executable code). Activation metadata, exclusion clause, context budget, progressive disclosure, control tuning, explain-the-why, template scaffold, in-skill examples, known gotchas, execution checklist, self-correcting loop, plan-validate-execute.
- [Building Skills for AI Agents: Lessons & Best Practices](https://anthonytd.com/blog/building-skills-for-ai-agents/) — Anthony Thong Do, 2026-06-25. Source for: A/B loop development (Agents A/B/C), evaluation-driven development, output-first vs spec-first workflows, pointers beat descriptions, data in data files / logic in skill files, split concerns by failure mode, drill into why on every bug, subagents for concurrency, don't over-optimize infrequent skills.
- [How much context do AI code reviews need?](https://graphite.com/guides/ai-code-review-context-full-repo-vs-diff) — Graphite. Source for: context scopes (diff/module/full-repo), memory/stateful agents, caching/incremental updates, hybrid strategy, feedback rejection. Directly validates the AAR ledger proposal.

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[skill-enforcement-layers]]
- [[llm-handoff-best-practices]]
- [[i'm-going-to-create-a-hook-to-enforce-discovery-be]]

