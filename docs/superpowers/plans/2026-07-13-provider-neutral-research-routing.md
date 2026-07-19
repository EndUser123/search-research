# Provider-Neutral Research Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, provider-neutral dry-run governor that recommends eligible research lanes without invoking providers or granting authority.

**Architecture:** Add a small pure-Python routing module next to `research-run.v1`. It will consume explicit capability records and task signals, apply hard exclusions and circuit states, then return an explainable ordered recommendation plus rejected lanes. It will not own provider commands, credentials, quota polling, source verification, or automatic fallback.

**Tech Stack:** Python 3 standard library, JSON-compatible dataclasses, pytest, existing `research-run.v1` documentation.

## Global Constraints

- Preserve the existing `research-run.v1` artifact contract and validator.
- Do not invoke providers, modify provider configuration, or add automatic fallback.
- Keep `agy` `RESTRICTED` and eligible only for explicit advisory roles.
- Treat configured-but-unready providers as ineligible.
- Treat quota data as an input; never infer quota availability from provider presence.
- Return transparent reasons for every rejection and recommendation.
- Avoid fake numerical optimization; use hard gates and deterministic ordered preferences.
- Preserve unrelated dirty workspace changes.

---

### Task 1: Add the routing decision model

**Files:**
- Create: `P:/tools/research_run_v1/router.py`
- Test: `P:/tests/research_run_v1/test_router.py`

**Interfaces:**
- `CapabilityRecord` describes one lane’s role, independence group, readiness, circuit, quota reserve, and capabilities.
- `TaskSignals` describes the missing information and authorization boundary.
- `recommend(signals, capabilities) -> RoutingRecommendation` returns ordered eligible lanes and explicit rejections.

- [ ] **Step 1: Write failing tests** for local-first routing, unavailable-provider rejection, restricted agy gating, redundant second-lane suppression, and quota-reserve rejection.
- [ ] **Step 2: Run `pytest -q P:/tests/research_run_v1/test_router.py` and confirm the new imports/functions fail.**
- [ ] **Step 3: Implement immutable dataclasses and deterministic gate order:** circuit `OPEN` rejects; readiness/authentication rejects; quota below reserve rejects; sensitivity/write/authority gates reject; agy requires explicit advisory role and evidence gathering only; otherwise rank by task fit and stable preference.
- [ ] **Step 4: Run the focused router tests and confirm they pass.**
- [ ] **Step 5: Review the diff for provider commands, credentials, fallback, or hidden side effects; remove any if present.**

### Task 2: Add representative capability inventory and documentation

**Files:**
- Modify: `P:/docs/research-run-v1.md`
- Test: `P:/tests/research_run_v1/test_router.py`

**Interfaces:**
- `default_capabilities()` returns records for local inspection, harness-native web, MMX, NotebookLM, and agy with conservative evidence-based states.

- [ ] **Step 1: Add tests asserting the default inventory marks local/native web as available candidates, MMX/NotebookLM as capability-only unless readiness is supplied, and agy as restricted/manual.**
- [ ] **Step 2: Implement `default_capabilities()` with no network probes and no credentials.**
- [ ] **Step 3: Document the recommendation schema, gate order, circuit states, and explicit non-goals in `research-run.v1`.**
- [ ] **Step 4: Run the complete research-run test directory.**

### Task 3: Verify the vertical slice and hand off authorization

**Files:**
- No additional source files.

- [ ] **Step 1: Run `pytest -q P:/tests/research_run_v1`.**
- [ ] **Step 2: Run a read-only Python smoke check that recommends a local lane for a local-context task and rejects agy for an ordinary automatic task.**
- [ ] **Step 3: Inspect `git diff -- P:/tools/research_run_v1 P:/tests/research_run_v1 P:/docs/research-run-v1.md P:/docs/superpowers/plans/2026-07-13-provider-neutral-research-routing.md`.**
- [ ] **Step 4: Record measured limitations: no provider invocation, no live readiness refresh, no quota delta measurement, no source verification, and no automatic execution.**
