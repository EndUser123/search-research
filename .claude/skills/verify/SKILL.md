---
name: verify
description: Verification orchestrator - 4-tier workflow (checklist -> component -> integration -> e2e) with contract verification, Contract Authority Packet consumption, fast-fail Tier 0, and post-hoc verification mode
version: "1.2.0"
status: stable
category: verification
triggers:
  - /verify
  - /verify <target>
  - /verify skill:<skillname>
  - /verify hook:<hookname>
  - /verify feature:<featurename>
  - /verify --deep-lens <target>
  - /verify --adversarial <target>
  - /verify --full-state <target>
  - /verify --contracts <target>
  - /verify --post-hoc
  - /verify --post-hoc --plan <plan_path>
aliases:
  - /verify
  - /verify skill:arch
  - /verify hook:breadcrumb_init
  - /verify feature:e2e
  - /verify --deep-lens skill:code
  - /verify --adversarial skill:arch
  - /verify --full-state hook:init
  - /verify --contracts hook:resume
  - /verify --post-hoc --plan .claude/plans/plan-20260313-example.md
workflow_steps:
  - detect_verification_mode
  - if post_hoc_mode:
    - load_chat_history_artifacts
    - generate_rtm
    - calculate_tsr
    - evaluate_conversation_completeness
    - generate_post_hoc_report
  - else:
    - detect_verification_target
    - run_tier0_checklist_verification
    - run_tier1_component_tests
    - run_tier2_integration_check
    - run_tier3_e2e_test
    - run_contract_integrity_check
    - generate_verification_report
suggest:
  - /search (integrated - pre-verification context discovery)
  - /trace (deep manual verification)
  - /testing-skills (skill QA)
  - /plan-workflow (plan creation and RTM validation)
  - /code (implementation with TSR tracking)

do_not:
  - claim "verified" without running all 4 tiers (real-time mode)
  - claim "verified" without meeting TSR >= 95% threshold (post-hoc mode)
  - skip Tier 0 (checklist) or Tier 3 (e2e) execution evidence
  - generate report without evidence from each tier
  - use post-hoc mode without plan artifact
---

# /verify - Verification Orchestrator

## Purpose

Unified 4-tier verification workflow combining automated testing and manual verification. **Verify before you trust.** All four tiers must pass for "verified" status.

For hook, handoff, resume, artifact, and multi-terminal workflows, verification also requires explicit contract-integrity proof.

### What This Solves

Skills/hooks/features pass component tests but fail in production due to configuration issues, integration breaks, or E2E failures.

Another recurring failure mode is producer-only proof: the producer writes an artifact or payload, but the real consumer never validates or successfully uses it.

**Solution**: 4-tier verification with evidence at each level:

| Tier | Name | What | Speed |
|------|------|------|-------|
| 0 | Checklist | Fast-fail config/structure check | Seconds |
| 1 | Component | Unit tests (pytest) | Seconds |
| 2 | Integration | Hook chain, router execution | Seconds |
| 3 | E2E | Actual skill/workflow invocation | Seconds-minutes |

## Quick Start

```bash
/verify skill:arch           # Verify a skill
/verify hook:breadcrumb_init # Verify a hook
/verify feature:e2e          # Verify a feature
/verify src/handoff.py       # Verify code file (component tests only)
/verify --post-hoc --plan .claude/plans/plan-example.md  # Post-hoc verification
```

**Target type detection**: `skill:name` -> SKILL.md, `hook:name` -> hook .py, `feature:name` -> workflow, bare path -> code file.

## Workflow Overview

### Real-Time Mode (4-Tier)

1. **Search for context** - Find related work before verifying (`/search`)
2. **Detect target** - Parse input to determine skill/hook/feature/code
3. **Tier 0: Checklist** - Fast-fail structural verification (stops on failure)
4. **Tier 1: Component** - pytest unit tests
5. **Tier 2: Integration** - Hook/router chain execution
6. **Tier 3: E2E** - Actual skill/workflow invocation
7. **Contract Integrity Check** - Producer/consumer boundary proof for required targets
8. **Generate RSN report** - Findings as Recommended Next Steps (only if issues found)

See `references/tier-workflow.md` for detailed commands, code examples, and expected output per tier.
See `references/rsn-reporting.md` for RSN formatter usage and output format.

### Post-Hoc Mode

Analyzes **completed work** through artifacts using LLM-as-Judge approach.

**Key Metrics**:
- **RTM**: Requirements Traceability Matrix (requirements -> tasks mapping, coverage %)
- **TSR**: Task Success Rate (completed/attempted x 100, threshold >= 95%)
- **LLM-as-Judge**: Conversation completeness score (0-100)

**PASS when**: TSR >= 95%, requirements coverage = 100%, acceptance criteria coverage = 100%, overall score >= 95.

See `references/post-hoc-verification.md` for workflow details, pass/fail criteria, and report format.

## Advanced Flags

