---
title: "External improvement ideas for /design: loop engineering, living specs, and structured review"
created: 2026-07-25
source: session-019f94c9-www-research
tags: [design-skill, loop-engineering, living-specs, spec-driven-development, design-review, improvement-ideas, external-research]
summary: >
  External research on design-doc processes, LLM-driven design review, and
  spec-driven development tools. Five improvement ideas for /design from
  industry and academic sources that go beyond what internal wiki scanning
  found. Key findings: living specs (vs static), structured review perspectives,
  verifiable stopping conditions, EARS notation for acceptance criteria, and
  spec lifecycle state machines.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://arxiv.org/abs/2509.09975 (Fukuda et al., automated design doc review)
  - https://addyosmani.com/blog/loop-engineering/ (loop engineering, Jun 2026)
  - https://www.augmentcode.com/tools/best-spec-driven-development-tools (SDD tools comparison, 2026)
  - https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html (Martin Fowler on SDD)
relations:
  - target: wiki/concepts/design-skill-preflight-gap.md
    type: extends
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
---

# External improvement ideas for /design

## Decision context

**Why this research was needed:** internal wiki scanning (this session, 9 findings) and red-team review (5 fixes) covered internal patterns. This research covers external patterns the wiki doesn't have — what the industry and academia are doing with LLM-driven design review and spec-driven development in 2025-2026.

## Finding 1: Living specs vs. static specs (the biggest gap)

**Source:** Augment Code SDD tools comparison; Martin Fowler on SDD

**What the industry says:** the #1 axis distinguishing SDD tools in 2026 is spec lifecycle — **living** (auto-updating during implementation) vs. **static** (written once, drifts immediately). Augment Cosmos, the top-rated tool, differentiates on living specs that track implementation changes and update the spec so downstream agents reference current truth.

**How this applies to /design:** our design doc is static. It's written once, revised in the write→review loop, then frozen. During implementation, the design doc drifts from the code immediately. The wiki already captures this: *"~80% of a design doc's bulk becomes obsolete the moment implementation starts."*

**Suggested change:** add a "Spec Reconciliation" step (new Step 7) that runs after implementation, comparing the implemented code against the design doc's Key Decisions and Architecture sections. Flag drift. This is NOT keeping the full doc alive — it's a one-time post-implementation check that captures what diverged and why.

**Priority:** medium — adds value but requires implementation context the design skill doesn't currently have.

## Finding 2: Structured review perspectives (11-perspective taxonomy)

**Source:** Fukuda et al., "Development of Automated Software Design Document Review Methods Using LLM" (arXiv:2509.09975, Sep 2025, 4 citations)

**What the paper says:** they organized design document review into **11 structured perspectives** and evaluated which ones LLMs can review vs. which need humans:
1. Consistency between design items
2. Consistency between descriptions across documents
3. Completeness of descriptions
4. Correctness of technical content
5. Traceability (requirements → design → implementation)
6. Conformance to standards/conventions
7. Feasibility of the design
8. Clarity and unambiguity
9. Appropriate level of detail
10. Security considerations
11. Performance considerations

They found LLMs are effective at perspectives 1-3 (consistency checking) and 6 (conformance), but need human input for 4 (correctness), 7 (feasibility), and 11 (performance).

