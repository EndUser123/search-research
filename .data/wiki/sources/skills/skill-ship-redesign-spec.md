# /skill-ship Redesign Spec

This redesign turns `/skill-ship` from a phase coordinator into a policy-driven meta-orchestrator that optimizes **skills**, **orchestrators**, and **outcomes** rather than merely enforcing workflow order.[cite:152][cite:119][cite:122]

## Goals

The current bundle shows that `/skill-ship` already enforces phase gates, freshness, and dynamic built-in discovery, but it does not yet select the best validation strategy for the specific risk and artifact type.[cite:152] The redesign goal is to make `/skill-ship` choose the right evaluators, depth, and adversarial checks based on expected blast radius, architecture impact, and long-term maintainability.[cite:152][cite:119][cite:122]

### Primary objectives

- Improve **solution quality**, not just implementation quality, by evaluating whether a generated skill or orchestrator solves the right problem and remains adaptable over time.[cite:152]
- Reuse existing ecosystem strengths: `/sqa` for layered implementation checks, `/arch` for architecture fit, `/rca` for adversarial falsification and evidence calibration, and `/sdlc` for contract primitives.[cite:152]
- Add measurable outcome scoring so “optimization” means better fit, adaptability, composability, context efficiency, observability, and failure tolerance rather than vague polish.[cite:152][cite:119][cite:122]

## Current-state diagnosis

The bundle describes `/skill-ship` as a 6-phase workflow with Context, Discovery, Knowledge Retrieval, Creation, Validation, Optimization, and Distribution, plus more detailed subphases such as 3a, 3b, 3c, and 3.5.[cite:152] It also shows that validation currently centers on spec conformance, YAML/triggers/context-bloat quality checks, and integration testing, which are necessary but insufficient for solution-quality assurance.[cite:152]

### What is working

- Phase-gate enforcement exists and should remain a core invariant.[cite:152]
- Subagent freshness is already treated as important, which is compatible with adversarial evaluator patterns.[cite:152]
- Dynamic built-in discovery via `builtins.json` already proves the system can externalize changeable assumptions instead of hard-coding them.[cite:152]

### Main gaps

| Gap | Why it matters | Evidence |
|---|---|---|
| No explicit solution-quality gate | A skill can pass spec and integration checks while still solving the wrong problem or creating future rigidity. | [cite:152] |
| Validation depth appears mostly static | High-risk orchestrators should receive deeper or adversarial review than low-risk prompt-only skills. | [cite:152] |
| No explicit policy engine | `/skill-ship` coordinates phases but does not clearly select the best strategy among `/sqa`, `/arch`, `/rca`, and `/sdlc`. | [cite:152] |
| No durable outcome rubric | Without scoring, “optimization” is subjective and hard to regress-test. | [cite:119][cite:122] |
| No clear evaluator/judge separation | Strong agent systems separate generation from critique and judgment to reduce self-grading bias. | [cite:119][cite:122] |

## Target architecture

The redesigned `/skill-ship` should act as a **policy router** and **evaluator-of-evaluators**. Instead of applying one mostly fixed workflow to every request, it should classify the request, predict risk, choose the minimum sufficient review depth, and escalate to adversarial review when warranted.[cite:152][cite:119][cite:122]

### Recommended role model

| Role | Purpose | Main outputs |
|---|---|---|
| Planner | Classify request type, artifact type, blast radius, and desired outcome. | Routing decision, review depth, required gates |
| Solution architect | Propose how to improve or build the target skill/orchestrator using existing primitives. | Design plan, reused components, assumptions register |
| Adversarial evaluator | Attack the proposal for rigidity, hidden assumptions, coupling, context blowup, and failure modes. | Blocking issues, risk register, counterexamples |
| Judge | Score proposal and decide pass / conditional pass / fail. | Rubric scores, final decision, required follow-ups |

This design follows the pattern used in robust agent evaluation systems: separate generation, critique, and judgment, then score structured outputs instead of trusting raw prose.[cite:119][cite:122]

## New workflow

The current flow should be expanded so that strategy selection and solution quality are assessed *before* implementation and *before* distribution.[cite:152]

### Proposed phases

| Phase | Name | Purpose | Blocking? |
|---|---|---|---|
| 0 | Context | Gather recent turns, workflow state, target scope, and existing artifacts. | Yes |
| 1 | Discovery | Classify request: create, refactor, optimize, repair, or distribute. | Yes |
| 1.5 | Knowledge retrieval | Gather patterns from existing skills, packages, docs, hooks, and prior evidence. | Yes |
| 1.6 | Solution framing | Define problem fit, desired outcomes, quality attributes, blast radius, and assumptions. | Yes |
| 1.7 | Policy routing | Choose review depth and which validators must be invoked. | Yes |
| 2 | Creation / change design | Produce the new or revised skill/orchestrator. | Yes |
| 3a | Spec validation | Compare implementation against the approved plan. | Yes |
| 3b | Quality validation | Check YAML, triggers, context bloat, ergonomics, and obvious implementation debt. | Yes |
| 3c | Integration validation | Validate invocation and ecosystem fit. | Conditional |
| 3.4 | Architecture / outcome gate | Evaluate solution quality, adaptability, and long-term risk. | Yes for medium/high risk |
| 3.5 | Adversarial review | Run falsification and targeted stress checks. | Yes for high risk |
| 4 | Optimization | Improve only after scoring and adversarial findings are available. | Conditional |
| 5 | Distribution | Publish only if gates pass and assumptions are externalized. | Yes |

