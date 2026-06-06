# 14-Model Evaluation Harness Design

**Goal:** Build a repeatable benchmark harness for the 14 configured OpenCode Go models that measures two things separately: architecture/reasoning quality and real coding ability.

**Context:** The `cc-skills-ai-api` plugin already has the transport and orchestration pieces we need:
- `bf_agent.run_domain_benchmark()` can score non-coding reasoning prompts today.
- `bf_agent.run_code()` already drives the tool loop for code tasks.
- Bifrost routing is already configured for the 14 OpenCode Go models.

The missing piece is a benchmark harness that treats reasoning and coding differently instead of collapsing them into one synthetic score.

---

## Problem Statement

We want to compare all 14 models in a way that is actually useful for routing decisions.

The current local benchmark path is good for structured answer quality, but it does not fully answer:

- Which models produce good architecture and rollout decisions under the same constraints?
- Which models can actually make correct code changes, not just describe them?
- Which models are reliable enough to trust as defaults for different task types?

The benchmark should surface those differences without hiding them behind compare-synthesis output.

---

## Recommendation

Use a two-lane harness:

1. `reasoning/architecture` lane
2. `coding` lane

Keep the lanes separate in scoring and reporting. Then publish one combined dashboard that shows the split scores and an overall weighted rank.

This is the recommended approach because it uses the plugin paths that already exist, but adds a real execution oracle for coding.

---

## Approaches Considered

### Option A: Reuse the existing benchmark heuristics only

Run `run_domain_benchmark()` over all models and score text outputs with deterministic term-based heuristics.

Pros:
- Fast to build
- No new execution harness
- Reuses existing plugin code directly

Cons:
- Good for reasoning, weak for coding
- Can reward style over correctness
- Does not prove the model can make a valid patch

### Option B: Two-lane harness with execution-backed coding benchmarks

Use the current benchmark runner for reasoning and add a coding suite that edits isolated fixtures, then runs hidden tests on the result.

Pros:
- Measures actual coding ability
- Reuses existing `bf_agent` transport and code loop
- Separates answer quality from executable correctness

Cons:
- More implementation work
- Needs fixture repos and hidden tests

### Option C: External benchmark integration only

Wrap SWE-bench style datasets or other public suites and drive them through `ai-api`.

Pros:
- Strong external comparability
- Less custom prompt design

Cons:
- More setup overhead
- Harder to keep aligned with the local routing/problem space
- Less useful for the specific models and workflows we actually route here

**Recommendation:** Option B.

---

## Proposed Architecture

### 1. Suite Orchestrator

Add a small benchmark runner that:

- loads a model list
- runs the reasoning lane
- runs the coding lane
- normalizes results into one artifact format
- writes a Markdown summary plus machine-readable JSON

This runner should not use `run_compare()` as the benchmark output. Compare mode is useful for synthesis, but benchmarking needs per-model raw results.

### 2. Reasoning Lane

Use the existing `run_domain_benchmark()` flow, but split the prompt pack into a stable reasoning set with two subdomains:

- `architecture`
- `planning`

That gives us coverage for:

- system boundaries
- failure modes
- rollout sequencing
- rollback planning
- dependency drift
- operational tradeoffs

Each case should:

- ask for a structured answer
- require explicit tradeoffs
- require a concrete recommendation
- penalize vague generic text

Scoring can stay deterministic in v1:

- required terms
- bonus terms
- penalty terms
- structure checks
- spread/robustness across cases

Optionally, a judge pass can be added later for tie-breaks and qualitative notes, but it should never replace the deterministic baseline.

### 3. Coding Lane

Create a small set of isolated coding fixtures that each represent a real patch task:

- bug fix
- behavior change
- small refactor with tests
- path/portability fix
- regression fix

For each coding case:

- copy the fixture repo into a temp workspace
- give the model the same task prompt
- let the model use the `run_code()` tool loop
- run hidden tests against the modified workspace
- score on pass/fail plus patch quality signals

Coding must be execution-backed. If a model writes a persuasive explanation but does not produce a passing patch, it should score low.

