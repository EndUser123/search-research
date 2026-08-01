---
title: "Skill performance and reliability: maximizing value while preventing LLM bypass"
created: 2026-07-22
source: session-2026-07-22 (/www compound research)
sources:
  - https://arxiv.org/abs/2606.10546
  - https://arxiv.org/abs/2503.18666
  - https://dev.to/akari_iku/how-to-stop-claude-code-skills-from-drifting-with-per-step-constraint-design-2ogd
  - https://www.mindstudio.ai/blog/token-reduction-strategies-ai-agents-cut-costs
  - https://www.reddit.com/r/ClaudeCode/comments/1se66cf/something_has_changed_claude_code_now_ignores/
tags: [skill-design, skill-enforcement, performance, reliability, agent-skills, anti-patterns, token-optimization]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "How to maximize skill performance (token efficiency, code-vs-prose balance) and reliability (preventing LLM bypass) based on SkillAxe diagnostic framework, AgentSpec runtime enforcement, per-step constraint design, and token optimization techniques."
---

# Skill performance and reliability: maximizing value while preventing LLM bypass

Synthesized from four web sources plus 8 existing wiki concepts. Addresses two questions:
(1) how to maximize skill performance without losing value, and (2) how to increase
reliability of skills actually being used as intended. Directly relevant to our /close,
/go, /tp, /aar, /handoff, /www skill portfolio.

## The critical finding: skills are execution knowledge, not answer quality

Source: [SkillAxe (arxiv 2606.10546)](https://arxiv.org/abs/2606.10546), ICSE 2026.

The SkillAxe paper's hierarchical decomposition reveals a surprising insight:

| Metric | No skill | With skill | Delta |
|--------|----------|------------|-------|
| Coverage (% tasks producing output) | 46.7% | 72.7% | **+26pp** |
| Quality (% correct among completed) | 57.1% | 57.1% | **0pp** |

Skills dramatically improve **execution reliability** (coverage) but do NOT improve
**answer quality** among tasks the agent already completes. Skills prevent crashes,
guide library usage, and provide format-handling strategies — they are *procedural
scaffolding*, not intelligence augmentation.

**Implication for our skills:** our skills should focus on **preventing execution
failures** (wrong file paths, missed verification steps, forgotten handoffs) rather
than trying to make the LLM "smarter." The /close scanner is a perfect example — it
mechanically prevents the "forgot to write a handoff" execution failure.

## The disconfirmation: LLM-authored skills provide zero gain

Source: SkillAxe paper, SkillsBench results.

> "LLM-authored skills provide no measurable improvement over bare agents, despite
> being syntactically fluent and often superficially plausible."

This means: writing skills *well* matters. A poorly-written skill is the same as
no skill at all. Human-authored skills improve pass rates by +16.2pp; LLM-authored
skills add 0pp. The gap is closed by SkillAxe's diagnostic refinement loop (47-67%
of the way to human-quality).

**Implication:** we should treat skill authoring as a first-class engineering activity,
not delegate it entirely to LLMs without human review.

## Five techniques for maximizing performance

### 1. Code where deterministic, prompt where judgment is needed

Source: our /close v3 improvement, SkillAxe fault attribution.

The SkillAxe framework distinguishes **instruction compliance** (did the agent follow
the skill?) from **skill quality** (was the instruction worth following?). When a
deterministic rule can be expressed as code, compliance becomes 100% — code doesn't
"skip" steps.

| Task | Mechanism | Why |
|------|-----------|-----|
| Scanning files, counting artifacts, filtering by ID | **Code** | Mechanical; compliance is 100% |
| Gate resolution (pre_satisfied / needs_attention) | **Code** | Deterministic rules on evidence |
| Deciding if work is "done" or "partial" | **Prompting** | Requires session-context judgment |
| Running sub-skills (/wiki, /aar, /check) | **Agent** | Each is a full skill |

This is the pattern our /close v3 uses: the scanner resolves all gates mechanically;
the LLM only fills judgment fields. **The scanner thinks; the LLM judges.**

### 2. Per-step constraint design (not per-skill freedom level)

