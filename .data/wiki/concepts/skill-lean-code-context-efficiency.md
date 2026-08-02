---
title: "Skill leanness: every SKILL.md line costs context budget on every invocation"
created: 2026-08-02
source: session-019fc303
tags: [skill-design, context-budget, token-efficiency, leanness, skill-lifecycle, decision]
summary: >
  SKILL.md files are loaded into context on every invocation. Every line competes
  with the task at hand for context budget. Skill bloat — in-file changelogs,
  provenance that devolves into version history, over-explanation of concepts the
  model already knows, additive narration steps over script output — degrades fleet
  performance even when the skill fires correctly. The principle: SKILL.md should
  contain only current procedure and design rationale that drives action. History
  lives in git.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/code-output-passthrough-narration-over-script-output.md
    type: complements
  - target: wiki/concepts/capability-node-architecture.md
    type: related
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: extends
---

# Skill leanness: every SKILL.md line costs context budget on every invocation

## Decision context

**Why this was needed:** during a `/skill-dev` session (2026-08-02), the operator observed that `/skill-dev` should check whether its target skill is lean and efficient. The immediate trigger was discovering that `/skill-dev`'s own Provenance section had grown to 20 lines of version-by-version changelog entries (v1.0, v1.2, v1.3, v1.4) — each repeating what was added in that version. This is pure history: it doesn't drive any action when the skill fires, and it consumes context tokens on every invocation. The same session had just established the AGENTS.md rule banning in-file changelogs; this concept generalizes that rule to all forms of skill bloat.

## The principle

SKILL.md files are not documentation — they are **operational procedure loaded into the LLM's context window on every invocation**. Every line has a cost:

1. **Token cost** — the line consumes context budget that competes with the task's own context (file contents, tool outputs, conversation history).
2. **Attention cost** — the LLM reads every line; irrelevant content dilutes the signal from the procedural instructions that actually matter.
3. **Maintenance cost** — bloat accumulates over time as skills are edited; each edit adds without removing, producing skills that are 2-3x longer than necessary.

## The 4 categories of bloat

| Category | What it looks like | Why it's bloat | Where it belongs |
|---|---|---|---|
| **In-file changelog** | `## Changelog` section with "v1.2: added X, v1.3: changed Y" | The LLM doesn't need to know what changed between versions — it needs to know what to do now | Git commit messages |
| **Redundant provenance** | Provenance sections that list version history instead of design rationale | Design rationale = *why* decisions were made (instructional). Version history = *what lines changed* (git's job). When provenance devolves into "v1.0 did X, v1.2 fixed Y, v1.3 added Z," it's a changelog in disguise | Git log; trim provenance to design decisions only |
| **Additive narration steps** | Procedural steps that tell the LLM to "read the output" and "summarize" or "alert on" what a script already produced | The LLM narrates over the script output instead of passing it through, adding latency and introducing hallucination risk | Replace with passthrough: "Present the script output as your response" (see [[code-output-passthrough-narration-over-script-output]]) |
| **Over-explanation** | Sections explaining concepts the model already knows, or re-explaining what AGENTS.md already establishes | If AGENTS.md has a rule, the skill can reference it in one line — it doesn't need to re-explain the rule | One-line reference to AGENTS.md section |

## How to detect bloat

The test for each section: **"does this drive action or decision when the skill fires?"**

- "No, it's history" → bloat (move to git)
- "No, the model already knows this" → bloat (remove)
- "No, the script already handles it" → bloat (remove the narration step)
- "No, AGENTS.md already covers it" → bloat (replace with one-line reference)

Line-count baselines for calibration:

| Skill complexity | Expected range | >Upper bound |
|---|---|---|
| Simple single-purpose | 50-150 lines | Almost certainly bloated |
| Multi-step procedural | 150-400 lines | Review for trim opportunities |
| Complex multi-mode | 400-700 lines | Borderline; justify each section |
| Any | >700 lines | Almost always bloated |

## What this means for our workspace

- **`/skill-dev` Step 1.5 Check 6** now scans for all 4 bloat categories as part of the static defect scan. A skill with bloat gets an advisory finding (not blocking like a broken path, but it feeds into the Improve recommendation).
- **AGENTS.md §"Skill changelogs (external, not in-file)"** bans in-file changelogs prospectively.
- **Self-application:** `/skill-dev`'s own Provenance section was trimmed from 20 lines of version history to 7 lines of design rationale in the same session that established this principle. Skills should lead by example.
- **Provenance sections stay** when they document *why* design decisions were made — that's instructional context that helps the next reader understand the skill's architecture. They become bloat when they devolve into *what changed in which version*. See [[skill-host-applicability-convention]] for an example of provenance that stays instructional (the host-tagging rationale) versus version history that should be trimmed.
- **Connection to [[agentic-sdlc-skill-lifecycle-architecture]]** — leanness is part of the MAINTAIN stage in the skill lifecycle. A skill that accumulates bloat over time enters lifecycle debt even if its logic is correct. [[skill-management-in-agentic-systems-research-survey]] covers the SLIM pattern that motivates periodic lifecycle review.

## Falsifier

This principle is wrong if:
- **Bloat doesn't actually impact performance** — if skills with 200 extra lines of changelog/provenance fire just as effectively as trimmed versions, the token/attention cost is theoretical, not real. Test: compare a bloated skill's firing quality against the trimmed version on the same task.
- **The LLM actually uses provenance context** — if sessions that load the full provenance make better decisions about the skill than sessions that load the trimmed version, the provenance is instructional, not bloat. The test: does the LLM ever reference the v1.2 red-team hardening when deciding how to use the skill? If not, it's noise.
- **Line-count thresholds are miscalibrated** — if well-functioning skills routinely exceed the thresholds without quality degradation, the thresholds need adjustment. Re-calibrate after measuring 10+ skills.

## Auto-related

- [[multi-model-ai-workflow-patterns]]
- [[context-management-in-claude-code]]
- [[grok-build-workflows-rhai-orchestration]]
- [[user-modeling-for-agentic-clis]]
- [[opentelemetry-structured-logging-patterns]]