### 4. Reporting Layer

Write results to a stable artifact directory under `.data/ai-api/benchmarks/`.

Each run should emit:

- raw per-case outputs
- per-model aggregate scores
- per-lane scores
- transport metadata
- latency metadata
- failure notes
- final ranking

The report should make it easy to answer:

- best model for architecture
- best model for coding
- most consistent model
- fastest acceptable model
- best overall compromise

---

## Data Model

### Benchmark Case

Each case should include:

- `id`
- `lane` (`reasoning` or `coding`)
- `domain` (`architecture`, `planning`, or `code`)
- `prompt`
- `expected_structure`
- `required_terms`
- `bonus_terms`
- `penalty_terms`
- `max_turns`
- `route`
- `tight_contract`
- `fixture_path` for coding cases
- `test_command` for coding cases

### Result Record

Each model/case result should include:

- `model`
- `case_id`
- `lane`
- `domain`
- `ok`
- `score`
- `subscores`
- `text_or_patch_summary`
- `tests_passed` for coding
- `latency_ms`
- `error`

### Aggregate Summary

Each model should get:

- reasoning score
- coding score
- combined score
- score variance
- case count
- failure count
- average latency

---

## Scoring Rules

### Reasoning

Score with a weighted blend of:

- structure compliance
- presence of concrete tradeoffs
- explicit recommendation
- risk/failure analysis
- operational realism
- evidence of constraint handling

### Coding

Score with a weighted blend of:

- hidden tests pass rate
- patch validity
- scope control
- unrelated file churn
- explanation quality only as a tie-breaker

The highest signal should always be test success, not narrative quality.

### Overall

Keep the combined rank separate from the lane ranks:

- `reasoning_rank`
- `coding_rank`
- `overall_rank`

That avoids a single blended score hiding that a model is strong in one lane and weak in the other.

---

## Proposed Files

The implementation should be small and bounded.

### Modify

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\bf_agent.py`
  - add a top-level suite runner or export helpers for the runner
  - keep the existing direct/compare/code paths intact

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\SKILL.md`
  - document the new benchmark entrypoint and result format

### Add

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\benchmark_suite.py`
  - suite definitions, model list loading, result schema, aggregation

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\ai-api\scripts\run_model_eval_suite.py`
  - CLI entrypoint for the full 14-model run

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\test_benchmark_suite.py`
  - unit tests for case loading, scoring, aggregation, and artifact writing

- `P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\tests\fixtures\model_eval\...`
  - isolated coding fixtures and hidden tests

### Optional later cleanup

- Extract the current benchmark case definitions out of `bf_agent.py` if the file grows too large.

---

## Validation Plan

The harness is only useful if it is reproducible.

We should verify:

- the full 14-model list loads correctly
- reasoning cases run end to end
- coding fixtures can be copied into a temp workspace
- hidden tests execute and gate the score
- artifacts are written to the expected `.data/ai-api` path
- a single model failure does not cancel the full run
- reruns produce stable structure and comparable scores

Recommended smoke tests:

- one architecture case against two models
- one coding fixture against two models
- one full lane run with all 14 models in dry-run mode

---

## Risks

- **Benchmark drift:** if prompts are not frozen, scores will be noisy.
- **Overfitting to prompt style:** term-based scoring can reward formatting instead of substance.
- **Coding false positives:** if hidden tests are too weak, a model can game the task.
- **Transport noise:** route differences can distort latency comparisons, so latency should be reported separately from quality.
- **State leakage:** coding tasks must run in isolated temp copies or results will contaminate each other.

Mitigations:

- freeze prompt packs
- keep test fixtures small and explicit
- score quality and latency separately
- isolate each coding run in a fresh workspace copy

---

## Open Questions

1. Do we want the first version to expose this as a new `ai-api` script, a new `ai-cli` subcommand, or both?
2. Should the 14-model list be hard-coded in a checked-in profile file or loaded from a Bifrost/provider manifest?
3. Do we want coding fixtures to live inside the plugin tree, or under a separate repo-local benchmark folder?