Source: [akari_iku (dev.to)](https://dev.to/akari_iku/how-to-stop-claude-code-skills-from-drifting-with-per-step-constraint-design-2ogd), February 2026.

Anthropic's "degrees of freedom" framework recommends one freedom level per skill.
The per-step approach argues this is insufficient — real skills contain steps that
need to diverge (exploration) and steps that need to converge (formatting, calculations).

Four constraint types, assigned **per step**:

| Type | Purpose | Strength | Example |
|------|---------|----------|---------|
| **Procedural (HOW)** | Sequential, repeatable | Medium | "Run the scanner, read the JSON" |
| **Criteria (WHAT)** | Quality/judgment matters | Strong | "Evaluate on cost, integration ease, learning cost" |
| **Template** | Fixed output format | Medium-Strong | "Output: `SESSION CLOSED: <date>`" |
| **Guardrail** | Things that must never happen | Strong | "Never claim done without ACCOUNTING block" |

**Anti-patterns:**
- **100% Procedural, 0% Criteria**: every step is "do X" with no quality standard
- **Selection without criteria**: "pick one" without saying what to base it on
- **Volume without quality**: "about 5 pages" specifies length but not standard

**Implication for our skills:** /www, /aar, /handoff could benefit from criteria-typed
constraints on their synthesis/output steps. Currently most steps are procedural.

### 3. Token optimization: externalize state, compress outputs

Source: [MindStudio token reduction guide](https://www.mindstudio.ai/blog/token-reduction-strategies-ai-agents-cut-costs).

Eight techniques ranked by leverage. The ones most applicable to skill execution:

| Technique | Token reduction | Our application |
|-----------|----------------|-----------------|
| **Semantic compression** of tool outputs | 70-90% | Scanner JSON → 8-line summary (not raw JSON) |
| **External state** (SQLite/JSON, not context) | 40-70% | close_accounting.py writes state to file, not context |
| **Capped thinking budgets** | 50-75% | Match model tier to task complexity (our model pool) |
| **Prompt caching** | 60-80% on cached portions | Keep SKILL.md body stable across calls |
| **Structured output** (JSON, not prose) | 40% | Scanner emits JSON, not prose paragraphs |
| **Model routing** | 80-95% combined | Route mechanical tasks to free pool members |

**Implication:** our /close v3 already implements 4 of 8 techniques (semantic
compression, external state, structured output, model routing via scanner). The
biggest remaining wins are prompt caching (keep skill content stable) and capped
thinking (don't use deep reasoning for mechanical steps).

### 4. Exclusion clauses: 3x discrimination margin

Source: SkillAxe trigger analysis (Appendix E).

Skills with explicit exclusion clauses achieve 3x wider discrimination margins than
skills without them. The mechanism: exclusion phrases create geometric separation
in the embedding space used for skill routing.

| Metric | No exclusions | With exclusions |
|--------|---------------|-----------------|
| Discrimination margin | 0.051 | **0.148** (3x) |
| Correct-skill similarity | 0.381 | 0.509 |
| Max-wrong similarity | 0.330 | 0.361 (barely changes) |

**Implication:** every skill description should have a "Do NOT use for..." line.
Our wiki already documents this ([[skill-authoring-patterns-dos-and-donts]] Don't #1),
but several skills still lack it.

### 5. Consolidate skills to reduce manifest size

Source: SkillAxe SpreadsheetBench results.

The SkillAxe library achieved the same accuracy as the naive library with **68% fewer
skills** (22 vs. 69). Fewer skills = smaller manifest injected into every prompt =
lower token cost and latency. The consolidated skills were also activated nearly 2x
as often (35.8% vs. 20.0%).

**Implication:** our skill portfolio has overlapping skills (/aar vs. /debrief, /check
vs. /review). Consolidation isn't just tidiness — it measurably improves activation
rates and reduces per-invocation token cost.

## Four techniques for preventing LLM bypass

### 1. Runtime enforcement: move from advisory to structural

Source: [AgentSpec (arxiv 2503.18666)](https://arxiv.org/abs/2503.18666), ICSE 2026.

Our wiki ([[skill-enforcement-layers]]) documents that Layer 1 (UserPromptSubmit
advisory injection) fails ~50% of the time. AgentSpec proposes a fundamentally
different approach: a **domain-specific language for runtime constraints** that
monitors agent actions in real-time.

AgentSpec achieves:
- **>90% prevention** of unsafe executions in code agent cases
- **100% elimination** of hazardous actions in embodied agent tasks
- **Millisecond overhead** — lightweight enough for production

The key insight: instead of telling the LLM "don't do X" in prose (which it may
ignore), define X as a runtime rule that intercepts tool calls before execution.

**How this maps to Grok Build:** our PreToolUse hooks are a primitive form of this
(pattern matching on tool names/args). AgentSpec's approach is more general: rules
with triggers, predicates, and enforcement mechanisms. The evolution path is from
regex matching → semantic rules → stateful constraint checking.

### 2. Output validators: refuse to accept non-compliant output

Source: our existing pattern (output_validator.py in /check), SkillAxe fault attribution.

The SkillAxe framework's "instruction compliance" dimension distinguishes:
- **Agent fault**: the skill's rule was clear, the agent didn't follow it
- **Skill fault**: the rule was vague or contradictory

An output validator catches both: if the output doesn't match the expected schema,
reject it and send it back with the specific contract violation cited. Our /check
skill already does this (`output_validator.validate_verifier_output`).

**Pattern:** every skill that produces structured output should have a validator.
The validator is the backstop that makes compliance non-optional.

### 3. Copyable checklists: make skipped steps visible

Source: [[compound-skill-improvement-patterns]], akari_iku article.

A checklist pasted into the conversation makes skipped steps visible to both model
and user. The model can see what it hasn't done yet; the user can see what the
model claims to have done.

```markdown
/www Progress:
- [ ] Phase 1: Query wiki
- [ ] Phase 2: Research gaps
- [ ] Phase 3: Persist findings
```

**Implication:** /www already has this. /aar, /handoff, and /close could add them.
The /close scanner makes this less necessary (the gates ARE the checklist), but for
skills without mechanical scanners, the copyable checklist is the enforcement tool.

### 4. Skills as execution knowledge: focus on what prevents crashes

Source: SkillAxe hierarchical decomposition.

Since skills improve coverage (execution reliability) but not quality (answer
correctness), the highest-value skill content is **procedural knowledge that prevents
execution failures**:

- File paths that are easy to get wrong
- Step sequences that are easy to skip
- Format requirements that are easy to drift from
- Library/API usage patterns that prevent crashes

**Example from SkillAxe:** a spreadsheet skill that warns "Word splits placeholder
text across multiple XML runs" prevents the #1 failure mode for template-filling
agents. This is worth more than any amount of "be careful and thorough" advisory text.

**Implication for our skills:** our most valuable skill content is the mechanical
knowledge (exact file paths, exact script invocations, exact JSON schemas) — not the
prose explanations of why. The /close scanner's gate resolution logic is more valuable
than the SKILL.md prose explaining why gates matter.

## Conflict: over-constraining vs. under-constraining

Source: disconfirmation search (Reddit, LinkedIn, HN).

Multiple sources warn that **too many instructions reduces compliance**:

> "As you pile on more instructions or data, the model's ability to follow any
> individual instruction decreases." — Addy Osmani

> "Over-prompting is stuffing your agent's prompt with rules, edge cases, and walls
> of 'never do this' that collectively paralyze the agent." — Adam Kalsey

This creates a tension: more constraints prevent drift, but too many constraints
cause the model to ignore all of them. The resolution:

1. **Per-step constraints** (akari_iku): constrain only the steps that need it, leave
   others free. Don't apply a blanket constraint level.
2. **Code where possible** (our /close pattern): move constraints from prose into code,
   reducing the instruction count the LLM must track.
3. **Progressive disclosure**: only load the constraints relevant to the current step,
   not all constraints for all steps at once.

## Relationship to our skill portfolio

| Our skill | Current enforcement | Improvement opportunity |
|-----------|--------------------|-----------------------|
| `/close` v3 | Scanner resolves gates mechanically | Already implements code-first pattern; add copyable checklist |
| `/go` | Prose steps with spawn recipes | Per-step constraint design; code for routing decisions |
| `/tp` | Two-lens architecture | Add exclusion clause; add output validator for critique format |
| `/aar` | Output validator + phase structure | Add copyable phase checklist; add criteria-typed constraints |
| `/handoff` | Preflight validator | Add exclusion clause; consolidate with /aar overlapping failure modes |
| `/www` | Copyable checklist + lifecycle gate | Already strong; could add semantic compression of wiki batch-read output |
| `/check` | Preprocessor + output validator | Already strong; the gold standard for our skills |
| `/review` | Findings.json + FINDINGS.md | Could add per-lens constraint typing |

## Actionable recommendations

1. **Add exclusion clauses to all skill descriptions** — 3x discrimination margin,
   near-zero cost, highest ROI single change.
2. **Audit each skill for per-step constraint types** — flag any skill that is 100%
   procedural with no criteria-typed steps.
3. **Move deterministic logic to code** where possible (the /close pattern). Every
   rule expressed in code is one fewer rule the LLM must track in prose.
4. **Add output validators** to skills that produce structured output. The validator
   is the enforcement backstop that makes compliance non-optional.
5. **Consolidate overlapping skills** — fewer skills = smaller manifest = higher
   activation rates (SkillAxe: 68% fewer skills, 2x activation).
6. **Audit token budget per skill** — any skill body >500 lines should be split
   (progressive disclosure). Any skill description >100 tokens needs tightening.

## Auto-related

- [[skill-enforcement-layers]]
- [[multi-agent-correlated-errors]]
- [[skill-enforcement-deep-dive]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
