---
title: "Spec-driven development tools and planning workflows: field survey and plan-writer improvement opportunities"
created: 2026-07-28
source: session-20260728 (/www research on plan-writer improvement)
tags: [spec-driven-development, plan-writer, llm-coding-workflow, sdd, spec-kit, kiro, tessl, planning, decomposition, over-engineering]
summary: >
  Field survey of spec-driven development (SDD) tools and LLM coding planning
  workflows (GitHub Spec Kit, AWS Kiro, Tessl, Addy Osmani's workflow) compared
  against our plan-writer skill. The industry converges on a 4-phase pipeline
  (Specify → Plan → Tasks → Implement) with human checkpoints — which we already
  have via /design → /plan-writer → /go. Key gaps identified: no problem-size
  scaling (Böckeler found SDD tools "a sledgehammer to crack a nut" for small
  bugs), review overload from verbose plans, no reverse traceability from code
  to spec, and no spec-anchored evolution. Böckeler's warning about
  "Verschlimmbesserung" (making things worse by trying to improve them) directly
  describes our v1-v4 over-engineering pattern. Six concrete improvements
  proposed for plan-writer.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://addyosmani.com/blog/ai-coding-workflow/ (Addy Osmani, Google, Jan 2026)
  - https://www.augmentcode.com/guides/automating-spec-driven-development-with-ai-agents (Augment Code, Sep 2025)
  - https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html (Birgitta Böckeler, Thoughtworks, Oct 2025)
  - https://github.com/github/spec-kit (GitHub Spec Kit, Sep 2025)
  - https://kiro.dev/ (AWS Kiro, 2025)
relations:
  - target: wiki/concepts/maker-checker-required-for-enforcement-work.md
    type: related
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques.md
    type: related
---

# Spec-driven development tools and planning workflows

## Decision context

**Why this research was needed:** session 019fa5a1 produced a close-authority
plan that went through 4 revision rounds, growing to ~900 lines with 4
workstreams. The operator challenged: "do you really feel it is much better?"
The answer was no — attestation was over-engineering. The root cause: the
plan-writer skill has a review loop (catches implementation bugs) but no
decomposition checkpoint (catches over-engineering). This research surveys
what other practitioners and tools do for LLM-assisted planning, to identify
improvements for plan-writer that address the root cause, not just the symptom.

## The field consensus: 4-phase pipeline

The industry has converged on a pipeline that maps directly to our existing
skill chain:

| Industry phase | Our equivalent | Human checkpoint |
|---|---|---|
| Specify | `/design` (or operator-written spec) | Spec review |
| Plan | `/plan-writer` | Plan review (mandatory loop for hard plans) |
| Tasks | `/plan-writer` task decomposition | Task-level review |
| Implement | `/go execute` | Code review (`/review`) |

This means our skill chain IS the industry-standard pipeline. The gaps are in
the details, not the structure.

## What practitioners agree on

**Addy Osmani (Google, Jan 2026):** "waterfall in 15 minutes" — rapid structured
planning before coding. Specs before code. Small iterative chunks. Context
packing (show the AI everything it needs). Commit often. Human in the loop.

**GitHub Spec Kit (Sep 2025):** Constitution (immutable rules), specify → plan
→ tasks with checklists at each phase. Heavy use of file-based prompts and
templates. Aspires to spec-anchored (spec lives with the feature).

**AWS Kiro (2025):** Requirements → Design → Tasks, each as a markdown doc.
Enforces human-in-the-loop at every phase. Lightweight (3 files per spec).

**Tessl (beta):** Spec-as-source (spec IS the code's source of truth). Generated
code marked `// GENERATED FROM SPEC - DO NOT EDIT`. 1:1 mapping between spec
and code file. Most ambitious but least proven.

**Birgitta Böckeler (Thoughtworks, Oct 2025):** The most critical assessment.
Found all three tools over-engineered for small problems. "Verschlimmbesserung"
— making things worse by trying to improve them. Warns about review overload,
false sense of control, and the MDD parallel (inflexibility + non-determinism).

## Key gaps in plan-writer (with sources)

### 1. No problem-size scaling (Böckeler)

Böckeler found Kiro turned a small bug fix into "4 user stories with 16
acceptance criteria" and Spec Kit was "overkill" for a 3-5 point story. Our
`--lite` flag helps but the default should be: "is this problem big enough for
a plan at all?" The decomposition checkpoint should ask this BEFORE writing
tasks.

### 2. Plan length budget (Böckeler: review overload)

Spec Kit created "a LOT of markdown files... repetitive... tedious to review."
Böckeler: "I'd rather review code than all these markdown files." Our v1-v4
plan grew to ~900 lines. The v5 stripping (630→203 lines) is the right
direction. Plans should have a length budget: hard plans ≤400 lines, soft plans
≤200. If exceeded, the decomposition checkpoint fires again.

### 3. AGENTS.md constraint check (Spec Kit's "constitution")

Spec Kit's constitution is checked at every phase. Our AGENTS.md serves the
same role but plan-writer doesn't explicitly verify tasks against it. The
6th completeness check (internal consistency) should also check consistency
with AGENTS.md rules.

### 4. Reverse traceability (Spec Kit, Tessl)

Spec Kit tasks trace back to requirement numbers. Tessl marks generated code.
Our plans have no reverse-traceability — once code is written, the plan is
dead weight. Adding a traceability matrix (task → requirement → spec section)
would help future sessions understand why code exists.

### 5. Spec-anchored option (Tessl)

For long-lived features, the plan should note whether it's spec-first
(disposable) or spec-anchored (update when code changes). This is a flag, not
a mechanism — but it surfaces the decision.

### 6. "Verschlimmbesserung" guard (Böckeler)

Böckeler's core warning: elaborate workflows amplify existing challenges
(review overload, hallucinations, false sense of control) rather than solving
them. The decomposition checkpoint addresses this structurally — but the
review loop should also ask "is this plan simpler than it needs to be?" not
just "does it have bugs?"

## What this means for our workspace

Our skill chain (`/design` → `/plan-writer` → `/go`) is structurally aligned
with the industry consensus. The improvements are:

1. **Problem-size gate** in plan-writer (before readiness gate)
2. **Plan length budget** (hard ≤400, soft ≤200, re-checkpoint if exceeded)
3. **AGENTS.md consistency check** (add to completeness check #6)
4. **Traceability matrix** (task → requirement)
5. **Spec-anchored flag** (disposable vs maintained)
6. **Simplicity check in review loop** ("is this plan simpler than it needs to be?")

These are additive improvements to the existing skill, not a rearchitecture.
This connects to [[maker-checker-required-for-enforcement-work]] (the review
loop is the maker-checker for plans), [[reactive-pattern-matching-and-closure-pressure]]
(closure pressure drives over-engineering just as it drives premature completion),
and [[llm-synthesis-quality-and-speed-techniques]] (Self-Refine curves inform
the review loop's diminishing-returns threshold).

## What people like

- **Structured phases with checkpoints** (everyone agrees this is the core value)
- **TDD task format** (Osmani: "invest in tests")
- **Human stays in the loop** (Stanford Human Agency Scale: equal partnership preferred)
- **Context packing** (Osmani: "don't make the AI operate on partial information")
- **Small iterative chunks** (Osmani, Böckeler, Spec Kit all agree)

## What people don't like

- **Over-verbose plans** (Böckeler: "tedious to review")
- **One-size-fits-all workflows** (Böckeler: "sledgehammer to crack a nut")
- **False sense of control** (Böckeler: agent ignores instructions despite all the files)
- **Too many intermediate artifacts** (Spec Kit creates 8+ files per spec)
- **Reviewing markdown instead of code** (Böckeler's strongest critique)

## Falsifier

These findings would be wrong if: (a) our plan-writer is already producing
high-quality plans that don't suffer from the over-engineering problem — but
session 019fa5a1 disproves this (v1-v4 was over-engineered); (b) the field
consensus shifts away from the 4-phase pipeline — unlikely given 5 independent
sources converging; (c) Böckeler's critique doesn't apply to our context
because our plans are used differently — possible, but the over-engineering
pattern matches.

## Receipts

- **Plan-writer review loop mechanism:** `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md` lines 387-510 (Mandatory review loop section). Verified by reading the skill file this session.
- **Decomposition checkpoint mechanism:** `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md` lines 210-243 (Decomposition checkpoint section). Added this session after the v1-v4 over-engineering pattern.
- **Plan-writer completeness checks:** `C:/Users/brsth/.grok/skills/plan-writer/SKILL.md` lines 330-360 (6 mandatory checks). Verified by reading.
- **Close-authority plan v1-v4 pattern:** `P:/docs/superpowers/plans/2026-07-28-close-authority-completion.md` revision history documents 4 rounds, 47 findings, 900→203 line reduction. [OBSERVED]
- **Industry 4-phase pipeline:** cited from 5 independent sources (Osmani, Augment Code, Spec Kit, Kiro, Tessl). No single source defines it; it emerges from convergence.

## Sources

- [Addy Osmani: My LLM coding workflow going into 2026](https://addyosmani.com/blog/ai-coding-workflow/) (Google, Jan 2026) — comprehensive workflow guide
- [Augment Code: Automating Spec-Driven Development](https://www.augmentcode.com/guides/automating-spec-driven-development-with-ai-agents) (Sep 2025) — enterprise SDD guide with metrics
- [Birgitta Böckeler: Understanding SDD — Kiro, spec-kit, and Tessl](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) (Thoughtworks, Oct 2025) — critical comparison, most useful source
- [GitHub Spec Kit](https://github.com/github/spec-kit) (Sep 2025) — open-source SDD toolkit
- [AWS Kiro](https://kiro.dev/) (2025) — spec-driven IDE
