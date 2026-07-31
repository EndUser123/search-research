---
title: "Code review speed comes from richer context, not more agents"
created: 2026-07-30
source: session-019fb49b (/www research on parallel code review)
tags: [code-review, llm-review, parallel-agents, context-bundle, diff-in-bundle, bugbot, ensemble, practitioner-research]
summary: >
  Practitioner evidence shows LLM code review speed comes from richer
  context bundles (diff + related code inline), not from parallelizing
  across more agents. Single-agent sequential review is faster for
  correctness-critical review because findings build on each other.
  Parallel multi-model review (BugBot's 8-pass ensemble, Multi-Review
  n=5-10) adds coverage breadth and reduces false positives via
  majority-voting, but at higher compute cost. Applied to /tp: diff-in-bundle
  for implementation reviews. Applied to /review: diff-in-bundle for
  specialist prompts. Parallel belongs in /review (defect hunting), not /tp
  (framing challenge).
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
sources:
  - "https://zylos.ai/zh/research/2026-03-01-multi-model-ai-code-review-convergence/ (Zylos Research, Mar 2026 — 5 architectural patterns for multi-model review)"
  - "https://www.shawnmayzes.com/ai-engineering/claude-code-subagents-when-to-split-work/ (Shawn Mayzes, Jul 2026 — when to split vs single agent)"
  - "https://medium.com/@danat.shekhe/codex-vs-native-subagents-vs-subagent-router-5a4e03d64c2c (Shekhe, May 2026 — Codex benchmark)"
  - "https://www.propelcode.ai/blog/parallel-coding-agents-code-review-branch-chaos (Propel, 2026 — guardrails for parallel agent review)"
relations:
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline
    type: complements — that covers when to delegate; this covers how to feed context for review
  - target: wiki/concepts/parallel-subagent-wait-all-gate
    type: related — parallel dispatch pattern; this adds the review-specific finding
  - target: wiki/concepts/adversarial-multi-agent-code-review
    type: refines — that covers multi-agent architecture; this adds speed/quality tradeoffs
---

# Code review speed comes from richer context, not more agents

## Decision context

During the yt-is integration session, a /tp review took 498 seconds / 20 tool
calls because the subagent had to discover the diff, existing parsers, and
library availability from scratch. The investigation of how to make LLM code
review faster surfaced a non-obvious finding: **the speed problem is context
starvation, not insufficient parallelism.**

## The finding

Practitioner evidence from multiple sources converges on one conclusion:

**Speed:** Richer context bundles (diff + related code inline) eliminate the
5-20 tool-call discovery phase. One well-fed agent is faster than two starving
agents running in parallel.

**Quality (single-agent sequential):** Code review requires accumulated
understanding — finding a bug in function A changes how you read function B.
Shawn Mayzes (practitioner blog): "A single agent with full context of the
whole problem will usually finish faster and more correctly than a coordinated
team." This applies to correctness-critical review (framing challenges, logic
bugs), not to coverage-maximizing review.

**Quality (parallel multi-model):** BugBot (Cursor) runs 8 parallel passes
with randomized file ordering and majority-votes results — 70% resolution rate
across 2M+ PRs/month. The Multi-Review paper (Sept 2025) showed +43.67% F1
improvement and +118.83% recall with n=5-10 independent passes. This adds
coverage breadth and reduces false positives, but at higher compute cost.

**The key distinction:** parallel multi-model review is for defect hunting
(different model families catch different bugs). Sequential single-agent
review is for framing challenges (accumulated understanding matters). Speed
comes from richer context in both cases.

## What was applied this session

| Skill | Change | Rationale |
|-------|--------|-----------|
| `/tp` | Step 1 context bundle now includes git diff + inline code + related code for implementation reviews | Eliminates 5-20 tool-call discovery; subagent critiques immediately |
| `/review` | Step 4 specialist prompts now inline the diff directly + known related code | Same speed win for parallel specialists; each gets evidence upfront |

Parallel multi-model review was NOT added to `/tp` (it's sequential by design —
framing challenges need accumulated context). `/review` already has parallel
specialists (Step 4, minimum 2 for standard depth).

## What this means for our workspace

- **For `/tp` reviewing an implementation:** always include the git diff in
  the context bundle. One well-fed agent beats two starving agents.
- **For `/review` specialist prompts:** always inline the diff + related code.
  The specialists already run in parallel; giving them richer context makes
  each one faster and more thorough.
- **The "narrow scope" anti-pattern is wrong:** telling a subagent to "narrow
  scope" when it needs more investigation means it stops looking at things it
  should look at. The fix is a richer bundle, not a narrower scope.
- **Parallel belongs in `/review` (defect hunting), not `/tp` (framing challenge).**

## Falsifier

This concept is wrong if single-agent review with diff-in-bundle is
consistently slower or less thorough than parallel multi-agent review for the
same diff. Test: run the same diff through both `/tp` (single, diff-in-bundle)
and `/review` (parallel, diff-in-bundle) and compare finding count + wall-clock
time across 5+ runs.

## Receipts

- **BugBot 8-pass ensemble + 70% resolution:** Zylos Research, Mar 2026
- **Multi-Review +43% F1, n=5-10:** arXiv 2509.01494, Sept 2025
- **"Single agent faster for accumulated-context tasks":** Shawn Mayzes, Jul 2026
- **Codex benchmark (4 min native vs 36 min router):** Shekhe, May 2026

## Related

- [[delegation-optimization-chunking-output-backend-discipline]] — when to delegate vs do inline; this adds the review-specific context-feeding pattern
- [[parallel-subagent-wait-all-gate]] — parallel dispatch mechanics; this adds when parallel helps review vs when it doesn't
- [[adversarial-multi-agent-code-review]] — multi-agent review architecture; this adds the speed/quality tradeoff data

## Sources

- [Multi-Model AI Code Review: Convergence Loops](https://zylos.ai/zh/research/2026-03-01-multi-model-ai-code-review-convergence/) (Zylos Research, Mar 2026) — 5 architectural patterns, convergence behavior, false positive crisis
- [Claude Code Subagents: When to Split Work](https://www.shawnmayzes.com/ai-engineering/claude-code-subagents-when-to-split-work/) (Shawn Mayzes, Jul 2026) — single vs parallel decision framework
- [Codex vs Native Subagents Benchmark](https://medium.com/@danat.shekhe/codex-vs-native-subagents-vs-subagent-router-5a4e03d64c2c) (Shekhe, May 2026) — speed/quality tradeoff data
- [Parallel Coding Agents: Code Review Guardrails](https://www.propelcode.ai/blog/parallel-coding-agents-code-review-branch-chaos) (Propel, 2026) — branch budgets, risk routing for parallel output
