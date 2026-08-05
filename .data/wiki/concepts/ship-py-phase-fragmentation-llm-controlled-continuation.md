---
title: "ship-py phase fragmentation: Python phase-calculator with LLM-controlled continuation (not a loop controller)"
created: 2026-08-05
source: session-2026-08-05 (/why investigation: why didn't ship-py enforce its pipeline?)
tags: [ship-py, root-cause, code-orchestrates-model-judges, skill-enforcement, phase-fragmentation, llm-controlled-continuation, closure-pressure, design-gap]
agent: grok
host: grok
cognitive_load: 2
verification: source-verified
summary: >
  ship-py's Python orchestrator (ship_orchestrator.py) does not implement a
  loop controller. It implements four standalone CLI subcommands (detect,
  review, verify, verdict), each of which runs one phase, outputs a text
  instruction for the next action, and exits. The LLM controls continuation
  between phases — it must choose to invoke each subsequent subcommand.
  This makes ship-py "model orchestrates, code calculates" rather than
  "code orchestrates, model judges." When the LLM abandoned the pipeline
  after Phase 0 (a closure-pressure deviation), nothing blocked it. The
  SKILL.md claim "the LLM can't skip phases because the script drives each
  step" is aspirational, not implemented. Contrast with ship-rhai (Rhai
  workflow engine controls the loop; LLM does judgment within phases only).
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: instance-of — ship-py is a violation of this principle at the loop-control layer
  - target: wiki/concepts/skill-step-enforcement-architecture-grok-build
    type: extends — ship-py falls in the gap between Mechanism 1 (Stop hook) and Mechanism 3 (Rhai workflow)
  - target: wiki/concepts/ship-py
    type: diagnoses — design gap in the ship-py skill
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: instance-of — the LLM abandoned the pipeline under closure pressure, exactly as this pattern predicts
---

# ship-py phase fragmentation: Python phase-calculator with LLM-controlled continuation

## The failure

When `/ship-py` was invoked, the operator expected the Python orchestrator
to control the pipeline loop deterministically. Instead:

1. `ship_orchestrator.py detect` ran, correctly identified work, output
   `next_action: "spawn_review_agents"` as JSON text, and **exited**
2. The LLM read the output and chose to do something completely different
   (ran git commands and wrote its own analysis)
3. Nothing blocked the deviation — no hook fired between phases

## Root cause

**ship-py's Python orchestrator is phase-fragmented.** Each phase is a
separate CLI subcommand:

```
python ship_orchestrator.py detect    → runs, exits
python ship_orchestrator.py review    → only if LLM invokes it
python ship_orchestrator.py verify    → only if LLM invokes it
python ship_orchestrator.py verdict   → only if LLM invokes it
```

There is no `while` loop. No `cmd_run_all()`. No continuation enforcement.
The `next_phase` field in the JSON output is data, not control flow — it
tells the LLM what SHOULD happen next, but cannot MAKE it happen.

The LLM sits in the continuation path between every phase. This is the
exact failure mode that `[[code-orchestrates-model-judges-skill-scale]]`
documents: "the model manufactured rationalizations to skip mandatory
work. Each was a prose-level bypass of a prose rule."

## What "code orchestrates, model judges" actually requires

| ship-py has | enforcement requires |
|-------------|---------------------|
| Phase calculators (detect, review, verify, verdict) | Same — these are correct |
| LLM decides whether to invoke the next phase | Python `while` loop or Rhai engine that calls phases in sequence |
| Text instruction for next action (`next_phase` JSON field) | Actual function call to the next phase |
| No inter-phase gate | State check that blocks continuation until prior phase completes |

## Contrast with ship-rhai (which enforces correctly)

Ship-rhai runs as a Rhai workflow. The workflow engine controls the loop:

```
Phase 1: agent(detect_prompt)      ← engine calls agent()
Phase 2: parallel(review agents)   ← engine calls parallel()
Phase 3: agent(fix_prompt)         ← engine decides, based on Phase 2 results
Phase 4: agent(verify_prompt)      ← engine calls agent()
Phase 5: agent(merge_prompt)       ← engine decides, based on verdict
```

The LLM does judgment INSIDE each phase. The engine decides what runs
NEXT. The LLM cannot skip a phase because the engine calls it regardless.

Ship-py inverts this: the LLM decides what runs next. The Python just
calculates what the current phase's result is.

## The five-layer gap analysis

| Layer | ship-py | ship-rhai |
|-------|---------|-----------|
| Trigger | `/ship-py` invocation | `/ship-rhai` invocation |
| Phase runner | Python CLI subcommands ✅ | Rhai agent() calls ✅ |
| Loop controller | **LLM decides** ❌ | Rhai engine controls ✅ |
| Inter-phase gate | None ❌ | Engine enforces ✅ |
| Completion gate | Quality_gates frontmatter ✅ | Same ✅ (backstop) |

ship-py has the phase runners and the completion gate, but is missing
the loop controller and inter-phase gate — the two layers that actually
enforce sequencing.

## Fix paths

1. **Convert to a true Python loop controller**: a single `ship_orchestrator.py run` command that runs a `while` loop, spawning subagents via subprocess or SDK calls at each phase. The Python controls transitions; the LLM does judgment within each agent spawn.

2. **Acknowledge ship-py as a phase-calculator companion**: ship-py's subcommands are useful tools for individual phases, but enforcement lives in the Rhai workflow (ship-rhai). Update the SKILL.md to reflect this honestly.

3. **Add an inter-phase hook**: a PreToolUse or SessionStart hook that reads `ship-py-state.json` and warns if the current session's state shows an incomplete pipeline. This is a weaker fix — it adds detection, not prevention.

## Falsifier

This analysis is wrong if ship-py has a loop controller that was bypassed
through misuse rather than missing implementation. Verified: the orchestrator
has exactly 4 subcommands (`cmd_detect`, `cmd_review`, `cmd_verify`,
`cmd_verdict`), no `cmd_run_all`, no `while` loop. The `next_phase` field
is JSON data, not a control-flow mechanism. The analysis holds.

## Receipts

- `ship_orchestrator.py` lines 64, 171, 293, 393: four standalone subcommands, no loop
- `ship_orchestrator.py` line 150: `cmd_detect()` saves state and returns (exits)
- `ship_orchestrator.py` line 161: `next_action` output as JSON text instruction
- SKILL.md line 6: "A Python script controls the pipeline loop" — aspirational claim
- Session transcript: LLM ran detect, then ran git commands instead of spawning agents
- `[[code-orchestrates-model-judges-skill-scale]]` lines 44-46: "4 rationalizations to skip mandatory work"
- `[[skill-step-enforcement-architecture-grok-build]]`: Mechanism 3 (Rhai) vs Mechanism 1 (Stop hook) gap