**How this applies to /design:** our reviewer currently has open-ended review domains. Mapping them to a structured taxonomy would ensure consistent coverage. We already cover most of these (consistency = Step 4.5 sweep, conformance = reviewer checks, security/performance = context-derived domains). The gap is **traceability (#5)** — we don't verify that requirements map to design elements map to PR plan tasks.

**Suggested change:** add a "Requirements Traceability Matrix" to the design doc template: each requirement → which design section addresses it → which PR implements it. The reviewer checks that every requirement has a traceable path through design to implementation.

**Priority:** high — traceability is the one perspective we structurally miss.

## Finding 3: Verifiable stopping conditions (`/goal` pattern)

**Source:** Addy Osmani, "Loop Engineering" (Jun 2026); Boris Cherny (Anthropic), Peter Steinberger

**What the article says:** the `/goal` pattern (in both Claude Code and Codex) keeps running until a **verifiable stopping condition** holds, checked by a **separate model** (not the one that did the work). The maker/checker split applied to the stop condition itself.

**How this applies to /design:** our design loop exits when the reviewer reports 0 open issues AND the critical friend returns PROCEED. But "0 open issues" is the reviewer's judgment — the same model that shares the writer's framing could miss something. A verifiable stopping condition would be: "all acceptance criteria from Step 0.8 premises are labeled [FACT] with receipts, AND the critical friend's falsifiers have been addressed or explicitly accepted."

**Suggested change:** the critical friend (Step 5.5) already checks premises, but it's advisory. Consider making the exit condition verifiable: the orchestrator checks that every [INFERENCE] premise has been either resolved (upgraded to [FACT] with receipt) or explicitly accepted by the user in Open Questions before allowing exit.

**Priority:** medium — the critical friend already catches most of this; this makes it mechanical.

## Finding 4: EARS notation for acceptance criteria

**Source:** Amazon Kiro; EARS (Easy Approach to Requirements Syntax)

**What the industry says:** Kiro uses EARS notation for requirements: `WHEN [condition] THE SYSTEM SHALL [behavior]`. This produces clear, testable acceptance criteria. Kiro's 2026 Requirements Analysis feature uses formal logic and SMT solvers to catch contradictions before code generation.

**How this applies to /design:** our acceptance criteria are "quantified: test count, specific verifiable conditions, backwards-compatibility requirement." EARS notation would make them structurally testable: instead of "all 121 tests pass," write `WHEN pytest runs on the test suite THE SYSTEM SHALL exit 0 with 121 passed, 0 failed`.

**Suggested change:** recommend EARS notation in the writer persona for acceptance criteria. Not mandatory (overkill for some designs) but recommended when the acceptance criteria are behavior-level.

**Priority:** low — formatting improvement, not structural.

## Finding 5: Spec lifecycle state machine (OpenSpec pattern)

**Source:** OpenSpec (52,100 GitHub stars); GitHub Spec Kit

**What the industry says:** OpenSpec enforces a strict three-phase state machine: **proposal → apply → archive**. No code is written until the proposal is approved. The spec directory separates current state (`specs/`) from active proposals (`changes/`). `openspec validate --strict` catches missing acceptance scenarios before approval.

**How this applies to /design:** our design doc goes from draft → review → final → (dies in temp). There's no "applied" state where the design is checked against implementation, and no "archive" state where lessons are extracted post-implementation.

**Suggested change:** this overlaps with Finding 1 (living specs). The lightweight version: add a "Post-Implementation Review" handoff step (Step 7) where the design doc's Key Decisions are checked against what was actually built. Promote divergences to wiki concepts. This is the "archive" phase — extracting durable knowledge from the design after it's been tested against reality.

**Priority:** medium — closes the loop between design and implementation.

## What we already have (no change needed)

- **Maker/checker split** — our writer/reviewer/critical-friend architecture already implements this (confirmed by the loop engineering article as the most important structural pattern)
- **Skills for project knowledge** — our AGENTS.md + SKILL.md system is exactly what Osmani describes
- **Persona-based agents** — our TOML personas match the Codex/Claude Code subagent pattern
- **Worktrees for isolation** — we have this via `isolation: worktree` on spawn_subagent

## Summary: 5 external improvement ideas

| # | Idea | Source | Priority | What changes in /design |
|---|------|--------|----------|------------------------|
| 1 | Spec reconciliation (post-implementation) | Living specs movement | medium | New Step 7: compare implemented code vs. design Key Decisions |
| 2 | Requirements traceability matrix | Fukuda et al. 11 perspectives | high | Add traceability matrix to design template + reviewer checks |
| 3 | Verifiable exit condition | `/goal` pattern | medium | Exit requires all [INFERENCE] premises resolved or accepted |
| 4 | EARS notation for acceptance criteria | Amazon Kiro | low | Recommend in writer persona |
| 5 | Spec lifecycle (proposal → applied → archived) | OpenSpec | medium | Post-implementation review handoff step |

## Disconfirmation

One way these ideas might NOT be improvements: our workspace is a **solo operator** running an AI fleet, not a team. Most SDD tools and loop-engineering patterns are designed for teams with 20-50+ engineers. The coordination overhead (living specs, traceability matrices, formal EARS notation) may not be worth it for a single decision-maker who can hold the design in their head. The Augment Cosmos reviewer notes: *"Solo developers on single-repo projects will find the platform scope unnecessary."*

**Counter:** our workspace is more complex than most teams — 46+ models, 80+ handoffs, multi-agent concurrency. The coordination problems that SDD tools solve are real here even without a team. But the implementation should be lightweight, not enterprise-grade.
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
