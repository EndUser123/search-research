# Provider-Neutral Routing Validation and Refinement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the research router against representative real decision shapes and refine only rules that cause observed unnecessary manual selection, stale-state use, redundant lanes, or authority-boundary errors.

**Architecture:** Keep `router.py` pure. Expand its input contract with explicit runtime-state freshness, evidence sufficiency, prior attempts, and escalation signals. Store a small JSON corpus with expected decisions and run it through the router without invoking any provider.

**Tech Stack:** Python standard library, JSON, pytest.

## Global Constraints

- Do not invoke `agy` or add a provider execution broker.
- Do not add automatic fallback or broad provider inventory.
- Unknown or stale readiness is never active.
- MMX may be automatic only when a caller supplies fresh healthy state and the task needs bounded external discovery.
- `agy` remains restricted advisory; a recorded advisory role is distinct from human approval or explicit lane selection.
- Existing evidence or a prior failed lane remains visible and affects the next recommendation.
- Human escalation is returned as data only; the router never asks, approves, or executes.

---

### Task 1: Add adaptive state and decision semantics

**Files:**
- Modify: `P:/tools/research_run_v1/router.py`
- Modify: `P:/tests/research_run_v1/test_router.py`

- [ ] Add explicit readiness state, observation time/expiry, quota reserve, attempted/failed lanes, evidence sufficiency, recorded role, agent selection, and human-escalation signals.
- [ ] Make MMX automatic only with fresh healthy state and an external-discovery signal.
- [ ] Allow restricted `agy` recommendation when the advisory role is recorded, without requiring per-call human approval or lane selection.
- [ ] Reject stale/unknown state, provenance-dependent `agy` use, authority-bearing use, sensitive/write use, and below-reserve quota.
- [ ] Preserve explicit rejection reasons and failed-lane visibility.
- [ ] Run focused tests before corpus evaluation.

### Task 2: Build and run the representative corpus

**Files:**
- Create: `P:/tests/research_run_v1/router_corpus.json`
- Create: `P:/tools/research_run_v1/evaluate_router.py`
- Create: `P:/tests/research_run_v1/test_router_corpus.py`

- [ ] Include 14 cases covering local history, repository inspection, current lookup, documentation discovery, primary verification, fixed-corpus synthesis, adversarial review, one-lane sufficiency, two-lane need, redundant second lane, degraded quota, unready provider, restricted agy, provider failure, and already-sufficient evidence.
- [ ] Record signals, provider state, expected recommendation, rejection rationale, escalation, and stop condition for each case.
- [ ] Run the corpus evaluator and preserve its JSON output under `P:/tmp/.codex/state/` without overwriting prior evidence.

### Task 3: Compare policy-only, prior router, and refined router

**Files:**
- Modify: `P:/docs/research-run-v1.md`

- [ ] Report actual corpus outcomes and qualitative baseline differences.
- [ ] Do not claim statistical improvement; report observed defects and unresolved cases.
- [ ] Document that routing remains recommendation-only and provider execution remains deferred.
- [ ] Run the full research-run test suite and syntax verification.
