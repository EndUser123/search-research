---
title: "Skill pipeline integration testing — orchestrator skills must be tested end-to-end"
created: 2026-08-07
source: session-019fd9ae-d977-70a2-803c-9b4d139d1303 (ship-py v2.0/v2.1 integration test)
sources:
  - Session 019fd9ae ship-py integration test (5 break points found)
  - Session 019fd9ae /tp root-cause analysis (4 root causes)
tags: [skill-design, integration-testing, orchestrator-skills, contract-drift, silent-pass, end-to-end, quality-gate]
summary: >
  Skills that orchestrate other skills (ship-py, /go, /close) must be
  integration-tested end-to-end — not just unit-tested for phase gates.
  The break points found in ship-py v2.0 (schema mismatches between
  expected JSON and actual tool output, dead-end paths where verdicts
  can't advance, silent-pass gaps where phases pass with empty data,
  cross-skill dependency fragility) are all integration-layer issues
  that unit tests cannot catch. Unit tests verify state-machine ordering;
  integration tests verify that the data contracts between phases
  actually match reality. The detection method is simple: run the full
  pipeline on a real (small) change and fix what breaks. This concept
  documents the 4 root causes, the integration test checklist, and the
  relationship to existing patterns.
agent: grok
host: grok
cognitive_load: 2
verification: observed
tier: warm
half_life_days: 180
relations:
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md
    type: extends — that concept covers producer-consumer field drift; this covers the integration test that detects it
  - target: wiki/concepts/done-trigger-fires-on-artifact-creation-not-integration.md
    type: example — ship-py v2.0 was declared done after unit tests passed, but integration testing found 5 break points
  - target: wiki/concepts/skill-pipeline-integration-testing.md
    type: self
---

# Skill pipeline integration testing

## Decision context

**Why this knowledge was needed:** ship-py v2.0 was built with 25 unit tests
all passing. The unit tests verify the state machine (phase ordering, gates,
verdict derivation). But when the pipeline was run end-to-end on a real
change, 5 break points emerged that no unit test caught:

1. **Schema mismatch** (refactor-scan): expected `{p0_count, p1_count, p2_count}` from /refactor --dry-run, but code_analysis.py produces `{summary: {dead_code_items, complexity_hotspots, cycles, test_gaps}}` — completely different field names.
2. **Path mismatch** (skill-dev): passed SKILL.md path to script_scan.py, but script_scan.py expects the skill directory. Result: every skill reported "SKILL.md not found."
3. **Silent pass** (check, risk): when no findings file is provided, both phases silently pass with zero findings instead of blocking.
4. **Dead-end path** (already_shipped): detect produces a 3-option menu that dead-ends — the pipeline can't continue.
5. **Verdict incompatibility** (SHIP VERIFIED → merge): post-commit mode produces SHIP VERIFIED, but merge only accepts SHIP DONE.

All 5 are integration-layer issues. Unit tests can't find them because they
test each phase in isolation. The break points live in the **seams between
phases** — the data contracts, the path conventions, the silent-default
behaviors.

## The 4 root causes

### 1. No skill validates integration contracts between skills

Each quality skill tests its own scope: `/skill-dev` checks static properties
(paths, frontmatter, version). `/check` verifies session claims. `/review`
finds code bugs. None validates the **integration layer** — the seams where
skills call each other, the data contracts between phases, the end-to-end
pipeline behavior.

### 2. Known-debt items have no automatic escalation

The `/tp {3}` panel identified `_check_ship_py_state` as rationalization
debt. It was documented in the handoff's Execution Status. But no skill
promoted it from "documented" to "actionable" without operator intervention.
Known debt sits until the operator manually says "fix them all."

### 3. Dead-end paths are invisible until exercised at runtime

