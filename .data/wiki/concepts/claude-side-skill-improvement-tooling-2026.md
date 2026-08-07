---
title: "Claude-side skill improvement tooling: what /skill-dev is missing vs Anthropic skill-creator"
created: 2026-08-06
source: session-019fd9ae (/www research on Claude-side skill improvement tooling)
sources:
  - external: https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
    title: "Anthropic skill-creator (official skill for creating, improving, and evaluating skills)"
    quality: 10
    primary_source: false
  - external: https://agentskills.io/skill-creation/evaluating-skills
    title: "Evaluating skill output quality — agentskills.io"
    quality: 9
    primary_source: true
  - external: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
    title: "Skill authoring best practices — Claude Platform Docs"
    quality: 10
    primary_source: true
  - external: https://azukiazusa.dev/en/blog/skill-create-skill-creation-and-improvement
    title: "Creating and Improving Skills with the Skill Create Skill"
    quality: 8
    primary_source: true
  - external: https://tessl.io/blog/anthropic-brings-evals-to-skill-creator-heres-why-thats-a-big-deal
    title: "Anthropic brings evals to skill-creator — tessl.io"
    quality: 7
    primary_source: false
tags: [skill-dev, skill-creator, eval-driven-development, skill-evaluation, quantitative-metrics, description-optimization, anthropic, agentskills, gap-analysis]
host: grok
agent: grok
verification: multi-source-verified
cognitive_load: 3
relations:
  - target: wiki/concepts/skill-management-in-agentic-systems-research-survey.md
    type: extends — adds Anthropic's official tooling to the research survey
  - target: wiki/concepts/skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency.md
    type: refines — the quantitative measurement gap is now backed by Anthropic's eval framework
summary: >
  Anthropic's skill-creator (v2, March 2026) implements eval-driven skill
  improvement with quantitative metrics that our /skill-dev lacks entirely.
  Key gaps: (1) eval-driven iteration (test cases → run → grade → benchmark →
  iterate), (2) description optimization loop (should-trigger queries tested
  via actual claude -p invocations), (3) quantitative metrics (pass rate,
  tokens, execution time), (4) A/B comparison (old vs new skill in parallel),
  (5) grader sub-agent (binary pass/fail with evidence). Our /skill-dev does
  retrospective MEC analysis (reasoning about past sessions) but never actually
  tests the skill. The agentskills.io eval format provides a portable standard.
  Recommended: integrate the eval-driven pattern into /skill-dev Mode 2.
---

# Claude-side skill improvement tooling: what /skill-dev is missing

## Decision context

**Why this research was needed:** during a `/skill-dev -dry-run` on ship-py,
the operator pointed out that several skill improvement ideas from the Claude
side were missed. The wiki was not queried for Claude-side skill tooling, and
Anthropic's `skill-creator` — the official tool for creating, improving, and
evaluating skills — had not been compared against our `/skill-dev`.

**What the research changed:** identified 5 concrete capability gaps between
our `/skill-dev` and Anthropic's `skill-creator`, plus 3 authoring best
practices from the Claude Platform docs that our skill checks don't cover.

## The 5 capability gaps

### Gap 1: Eval-driven iteration (the biggest gap)

**Anthropic's skill-creator** implements a full eval-driven improvement loop:

1. Create test cases (`evals/evals.json` with prompts, expected outputs, files)
2. Run each test case with and without the skill (parallel subagents)
3. Grade results: binary pass/fail per assertion, backed by evidence
4. Aggregate benchmarks: pass rate, execution time, token consumption
5. Present HTML report for human review
6. Iterate: propose improvements → re-run → compare

**Our /skill-dev** does retrospective MEC analysis — reasoning about whether
past sessions depended on the skill. It never creates test cases, never runs
the skill against defined scenarios, and never produces quantitative metrics.
Every assessment is `[INFERENCE]`.

**The structural difference:** skill-creator answers "does this skill produce
better outputs than not having it?" with data. /skill-dev answers "did past
sessions use the skill's output?" with reasoning. Both are valuable, but
the eval-driven approach is the field standard for skill improvement.

Source: [agentskills.io/evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills),
[Anthropic skill-creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)

### Gap 2: Description optimization loop

**skill-creator** generates should-trigger and should-not-trigger queries,
then tests whether the description actually triggers the skill using real
`claude -p` invocations. It iterates to find the description that maximizes
triggering accuracy. Cost: ~$5 in API credits.

**Our /skill-dev** has Step 2.7 "trigger accuracy assessment" which uses LLM
judgment (v1) — it generates queries and reasons about whether the description
would match. It never actually tests triggering.

**The gap:** we can reason about triggering accuracy, but skill-creator
measures it. Measurement > reasoning for this metric.

