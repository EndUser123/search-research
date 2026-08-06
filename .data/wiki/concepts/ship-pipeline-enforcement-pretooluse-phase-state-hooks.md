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

**Build a PreToolUse phase-state hook that enhances the existing ship skills
(ship-rhai and ship-py).** The hook is ship-variant-agnostic — it reads
whichever phase-state file the active ship skill writes, and blocks `git push`
when the pipeline hasn't reached merge-ready.

The field has converged on PreToolUse hooks that read a phase-state file
and block git operations when prior pipeline phases haven't completed. This
adds a proactive enforcement layer to the ship skills without replacing them.

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
| Platform constraint | ✅ Works (PreToolUse fires, exit 2 blocks) | ⚠️ Known gap: Python can't call spawn_subagent; LLM controls continuation | ✅ Works (Rhai workflow controls phases) |
| Proven by field | ✅ 10 projects, saytooy_arch 18→0 | ❌ No practitioner evidence | ❌ No practitioner evidence |
| Adds proactive enforcement | ✅ Blocks push before it happens | ❌ Post-hoc only | ⚠️ Workflow controls phases but doesn't gate push |
| Composes with existing | ✅ Enhances both ship skills | ❌ Separate pipeline | ❌ Separate pipeline |

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

Both ship skills remain active and under development. The PreToolUse
phase-state hook is an **additive enforcement layer** — it does not replace
either skill. Both ship skills write their phase state to variant-specific
files (`ship-phase-rhai.json` / `ship-phase-py.json`) in a session-scoped
directory. The hook reads whichever file exists.

- **ship-py**: remains active. Known gap (LLM controls inter-phase
  continuation — see [[ship-py-phase-fragmentation-llm-controlled-continuation]])
  is addressed by the hook blocking push until the pipeline completes
  mechanically, regardless of whether the LLM tried to skip ahead.
- **ship-rhai**: remains active. The Rhai workflow provides deterministic
  phase ordering; the hook adds push-gating on top.

The `/ship` entry point may eventually unify these, but both skills are
being actively tested and improved — not retired.

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
