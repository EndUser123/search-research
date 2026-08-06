---
title: "Ship pipeline enforcement: how other teams solve the mandatory-step problem (field research 2026-08-06)"
created: 2026-08-06
source: /www research session (wiki → web → wiki)
tags: [ship-pipeline, enforcement, field-research, pretooluse-hooks, workflow-runtime, fsm, acd, code-orchestrates-model-judges, anti-bypass, state-machine]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  How other teams enforce mandatory pipeline phases (review → fix → verify → merge)
  for AI coding agents. Five patterns identified across 10+ sources: (1) workflow
  runtime holds the loop, (2) hook-enforced context isolation + state transitions,
  (3) CI/CD pipeline as the enforcement mechanism, (4) state-machine + dependency
  graph with anti-bypass protection, (5) nonce-proof reads for challenge-response.
  Our PreToolUse phase-state hook is one layer; the field consistently uses multiple
  layers. Key gap: we lack anti-bypass protection (agents can claim compliance)
  and the automated dispatch engine pattern (orchestrator reads state from disk,
  dispatches next phase, updates state — stateless between invocations).
relations:
  - target: wiki/concepts/ship-pipeline-enforcement-pretooluse-phase-state-hooks
    type: extends — adds field validation and the missing layers we don't have
  - target: wiki/concepts/ship-py-phase-fragmentation-llm-controlled-continuation
    type: informs — field confirms the problem is real and universal
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: validates — multiple field implementations confirm the principle
  - target: wiki/concepts/skill-step-enforcement-architecture-grok-build
    type: expands — adds patterns not in the original mechanism analysis
---

# Ship pipeline enforcement: field solutions (2026-08-06)

## The universal problem