| Flag | Purpose | Detail |
|------|---------|--------|
| `--deep-lens` | 6-lens code review | State, identity, I/O, concurrency, errors, tests |
| `--adversarial` | 7+1 agent stress test | Parallel adversarial agents + meta-analyst |
| `--full-state` | Source->Logic->Read verification | Detect silent write failures, stale state |
| `--contracts` | Boundary contract verification | Required fields, consumer validation, freshness, stale rejection |

**Combinations**: `--deep-lens --adversarial skill:arch` | `--deep-lens --full-state skill:code` | All three.

See `references/advanced-flags.md` for full details, agent descriptions, combining flags, and performance expectations.

## Multi-Agent Strategy

Different agents per tier to reduce same-model bias: Tier 0 = lead model, Tier 1 = pytest (tool), Tier 2 = /testing-skills subagent, Tier 3 = /trace subagent + manual.

See `references/multi-agent-strategy.md` for agent assignments, bias reduction strategy, and when multi-agent matters most.

## Validation Rules

### Prohibited Actions

- Skip tiers or fake evidence
- Hide failures or claim "verified" prematurely
- Use post-hoc mode without plan artifact

### Required Checks

- Tier 0: Verify checklist completeness before running tests
- Tier 1: Show pytest output with pass/fail counts
- Tier 2: Verify hook chain executes without exceptions
- Tier 3: Demonstrate actual skill/workflow invocation
- Contract check: verify producer fields, consumer expectations, stale rejection, and failure behavior for missing required fields
- After any tier fails: Document specific failure and fix recommendation

### Contract Verification Mode

Use `--contracts` or apply contract verification automatically when the target touches:

- handoff envelopes
- resume/restore paths
- evidence or plan artifacts
- hook/router payloads
- provider/session/transcript projections
- multi-terminal shared state

Required proof:

1. Producer emits the required fields.
2. Consumer explicitly validates or depends on those fields.
3. Missing required fields fail in the intended way.
4. Stale or superseded artifacts are rejected or invalidated in the intended way.
5. Transcript/workspace truth beats stale summary state where applicable.
6. If a `Contract Authority Packet` exists, runtime behavior matches its schema/version, freshness authority, invalidation semantics, transcript-vs-artifact precedence, and declared failure behavior.

For contract-sensitive targets, missing or stale `Contract Authority Packet` input is itself a verification failure unless `/arch` explicitly classified the work as not requiring one.

### Quality Levels

| Level | Criteria |
|-------|----------|
| VERIFIED | All 4 tiers pass with evidence, plus contract proof when applicable |
| PARTIAL | 1-3 tiers pass, document gaps |
| FAILED | 0-2 tiers pass or critical failure |

## Constitution Alignment

- **PART T (Truthfulness)**: Report all failures honestly
- **PART P (Testing Workflow)**: Systematic validation required
- **PART L (Success Protocol)**: Do not claim "verified" without evidence

## Routing Behavior

`/verify` proves or disproves behavior. It should route rather than absorb other ownership domains:

- suggest `/arch` when failures are architectural or contract-design failures
- suggest `/planning` when the plan artifact, contract matrix, or packet consumption is insufficient
- suggest `/code` when the issue is a concrete implementation defect

`/verify` may fail the target and recommend the owning skill, but it must not silently redesign architecture or rewrite plans.

## Response Format

All responses MUST be prefixed with `[VERIFY]`.

## Dependencies

- `evidence_store.py` (TASK-000): Session-scoped evidence storage
- `StopHook_unverified_stance.py` (TASK-002): Completion claim verification
- `PostToolUse_e2e_tracker.py` (TASK-003): E2E workflow tracking
- `/trace skill`: Deep manual verification
- `/testing-skills`: Skill QA

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill definition (this file) |
| `__main__.py` | Entry point with CLI argument parsing |
| `core/verifier.py` | Core verification orchestration (includes post-hoc) |
| `tiers/tier0_checklist.py` | Tier 0: Checklist verification |
| `tiers/tier1_component.py` | Tier 1: Component test runner |
| `tiers/tier2_integration.py` | Tier 2: Integration checker |
| `tiers/tier3_e2e.py` | Tier 3: E2E test runner |
| `tiers/post_hoc_analyzer.py` | Post-hoc verification analyzer |
| `report.py` | Verification report generator |
| `tests/test_verify.py` | Unit tests |
| `tests/test_post_hoc.py` | Post-hoc unit tests |
| `tests/test_integration.py` | Integration tests |
| `tests/test_integration_post_hoc.py` | Post-hoc integration tests |

## Reference Files

| File | Content |
|------|---------|
| `references/tier-workflow.md` | Detailed tier commands, code, expected output |
| `references/rsn-reporting.md` | RSN formatter usage and output format |
| `references/post-hoc-verification.md` | Post-hoc workflow, metrics, pass/fail criteria |
| `references/advanced-flags.md` | --deep-lens, --adversarial, --full-state details |
| `references/multi-agent-strategy.md` | Agent assignments and bias reduction |
| `references/troubleshooting.md` | Common issues and solutions |
| `references/changelog.md` | Version history |
