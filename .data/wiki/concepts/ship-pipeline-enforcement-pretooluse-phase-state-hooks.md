---
title: "Ship pipeline enforcement: PreToolUse phase-state hooks (field consensus architecture)"
created: 2026-08-05
source: session-2026-08-05 (/www research + /why + /tp on ship-py/ship-rhai)
tags: [ship-pipeline, enforcement, pretooluse-hooks, phase-state-machine, code-orchestrates-model-judges, field-consensus, architecture-decision, retire-ship-py, retire-ship-rhai]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  The field has converged on PreToolUse hooks + phase state machine as the
  dominant enforcement pattern for AI agent ship pipelines (review → fix →
  verify → merge). 10 projects studied; the strongest practitioner evidence
  is saytooy_arch (18 incidents with prose-only enforcement → 0 after moving
  to PreToolUse hooks). The architecture: a tiny phase-state file tracks
  which pipeline phase the session is in; a PreToolUse hook reads it on
  every git push/merge call and blocks (exit 2) if prior phases haven't
  completed. This supersedes both ship-py (can't work — Python can't call
  spawn_subagent) and ship-rhai (overengineered — the Rhai engine adds
  unproven operational complexity without adding enforcement value over
  hooks). Decision: retire both, build the PreToolUse phase-state hook.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: applies — hooks are the "code orchestrates" layer at the enforcement scale
  - target: wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation
    type: supersedes — the root cause analysis that motivated this architecture decision
  - target: wiki/concepts/skill-step-enforcement-architecture-grok-build
    type: refines — fills the gap between Mechanism 1 (Stop hook) and Mechanism 3 (Rhai workflow) with the field-validated approach
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: extends — PreToolUse phase-state is the missing enforcement layer
---

# Ship pipeline enforcement: PreToolUse phase-state hooks

## Decision

**Retire ship-py and ship-rhai. Build a PreToolUse phase-state hook.**

The field has converged on a simpler, more reliable architecture than either
Python loop control or Rhai workflow enforcement: PreToolUse hooks that read
a phase-state file and block git operations when prior pipeline phases
haven't completed.

## Evidence from /www research (10 projects studied)

The strongest practitioner evidence is `saytooy_arch` (Zenn, 2026):

> "I organized a multi-agent development team (15+ agents) using Claude Code
> to build a SaaS application. Even though I wrote 'skipping stages is
> prohibited' in quality_process.md, in practice: Implementation began without
> screen design documents. Tests were written without test specifications.
> Deployment was attempted without review records. **18 incidents occurred.**
> Out of the 18 incidents, **zero have recurred** since the introduction of
> the hooks."

Same phases, same team, same model. The only change was moving from prose
rules to PreToolUse hooks that exit 2.

### The pattern across all 10 projects

Every successful implementation uses the same layered architecture:

| Layer | Mechanism | What it catches |
|-------|-----------|----------------|
| PreToolUse hook | Exit 2 on git push/merge when phase state ≠ "merge-ready" | Agent skips review/verify and tries to merge |
| Stop hook | Block completion when evidence artifacts missing | Agent declares "done" without running checks |
| Adversarial review | Fresh-context subagent grades the diff | Writer grades own work (confirmation bias) |
| Mechanical receipt | Gate CLI derives verdict from evidence files | Agent fakes completion claim |

Our workspace already has layers 2-4 (quality_gates Stop hook, /review
skill, ship_receipt.py). We're missing layer 1: the PreToolUse phase-state
hook.

## Why this beats ship-py and ship-rhai

| Criterion | PreToolUse hooks | ship-py | ship-rhai |
|-----------|-----------------|---------|-----------|
| Platform constraint | ✅ Works (PreToolUse fires, exit 2 blocks) | ❌ Python can't call spawn_subagent | ⚠️ Works but unproven |
| Proven by field | ✅ 10 projects, saytooy_arch 18→0 | ❌ No practitioner evidence | ❌ No practitioner evidence |
| Simplicity | ✅ Hook + state file | ❌ 4 subcommands, LLM relay | ❌ Rhai engine + journaling + budget |
| Failure surface | 1 (hook crash = fail-open) | 4 (subcommand exits, LLM deviation, state file, Python errors) | 5+ (subagent silent failure, model slug 404, smoke-check gap, launch staleness, session death) |
| Composes with existing | ✅ quality_gates + ship_receipt.py | ❌ Separate pipeline | ❌ Separate pipeline |

## The architecture

```
Operator types /ship
  → Skill writes phase state: {"phase": "review", "session": "<id>"}
  → Agent runs /review (produces FINDINGS.md)
  → Skill writes phase state: {"phase": "verify", "session": "<id>"}
  → Agent runs /check (produces check-run.json)
  → Agent runs ship_receipt.py (derives SHIP DONE / SHIP BLOCKED)
  → If SHIP DONE: Skill writes phase state: {"phase": "merge-ready", "session": "<id>"}
  → PreToolUse hook allows git push/merge
  → If SHIP BLOCKED: phase state stays at "verify", hook blocks push
```

Enforcement layers:
1. **PreToolUse hook** (`PreToolUse_ship_phase_gate.py`): reads phase state
   file, blocks `git push`/`git merge` unless phase = "merge-ready"
2. **Stop hook** (existing `quality_gates_frontmatter.py`): blocks completion
   when check-run.json or FINDINGS.md missing for invoked ship skills
3. **Mechanical receipt** (existing `ship_receipt.py`): derives verdict from
   evidence, not from LLM self-report

## What ship-py and ship-rhai become

- **ship-py**: retired. The orchestrator subcommands (`detect`, `review`,
  `verify`, `verdict`) are useful as standalone tools but the skill itself
  is marked as superseded. The SKILL.md points to the hook-based approach.
- **ship-rhai**: retired. The Rhai workflow was a design experiment that
  added complexity without proportional enforcement value. The workflow file
  is kept for reference but not the primary path.

The `/ship` skill (prose) becomes the entry point, with hook enforcement
providing the structural backbone.

## Sources

- `saytooy_arch` — "Physically Enforcing AI Agent Process Transitions with
  Hooks" (Zenn, 2026): 18 incidents → 0 with PreToolUse hooks.
  https://zenn.dev/saytooy_arch/articles/04-hook-phase-gate
- `prgazevedo/claude-code-workflows` — Phase state machine + PreToolUse
  hooks + REVIEW-skip protection.
  https://github.com/prgazevedo/claude-code-workflows
- `omeeragtoprak/agentic-engineering-protocol` — 5 phases + Stop hook +
  4 fresh-context adversarial auditors.
  https://github.com/omeeragtoprak/agentic-engineering-protocol
- `ShunsukeHayashi/mergegate` — Engine-agnostic Rust CLI gate.
  https://github.com/ShunsukeHayashi/mergegate
- `ThreeMoonsLab/agents-shipgate` — Static Tool-Use Readiness gate; "gate
  is the product, hooks are the feedback loop, CI is authoritative."
  https://github.com/ThreeMoonsLab/agents-shipgate
- `aws-samples/sample-specship` — 7 parallel adversarial validators with
  self-healing recovery loop (3-cycle cap).
  https://github.com/aws-samples/sample-specship
- `ranjankumar.in` — "Hooks: The Enforcement Layer That Turns Agent Policy
  Into Agent Fact" (Probabilistic-to-Deterministic Boundary).
  https://ranjankumar.in/hooks-policy-as-code-agent-enforcement
- Full research file: `P:/tmp/www-ship-pipeline-enforcement.md`
