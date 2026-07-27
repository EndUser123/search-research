---
title: "/design speedup: --fast mode, parallel pre-write, parallel review, model cascading"
created: 2026-07-27
source: session-019f9a3c (/go implementation of /www recommendations)
tags: [skill-design, design-skill, parallelism, model-cascading, speedup, fast-mode, llm-behavior, cross-host]
summary: >
  Four research-backed speedups implemented in the /design SKILL.md to cut
  wall-clock time from ~25-30 min to ~10-15 min per design run. (1) --fast
  mode: 2-round default per RefineBench 2025 evidence (frontier models gain
  only +1.8% over 5 turns of self-refinement). (2) Step 0.9: parallel
  pre-write dispatch when >=2 of Steps 0.5-0.8 fire. (3) Parallel review:
  split 11 check dimensions across 3-4 reviewers for complex designs.
  (4) Model cascading: cheap models (minimax-m3) for pre-write steps,
  frontier only for writer + critical friend. Parallel section drafting
  was explicitly REJECTED — the merge step costs as much as the
  parallelism saved, and no major AI coding tool parallelizes design-doc
  authoring. Commits: 76b4634, 0d9a41b.
agent: grok
host: both
cognitive_load: 2
verification: research-backed
sources:
  - "P:/.data/wiki/concepts/llm-synthesis-quality-and-speed-techniques.md (session-019f9a3c)"
  - "P:/.data/wiki/concepts/parallelizing-design-doc-generation-what-works.md (session-019f9a3c)"
  - "Self-Refine (Madaan et al. 2023, arxiv 2303.17651)"
  - "RefineBench (2025, arxiv 2511.22173)"
  - "RouteLLM (lmsys 2024)"
relations:
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques
    type: implemented-by — this concept is the implementation of that research's recommendations
  - target: wiki/concepts/parallelizing-design-doc-generation-what-works
    type: implemented-by — this concept implements the speedup direction from that research
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: refines — adds --fast mode and parallel dispatch to the /design skill
---

# /design speedup: --fast mode, parallel pre-write, parallel review, model cascading

## Decision context

**Why this was needed.** The /design skill took 25-30 minutes per run,
dominated by serial write→review→revise→re-review cycles. The operator
asked whether parallel multi-agent orchestration could speed it up. Two
/www research runs established that parallel section drafting fails (the
merge step eats the gain) but parallel pre-write + parallel review +
a 2-round default work. The /go run implemented the four winning
recommendations.

**What alternatives were explored.** See
[[parallelizing-design-doc-generation-what-works]] for the full
alternatives analysis. The rejected alternative was parallel section
drafting (the operator's original idea) — disconfirmed by every major AI
coding tool survey and the LangGraph orchestrator-worker pattern's own
acknowledgment that the merge step "often costs as much as the parallel
writers combined."

## Receipts

- **[FACT]** Commit 76b4634 in `~/.grok` repo: 4 changes applied to
  `skills/design/SKILL.md` (+48/-3 lines). Verified via `git show 76b4634`.
- **[FACT]** Commit 0d9a41b: off-by-one fix in parallel review table.
  Verified via `git show 0d9a41b`.
- **[FACT]** RefineBench 2025 (arxiv 2511.22173): +1.8% over 5 turns.
  Self-Refine (arxiv 2303.17651): ~20% average improvement, rounds 1-2.
- **[FACT]** RouteLLM (lmsys 2024): 40-85% cost reduction.
- **[INFERENCE]** "~10-15 min per design run" is estimated from the
  research evidence (saves ~13-18 min off ~25-30 min), not measured on
  a real --fast run. Needs validation.
- **[INFERENCE]** "No quality loss from cheaper models" on pre-write
  steps is derived from RouteLLM's chat/QA evidence, not design-doc
  pre-write specifically. Needs A/B testing.

## The four changes

### 1. --fast mode (2-round default)

When the user invokes `/design --fast`, default to 2 review-revise
rounds (draft → review → revise → re-review → critical friend → done).
Do not run a 3rd round unless the re-review surfaces a critical or major
issue. Skip the consistency sweep (Step 4.5). Still run all pre-write
steps (0.5-0.8) and the critical friend (Step 5.5).

**Rationale:** RefineBench 2025 shows even frontier models gain only
+1.8% over 5 turns of self-refinement. Self-Refine (Madaan 2023) shows
~20% average improvement with biggest gains in rounds 1-2. The 2-round
default captures ~80% of the available improvement.

### 2. Step 0.9: Parallel pre-write dispatch

When ≥2 of Steps 0.5, 0.6, 0.7, 0.8 will run, dispatch them as parallel
background subagents instead of serially. Wait-all gate before proceeding
to Step 1.

**Rationale:** the /www skill's own provenance validates parallel
pre-write: "4 parallel M3 subagents completed in ~90-140s." The four
pre-write steps are independent by design.

### 3. Parallel review (Step 2 option)

For complex designs (>1500 lines, ≥4 appendix sections), split the 11
review dimensions across 3-4 parallel reviewer subagents. Deduplicate
findings, assign unified F-NN IDs.

**Rationale:** the reviewer's 11 check dimensions are independent. Splitting
them saves ~2-3 min with no quality loss.

### 4. Model cascading

Use cheaper models for mechanical pre-write steps (minimax-m3 for 0.5,
0.6, 0.7) and parent-inherited for 0.8 (needs reasoning). Only the writer
(Step 1) and critical friend (Step 5.5) need the frontier model.

**Rationale:** RouteLLM cascading evidence shows 40-85% cost reduction
with ~95% of frontier quality retained. Pre-write steps are mechanical
extraction/research/summarization — no quality loss from cheaper models.

## Steeman (rejected alternative)

**Parallel section drafting.** The operator's original idea: multiple
writers each draft a section in parallel, then a critic-friend merges.
The evidence disconfirmed this: every major AI coding tool (Cursor,
Devin, Copilot Workspace, Codex, Jules, BMAD) generates design docs
serially. LangGraph's orchestrator-worker pattern acknowledges the merge
step needs a costly LLM synthesizer pass. MAST taxonomy (NeurIPS 2025)
found 41-87% failure rates in multi-agent systems. The merge step costs
as much as the parallelism saved.

## Falsifier

This decision is wrong if:
- The 2-round default produces materially worse designs than 3+ rounds on
  a controlled A/B test (RefineBench currently disconfirms)
- Model cascading degrades pre-write quality on design docs specifically
  (RouteLLM data is from chat/QA, not design)
- Parallel pre-write introduces hidden dependencies between steps that
  break the parallel dispatch (steps are designed to be independent)

**Discriminating test:** run `/design --fast` on 3 real designs. Compare
critical-friend verdicts and review-finding counts against the current
3-round baseline. If quality is equivalent, the speedup is validated.

## Known interaction gaps (from /review, 2026-07-27)

Two undefined interactions were identified by /review and accepted as
documented caveats:
- **R-001:** `--fast` + `--lite` passed together → undefined which wins
  (recommendation: `--lite` wins as the simpler pipeline)
- **R-002:** Step 0.8 model cascading says "parent-inherited" but Step
  0.9 says "dispatch each as subagent" — parent-inherited can't be a
  background subagent (recommendation: 0.8 runs inline while 0.5-0.7
  run in parallel)

Both are one-sentence fixes deferred to the next SKILL.md edit.

## Related

- [[llm-synthesis-quality-and-speed-techniques]] — the research backing these changes
- [[parallelizing-design-doc-generation-what-works]] — the research that disconfirmed parallel section drafting
- [[agentic-sdlc-skill-lifecycle-architecture]] — the skill lifecycle these changes fit into