### Why these new phases matter

The additional `1.6`, `1.7`, `3.4`, and `3.5` phases explicitly add solution-quality review and risk-based routing, which are missing from the current bundle description.[cite:152] This aligns with broader best practice in architecture validation and agent evaluation, where quality attributes, explicit criteria, and independent judgment improve outcome quality.[cite:83][cite:119][cite:122]

## Routing matrix

`/skill-ship` should stop applying the same validator stack to every request. The routing decision should depend on artifact type and blast radius.[cite:152]

| Request / artifact type | Risk level | Required validators | Notes |
|---|---|---|---|
| Prompt-only skill tweak | Low | 3a, 3b-light | Skip adversarial unless routing logic changes. |
| New skill with triggers | Medium | 3a, 3b, 3c, 3.4 | Add assumptions register and fallback checks. |
| Orchestrator / dispatcher | High | 3a, 3b, 3c, 3.4, 3.5 | Must include architecture and adversarial review. |
| Dynamic config / built-in discovery / hooks | High | 3a, 3b, 3c, 3.4, stale-data checks, fallback checks | Prevent hidden runtime coupling. |
| Contract or primitive changes | High | `/sqa` full, `/arch`, `/rca`, `/sdlc` contract checks | Highest blast radius. |
| Distribution-only update | Low/Medium | 3c, release checks | No deep revalidation unless behavior changed. |

## Evaluator roles and lenses

The evaluator layer should be multi-lens rather than generic. Each lens should have explicit focus so the system avoids bland, low-signal review.[cite:119][cite:122]

### Recommended evaluator lenses

- **Problem-fit lens**: Does this solve the actual user/system problem or only improve local implementation details?[cite:152]
- **Adaptability lens**: Are there hard-coded thresholds, fixed lists, path assumptions, tool-name assumptions, or rigid routing logic?[cite:152]
- **Architecture lens**: Does the design increase coupling, duplicate existing skill responsibilities, or bypass contract primitives?[cite:152]
- **Failure-mode lens**: How does the artifact fail when built-ins change, configs are missing, paths differ, or context is incomplete?[cite:152]
- **Evidence lens**: Are claims supported by observed files/configs/tests or are they speculative?[cite:152]
- **Context-efficiency lens**: Is the token footprint justified, or is the design bloated relative to value delivered?[cite:152]

## Outcome rubric

Every candidate output should receive explicit scores. This creates a basis for pass/fail and later regression testing.[cite:119][cite:122]

| Dimension | Description | Gate rule |
|---|---|---|
| Problem fit | Solves the right problem and respects user intent. | <3 = fail |
| Adaptability | Avoids hard-coded assumptions and tolerates ecosystem change. | <3 = fail |
| Composability | Reuses `/sqa`, `/arch`, `/rca`, `/sdlc` instead of cloning logic. | <3 = conditional fail |
| Context efficiency | Uses minimal context for the required quality level. | <3 = revise |
| Observability | Emits enough state/evidence to debug failures later. | <3 = revise |
| Failure tolerance | Degrades safely and exposes fallback behavior. | <3 = fail |
| Six-month maintainability | Future changes are understandable and low-risk. | <3 = fail |

### Decision policy

- Any **critical adversarial finding** blocks distribution.[cite:152]
- Any score below 3 in Problem fit, Adaptability, or Failure tolerance is an automatic fail.[cite:119][cite:122]
- Mean score below 4 for orchestrators requires revision before distribution.[cite:119][cite:122]

## Assumptions register

Every generated or modified skill/orchestrator should emit an assumptions register as part of its artifact metadata. This is one of the highest-leverage changes because it makes hidden rigidity visible.[cite:152]

### Required fields

- Expected repo topology
- Expected tool availability
- Config sources and precedence
- Built-in agent assumptions
- Path assumptions
- Fallback behavior when discovery fails
- Freshness assumptions about docs/config/runtime state
- Known non-goals

## File and module changes

The bundle identifies the most relevant `/skill-ship` files: `SKILL.md`, `references/workflow-phases.md`, `references/agent-tool-usage.md`, `validators/context_size.py`, tests, examples, and config files such as `builtins.json`.[cite:152] The redesign should focus there first.

### Recommended edits

