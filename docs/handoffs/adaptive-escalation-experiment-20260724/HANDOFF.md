---
thread_id: adaptive-escalation-experiment-20260724
parent_handoff_path: none
current_session_id: 019f7e24-0513-7773-875d-5a3e3051dc8f
current_terminal_id: console_43ffe471-3979-44b1-8150-480c4cd00797
produced_at: 2026-07-24T02:30:00Z
status: open
handoff_type: future-experiment
---

# Handoff: Adaptive escalation and task-aware context packaging experiment

## Objective

Design and run a bounded experiment to measure whether adaptive model
escalation, task-aware subagent context packaging, and model/subagent quality
scoring produce measurably better outcomes than the current static model-lane
approach in `/go`.

## Why this matters

The `/go` skill currently uses two static model lanes (Reasoning: Nemotron/GLM,
Code: Ornith/Gemini-Flash). The fleet has 7+ providers with different quality,
cost, and latency profiles. There is no measured evidence for when escalation
from free to subscription models produces enough quality improvement to justify
the quota cost. The operator explicitly does not want user-visible nagging,
forced rollover, global caps, or arbitrary fanout limits.

## Scope (bounded experiment only)

- **Adaptive escalation**: measure quality delta when escalating from free
  models (Ornith, DiffusionGemma, Nemotron) to subscription (GLM-5.2, MiniMax-M3)
  on tasks where the free model's output was rated below quality floor
- **Task-aware context packaging**: measure whether injecting context pointers
  (transcript path, compaction segments, search terms, prior artifacts) into
  subagent prompts reduces tool-call count and improves output quality
- **Model/subagent quality scoring**: develop a lightweight scoring rubric
  (verified finding yield, not subjective quality) for comparing model outputs
- **Cost and latency**: track per-task token cost, request count, wall time
- **Stop/kill criteria**: define when to abandon a model lane for a task class

## Out of scope

- Forced session rollover
- Global model/subagent caps
- User-visible nagging or persistent status lines
- Workflow-budget changes without measured evidence
- Generic PM platform

## Current state

- `/go` wave table defines two lanes with pool members (see SKILL.md)
- `merge_files.py` exists at `P:/.agents/scripts/merge_files.py` for request-based
  quota optimization (measured 9x reduction on agy)
- Wiki: `model-fleet-provider-pools.md` has per-5h quotas and provider inventory
- Wiki: `langgraph-vs-wrapper-scripts-skill-enforcement.md` documents the
  decision to use wrapper scripts over state machines
- Red-team overlay at `P:/.grok/skills/red-team/SKILL.md` has cross-model
  specialist dispatch but routing policy is undefined

## Dependencies

- `dispatch_cross_model.py` wrapper script (not yet built — handoff at
  `tp-pool-composition-review-20260723`)
- Quota measurement infrastructure (current: manual `cc-ccr -Test`)

## Success criteria

- Bounded experiment with ≥3 task classes, ≥5 samples per class per lane
- Measured quality delta (verified finding yield, not subjective)
- Cost-per-finding metric established
- Clear recommendation: escalate / don't escalate / per-task-class

## Verification

- Run experiment via `evidence-driven-experiment-loop` skill
- Record results in wiki concept with `sources:` and `created:` frontmatter
- No production changes without measured evidence

## Prohibited assumptions

- Do not assume free models are always insufficient
- Do not assume subscription models are always better
- Do not change `/go` wave table without measured evidence

## Next safe action

1. Define 3 task classes (e.g., code review, implementation, debugging)
2. Create 5 representative tasks per class from prior session transcripts
3. Run each task on free-lane and subscription-lane models
4. Score outputs using verified-finding-yield rubric
5. Report measured quality delta and cost-per-finding
