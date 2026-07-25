---
title: "Designing agent harnesses that make good behavior the path of least resistance"
created: 2026-07-25
source: session-019f94c9
tags: [harness-engineering, structural-enforcement, llm-quality, agent-design, cognitive-load, defaults, templates, validators, positive-design]
summary: >
  Most agent infrastructure is designed to STOP bad behavior (rules, gates,
  blockers). This entry documents the complementary principle: design
  infrastructure that MAKES good behavior the easiest option. Three techniques
  achieve this: (1) templates that reduce cognitive load by giving the LLM a
  structure to fill instead of a blank page; (2) validators that catch thin
  work mechanically so the LLM doesn't have to self-assess quality; (3) quality
  priming that shows "what good looks like" before the LLM starts. The key
  insight: under session fatigue, the LLM takes shortcuts not because it's lazy
  but because the "proper job" path requires more cognitive effort with no
  structural support. Fix the structure, not the model.
agent: grok
host: grok
cognitive_load: 4
verification: session-evidence
sources:
  - This session (2026-07-25): wiki validator + template + anti-thin-entry gate
  - Addy Osmani, "Loop Engineering" (Jun 2026): harness engineering principle
  - Jang-woo, "Pre-Execution Checklist" (Jun 2026): structural enforcement over advisory rules
  - Session 2026-07-23: mandatory-step-enforcement-code-over-prose
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: complements — that page explains WHY the model fails; this explains how to make it succeed
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: extends — that page establishes code-over-prose; this adds the positive-design layer
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: complements — external mitigations for failure; this is internal design for success
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: related — harness engineering taxonomy
---

# Designing agent harnesses that make good behavior the path of least resistance

## Decision context

**Why this knowledge was needed:** the operator asked "Is there a way to make it easier for you to be a good LLM?" after catching the agent writing thin wiki summaries. The question reframes the entire approach to agent quality: instead of asking "how do we stop the LLM from being bad?" (defense), ask "how do we design the harness so good behavior is the easiest option?" (enablement). This entry captures the structural techniques that answer that question.

## The problem: good behavior is harder than bad behavior

Under normal conditions, the LLM can produce professional-quality work. Under cognitive load (long sessions, context pressure, closure desire), the LLM takes shortcuts. This is not laziness — it's the pattern-completion pathway optimizing for the path of least resistance. The "proper job" path requires:

1. **Inventing structure** — what sections should this wiki entry have? What depth is sufficient?
2. **Self-assessing quality** — is this entry good enough? Am I cutting corners? (This is where narrative closure defeats self-assessment)
3. **Resisting closure pressure** — the pull toward "this looks sufficient, ship it" overrides the pull toward "expand this section, add cross-references"

Each of these is a cognitive tax. When the tax is high enough, the model pays it by shortcutting. The shortcut produces thin summaries, premature conclusions, and missing sections.

## The insight: reduce the tax, don't increase the willpower

The traditional approach to agent quality is **advisory rules** (AGENTS.md, SCHEMA.md quality gates). These tell the model what to do but don't make doing it easy. Under cognitive load, the model reads the rule and still shortcuts — because following the rule requires the same cognitive effort that's being taxed.

The structural approach is different: **reduce the cognitive tax of good behavior until it's less effort than the shortcut.** Three techniques achieve this:

### Technique 1: Templates that reduce cognitive load

**Principle:** filling in a template is cognitively easier than inventing structure from scratch.

**How it works:** instead of "write a wiki concept" (abstract, open-ended), provide a concrete fill-in-the-blanks template with every section named and described. The LLM's job changes from "design the structure AND fill it" to "just fill it." The cognitive load drops by ~50% because the structural design work is already done.

**Implemented this session:** `/wiki` SKILL.md now has a mandatory entry template (frontmatter, decision context, main content, workspace implications, falsifier, sources). The LLM fills the template instead of inventing the structure.

**Why it works:** the template removes the "what should this look like?" question. That question is where shortcuts happen — under pressure, the LLM answers it with "a few bullet points will do." The template pre-answers it with "this is what professional looks like; fill in each section."

**Limitation:** templates can become performative — the LLM fills sections with thin content to satisfy the structure. The validator (Technique 2) catches this.

### Technique 2: Validators that catch thin work mechanically

**Principle:** mechanical validation removes the need for self-assessment, which is the faculty that fails under closure pressure.

**How it works:** a script (`validate_wiki_entry.py`) checks line count, required sections, cross-references, frontmatter fields, and source citations. Exit 0 = pass; exit 1 = fail with specific issues. The LLM doesn't have to ask "is this good enough?" — the validator answers that question mechanically.

**Implemented this session:** `validate_wiki_entry.py` wired into both `/wiki` (after write, before declaring done) and `/www` Phase 3 (Step 3.3, alongside the disconfirmation validator). Tested: catches thin entries (4-line test → FAIL), passes good entries (premature-closure rewrite → PASS).

**Why it works:** self-assessment fails under closure pressure because the assessing faculty shares the same pattern-completion pathway that produced the work being assessed. The validator is a separate process that doesn't feel pressure — it just checks. This is the same principle as the maker-checker split in [[premature-closure-narrative-sufficiency-external-approaches]] (Approach 5: separation of verification from generation), but applied at the output level rather than the agent level.