Source: [azukiazusa.dev walkthrough](https://azukiazusa.dev/en/blog/skill-create-skill-creation-and-improvement)

### Gap 3: Quantitative metrics

**skill-creator** tracks per-eval:
- Pass rate (assertions passed / total)
- Execution time (wall-clock seconds)
- Token consumption (total tokens consumed)
- Standard deviation across runs

**Our /skill-dev** has zero quantitative metrics. The MEC score is a label
(High/Medium/Low/Negative), not a measurement. Every claim is `[INFERENCE]`.

### Gap 4: A/B comparison with actual execution

**skill-creator** runs old vs new skill versions in parallel and compares
quantitatively. The `comparator.md` agent does blind comparison — it doesn't
know which output came from which version.

**Our /skill-dev** has "held-out validation" (Mode 2 Step 4) which is
reasoning about whether the improvement would have helped on training
sessions without hurting held-out sessions. No actual execution.

### Gap 5: Grader sub-agent

**skill-creator** has a dedicated `grader.md` agent that:
- Scores each assertion as binary pass/fail
- Requires concrete evidence for every PASS
- Critiques the assertions themselves (trivially satisfied? too hard?)
- Outputs structured `grading.json`

**Our /skill-dev** has no grading step. The MEC analysis is holistic reasoning,
not per-assertion grading.

## The agentskills.io eval format

agentskills.io defines a portable eval file format that standardizes skill
testing:

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "realistic user message",
      "expected_output": "human-readable description of success",
      "files": ["evals/files/input.txt"],
      "assertions": [
        "programmatically verifiable statement",
        "specific and observable check"
      ]
    }
  ]
}
```

Key principles from the format:
- **Start with 2-3 test cases** — don't over-invest before first results
- **Vary the prompts** — different phrasings, formality levels, edge cases
- **Assertions are post-hoc** — add them after seeing first outputs
- **Remove assertions that always pass** — they don't differentiate skill value
- **Study assertions that pass with skill but fail without** — this is where
  the skill adds value

This format is portable: any skill can adopt it without tooling changes.

## Authoring best practices we don't check for

From the Claude Platform docs, 3 patterns our scanner doesn't cover:

### 1. Degrees of freedom framework

The docs classify instructions by fragility:
- **High freedom** (text guidance): multiple valid approaches, context-dependent
- **Medium freedom** (parameterized scripts): preferred pattern, some variation
- **Low freedom** (exact commands): fragile operations, consistency critical

Our scanner doesn't check whether the skill's instructions match the
appropriate freedom level for each task. A skill that gives high-freedom
instructions for a low-freedom task (like database migrations) is a defect.

### 2. "Solve, don't defer" for scripts

The docs say scripts should handle errors explicitly, not defer to Claude:
```python
# Good: handle errors
try:
    with open(path) as f: return f.read()
except FileNotFoundError:
    # Create default instead of failing
    ...
except PermissionError:
    return ""

# Bad: defer to Claude
return open(path).read()  # Just fail and let Claude figure it out
```

Our scanner catches "unguarded file-not-found" (Check 7) but doesn't check
whether error handling actually solves the problem or just re-raises.

### 3. "Build evaluations first" principle

The docs are explicit: "Create evaluations BEFORE writing extensive
documentation. This ensures your Skill solves real problems rather than
documenting imagined ones." Our /skill-dev creates evaluations after the
skill is built — or not at all.

## What this means for /skill-dev

The eval-driven pattern is the biggest missing capability. Adding it would
transform /skill-dev from a reasoning-only tool to a measurement tool.

**Recommended integration path:**
1. **Mode 2.5 (new): eval-driven improvement** — between Mode 2 (propose) and
   operator apply. Creates test cases, runs them, grades results, produces
   benchmark.json. This is the held-out validation Step 4 always wanted to be
   but couldn't because it was reasoning, not execution.
2. **Adopt the agentskills.io eval format** — portable, standardized, already
   documented. Store evals in `<skill-path>/evals/evals.json`.
3. **Description optimization** — port skill-creator's should-trigger query
   pattern into our Step 2.7. Test with actual spawn_subagent, not LLM judgment.
4. **Quantitative metrics** — track pass rate, tokens, execution time. These
   are the measurements that make MEC scores evidence-based, not inference-based.

**Cross-host note:** skill-creator is a Claude Code plugin. On Grok Build,
we'd adapt the pattern using spawn_subagent instead of `claude -p`, and our
own grader subagent instead of grader.md. The eval format and workflow
translate directly.

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| skill-creator has eval-driven iteration | [agentskills.io/evaluating-skills](https://agentskills.io/skill-creation/evaluating-skills) — read in full this session | [OBSERVED] — primary source |
| skill-creator has description optimization loop | [azukiazusa.dev](https://azukiazusa.dev/en/blog/skill-create-skill-creation-and-improvement) — read in full | [OBSERVED] — primary source |
| Our /skill-dev has no quantitative metrics | `skill-dev/SKILL.md` Step 4 — MEC is labeled, not measured | [OBSERVED] — code read this session |
| agentskills.io eval format is portable JSON | [agentskills.io](https://agentskills.io/skill-creation/evaluating-skills) — format documented with examples | [OBSERVED] — primary source |
| Claude best practices say "build evaluations first" | [platform.claude.com best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — read in full | [OBSERVED] — primary source |

## Falsifier

This analysis is wrong if:
- The eval-driven approach doesn't work on Grok Build (spawn_subagent can't
  isolate skill context the way `claude -p` can) — [UNTESTED]
- The quantitative metrics don't correlate with skill quality (pass rate
  doesn't predict real-world value) — [INFERENCE] — needs measurement
- Our retrospective MEC approach produces better assessments than eval-driven
  (possible for skills where firing context matters more than output quality)

## Related concepts

- [[skill-management-in-agentic-systems-research-survey]] — the SLIM/CODESKILL research foundation our /skill-dev is built on
- [[skill-effectiveness-measurement-gaps-trigger-accuracy-token-efficiency]] — documents the trigger-accuracy and token-efficiency measurement gaps
- [[code-orchestrates-model-judges-skill-scale]] — the eval-driven pattern is code orchestrating (test runner) + model judging (grader agent)
- [[mechanical-enforcement-of-llm-skill-steps-2026]] — evals are mechanical enforcement of skill quality, same principle
- [[skill-authoring-patterns-dos-and-donts]] — our existing authoring patterns; the Claude best practices complement these