| File / module | Change |
|---|---|
| `SKILL.md` | Add mission shift: from phase coordinator to policy-driven optimizer; define new phases 1.6, 1.7, 3.4, 3.5. |
| `references/workflow-phases.md` | Document new gates, routing matrix, decision policy, and required outputs per phase. |
| `references/agent-tool-usage.md` | Define evaluator roles, lenses, and when to invoke `/sqa`, `/arch`, `/rca`, and `/sdlc`. |
| `validators/context_size.py` | Extend from simple line thresholds to risk-aware context budgeting recommendations. |
| `config/` | Add `routing-policy.json`, `risk-matrix.json`, and `rubric.json` so policy is configurable rather than embedded in prompts. |
| `tests/` | Add routing tests, rubric tests, adversarial regression tests, and “wrong-strategy” prevention tests. |
| `examples/WORKFLOW-EXAMPLES.md` | Include examples for low-risk prompt tweak, high-risk orchestrator, and contract-primitive change. |

## Suggested config structures

Configuration should be externalized instead of hidden in prose so the orchestrator can evolve without code edits.[cite:152]

### `routing-policy.json`

```json
{
  "artifact_types": {
    "prompt_skill": ["3a", "3b_light"],
    "new_skill": ["3a", "3b", "3c", "3.4"],
    "orchestrator": ["3a", "3b", "3c", "3.4", "3.5"],
    "contract_change": ["sqa_full", "arch", "rca", "sdlc_contracts"]
  }
}
```

### `rubric.json`

```json
{
  "dimensions": [
    "problem_fit",
    "adaptability",
    "composability",
    "context_efficiency",
    "observability",
    "failure_tolerance",
    "maintainability_6m"
  ],
  "fail_if_below": {
    "problem_fit": 3,
    "adaptability": 3,
    "failure_tolerance": 3
  },
  "orchestrator_min_average": 4
}
```

## Test strategy

A redesign like this needs tests that verify policy choices, not just syntax or file generation.[cite:119][cite:122]

### Must-have tests

- **Routing tests**: Given artifact type and risk, does `/skill-ship` invoke the correct validators?[cite:152]
- **Adversarial regression tests**: Known rigid or over-coupled designs should be rejected consistently.[cite:119][cite:122]
- **Assumptions-register tests**: Fail if hidden assumptions are not emitted.[cite:152]
- **Rubric tests**: Fail if mandatory dimensions are missing or scores violate policy.[cite:119][cite:122]
- **Composition tests**: Fail when logic that belongs in `/sqa`, `/arch`, `/rca`, or `/sdlc` is duplicated instead of delegated.[cite:152]

## Best-practice prompt templates

### Planner prompt

```text
Classify this request by artifact type, blast radius, and outcome goal.
Choose the minimum sufficient validation depth.
Output:
- artifact_type
- risk_level
- required_validators
- required_gates
- assumptions_to_test
```

### Adversarial evaluator prompt

```text
Attack this proposed skill/orchestrator.
Find rigidity, hard-coded assumptions, context blowup, duplicated responsibilities,
and failure modes under missing config, changed built-ins, altered repo layout,
or stale discovery.
Output only evidence-backed findings.
```

### Judge prompt

```text
Score this proposal on:
problem_fit, adaptability, composability, context_efficiency,
observability, failure_tolerance, maintainability_6m.
Return pass / conditional_pass / fail.
Block if any critical finding exists or required dimensions score below threshold.
```

## Migration plan

A staged rollout reduces disruption and makes it easier to validate improvements empirically.[cite:119][cite:122]

### Phase 1: Policy layer

- Add routing policy and rubric config files.
- Update `SKILL.md` and workflow references.
- Keep old validation behavior as fallback.

### Phase 2: New gates

- Implement 1.6 Solution framing and 1.7 Policy routing.
- Implement 3.4 Architecture/outcome gate.
- Run in shadow mode first to compare decisions against current behavior.

### Phase 3: Adversarial mode

- Introduce 3.5 adversarial review for high-risk artifacts.
- Add regression tests for known failures.
- Track false-positive and false-negative rates over several runs.[cite:119][cite:122]

### Phase 4: Tighten distribution gate

- Require rubric scores and assumptions register before distribution.
- Make pass/fail criteria enforceable rather than advisory.

## Immediate next steps

1. Add the new phases and routing matrix to `SKILL.md` and `workflow-phases.md`.[cite:152]
2. Externalize routing and rubric rules into JSON config files.[cite:152]
3. Promote `/arch` and `/rca` to required validators for orchestrators and contract-adjacent changes.[cite:152]
4. Add an assumptions register to every generated artifact.[cite:152]
5. Build regression tests around wrong-strategy selection and missed rigidity findings.[cite:119][cite:122]

## Bottom line

The most important change is to stop treating optimization as late-stage polish. In the redesigned system, optimization begins with **solution framing**, continues through **policy-based validator selection**, and ends with **independent judgment against a durable rubric**.[cite:152][cite:119][cite:122]