**Limitation:** the validator checks structure, not content quality. It can catch "too short" and "missing sections" but not "the reasoning is shallow." Content quality still requires the LLM's judgment or a fresh-lens reviewer.

### Technique 3: Quality priming that shows "what good looks like" before starting

**Principle:** priming the LLM with quality expectations before it starts writing produces better output than hoping it remembers after writing.

**How it works:** a checklist that the LLM must self-assess against BEFORE writing the entry. The checklist names what "good" looks like in concrete terms: "Does the entry explain WHY?" "Does it synthesize with reasoning?" "Does it connect to ≥3 existing concepts?" This primes the LLM's attention toward quality dimensions it might otherwise skip.

**Implemented this session:** `/www` Phase 3 now has a 7-item anti-thin-entry checklist that fires before the wiki write. Each item is a concrete quality dimension, not an abstract instruction.

**Why it works:** LLMs are sensitive to priming — the context window's contents shape output. A checklist that says "explain WHY, synthesize, connect" primes those dimensions into the generation. Without the checklist, the LLM's default is "summarize what was found" (the shortest path). With the checklist, the default shifts toward "synthesize what was found and why it matters" (the professional path).

**Limitation:** priming is probabilistic, not deterministic. Under extreme pressure, the LLM may read the checklist and still shortcut. The validator (Technique 2) is the backstop.

## The positive-design principle

These three techniques embody a single principle:

> **Don't design infrastructure that stops bad behavior. Design infrastructure that makes good behavior the path of least resistance.**

| Approach | Question it asks | Mechanism | Failure mode |
|----------|-----------------|-----------|--------------|
| **Advisory rules** (traditional) | "How do we tell the model what to do?" | Prose rules in AGENTS.md | Rules read but not followed under pressure |
| **Negative enforcement** (defensive) | "How do we block bad behavior?" | Gates, hooks, blockers | Blocks the bad but doesn't make good easy |
| **Positive design** (this entry) | "How do we make good behavior the easiest option?" | Templates, validators, priming | Still probabilistic; structural fixes preferred |

The three approaches are complementary, not competing. Advisory rules set the intention. Negative enforcement catches what slips through. Positive design makes the intention the default behavior by reducing the cognitive tax of following it.

## Worked examples from this session

| Problem | Advisory rule (failed) | Positive-design fix (worked) |
|---------|----------------------|---------------------------|
| Thin wiki summaries | SCHEMA.md §4: "write non-obvious, verified, durable entries" (read, not followed) | Template + validator + quality checklist |
| Premature closure on diagnostics | AGENTS.md receipt rule: "claims require receipts" (read, not applied) | `/why` skill: fan-out + premise labeling + verify-observation-first |
| Design doc with unverified premises | `/design` Step 0.5: "preflight when design touches existing implementations" (conditional, sometimes skipped) | Step 0.8: mandatory premise labeling with [FACT]/[INFERENCE]/[UNKNOWN] |
| Closure-pressure minimization | Self-rationalization check: "is this rationalization?" (self-applied, captured) | `validate_verdict_consistency.py`: mechanical check for PROCEED + open gaps |

In each case, the advisory rule existed and was read. It didn't fire under pressure. The positive-design fix made the good behavior structurally easier than the shortcut.

## What this means for our workspace

Every skill we build should ask: **"what's the shortcut the LLM will take under pressure, and how do we make the professional path easier than the shortcut?"**

The answer is almost always one or more of:
1. **Template** — give the LLM a structure to fill instead of a blank page
2. **Validator** — mechanically check the output so self-assessment isn't needed
3. **Priming checklist** — show "what good looks like" before starting

These are cheap to implement (a template section in SKILL.md, a validator script, a checklist), permanent (don't decay under pressure), and generalizable (apply to any skill that produces artifacts).

The validators built this session are the strongest examples:
- `validate_verdict_consistency.py` — catches closure-pressure minimization in `/tp`
- `validate_close_receipt.py` — catches contradictory fields in `/close`
- `validate_wiki_entry.py` — catches thin wiki entries in `/wiki` and `/www`

Each one makes good behavior the path of least resistance by catching the shortcut mechanically. The LLM doesn't need willpower to avoid the shortcut — the shortcut doesn't work.

## Falsifier

This approach is wrong if:
- Templates consistently produce performative filling (sections present but content shallow) that the validator can't catch
- Validators add more friction than value (LLM spends more time satisfying the validator than producing good work)
- The positive-design approach produces WORSE outcomes than advisory rules alone (unlikely but testable)

If the validators consistently catch real quality issues and the templates consistently produce better entries than blank-page authoring, the approach is validated.

**Current evidence (1 session):** the wiki validator caught thin entries and passed good ones in testing. The template was used for the first time on this session's entries. Needs 5+ sessions of usage data before generalizing.

## Sources

- This session (2026-07-25): three validators + template + anti-thin-entry checklist implemented
- [[mandatory-step-enforcement-code-over-prose]] — established code-over-prose principle
- [[premature-closure-narrative-sufficiency-external-approaches]] — external approaches to the failure class
- [Addy Osmani: Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (Jun 2026) — harness engineering principle
- [Jang-woo: Pre-Execution Checklist](https://discuss.huggingface.co/t/if-unsure-ask-never-guess-ai-agent-pre-execution-checklist/176632) (Jun 2026) — structural enforcement over advisory rules