Every team running multi-phase AI agent pipelines hits the same wall: agents skip mandatory steps despite clear prose rules. GitHub issue [anthropics/claude-code#49192](https://github.com/anthropics/claude-code/issues/49192) documents the exact pattern we experience:

> "Every agent skips some or all of these steps. When directly asked 'did you read all the files?', the agent said 'yes' — then admitted it hadn't when pressed."

> "CLAUDE.md instructions are supposed to be authoritative. There is no mechanism for users to enforce that instructions were actually followed."

> "Adding more rules to CLAUDE.md doesn't help because **the agent skips CLAUDE.md too.**"

This is not a workspace-specific problem. It is a structural property of LLM agents.

## The five enforcement patterns the field uses

### Pattern 1: Workflow runtime holds the loop

**Source:** [Claude Code official dynamic workflows](https://code.claude.com/docs/en/workflows) (Anthropic, 2026)

The official Anthropic solution is the `workflow` feature: a JavaScript script orchestrates subagents. The **script** holds the loop, branching, and intermediate results. Claude does judgment *inside* each agent spawn.

| Approach | Who decides what runs next | Where state lives |
|----------|--------------------------|-------------------|
| Subagents | Claude, turn by turn | Claude's context |
| Skills | Claude, following the prompt | Claude's context |
| Agent teams | The lead agent, turn by turn | A shared task list |
| **Workflows** | **The script** | **Script variables** |

Key quote: *"A workflow moves the plan into code. With subagents, skills, and agent teams, Claude is the orchestrator. A workflow script holds the loop, the branching, and the intermediate results itself."*

**Grok Build equivalent:** the Rhai workflow tool (`workflow` in the tool surface). This is the direct equivalent of Claude Code's dynamic workflows — the Rhai engine holds the loop, and agents do judgment within each `agent()` call.

**Why this matters for us:** our `/ship-rhai` skill was marked SUPERSEDED, but the workflow *runtime* is the exact mechanism the field recommends for loop control. The Rhai workflow tool is not the problem — the problem was in how ship-rhai used it.

### Pattern 2: Hook-enforced context isolation + state transitions

**Source:** [itsaldrincr/claude-code-fsm-workflow](https://github.com/itsaldrincr/claude-code-fsm-workflow) (GitHub, 23 subagents, 590+ tests, MIT)

The FSM Workflow project replaces persona-based prompting with mechanical enforcement. Key mechanisms:

- **Hook-enforced write authority:** workers physically cannot read `MAP.md` or `CLAUDE.md` (`permissionDecision: deny` from hooks). Only the task-planner can write the state file.
- **Hook-enforced context isolation:** workers receive exactly one input: a task file path. No ambient context, no drift.
- **Nonce-proof reads:** every task file carries a `checkpoint` hex string. Workers must echo the current nonce. Challenge-response, not vibes.
- **State transition validation:** `validate_map_transition.py` blocks invalid state transitions (e.g., PENDING→DONE without passing through IN_PROGRESS→REVIEW→TESTED).
- **Automated dispatch engine:** `orchestrate.py` reads MAP.md state from disk, decides the next action, dispatches the right agent, updates state. **Stateless between invocations — all state lives on disk.**

Key quote: *"Most multi-agent packages give you persona prompts that bias the model's output distribution but do nothing mechanical to stop bad behavior. This package replaces persona with enforcement."*

**Gap in our workspace:** we have a PreToolUse hook that blocks `git push` (`PreToolUse_ship_phase_gate.py`), but we do NOT have:
- Anti-bypass protection (agents can self-mark phases as complete)
- Context isolation enforcement (agents can read anything)
- State transition validation (no `validate_map_transition.py` equivalent)
- Automated dispatch engine (our orchestrator exits after each phase)

### Pattern 3: CI/CD pipeline as the enforcement mechanism

**Source:** [MinimumCD Agentic Continuous Delivery framework](https://beyond.minimumcd.org/docs/agentic-cd/operations/pipeline-enforcement/) (2026)

The MinimumCD framework uses traditional CI/CD stages as enforcement:

| Stage | What it enforces |
|-------|-----------------|
| Pre-commit gates (lint, type check, SAST) | Mechanical errors agents produce most |
| CI Stage 1 (build + unit tests) | Acceptance criteria |
| CD Stage 1 (contract + schema tests) | System constraints at integration boundaries |
| CD Stage 2 (mutation testing, perf benchmarks) | Subtle correctness issues agents introduce |
| Acceptance tests | User-facing behavior in production-like environment |
| Production verification (canary + auto-rollback) | Final safety net |

**Expert validation agents** fill gaps standard tools can't cover:

| Agent | What it validates | Catches |
|-------|------------------|---------|
| Test fidelity agent | Test code exercises the spec's scenarios | Tests that omit edge cases |
| Implementation coupling agent | Tests verify behavior, not internals | Tests that break on refactor |
| Architectural conformance agent | Code follows feature description constraints | Module boundary violations |
| Intent alignment agent | Change addresses the stated problem | Technically correct, wrong problem |

Key adoption principle: *"Do not deploy expert agents and immediately reduce human review. Run expert agents in parallel with human review for at least 20 cycles before any reduction."*

**Gap in our workspace:** we have no CI/CD pipeline enforcement for agent-generated code. The ship pipeline is entirely in-session — there's no external system that gates merges.

### Pattern 4: State-machine + dependency graph with anti-bypass

**Source:** [workflow-enforcement skill](https://claudeskills.club/skills/workflow-enforcement-by-chkim-su) (Claude Skills marketplace)

A protocol-based enforcement system using dependency graphs and state machines:

- **Dependency-ordered validations:** `functional_test` requires both `validate_all` and `form_audit` to pass first. The dependency graph is the enforcement.
- **Anti-bypass protection:** protected validations can only be marked via hooks (`--from-hook` flag). Manual invocation fails:

```bash
# This FAILS (manual bypass attempt)
python3 forge-state.py mark-validation form_selection_audit passed

# This SUCCEEDS (triggered by hook after agent completes)
python3 forge-state.py mark-validation form_selection_audit passed --from-hook
```

- **Exit code policy:** `exit(0)` = ALLOW, `exit(1)` = WARN, `exit(2)` = BLOCK (always blocks in PreToolUse)

**Gap in our workspace:** our phase-state file can be written by any process. There's no `--from-hook` flag mechanism to prevent the LLM from self-marking phases as complete.

### Pattern 5: Paired adversarial wave gate

**Source:** FSM Workflow project (itsaldrincr, same as Pattern 2)

After each wave of agent work, two independent bug-scanners review the batch on deterministic file shards. **Both must APPROVE** to open the gate. REVISE routes flagged tasks to code-fixer (simple) or debugger (complex). Max 3 rounds.

Key design choice: not per-task review (too slow), not skippable (too risky). Batch-level paired review at wave boundaries.

**Gap in our workspace:** our `/review` skill does specialist review, but there's no paired gate where two independent reviewers must both approve before the pipeline advances.

## What the field consensus tells us

### Our PreToolUse hook is necessary but not sufficient

The field consistently uses **multiple layers**, not one:

| Layer | We have | Field standard |
|-------|---------|---------------|
| PreToolUse gate (block git push) | ✅ | ✅ |
| Anti-bypass protection (--from-hook) | ❌ | ✅ (multiple projects) |
| State transition validation | ❌ | ✅ (FSM workflow, enforcement skill) |
| Automated dispatch engine | ❌ | ✅ (FSM orchestrate.py, workflow runtime) |
| Paired adversarial wave gate | ❌ | ✅ (FSM bug-scanner pair) |
| CI/CD pipeline enforcement | ❌ | ✅ (MinimumCD ACD) |
| Context isolation enforcement | ❌ | ✅ (FSM block-worker-reads) |

### The workflow runtime is the loop controller we need

The Claude Code dynamic workflows documentation is explicit: the workflow runtime holds the loop, not Claude. This is the "code orchestrates, model judges" principle implemented at the platform level.

On Grok Build, the Rhai workflow tool is the equivalent. The issue isn't that ship-rhai was wrong to use Rhai — the issue was in how ship-rhai delegated to single agents per phase rather than having the Rhai engine control the full loop with the LLM doing judgment inside each `agent()` call.

### Anti-bypass is the missing enforcement layer

The most novel pattern from the field is **anti-bypass protection**: the LLM cannot self-mark phases as complete. Only hooks (triggered by actual tool execution) can write the "passed" state. This closes the "agent claims it did the work" gap.

Our phase-state file (`ship-phase-py.json`) can be written by any process, including the LLM directly. Adding a `--from-hook` flag or equivalent cryptographic check would close this gap.

## Actionable recommendations for our workspace

1. **Use the Rhai workflow tool as the loop controller.** Not ship-rhai's "one agent per phase" design — a workflow script that controls the full pipeline loop, dispatching agents for judgment work within each phase. The script holds state; agents hold judgment.

2. **Add anti-bypass protection to the phase-state file.** Phase transitions should require a hook-generated token, not just a JSON write. The LLM cannot self-advance the pipeline.

3. **Add a paired review gate.** After the review phase, two independent reviewers (different model families) must both APPROVE before the pipeline advances to verify. Not per-finding — batch-level.

4. **Add state transition validation.** A hook or script that blocks invalid transitions (e.g., skipping review → trying merge). The FSM Workflow's `validate_map_transition.py` is the model.

5. **Consider CI/CD integration.** For agent-generated code that reaches merge, a CI gate (GitHub Actions) that runs the receipt validator provides an enforcement layer that doesn't depend on the LLM at all.

## Falsifier

This analysis is wrong if:
- The Rhai workflow tool on Grok Build cannot control a multi-phase loop the way Claude Code's workflow runtime does (would need live test)
- Anti-bypass protection is impractical on Grok Build (no hook can inject tokens into state writes)
- The operator's actual problem is something else entirely (not pipeline enforcement)

## Sources

- [Claude Code dynamic workflows](https://code.claude.com/docs/en/workflows) — official documentation (Anthropic, 2026)
- [itsaldrincr/claude-code-fsm-workflow](https://github.com/itsaldrincr/claude-code-fsm-workflow) — 23-subagent FSM pipeline with hook enforcement (GitHub, MIT)
- [MinimumCD Agentic CD pipeline enforcement](https://beyond.minimumcd.org/docs/agentic-cd/operations/pipeline-enforcement/) — ACD framework with expert validation agents (2026)
- [workflow-enforcement skill](https://claudeskills.club/skills/workflow-enforcement-by-chkim-su) — dependency graph + anti-bypass (Claude Skills marketplace)
- [anthropics/claude-code#49192](https://github.com/anthropics/claude-code/issues/49192) — universal problem report: agents skip mandatory steps
- [Echofold: autonomous Claude Code guide](https://echofold.ai/news/how-to-automate-claude-code-autonomous-development) — "Hooks are the enforcement mechanism of the entire pipeline"
- [[ship-pipeline-enforcement-pretooluse-phase-state-hooks]] — our existing concept (single layer, confirmed by field but incomplete)
- [[ship-py-phase-fragmentation-llm-controlled-continuation]] — the root cause analysis
- [[code-orchestrates-model-judges-skill-scale]] — the principle, validated by Claude Code's workflow design