Static analysis can't find dead-end paths. Unit tests don't exercise them
(they cover state-machine ordering, not "what happens when the pipeline runs
in post-commit mode"). The only way to find them is to **run the full
pipeline on real work**.

### 4. Cross-skill runtime path dependencies are undocumented contracts

Ship-py depended on `ship-rhai/__lib/ship_receipt.py` via a hardcoded path.
The `depends_on` frontmatter listed ship-rhai, but nothing validated that
the runtime path matched. If ship-rhai is renamed, ship-py breaks silently.

## Detection method: run the pipeline end-to-end

The integration test is not a separate framework — it IS the pipeline
itself. The procedure:

1. Create a small, real change (a README addition, a `__version__` bump)
2. Commit it (so the pipeline has work to detect)
3. Run each phase in sequence
4. Fix what breaks
5. Record the wall-clock time per phase

This is the **bootstrap pattern**: an orchestrator skill must be run on
itself (or on a small test change) before it can be declared done.

### Integration test checklist for orchestrator skills

- [ ] **Detect produces non-empty output** — file-type routing fires, pre_review_phases is populated
- [ ] **Each phase either produces evidence or blocks** — no silent-pass with empty data
- [ ] **Each phase's expected JSON schema matches the actual producer's output** — grep the producer's output for the expected field names
- [ ] **Every terminal path produces a valid verdict** — no dead-ends where the pipeline can't continue
- [ ] **Cross-skill dependencies use `__file__`-relative paths** — no hardcoded paths to other skills' directories
- [ ] **Post-commit mode (already_shipped) routes through the full pipeline** — not a dead-end menu
- [ ] **The verdict output is consumable by /todo** — structured findings, not just counts

## Relationship to existing patterns

- **[[producer-consumer-contract-drift-in-skill-chains]]:** that concept
  documents the anti-pattern (producer writes fields consumers don't read).
  This concept is the integration test that detects it — run the pipeline,
  and the schema mismatch surfaces immediately.
- **[[done-trigger-fires-on-artifact-creation-not-integration]]:** that
  concept documents declaring done when an artifact is created but not
  wired in. Ship-py v2.0 was declared done after 25 unit tests passed.
  The integration test found 5 break points. The "structural test" from
  that concept applies: "what would I do differently if the artifact
  didn't exist yet?" — for ship-py, the answer was "run the pipeline."
- **[[verification-claim-admissibility]]:** integration tests sit between
  unit tests (Component_PROVEN) and live deployment (LIVE_NOT_PROVEN).
  An integration-tested orchestrator is `COMPONENT_PROVEN — LIVE_NOT_PROVEN`,
  not `PROVEN`.

## What this means for our workspace

1. **Orchestrator skills (ship-py, /go, /close) need an integration test
   step in their lifecycle.** Not a separate testing framework — the
   integration test IS running the pipeline. The skill's SKILL.md should
   document how to run it.
2. **`/skill-dev` should add Check 11: inter-skill contract validation.**
   For orchestrator skills, grep the expected JSON field names against
   the producer skill's actual output. Zero matches = contract drift risk.
3. **The "silently pass with empty data" failure mode is the highest-
   priority detection target.** Every phase in an orchestrator must either
   produce real evidence or block with a clear message. Silent-pass is
   worse than block — it creates false confidence.

## Falsifier

This concept is wrong if:
- The integration test break points were one-off issues unique to ship-py
  (not a general pattern) — future orchestrator skills would pass without
  integration testing
- The contract drift detection produces too many false positives — the
  check becomes noise and gets disabled
- The end-to-end test is too slow to run routinely — the pipeline takes
  too long and gets skipped

## Receipts

- Ship-py integration test output (session 019fd9ae): 5 break points found and fixed
- Ship-py v2.1 commit (c8e50e0): all 8 gaps fixed, 72/72 tests pass
- `/tp {3}` panel output (session 019fd9ae): 2/3 lenses converged on "hardcoded check is rationalization"

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[mermaid-and-code-visualization-skills-landscape]]
- [[claude-code-skills-and-mcp-integration]]

